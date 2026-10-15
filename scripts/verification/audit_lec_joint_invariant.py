"""Reread paired current-gold joint induction proofs; do not run SAT anew.

Reconstruct original obligations and replay saved resolution proofs. This audit
does not replace either of the two independent native proof executions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from lec_joint_invariant import (RESET, alias_cofactor, evaluate_raw, joint_predicate,
                                 nonvacuity, protocol_checks, satisfies_joint,
                                 specification, xor)
from lec_onehot_boolean import ROOT, DAG, enforce_process_memory, sha
from lec_onehot_sat import tseitin, verify_resolution
from lec_reset_base import read_aig_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-base", required=True)
    args = parser.parse_args()
    base = Path(args.out_base).resolve()
    destinations = [base.with_suffix(ext) for ext in (".json", ".md")]
    if not base.is_relative_to(ROOT) or any(p.exists() for p in destinations):
        raise ValueError("New research audit receipt paths required")
    memory = enforce_process_memory()
    rels = ["results/dm_joint_invariant_20261010_p1.json",
            "results/dm_joint_invariant_20261010_p2.json",
            "results/dm_joint_model_fault_20261010_p1.json",
            "results/dm_joint_model_fault_20261010_p2.json",
            "results/lec_joint_invariant_controls_20261010.json",
            "scripts/verification/audit_lec_joint_invariant.py"]
    hashes = {rel: sha(ROOT / rel) for rel in rels}
    a, b, n1, n2, controls = [json.loads((ROOT / rel).read_text()) for rel in rels[:5]]
    for proof, key in ((a, "input_sha256"), (b, "input_sha256"),
                       (n1, "input_sha256"), (n2, "input_sha256"), (controls, "source_sha256")):
        for rel, digest in proof[key].items():
            if sha(ROOT / rel) != digest:
                raise ValueError("Current source differs from receipt: " + rel)
            hashes[rel] = digest
    if a != b or (ROOT / rels[0]).read_bytes() != (ROOT / rels[1]).read_bytes() or \
            n1 != n2 or (ROOT / rels[2]).read_bytes() != (ROOT / rels[3]).read_bytes():
        raise ValueError("Independent complete proof/control executions differ")
    expected_counts = {"PROVED_STRUCTURAL_COFACTOR": 266, "PROVED_BOOLEAN_CNF": 20,
                       "DISPROVED_UNDER_RECORDED_ASSUMPTIONS": 0, "UNKNOWN": 0}
    if a["counts"] != expected_counts or len(a["obligations"]) != 286 or \
            a["reset_phase"] != RESET or a["full_sequential_LEC"] != "OPEN" or \
            a["source_undefined_zero_abstraction_gap"] != "OPEN" or \
            a["interrupted_or_arbitrary_reset_phase_invariant_closure"] != "OPEN":
        raise ValueError("Joint proof scope or complete population differs")
    if controls["status"] != "PASS_JOINT_INVARIANT_CHECKER_CONTROLS" or \
            controls["control_count"] != 15 or any(r["status"] != "PASS" for r in controls["controls"]):
        raise ValueError("New joint checker controls incomplete")
    graph = read_aig_bytes((ROOT / "asic/equiv/lec/gold_god_r14.aig").read_bytes())
    pairs = json.loads((ROOT / "asic/equiv/lec/pairsAR14.json").read_text())
    spec = json.loads((ROOT / "asic/equiv/lec/AR14_spec.json").read_text())
    info = specification(graph, pairs, spec)
    if info != a["joint_invariant_I_Q"] or info != n1["joint_invariant_I_Q"]:
        raise ValueError("Recorded I(Q) differs from exact current specification")
    constants, aliases = info["constants"], info["duplicate_aliases"]
    checked = []

    def check_row(row, dag, premise, violation, expected):
        for key, value in expected.items():
            if row[key] != value:
                raise ValueError("Stored obligation differs: " + key)
        conditions = expected["reset_conditions"]
        if row["nonvacuity"] != nonvacuity(graph, info, conditions):
            raise ValueError("Stored nonvacuity witness differs")
        root = dag.AND(premise, violation)
        if (row["joint_premise_literal"], row["D_violation_literal"], row["conditional_violation_literal"]) != \
                (premise, violation, root):
            raise ValueError("Recorded root does not reproduce original cofactored obligation")
        decision = row["decision"]
        if decision["status"] == "PROVED_STRUCTURAL_COFACTOR":
            if root != 0:
                raise ValueError("Structural closure root is not literal zero")
            steps = 0
        elif decision["status"] == "PROVED_BOOLEAN_CNF":
            clauses, index = tseitin(dag, root)
            if (len(index), len(clauses)) != (decision["CNF_variables"], decision["CNF_initial_clauses"]):
                raise ValueError("Reconstructed CNF population differs")
            steps = verify_resolution(clauses, decision["resolution_certificate"],
                                      decision["terminal_empty_clause_derivation"], dag.deadline)
            if steps != decision["resolution_steps"] or steps != decision["independently_replayed_resolution_steps"]:
                raise ValueError("Stored resolution derivation count differs")
        else:
            raise ValueError("Every target must contain a complete semantic proof")
        checked.append({"kind": row["kind"], "status": decision["status"],
                        "resolution_steps_replayed": steps})

    dag = DAG(graph["inputs"], time.monotonic() + 10)
    outputs = alias_cofactor(dag, graph, {**constants, **RESET}, aliases, aliases)
    premise = joint_predicate(dag, graph, info, {**constants, **RESET})
    cursor = 0
    for qname, expected in constants.items():
        dag.deadline = time.monotonic() + 10
        dname = qname.replace("lec_q_", "lec_d_")
        check_row(a["obligations"][cursor], dag, premise, outputs[dname] ^ expected,
                  {"kind": "constant", "Q": qname, "D": dname,
                   "expected": expected, "reset_conditions": RESET})
        cursor += 1
    for qname, partner in aliases.items():
        dag.deadline = time.monotonic() + 10
        dname, pname = qname.replace("lec_q_", "lec_d_"), partner.replace("lec_q_", "lec_d_")
        check_row(a["obligations"][cursor], dag, premise, xor(dag, outputs[dname], outputs[pname]),
                  {"kind": "duplicate", "Q": qname, "paired_Q": partner,
                   "D": dname, "paired_D": pname, "reset_conditions": RESET})
        cursor += 1
    del dag, outputs
    for group in info["onehot_groups"]:
        for active in range(len(group["Q"])):
            conditions = {**RESET, **{name: int(i == active) for i, name in enumerate(group["Q"])}}
            assignments = {**constants, **conditions}
            dag = DAG(graph["inputs"], time.monotonic() + 10)
            outputs = alias_cofactor(dag, graph, assignments, aliases, aliases)
            premise = joint_predicate(dag, graph, info, assignments)
            check_row(a["obligations"][cursor], dag, premise,
                      dag.onehot_violation([outputs[name] for name in group["D"]]),
                      {"kind": "onehot", "group": group["name"], "active_current_bit": active,
                       "group_Q": group["Q"], "D": group["D"], "reset_conditions": conditions})
            cursor += 1
    if cursor != 286:
        raise ValueError("Missing or duplicated obligation population")
    protocols = protocol_checks(graph)
    if protocols != a["synchronizer_protocol"] or any(r["status"] != "PROVED_STRUCTURAL_PROTOCOL" for r in protocols):
        raise ValueError("Separate synchronizer protocol equations do not reproduce")

    if n1["status"] != "PASS_ACTUAL_RAW_MODEL_JOINT_PREMISE_RARE_FAULT_CONTROL":
        raise ValueError("Actual-model semantic control incomplete")
    group = info["onehot_groups"][0]
    conditions = {**RESET, **{name: int(i == 0) for i, name in enumerate(group["Q"])}}
    if conditions != n1["reset_and_own_code_conditions"]:
        raise ValueError("Fault control conditions differ")
    assignments = {**constants, **conditions}
    dag = DAG(graph["inputs"], time.monotonic() + 10)
    outputs = alias_cofactor(dag, graph, assignments, aliases, aliases)
    premise = joint_predicate(dag, graph, info, assignments)
    values = [outputs[name] for name in group["D"]]
    baseline_root = dag.AND(premise, dag.onehot_violation(values))
    if baseline_root != 0 or n1["baseline"]["decision"]["status"] != "PROVED_STRUCTURAL_COFACTOR":
        raise ValueError("Actual fault baseline is not proved")
    excluded = set(assignments) | set(aliases) | {name for g in info["onehot_groups"] for name in g["Q"]}
    free = [i for i, name in enumerate(graph["input_names"]) if name not in excluded][:24]
    if n1["trigger_inputs"] != [graph["input_names"][i] for i in free]:
        raise ValueError("Actual fault trigger set differs")
    trigger = 1
    for i in free:
        trigger = dag.AND(trigger, 2 * (i + 1))
    mutated = [dag.OR(values[0], trigger), dag.OR(values[1], trigger), *values[2:]]
    root = dag.AND(premise, dag.onehot_violation(mutated))
    decision = n1["negative"]["decision"]
    if decision["status"] != "DISPROVED_UNDER_RECORDED_ASSUMPTIONS":
        raise ValueError("Actual fault requires SAT, not a tool or resource failure")
    full = dict.fromkeys(graph["input_names"], 0)
    full.update(decision["counterexample"])
    full.update(constants)
    full.update(conditions)
    for source, target in aliases.items():
        full[source] = full[target]
    if any(full[graph["input_names"][i]] != 1 for i in free) or not satisfies_joint(full, info, conditions):
        raise ValueError("Actual fault witness violates a trigger or joint premise")
    original = evaluate_raw(graph, full)
    old_code = [original[name] for name in group["D"]]
    faulty_code = [old_code[0] | 1, old_code[1] | 1, *old_code[2:]]
    if old_code != n1["original_raw_D_code_at_witness"] or \
            faulty_code != n1["mutated_D_code_at_witness"] or sum(old_code) != 1 or sum(faulty_code) < 2:
        raise ValueError("Original raw fault witness is not reproduced")
    numeric = {i: full[name] for i, name in enumerate(graph["input_names"])}
    if dag.evaluate(root, numeric) != 1:
        raise ValueError("Fault witness does not satisfy conditional violation DAG")
    clauses, index = tseitin(dag, root)
    assignment = decision["CNF_assignment"]
    if len(assignment) != len(index) + 1 or not all(
            any(assignment[abs(lit)] == (1 if lit > 0 else -1) for lit in c) for c in clauses):
        raise ValueError("Fault CNF assignment fails a clause")
    if any(sha(ROOT / rel) != digest for rel, digest in hashes.items()):
        raise ValueError("Frozen evidence changed during audit")

    receipt = {"status": "VERIFIED_TWO_INDEPENDENT_CURRENT_GOLD_JOINT_INDUCTION_EXECUTIONS",
               "scope": "Current raw gold I(Q) => I(D), only the recorded deasserted reset phase",
               "full_sequential_LEC": "OPEN", "source_undefined_zero_abstraction_gap": "OPEN",
               "interrupted_or_arbitrary_reset_phase_invariant_closure": "OPEN",
               "independent_kernel_review": "PENDING_SEPARATE_REVIEW_RECEIPT",
               "input_and_evidence_sha256": hashes, "memory_enforcement": memory,
               "all_fields_and_bytes_match": True, "fields_ignored_in_pair_comparison": [],
               "joint_invariant_population": {"constant": 235, "duplicate": 28,
                                               "onehot_groups": 4, "legal_onehot_code_cases": 23},
               "counts": expected_counts, "replayed_obligations": checked,
               "separate_synchronizer_protocol_equations": protocols,
               "actual_model_negative_controls_paired_and_replayed": True,
               "negative_control_original_raw_D_code": old_code,
               "negative_control_mutated_D_code": faulty_code,
               "native_independent_executions": [
                   {"pass": 1, "command": "python scripts/verification/lec_joint_invariant.py --out results/dm_joint_invariant_20261010_p1.json --controls results/lec_joint_invariant_controls_20261010.json",
                    "native_exit_code": 0, "tool_chunks": ["31f010", "8b83d2"], "tool_session_id": 11953,
                    "tool_reported_wait_seconds": [10.0025717, 0.000007]},
                   {"pass": 2, "command": "python scripts/verification/lec_joint_invariant.py --out results/dm_joint_invariant_20261010_p2.json --controls results/lec_joint_invariant_controls_20261010.json",
                    "native_exit_code": 0, "tool_chunks": ["55b99f", "9a5334"], "tool_session_id": 6759,
                    "tool_reported_wait_seconds": [10.014234, 0.0000075]}],
               "timing_note": "Both tool invocations yielded; polling wait durations are not complete native process wall times",
               "native_actual_model_control_executions": [
                   {"pass": 1, "tool_chunk": "d7a0c7", "native_exit_code": 0, "tool_reported_wall_time_seconds": 0.9635166},
                   {"pass": 2, "tool_chunk": "a7a225", "native_exit_code": 0, "tool_reported_wall_time_seconds": 0.8004223}],
               "checker_control_groups": 15,
               "audit_is_measurement_double_execution": False,
               "heavy_external_formal_tools_executed": False}
    destinations[0].write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    lines = ["# Current gold joint invariant induction", "",
             "Two independent native executions prove every one of the 286 recorded deasserted-phase obligations and reproduce every field and byte. I(Q) explicitly contains all 235 constant constraints, 28 duplicate equalities and four legal one-hot groups. All remaining raw state and inputs remain arbitrary symbolic values.", "",
             "The 235 constant, 28 duplicate and three LCD legal-code closures are structural zero roots. The six AXI and fourteen ALU legal-code closures have exact CNF resolution proofs. This audit reconstructs every original conditional violation and separately replays saved resolution certificates, without running SAT anew.", "",
             "| Obligation | Cases | Proved | UNKNOWN / counterexamples |",
             "|---|---:|---:|---:|", "| Constants | 235 | 235 | 0 / 0 |",
             "| Duplicate equalities | 28 | 28 | 0 / 0 |", "| Legal group codes | 23 | 23 | 0 / 0 |", "",
             "The assumptions have explicit satisfying assignments. Completing free inputs with zero for one witness is not a zero-initialization axiom. Two actual-model rare 24-input fault controls satisfy every joint premise; the original raw LCD D code is " + str(old_code) + " and the in-memory mutated code is " + str(faulty_code) + ". A timeout, missing output or UNKNOWN cannot count as a negative-control pass.", "",
             "Separate unrestricted synchronizer equations prove external reset 0 gives both D=0, and external reset 1 gives meta D=1 with sync D equal the current meta Q. Existing paired gold reset-base evidence is pinned. This report proves the deasserted phase only: arbitrary/interrupted reset-phase invariant closure remains OPEN.", "",
             "The source undefined-zero Boolean abstraction gap, raw N1/final reset coupling, mapped boundaries and complete sequential RTL-to-netlist equivalence remain OPEN. The independently reviewed SAT kernel is frozen; independent review of this new joint substitution/premise construction is a separate pending receipt.", "",
             "Every actual proof process had a kernel-enforced 512 MiB limit and each obligation a 10-second deadline, using fixed existing CNF budgets. Both actual native proof invocations and both actual-model controls exited 0. The complete proof process wall times were not captured when tool calls yielded and are not inferred from polling intervals.", "",
             "Input, source and evidence hashes, exact completeness checks, protocol equations and execution records are retained in the companion JSON. No retained source, RTL, model or live PD/benchmark input was changed.", ""]
    destinations[1].write_text("\n".join(lines), encoding="ascii")
    print("PASS: paired 286 joint obligations and actual-model controls reconstructed and replayed")


if __name__ == "__main__":
    main()
