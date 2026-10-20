"""Finite controls for exact recorded aliasing and joint-premise induction.

These controls validate new checker semantics, not full sequential equivalence.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
import time

from lec_onehot_boolean import ROOT, DAG, enforce_process_memory, sha
from lec_joint_invariant import (alias_cofactor, assess, effective_q, evaluate_raw,
                                 joint_predicate, nonvacuity, recheck_counterexample,
                                 satisfies_joint)


def fixture():
    names = ["reset_n", "lec_q_p19088", "lec_q_p19089", "lec_q_g00056",
             "lec_q_g00000", "lec_q_p00000", "lec_q_p00001", "lec_q_p00002",
             "lec_q_p00003", "lec_q_p00004", "unreset_memory_q"]
    graph = {"inputs": len(names), "input_names": names, "ands": [],
             "output_names": ["lec_d_g00056", "lec_d_g00000", "lec_d_p00000",
                              "lec_d_p00001", "lec_d_p00002", "lec_d_p00003",
                              "lec_d_p00004", "unreset_D"],
             "outputs": [2 * (i + 1) for i in (3, 4, 5, 6, 7, 8, 9, 10)]}
    info = {"constants": {"lec_q_g00056": 0},
            "duplicate_aliases": {"lec_q_g00000": "lec_q_p00000"},
            "onehot_groups": [
                {"name": "fixture_a", "Q": ["lec_q_p00001", "lec_q_p00002"],
                 "D": ["lec_d_p00001", "lec_d_p00002"]},
                {"name": "fixture_b", "Q": ["lec_q_p00003", "lec_q_p00004"],
                 "D": ["lec_d_p00003", "lec_d_p00004"]}]}
    return graph, info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--cnf-controls", required=True)
    args = parser.parse_args()
    out, cnf_controls = Path(args.out).resolve(), Path(args.cnf_controls).resolve()
    if out.exists() or not out.is_relative_to(ROOT) or not cnf_controls.is_relative_to(ROOT):
        raise ValueError("New research control receipt required")
    memory = enforce_process_memory()
    cnf = json.loads(cnf_controls.read_text())
    if cnf["status"] != "PASS_BOUNDED_CNF_CHECKER_CONTROLS":
        raise ValueError("Successful frozen CNF controls required")
    for rel, digest in cnf["source_sha256"].items():
        if sha(ROOT / rel) != digest:
            raise ValueError("Frozen CNF source changed")
    paths = [ROOT / p for p in ("scripts/verification/check_lec_joint_invariant.py",
                               "scripts/verification/lec_joint_invariant.py",
                               "scripts/verification/lec_onehot_sat.py",
                               "scripts/verification/lec_onehot_boolean.py",
                               "scripts/verification/lec_reset_base.py")]
    paths.append(cnf_controls)
    hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    rows = []

    def record(name, **detail):
        rows.append({"name": name, "status": "PASS", **detail})

    def reject(name, function):
        try:
            function()
        except ValueError:
            record(name, actual_rejection="ValueError")
        else:
            raise ValueError("Unsound fixture accepted: " + name)

    graph, info = fixture()
    conditions = {"reset_n": 1, "lec_q_p19088": 1, "lec_q_p19089": 1}
    assignments = {**conditions, **info["constants"]}
    aliases = info["duplicate_aliases"]
    dag = DAG(graph["inputs"], time.monotonic() + 10)
    outputs = alias_cofactor(dag, graph, assignments, aliases, aliases)
    if outputs["lec_d_g00056"] != 0 or outputs["lec_d_g00000"] != outputs["lec_d_p00000"] or \
            outputs["unreset_D"] != 2 * graph["inputs"]:
        raise ValueError("Alias cofactor either misses recorded invariant or changes free state")
    for bits in itertools.product((0, 1), repeat=6):
        full = dict.fromkeys(graph["input_names"], 0)
        full.update(assignments)
        full.update(dict(zip(graph["input_names"][5:], bits)))
        full["lec_q_g00000"] = full["lec_q_p00000"]
        original = evaluate_raw(graph, full)
        numeric = {i: full[name] for i, name in enumerate(graph["input_names"])}
        if any(dag.evaluate(literal, numeric) != original[name] for name, literal in outputs.items()):
            raise ValueError("Recorded substitution differs from original graph under equality premise")
    record("Exact recorded substitution against original graph", truth_assignments=64,
           unrelated_unreset_state_remains_symbolic=True)
    for unreset in (0, 1):
        complete = dict.fromkeys(range(graph["inputs"]), 0)
        complete[graph["inputs"] - 1] = unreset
        if dag.evaluate(outputs["unreset_D"], complete) != unreset:
            raise ValueError("Unreset state was incorrectly zeroed")
    record("Both values of unchanged unreset state", cases=2)

    rejects = [
        ("Unrecorded alias target", aliases, {"lec_q_g00000": "lec_q_p00001"}, assignments),
        ("Nonpaired alias target", {"lec_q_g00000": "unreset_memory_q"},
         {"lec_q_g00000": "unreset_memory_q"}, assignments),
        ("Alias source tied to zero", aliases, aliases, {**assignments, "lec_q_g00000": 0}),
        ("Unknown substitution", aliases, aliases, {**assignments, "not_a_signal": 0}),
        ("Boolean type confusion", aliases, aliases, {**assignments, "reset_n": True}),
        ("Alias cycle", {"lec_q_p00000": "lec_q_p00000"},
         {"lec_q_p00000": "lec_q_p00000"}, assignments),
    ]
    for name, candidate, allowed, fixed in rejects:
        reject(name, lambda candidate=candidate, allowed=allowed, fixed=fixed:
               alias_cofactor(dag, graph, fixed, candidate, allowed))

    premise = joint_predicate(dag, graph, info, assignments)
    witnessed = nonvacuity(graph, info, conditions)
    if not witnessed["joint_premise_satisfiable"]:
        raise ValueError("Nonvacuity witness missing")
    truth_cases = 0
    for bits in itertools.product((0, 1), repeat=4):
        numeric = dict.fromkeys(range(graph["inputs"]), 0)
        numeric.update(dict(zip(range(6, 10), bits)))
        expected = int(sum(bits[:2]) == 1 and sum(bits[2:]) == 1)
        if dag.evaluate(premise, numeric) != expected:
            raise ValueError("Joint one-hot predicate differs from exhaustive independent truth table")
        truth_cases += 1
    record("Exact simultaneous group premise", truth_assignments=truth_cases)
    reject("Contradictory selected group code is not vacuous PASS",
           lambda: nonvacuity(graph, info, {**conditions, "lec_q_p00001": 0, "lec_q_p00002": 0}))
    positive = assess(dag, premise, dag.onehot_violation(
        [outputs["lec_d_p00001"], outputs["lec_d_p00002"]]))
    if positive["decision"]["status"] not in ("PROVED_STRUCTURAL_COFACTOR", "PROVED_BOOLEAN_CNF"):
        raise ValueError("Identity next-state code does not preserve joint invariant")
    record("Joint legal identity transition", verdict=positive["decision"]["status"])

    bad_graph = {**graph, "outputs": list(graph["outputs"])}
    bad_graph["outputs"][3:5] = [1, 1]
    bad_dag = DAG(graph["inputs"], time.monotonic() + 10)
    bad_outputs = alias_cofactor(bad_dag, bad_graph, assignments, aliases, aliases)
    bad_premise = joint_predicate(bad_dag, bad_graph, info, assignments)
    negative = {"kind": "onehot", "D": ["lec_d_p00001", "lec_d_p00002"],
                **assess(bad_dag, bad_premise, bad_dag.onehot_violation(
                    [bad_outputs["lec_d_p00001"], bad_outputs["lec_d_p00002"]]))}
    if negative["decision"]["status"] != "DISPROVED_UNDER_RECORDED_ASSUMPTIONS":
        raise ValueError("Mutated transition requires actual SAT, not UNKNOWN or missing output")
    recheck_counterexample(bad_graph, info, conditions, negative)
    if negative["original_raw_D_at_counterexample"] != [1, 1] or \
            not negative["counterexample_satisfies_every_joint_premise"]:
        raise ValueError("Actual fixture counterexample not reproduced with all joint premises")
    record("Counterexample satisfies every joint premise", bad_D_code=[1, 1])

    malformed = {**negative, "decision": {**negative["decision"], "counterexample": {
        graph["input_names"].index("lec_q_p00001"): 0,
        graph["input_names"].index("lec_q_p00002"): 0}}}
    reject("A raw witness violating the premise is rejected",
           lambda: recheck_counterexample(bad_graph, info, conditions, malformed))
    reject("Incomplete original-graph witness is rejected", lambda: evaluate_raw(graph, {}))
    expired = DAG(1, time.monotonic() - 1)
    unknown = assess(expired, 1, 2)
    if unknown["decision"]["status"] != "UNKNOWN" or unknown["decision"]["reason"] != "TIME_BOUND":
        raise ValueError("Expired structural case cannot pass")
    record("Structural deadline is UNKNOWN", actual=unknown["decision"]["status"])

    if any(sha(ROOT / rel) != digest for rel, digest in hashes.items()):
        raise ValueError("Joint/CNF checker changed during controls")
    receipt = {"status": "PASS_JOINT_INVARIANT_CHECKER_CONTROLS",
               "source_sha256": hashes, "memory_enforcement": memory,
               "control_count": len(rows), "controls": rows,
               "scope": "Finite new cofactor/alias/joint-premise checker controls; frozen CNF controls separately required; actual raw-model fault control separately required"}
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print("PASS:", len(rows), "joint invariant checker controls")


if __name__ == "__main__":
    main()
