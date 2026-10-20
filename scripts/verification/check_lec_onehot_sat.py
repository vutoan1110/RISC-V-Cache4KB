"""Independent finite truth-table and negative controls for the CNF checker.

Control results validate this bounded checker, not RTL or sequential LEC.
"""
from __future__ import annotations

import argparse
import copy
import itertools
import json
from pathlib import Path
import random
import time

import lec_onehot_sat as sat
from lec_onehot_boolean import ROOT, DAG, BoundReached, enforce_process_memory, sha


def brute(clauses, variables):
    for bits in itertools.product((0, 1), repeat=variables):
        if all(any(bits[abs(lit) - 1] == int(lit > 0) for lit in clause)
               for clause in clauses):
            return bits
    return None


def checked(clauses, variables):
    solver = sat.Solver(clauses, variables, time.monotonic() + 10)
    result = solver.solve()
    expected = brute(clauses, variables)
    if (result["status"] == "SAT") != (expected is not None):
        raise ValueError("Solver disagrees with exhaustive CNF truth table")
    if result["status"] == "UNSAT":
        sat.verify_resolution(clauses, result["certificate"], result["terminal"],
                              time.monotonic() + 10)
    else:
        assignment = result["assignment"]
        if not all(any(assignment[abs(lit)] == (1 if lit > 0 else -1)
                       for lit in clause) for clause in clauses):
            raise ValueError("SAT assignment does not satisfy original CNF")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if out.exists() or not out.is_relative_to(ROOT):
        raise ValueError("New research control output required")
    memory = enforce_process_memory()
    paths = [ROOT / p for p in ("scripts/verification/lec_onehot_sat.py",
                               "scripts/verification/check_lec_onehot_sat.py",
                               "scripts/verification/lec_onehot_boolean.py",
                               "scripts/verification/lec_reset_base.py")]
    hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    rows = []

    def record(name, detail):
        rows.append({"name": name, "status": "PASS", **detail})

    def reject(name, function):
        try:
            function()
        except ValueError:
            record(name, {"actual_rejection": "ValueError"})
        else:
            raise ValueError("Invalid checker input accepted: " + name)

    # Every subset of every normalized nonempty two-variable clause.
    pool = [(1,), (-1,), (2,), (-2,), (1, 2), (1, -2), (-1, 2), (-1, -2)]
    counts = {"SAT": 0, "UNSAT": 0}
    for mask in range(1 << len(pool)):
        clauses = [list(pool[i]) for i in range(len(pool)) if mask & (1 << i)]
        result = checked(clauses, 2)
        counts[result["status"]] += 1
    record("All 256 two-variable CNF subsets", counts)
    checked([[]], 0)
    checked([], 0)
    record("Explicit empty clause and empty formula", {"cases": 2})

    rng = random.Random(20261010)
    counts = {"SAT": 0, "UNSAT": 0}
    learned = 0
    for case in range(600):
        variables = 1 + case % 6
        clauses = []
        for _ in range(rng.randrange(0, 25)):
            chosen = rng.sample(range(1, variables + 1), rng.randrange(1, variables + 1))
            clauses.append([v if rng.getrandbits(1) else -v for v in chosen])
        result = checked(clauses, variables)
        counts[result["status"]] += 1
        learned += len(result.get("certificate", []))
    if not learned or not all(counts.values()):
        raise ValueError("Random finite controls did not exercise both verdicts and learning")
    record("600 deterministic CNFs, one to six variables", {**counts, "learned_clauses": learned})

    # Three pigeons in two holes is false and requires nontrivial search.
    pigeon = [[1, 2], [3, 4], [5, 6], [-1, -3], [-1, -5], [-3, -5],
              [-2, -4], [-2, -6], [-4, -6]]
    proof = checked(pigeon, 6)
    if proof["status"] != "UNSAT" or not proof["certificate"]:
        raise ValueError("Control must include learned resolution clauses")
    record("Pigeonhole exact learned-clause UNSAT replay",
           {"learned_clauses": len(proof["certificate"])})

    def cert_reject(name, change):
        bad = copy.deepcopy(proof)
        change(bad)
        reject(name, lambda: sat.verify_resolution(pigeon, bad["certificate"],
                                                   bad["terminal"], time.monotonic() + 10))

    cert_reject("Future-parent certificate rejected",
                lambda p: p["certificate"][0].update(parent=99999))
    cert_reject("Wrong learned-clause certificate rejected",
                lambda p: p["certificate"][0].update(clause=[1, 2, 3, 4, 5, 6]))
    cert_reject("Wrong pivot certificate rejected",
                lambda p: p["certificate"][0]["resolution"][0].__setitem__(1, 99999))
    cert_reject("False terminal empty-clause derivation rejected",
                lambda p: p["terminal"].update(parent=0, resolution=[]))
    cert_reject("Noninteger reason rejected",
                lambda p: p["certificate"][0]["resolution"][0].__setitem__(0, True))

    for clause in ([0], [True], [1, 1], [1, -1], [7]):
        reject("Malformed CNF clause " + repr(clause),
               lambda clause=clause: sat.Solver([clause], 6, time.monotonic() + 10))

    # Tseitin equality is independently evaluated at every original PI assignment.
    dag = DAG(4, time.monotonic() + 10)
    a, b, c, d = 2, 4, 6, 8
    ab_xor = dag.OR(dag.AND(a, b ^ 1), dag.AND(a ^ 1, b))
    roots = [0, 1, a, a ^ 1, dag.AND(a, b), dag.OR(a, b), ab_xor,
             dag.AND(ab_xor, dag.OR(c, d)),
             dag.onehot_violation([a, b, c, d]),
             dag.onehot_violation([dag.AND(a, b), dag.AND(a, b ^ 1), a ^ 1])]
    assignments = 0
    for root in roots:
        clauses, index = sat.tseitin(dag, root)
        for bits in itertools.product((0, 1), repeat=4):
            fixed = [list(c) for c in clauses]
            for i, bit in enumerate(bits):
                if 2 * (i + 1) in index:
                    var = index[2 * (i + 1)]
                    fixed.append([var if bit else -var])
            solver = sat.Solver(fixed, len(index), time.monotonic() + 10)
            result = solver.solve()
            original = dag.evaluate(root, dict(enumerate(bits)))
            if (result["status"] == "SAT") != bool(original):
                raise ValueError("Tseitin CNF differs from direct original DAG truth table")
            if result["status"] == "UNSAT":
                sat.verify_resolution(fixed, result["certificate"], result["terminal"],
                                      time.monotonic() + 10)
            assignments += 1
    record("Tseitin AND, NOT, OR, XOR and one-hot truth tables",
           {"roots": len(roots), "PI_assignments": assignments})
    positive = sat.decide_sat(dag, roots[-1])
    if positive["status"] != "PROVED_BOOLEAN_CNF":
        raise ValueError("Distributive exact one-hot identity did not prove")
    record("Nonstructural one-hot identity UNSAT", {"verdict": positive["status"]})

    rare_dag = DAG(24, time.monotonic() + 10)
    rare = 1
    for i in range(24):
        rare = rare_dag.AND(rare, 2 * (i + 1))
    fault = rare_dag.onehot_violation([1, rare])
    negative = sat.decide_sat(rare_dag, fault)
    if negative["status"] != "DISPROVED_UNDER_RECORDED_ASSUMPTIONS" or \
            any(negative["counterexample"].get(i) != 1 for i in range(24)) or \
            rare_dag.evaluate(fault, negative["counterexample"]) != 1:
        raise ValueError("Rare 24-input fault lacks a real raw-DAG witness")
    record("Rare 24-input counterexample", {"activation_fraction": "1 / 16777216",
                                             "trigger_values": [1] * 24})
    reject("Missing witness input rejected", lambda: rare_dag.evaluate(fault, {}))
    zero_witness = dict(enumerate([0] * 24))
    if rare_dag.evaluate(fault, zero_witness) != 0:
        raise ValueError("Independent false-witness control did not reject fault activation")
    record("False all-zero fault witness is not accepted", {"original_DAG_value": 0})

    bounded = DAG(2, time.monotonic() + 10)
    formula = bounded.OR(2, 4)
    decision_limit = sat.decide_sat(bounded, formula, decision_bound=0)
    if decision_limit.get("reason") != "DECISION_BOUND" or decision_limit["status"] != "UNKNOWN":
        raise ValueError("Decision budget was not classified UNKNOWN")
    expired = DAG(1, time.monotonic() - 1)
    timeout = sat.decide_sat(expired, 2)
    if timeout.get("reason") != "TIME_BOUND" or timeout["status"] != "UNKNOWN":
        raise ValueError("Timeout was not classified UNKNOWN")
    original_limit = sat.MAX_VARIABLES
    try:
        sat.MAX_VARIABLES = 0
        size_limit = sat.decide_sat(bounded, formula)
    finally:
        sat.MAX_VARIABLES = original_limit
    if size_limit.get("reason") != "CNF_VARIABLE_BOUND" or size_limit["status"] != "UNKNOWN":
        raise ValueError("CNF size bound was not classified UNKNOWN")
    record("Three resource limits produce UNKNOWN", {"cases": 3})

    if any(sha(ROOT / rel) != digest for rel, digest in hashes.items()):
        raise ValueError("Checker sources changed during controls")
    receipt = {"status": "PASS_BOUNDED_CNF_CHECKER_CONTROLS", "source_sha256": hashes,
               "memory_enforcement": memory, "scope": "Finite checker controls only; no RTL or full sequential proof",
               "control_count": len(rows), "controls": rows}
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print("PASS:", len(rows), "bounded CNF checker controls")


if __name__ == "__main__":
    main()
