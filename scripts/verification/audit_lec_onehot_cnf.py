"""Reread current paired CNF subproofs; never execute a new formal solver.

This audit is not a second measurement: both independent native CLI proof runs
already exist. It reconstructs each original cone and replays stored resolution.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from lec_onehot_boolean import ROOT, DAG, case_conditions, enforce_process_memory, sha
from lec_onehot_sat import tseitin, verify_resolution
from lec_reset_base import read_aig_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-base", required=True)
    args = parser.parse_args()
    base = Path(args.out_base).resolve()
    destinations = [base.with_suffix(ext) for ext in (".json", ".md")]
    if not base.is_relative_to(ROOT) or any(p.exists() for p in destinations):
        raise ValueError("New research audit paths required")
    memory = enforce_process_memory()
    rels = ["results/dm_alu_onehot_cnf_20261010_p1.json",
            "results/dm_alu_onehot_cnf_20261010_p2.json",
            "results/dm_onehot_cnf_model_fault_20261010_p1.json",
            "results/dm_onehot_cnf_model_fault_20261010_p2.json",
            "results/lec_onehot_sat_controls_20261010.json",
            "results/dm_onehot_boolean_20261010_p1.json",
            "scripts/verification/audit_lec_onehot_cnf.py"]
    hashes = {rel: sha(ROOT / rel) for rel in rels}
    a, b, n1, n2, controls, previous = [json.loads((ROOT / rel).read_text()) for rel in rels[:6]]
    for receipt, key in ((a, "input_sha256"), (b, "input_sha256"),
                         (n1, "input_sha256"), (n2, "input_sha256"),
                         (controls, "source_sha256")):
        for rel, digest in receipt[key].items():
            if sha(ROOT / rel) != digest:
                raise ValueError("Current input differs from proof receipt: " + rel)
            hashes[rel] = digest
    if a != b or (ROOT / rels[0]).read_bytes() != (ROOT / rels[1]).read_bytes():
        raise ValueError("Independent ALU executions differ on a field or byte")
    if n1 != n2 or (ROOT / rels[2]).read_bytes() != (ROOT / rels[3]).read_bytes():
        raise ValueError("Independent actual-model controls differ")
    if a["counts"] != {"PROVED_BOOLEAN_CNF": 14,
                       "DISPROVED_UNDER_RECORDED_ASSUMPTIONS": 0, "UNKNOWN": 0} or \
            a["full_sequential_LEC"] != "OPEN":
        raise ValueError("Require all fourteen model subproofs and qualified full scope")
    if controls["status"] != "PASS_BOUNDED_CNF_CHECKER_CONTROLS" or \
            controls["control_count"] != 20 or any(c["status"] != "PASS" for c in controls["controls"]):
        raise ValueError("Checker controls are incomplete")
    raw = ROOT / "asic/equiv/lec/gold_god_r14.aig"
    graph = read_aig_bytes(raw.read_bytes())
    pairs = json.loads((ROOT / "asic/equiv/lec/pairsAR14.json").read_text())
    spec = json.loads((ROOT / "asic/equiv/lec/AR14_spec.json").read_text())
    group = next(g for g in spec["onehot_gold"] if g["name"] == "alu_ctrl_e")
    old_alu = [r for r in previous["obligations"] if r["group"] == "alu_ctrl_e"]
    if len(a["obligations"]) != 14 or len(old_alu) != 14:
        raise ValueError("ALU obligation population mismatch")
    dnames = {i: f"lec_d_p{k:05d}" for k, (i, _) in enumerate(pairs["pairs"])}
    dnames.update({i: f"lec_d_g{k:05d}" for k, i in enumerate(pairs["gold_only"])})
    reset = {"reset_n": 1, "lec_q_p19088": 1, "lec_q_p19089": 1}
    checked = []
    for active, row in enumerate(a["obligations"]):
        assumptions = case_conditions(graph, pairs, group, active, reset)
        if row["active_current_bit"] != active or row["group"] != group["name"] or \
                row["group_gold_indices"] != group["gold"] or row["assignments"] != assumptions or \
                old_alu[active]["assignments"] != assumptions or row["status"] != "PROVED_BOOLEAN_CNF":
            raise ValueError("Obligation or recorded assumption changed")
        dag = DAG(graph["inputs"], time.monotonic() + 10)
        outputs = dag.cofactor(graph, assumptions)
        root = dag.onehot_violation([outputs[dnames[i]] for i in group["gold"]])
        clauses, index = tseitin(dag, root)
        if row["CNF_variables"] != len(index) or row["CNF_initial_clauses"] != len(clauses):
            raise ValueError("Stored CNF does not reproduce the exact raw cone")
        steps = verify_resolution(clauses, row["resolution_certificate"],
                                  row["terminal_empty_clause_derivation"], dag.deadline)
        if steps != row["resolution_steps"] or steps != row["independently_replayed_resolution_steps"]:
            raise ValueError("Resolution proof count differs")
        checked.append({"active_current_bit": active, "resolution_steps_replayed": steps,
                        "CNF_variables": len(index), "CNF_initial_clauses": len(clauses)})

    if n1["status"] != "PASS_ACTUAL_RAW_MODEL_CNF_RARE_ONEHOT_FAULT_CONTROL" or \
            n1["baseline"]["status"] != "PROVED_BOOLEAN_CNF" or \
            n1["negative"]["status"] != "DISPROVED_UNDER_RECORDED_ASSUMPTIONS":
        raise ValueError("Actual-model semantic fault controls incomplete")
    axi = next(g for g in spec["onehot_gold"] if g["name"] == "axi_last_grant")
    conditions = case_conditions(graph, pairs, axi, 0, reset)
    if n1["assignments"] != conditions:
        raise ValueError("Actual-model fault control assumption mismatch")
    dag = DAG(graph["inputs"], time.monotonic() + 10)
    outputs = dag.cofactor(graph, conditions)
    values = [outputs[dnames[i]] for i in axi["gold"]]
    baseline_clauses, _ = tseitin(dag, dag.onehot_violation(values))
    verify_resolution(baseline_clauses, n1["baseline"]["resolution_certificate"],
                      n1["baseline"]["terminal_empty_clause_derivation"], dag.deadline)
    named = dict(zip(graph["input_names"], range(graph["inputs"])))
    free = [i for i, name in enumerate(graph["input_names"]) if name not in conditions][:24]
    if n1["trigger_inputs"] != [graph["input_names"][i] for i in free]:
        raise ValueError("Rare-control trigger set changed")
    trigger = 1
    for i in free:
        trigger = dag.AND(trigger, 2 * (i + 1))
    mutated = [dag.OR(values[0], trigger), dag.OR(values[1], trigger), *values[2:]]
    witness = {named[name]: v for name, v in n1["negative"]["counterexample"].items()}
    if any(witness.get(i) != 1 for i in free):
        raise ValueError("Fault witness does not trigger all 24 free inputs")
    full = {i: 0 for i in range(graph["inputs"])}
    full.update(witness)
    old_code = [dag.evaluate(v, full) for v in values]
    bad_code = [dag.evaluate(v, full) for v in mutated]
    negative_root = dag.onehot_violation(mutated)
    if old_code != n1["original_code_at_fault_witness"] or \
            bad_code != n1["mutated_code_at_fault_witness"] or \
            sum(old_code) != 1 or sum(bad_code) < 2 or dag.evaluate(negative_root, full) != 1:
        raise ValueError("Fault counterexample is not reproduced on original model DAG")
    clauses, _ = tseitin(dag, negative_root)
    assignment = n1["negative"]["CNF_assignment"]
    if not all(any(assignment[abs(lit)] == (1 if lit > 0 else -1) for lit in c) for c in clauses):
        raise ValueError("Fault counterexample does not satisfy the exact CNF")
    if any(sha(ROOT / rel) != digest for rel, digest in hashes.items()):
        raise ValueError("Proof/checker inputs changed during audit")

    executions = [
        {"pass": 1, "command": "python scripts/verification/lec_onehot_sat.py --out results/dm_alu_onehot_cnf_20261010_p1.json --controls results/lec_onehot_sat_controls_20261010.json",
         "native_exit_code": 0, "tool_chunks": ["7d79ef", "0948cc"],
         "tool_session_id": 90306,
         "tool_reported_wait_seconds": [10.0151781, 0.000013],
         "total_native_elapsed_seconds": None,
         "timing_note": "First invocation yielded; tool wait durations are not complete native process elapsed time."},
        {"pass": 2, "command": "python scripts/verification/lec_onehot_sat.py --out results/dm_alu_onehot_cnf_20261010_p2.json --controls results/lec_onehot_sat_controls_20261010.json",
         "native_exit_code": 0, "tool_chunks": ["905c13"],
         "tool_reported_wall_time_seconds": 9.5508768},
    ]
    receipt = {"status": "VERIFIED_TWO_INDEPENDENT_CNF_BOOLEAN_MODEL_EXECUTIONS",
               "scope": "Fourteen current DM ALU one-hot next-state obligations only; same recorded assumptions as bounded BDD stage",
               "full_sequential_LEC": "OPEN", "source_undefined_zero_abstraction_gap": "OPEN",
               "independent_kernel_review": "PENDING_SEPARATE_REVIEW_RECEIPT",
               "memory_enforcement": memory, "input_and_evidence_sha256": hashes,
               "counts": a["counts"], "all_fields_and_bytes_match": True,
               "fields_ignored_in_pair_comparison": [],
               "actual_model_negative_controls_paired_and_replayed": True,
               "negative_control_original_code": old_code, "negative_control_mutated_code": bad_code,
               "negative_control_activation_fraction": "1 / 16777216",
               "checker_control_groups": 20, "replayed_obligations": checked,
               "native_independent_executions": executions,
               "audit_is_measurement_double_execution": False,
               "heavy_external_formal_tools_executed": False}
    destinations[0].write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    rows = ["# Current DM ALU Boolean CNF subproof", "",
            "The fourteen raw-model ALU next-state one-hot obligations are UNSAT under exactly the recorded reset-deasserted conditions and each own current one-hot code. Two independent native CLI invocations reproduce every field and byte. This audit reconstructs all fourteen original cones and separately replays their exact resolution derivations of the empty clause.", "",
            "The original source's undefined-zero Boolean abstraction gap and full sequential RTL-to-netlist equivalence remain OPEN. No assumptions on other state groups, gold-only constant candidates or unreset memory contents were added. Independent kernel review is a separate pending receipt.", "",
            "All cases contain 4958 CNF variables and 12142 initial clauses; the proof search used 694-762 decisions, 38-41 conflicts and 2538-2685 resolution steps per case. The process had a kernel-enforced 512 MiB limit and a 10-second deadline per obligation.", "",
            "Twenty checker control groups include exhaustive small CNF/encoding truth tables, malformed resolution certificates and explicit UNKNOWN limits. Two independently executed actual-model controls prove the unchanged AXI baseline and detect an in-memory fault activating only when 24 free input bits all equal 1. At the raw-DAG witness the original code is `[1, 0, 0]` and the mutated code is `[1, 1, 0]`.", "",
            "| Current ALU bit | Resolution steps |", "|---:|---:|"]
    rows += [f"| {row['active_current_bit']} | {row['resolution_steps_replayed']} |" for row in checked]
    rows += ["", "Both actual native invocations exited 0. The second completed within the tool-reported 9.5508768 seconds. The first yielded its tool call; a complete native wall time was not captured and is not inferred from the polling interval.", "",
             "Source, input, execution and control hashes are recorded in the companion JSON. The retained AIG and RTL files were not modified.", ""]
    destinations[1].write_text("\n".join(rows), encoding="ascii")
    print("PASS: paired 14 ALU CNF proofs and actual-model controls reread and replayed")


if __name__ == "__main__":
    main()
