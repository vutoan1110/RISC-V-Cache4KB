"""Meaningful positive, semantic-fault and resource gates for bounded ROBDDs."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import time

from lec_onehot_boolean import (ROOT, BDD, DAG, BoundReached, case_conditions,
                                decide, enforce_process_memory, sha)


def controls():
    records = []

    def checked(name, result, expected):
        if result["status"] != expected:
            raise AssertionError((name, result, expected))
        records.append({"name": name, "expected": expected, "actual": result["status"],
                        "witness_original_DAG_evaluation":
                        result.get("counterexample_original_DAG_evaluation"),
                        "scope": "Checker fixture, not a chip measurement"})

    def dag(n=3):
        return DAG(n, time.monotonic() + 5)

    a = dag()
    x, y, z = 2, 4, 6
    # The two forms require Boolean distributivity, not only AIG hash identities.
    distributed = a.OR(a.AND(x, y), a.AND(x, y ^ 1))
    checked("distributivity_onehot_positive", decide(a, a.onehot_violation([distributed, x ^ 1])),
            "PROVED_BOOLEAN_COFACTOR")
    a = dag()
    left = a.AND(x, a.OR(y, z))
    right = a.OR(a.AND(x, y), a.AND(x, z))
    difference = a.OR(a.AND(left, right ^ 1), a.AND(left ^ 1, right))
    checked("independent_distributivity_positive", decide(a, difference),
            "PROVED_BOOLEAN_COFACTOR")
    checked("constant_valid_code_positive", decide(dag(), 0), "PROVED_BOOLEAN_COFACTOR")

    a = dag(24)
    rare = 1
    for i in range(24):
        rare = a.AND(rare, 2 * (i + 1))
    result = decide(a, a.onehot_violation([1, rare]))
    checked("rare24_duplicate_code_negative", result, "DISPROVED_UNDER_RECORDED_ASSUMPTIONS")
    if result["counterexample"] != {i: 1 for i in range(24)}:
        raise AssertionError("Rare fault requires the exact all-ones witness")
    a = dag(24)
    rare = 1
    for i in range(24):
        rare = a.AND(rare, 2 * (i + 1))
    checked("rare24_missing_hot_bit_negative", decide(a, a.onehot_violation([rare ^ 1, 0])),
            "DISPROVED_UNDER_RECORDED_ASSUMPTIONS")
    a = dag()
    checked("ordinary_duplicate_state_negative", decide(a, a.onehot_violation([x, x])),
            "DISPROVED_UNDER_RECORDED_ASSUMPTIONS")
    checked("allzero_state_negative", decide(dag(), 1), "DISPROVED_UNDER_RECORDED_ASSUMPTIONS")

    a = dag()
    checked("support_limit_unknown", decide(a, a.AND(x, y), max_support=1), "UNKNOWN")
    a = dag()
    checked("node_limit_unknown", decide(a, x, max_nodes=0), "UNKNOWN")
    a = dag()
    checked("apply_cache_limit_unknown", decide(a, a.AND(x, y), max_cache=0), "UNKNOWN")
    a = DAG(3, time.monotonic() - 1)
    checked("time_limit_unknown", decide(a, x), "UNKNOWN")

    # Cross-check the entire BDD kernel against direct Python Boolean formulas.
    b = BDD([0, 1, 2, 3], time.monotonic() + 5)
    bs = [b.var(i) for i in range(4)]
    formulas = [(b.apply("and", bs[0], bs[1]), lambda q: q[0] & q[1]),
                (b.NOT(bs[0]), lambda q: 1 - q[0]),
                (b.apply("xor", bs[0], bs[1]), lambda q: q[0] ^ q[1]),
                (b.apply("and", b.NOT(b.apply("and", bs[0], bs[1])),
                         b.apply("xor", bs[2], bs[3])),
                 lambda q: (1 - (q[0] & q[1])) & (q[2] ^ q[3]))]
    for assignment in itertools.product((0, 1), repeat=4):
        for root, expected in formulas:
            node = root
            while node >= 2:
                rank, low, high = b.nodes[node]
                node = high if assignment[rank] else low
            if node != expected(assignment):
                raise AssertionError("BDD differs from independent Boolean truth table")
    records.append({"name": "full_kernel_truth_tables", "actual": "PASS",
                    "formula_count": 4, "assignments_per_formula": 16,
                    "scope": "Independent Python truth functions versus BDD traversal"})

    def reject(name, fn):
        try:
            fn()
        except ValueError:
            records.append({"name": name, "actual": "REJECTED",
                            "scope": "Checker integrity rejection, not semantic chip failure"})
        else:
            raise AssertionError("Missing rejection: " + name)

    reject("empty_output_group", lambda: dag().onehot_violation([]))
    reject("unbound_witness_input", lambda: dag().evaluate(x, {}))
    reject("unsupported_operation", lambda: b.apply("or", bs[0], bs[1]))
    reject("zero_has_no_witness", lambda: b.witness(0))
    graph = {"input_names": ["reset_n", "lec_q_p19088", "lec_q_p19089", "lec_q_p00000"]}
    pairs = {"gold": [{}], "gate": [{}], "pairs": [[0, 0]], "gold_only": [], "gate_only": []}
    group = {"gold": [0]}
    reset = {"reset_n": 1, "lec_q_p19088": 1, "lec_q_p19089": 1}
    conditions = case_conditions(graph, pairs, group, 0, reset)
    if conditions != {**reset, "lec_q_p00000": 1}:
        raise AssertionError("Unexpected extra premise in accepted cofactor")
    records.append({"name": "exact_reset_and_own_group_only", "actual": "PASS"})
    reject("extra_constant_tying", lambda: case_conditions(graph, pairs, group, 0,
           {**reset, "lec_q_g00088": 0}))
    reject("wrong_reset_polarity", lambda: case_conditions(graph, pairs, group, 0,
           {**reset, "reset_n": 0}))
    reject("empty_current_group", lambda: case_conditions(graph, pairs, {"gold": []}, 0, reset))
    reject("duplicate_current_group_bit", lambda: case_conditions(graph, pairs, {"gold": [0, 0]}, 0, reset))
    reject("missing_group_input", lambda: case_conditions({"input_names": graph["input_names"][:-1]},
           pairs, group, 0, reset))
    reject("restricted_onehot_decoder_graph", lambda: case_conditions(
           {"input_names": graph["input_names"] + ["lec_oh_ax0"]}, pairs, group, 0, reset))
    reject("unmapped_group_bit", lambda: case_conditions(graph, pairs, {"gold": [1]}, 0, reset))
    reject("invalid_current_code", lambda: case_conditions(graph, pairs, group, 1, reset))
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if not out.is_relative_to(ROOT) or out.exists():
        raise ValueError("Controls output must be new and in research")
    memory = enforce_process_memory()
    records = controls()
    sources = [Path(__file__), ROOT / "scripts/verification/lec_onehot_boolean.py",
               ROOT / "scripts/verification/lec_reset_base.py"]
    j = {"status": "PASS_BOUNDED_BOOLEAN_CHECKER_CONTROLS", "memory_enforcement": memory,
         "source_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in sources},
         "controls": records, "full_chip_proof": False}
    out.write_text(json.dumps(j, indent=2) + "\n", encoding="ascii")
    print("PASS", len(records), "controls; fixtures are not chip measurements")


if __name__ == "__main__":
    main()
