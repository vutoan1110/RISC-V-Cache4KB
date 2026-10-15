"""Audit completed paired sampled-reset proofs without rerunning a solver."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from lec_joint_invariant import (alias_cofactor, evaluate_raw, joint_predicate,
                                 nonvacuity, satisfies_joint, specification, xor)
from lec_onehot_boolean import ROOT, DAG, enforce_process_memory, sha
from lec_onehot_sat import tseitin, verify_resolution
from lec_reset_base import read_aig_bytes
from lec_reset_phase import PHASES, conditions_for, protocol_phase, relation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-base", required=True)
    args = parser.parse_args()
    base = Path(args.out_base).resolve()
    destinations = [base.with_suffix(ext) for ext in (".json", ".md")]
    if not base.is_relative_to(ROOT) or any(path.exists() for path in destinations):
        raise ValueError("New research audit paths required")
    memory = enforce_process_memory()
    rels = ["results/dm_reset_phase_20261010_p1.json", "results/dm_reset_phase_20261010_p2.json",
            "results/dm_reset_phase_fault_20261010_p1.json", "results/dm_reset_phase_fault_20261010_p2.json",
            "results/lec_reset_phase_controls_20261010.json", "scripts/verification/audit_lec_reset_phase.py"]
    hashes = {rel: sha(ROOT / rel) for rel in rels}
    first, second, negative1, negative2, controls = [json.loads((ROOT / rel).read_text()) for rel in rels[:5]]
    for receipt, key in ((first, "input_sha256"), (second, "input_sha256"),
                         (negative1, "input_sha256"), (negative2, "input_sha256"), (controls, "source_sha256")):
        for rel, digest in receipt[key].items():
            if sha(ROOT / rel) != digest:
                raise ValueError("Receipt input differs from current retained file: " + rel)
            hashes[rel] = digest
    if first != second or (ROOT / rels[0]).read_bytes() != (ROOT / rels[1]).read_bytes() or \
            negative1 != negative2 or (ROOT / rels[2]).read_bytes() != (ROOT / rels[3]).read_bytes():
        raise ValueError("Independent native proof/control executions differ")
    if controls["status"] != "PASS_RESET_PHASE_CHECKER_CONTROLS" or controls["control_count"] != 11 or \
            any(row["status"] != "PASS" for row in controls["controls"]):
        raise ValueError("Phase controls incomplete")
    if first["phase_count"] != 6 or first["phase_order"] != [list(p) for p in PHASES] or \
            first["total_closure_obligations"] != 1716 or len(first["phases"]) != 6:
        raise ValueError("Reachable phase coverage differs")
    for key in ("between_edge_asynchronous_source_events", "source_undefined_zero_abstraction_gap",
                "raw_N1_final_reset_coupling", "full_sequential_LEC"):
        if first[key] != "OPEN":
            raise ValueError("Model phase result was expanded into an unproved scope")
    graph = read_aig_bytes((ROOT / "asic/equiv/lec/gold_god_r14.aig").read_bytes())
    pairs = json.loads((ROOT / "asic/equiv/lec/pairsAR14.json").read_text())
    spec = json.loads((ROOT / "asic/equiv/lec/AR14_spec.json").read_text())
    info = specification(graph, pairs, spec)
    if first["joint_invariant_I_Q"] != info or negative1["joint_invariant_I_Q"] != info:
        raise ValueError("Current joint invariant differs")
    constants, aliases = info["constants"], info["duplicate_aliases"]
    summaries = []

    def check_row(row, dag, premise, violation, expected):
        for key, value in expected.items():
            if row[key] != value:
                raise ValueError("Obligation target differs: " + key)
        if row["nonvacuity"] != nonvacuity(graph, info, expected["reset_conditions"]):
            raise ValueError("Joint/phase nonvacuity witness differs")
        root = dag.AND(premise, violation)
        if (row["joint_premise_literal"], row["D_violation_literal"], row["conditional_violation_literal"]) != \
                (premise, violation, root):
            raise ValueError("Original conditional violation does not reproduce")
        decision = row["decision"]
        if decision["status"] == "PROVED_STRUCTURAL_COFACTOR":
            if root != 0:
                raise ValueError("Structural proof root is not literal zero")
            return 0
        if decision["status"] != "PROVED_BOOLEAN_CNF":
            raise ValueError("Unknown or counterexample cannot be promoted")
        clauses, index = tseitin(dag, root)
        if len(index) != decision["CNF_variables"] or len(clauses) != decision["CNF_initial_clauses"]:
            raise ValueError("Retained proof does not match original CNF")
        steps = verify_resolution(clauses, decision["resolution_certificate"],
                                  decision["terminal_empty_clause_derivation"], dag.deadline)
        if steps != decision["resolution_steps"] or steps != decision["independently_replayed_resolution_steps"]:
            raise ValueError("Resolution proof count differs")
        return steps

    for phase, saved in zip(PHASES, first["phases"]):
        if saved["phase"] != list(phase) or saved["phase_relation_R"] is not True or len(saved["obligations"]) != 286:
            raise ValueError("Phase identity or complete population differs")
        protocol = protocol_phase(graph, phase)
        if protocol != saved["protocol"] or protocol["status"] != "PROVED_STRUCTURAL_PHASE_TRANSITION" or \
                protocol["expected_next_relation_R"] is not True:
            raise ValueError("Raw synchronizer transition does not reproduce")
        expected_counts = {"PROVED_STRUCTURAL_COFACTOR": 266 if phase == (1, 1, 1) else 286,
                           "PROVED_BOOLEAN_CNF": 20 if phase == (1, 1, 1) else 0,
                           "DISPROVED_UNDER_RECORDED_ASSUMPTIONS": 0, "UNKNOWN": 0}
        if saved["counts"] != expected_counts:
            raise ValueError("Exact phase counts differ")
        conditions = conditions_for(phase)
        assignments = {**constants, **conditions}
        dag = DAG(graph["inputs"], time.monotonic() + 10)
        outputs = alias_cofactor(dag, graph, assignments, aliases, aliases)
        premise = joint_predicate(dag, graph, info, assignments)
        cursor, steps = 0, 0
        for qname, expected in constants.items():
            dag.deadline = time.monotonic() + 10
            dname = qname.replace("lec_q_", "lec_d_")
            steps += check_row(saved["obligations"][cursor], dag, premise, outputs[dname] ^ expected,
                               {"kind": "constant", "Q": qname, "D": dname,
                                "expected": expected, "reset_conditions": conditions})
            cursor += 1
        for qname, partner in aliases.items():
            dag.deadline = time.monotonic() + 10
            dname, pname = qname.replace("lec_q_", "lec_d_"), partner.replace("lec_q_", "lec_d_")
            steps += check_row(saved["obligations"][cursor], dag, premise, xor(dag, outputs[dname], outputs[pname]),
                               {"kind": "duplicate", "Q": qname, "paired_Q": partner,
                                "D": dname, "paired_D": pname, "reset_conditions": conditions})
            cursor += 1
        del dag, outputs
        for group in info["onehot_groups"]:
            for active in range(len(group["Q"])):
                selected = {**conditions, **{name: int(i == active) for i, name in enumerate(group["Q"])}}
                assignments = {**constants, **selected}
                dag = DAG(graph["inputs"], time.monotonic() + 10)
                outputs = alias_cofactor(dag, graph, assignments, aliases, aliases)
                premise = joint_predicate(dag, graph, info, assignments)
                steps += check_row(saved["obligations"][cursor], dag, premise,
                                   dag.onehot_violation([outputs[name] for name in group["D"]]),
                                   {"kind": "onehot", "group": group["name"], "active_current_bit": active,
                                    "group_Q": group["Q"], "D": group["D"], "reset_conditions": selected})
                cursor += 1
        if cursor != 286:
            raise ValueError("Target enumeration missing/duplicate")
        summaries.append({"phase": list(phase), "counts": expected_counts,
                          "original_obligations_reconstructed": cursor,
                          "resolution_steps_replayed": steps, "protocol": protocol})
        print("audited phase", phase, flush=True)

    if negative1["status"] != "PASS_ACTUAL_RAW_MODEL_RARE_RESET_PHASE_FAULT_CONTROL" or negative1["phase"] != [0, 1, 1]:
        raise ValueError("Actual interrupted-reset semantic control incomplete")
    conditions = conditions_for((0, 1, 1))
    if negative1["assignments"] != conditions:
        raise ValueError("Fault phase conditions differ")
    unrestricted = DAG(graph["inputs"], time.monotonic() + 10)
    raw = unrestricted.cofactor(graph, conditions)
    if [raw["lec_d_p19088"], raw["lec_d_p19089"]] != [0, 0]:
        raise ValueError("Raw protocol baseline is not an unrestricted proof")
    del unrestricted, raw
    assignments = {**constants, **conditions}
    dag = DAG(graph["inputs"], time.monotonic() + 10)
    outputs = alias_cofactor(dag, graph, assignments, aliases, aliases)
    premise = joint_predicate(dag, graph, info, assignments)
    meta, sync = outputs["lec_d_p19088"], outputs["lec_d_p19089"]
    if dag.AND(premise, dag.AND(sync, meta ^ 1)) != 0:
        raise ValueError("Fault baseline relation R(D) is not proved")
    excluded = set(assignments) | set(aliases) | {name for g in info["onehot_groups"] for name in g["Q"]}
    free = [i for i, name in enumerate(graph["input_names"]) if name not in excluded][:24]
    if negative1["trigger_inputs"] != [graph["input_names"][i] for i in free]:
        raise ValueError("Rare trigger set differs")
    rare = 1
    for i in free:
        rare = dag.AND(rare, 2 * (i + 1))
    mutated_sync = dag.OR(sync, rare)
    root = dag.AND(premise, dag.AND(mutated_sync, meta ^ 1))
    decision = negative1["negative"]["decision"]
    if decision["status"] != "DISPROVED_UNDER_RECORDED_ASSUMPTIONS":
        raise ValueError("Semantic negative control needs SAT")
    full = dict.fromkeys(graph["input_names"], 0)
    full.update(decision["counterexample"])
    full.update(constants)
    full.update(conditions)
    for source, target in aliases.items():
        full[source] = full[target]
    if not satisfies_joint(full, info, conditions) or any(full[graph["input_names"][i]] != 1 for i in free):
        raise ValueError("Fault witness fails a joint premise or rare trigger")
    raw = evaluate_raw(graph, full)
    original = [raw["lec_d_p19088"], raw["lec_d_p19089"]]
    mutated = [original[0], original[1] | 1]
    if original != [0, 0] or mutated != [0, 1] or not relation(*original) or relation(*mutated):
        raise ValueError("Actual raw witness does not isolate the in-memory phase fault")
    numeric = {i: full[name] for i, name in enumerate(graph["input_names"])}
    if dag.evaluate(root, numeric) != 1:
        raise ValueError("Raw-DAG witness does not satisfy conditional phase violation")
    clauses, index = tseitin(dag, root)
    assignment = decision["CNF_assignment"]
    if len(assignment) != len(index) + 1 or not all(
            any(assignment[abs(lit)] == (1 if lit > 0 else -1) for lit in clause) for clause in clauses):
        raise ValueError("Semantic fault CNF witness fails a clause")
    if any(sha(ROOT / rel) != digest for rel, digest in hashes.items()):
        raise ValueError("Frozen proof evidence changed during audit")

    receipt = {"status": "VERIFIED_TWO_INDEPENDENT_REACHABLE_SAMPLED_RESET_PHASE_EXECUTIONS",
               "input_and_evidence_sha256": hashes, "memory_enforcement": memory,
               "all_fields_and_bytes_match": True, "fields_ignored_in_pair_comparison": [],
               "phase_count": 6, "closure_obligations": 1716,
               "total_counts": {"PROVED_STRUCTURAL_COFACTOR": 1696, "PROVED_BOOLEAN_CNF": 20,
                                "DISPROVED_UNDER_RECORDED_ASSUMPTIONS": 0, "UNKNOWN": 0},
               "phase_relation_R": "(not sync_Q) OR meta_Q; pair00,10,11 after established sampled-reset base",
               "phase_summaries": summaries,
               "actual_semantic_fault_controls_paired_and_raw_replayed": True,
               "fault_original_raw_next_meta_sync": original, "fault_mutated_next_meta_sync": mutated,
               "negative_witness_satisfies_all_joint_and_phase_premises": True,
               "native_independent_proof_executions": [
                   {"pass": 1, "command": "python scripts/verification/lec_reset_phase.py --out results/dm_reset_phase_20261010_p1.json --controls results/lec_reset_phase_controls_20261010.json",
                    "native_exit_code": 0, "tool_chunks": ["aeaf8e", "ae657c"], "tool_session_id": 55506,
                    "tool_reported_wait_seconds": [10.0162306, 0.0000093]},
                   {"pass": 2, "command": "python scripts/verification/lec_reset_phase.py --out results/dm_reset_phase_20261010_p2.json --controls results/lec_reset_phase_controls_20261010.json",
                    "native_exit_code": 0, "tool_chunks": ["75c8d5", "9b5523"], "tool_session_id": 3399,
                    "tool_reported_wait_seconds": [10.0112914, 3.7528002]}],
               "native_actual_fault_executions": [
                   {"pass": 1, "tool_chunk": "79edf2", "native_exit_code": 0, "tool_reported_wall_seconds": 0.7172036},
                   {"pass": 2, "tool_chunk": "f5be88", "native_exit_code": 0, "tool_reported_wall_seconds": 0.7759284}],
               "timing_note": "Proof tool calls yielded; polling wait durations do not establish complete native process wall time",
               "sampled_interrupted_reset_bridge": "PROVED_RAW_BOOLEAN_CLOCK_STEPS_ONLY",
               "between_edge_asynchronous_source_events": "OPEN", "source_undefined_zero_abstraction_gap": "OPEN",
               "raw_N1_final_reset_coupling": "OPEN", "full_sequential_LEC": "OPEN",
               "independent_phase_review": "PENDING_SEPARATE_REVIEW_RECEIPT",
               "audit_is_measurement_double_execution": False, "heavy_external_formal_tools_executed": False}
    destinations[0].write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    lines = ["# Current-gold sampled reset phase bridge", "",
             "Two independent native runs prove all 1716 closures and reproduce every field and byte. Every reachable synchronizer phase after an established sampled reset base is covered, with arbitrary sampled external reset reassertion/release. The joint invariant retains all 235 constants, 28 duplicate equalities and four legal one-hot groups; all other raw state and inputs remain symbolic.", "",
             "| External reset_n | Meta Q | Sync Q | Structural closures | CNF closures | UNKNOWN / counterexample |",
             "|---:|---:|---:|---:|---:|---:|"]
    for item in summaries:
        e, m, s = item["phase"]
        lines.append(f"| {e} | {m} | {s} | {item['counts']['PROVED_STRUCTURAL_COFACTOR']} | {item['counts']['PROVED_BOOLEAN_CNF']} | 0 / 0 |")
    lines += ["", "The raw equations are Dmeta=external_reset_n and Dsync=external_reset_n AND current_meta_Q. They preserve R=(not sync_Q) OR meta_Q. One sampled asserted edge establishes pair00 regardless of prior synchronizer state; the next sampled asserted edge invokes the pinned universal gold reset base. Initial pair01 is not assumed impossible before reset. No unreset RAM, tags or register array is assigned zero as an axiom.", "",
              "This audit reconstructs all 1716 original conditional violations, checks literal-zero structural closures and replays every retained CNF resolution certificate without a new SAT solve. Premises are explicitly nonvacuous. Both actual semantic controls detect a rare 24-input in-memory Dsync fault during phase(0,1,1): original next pair00 becomes faulty01, with every I(Q) and R(Q) premise satisfied.", "",
              "The result covers completed clock steps of the existing Boolean graph, including arbitrary external-reset changes between those steps. RTL asynchronous reset events between edges, the source X/Z-to-Boolean abstraction gap, raw GOLD-to-N1-to-final initial-state coupling and complete sequential LEC remain OPEN. Independent review is a separate pending receipt.", "",
              "Actual proof processes were kernel-limited to512 MiB with10 seconds per obligation and fixed frozen CNF budgets. Both proof CLIs and both semantic control CLIs exited0. Complete proof process wall time was not captured when tool calls yielded and is not inferred from polling intervals. Input/source/artifact hashes and execution records are in the companion JSON.", ""]
    destinations[1].write_text("\n".join(lines), encoding="ascii")
    print("PASS: paired six phases /1716 closures and semantic fault controls reconstructed; scope remains qualified")


if __name__ == "__main__":
    main()
