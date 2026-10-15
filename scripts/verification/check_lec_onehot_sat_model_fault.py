"""CNF verifier control on an actual pinned raw-model cone, mutated in memory.

The source AIG stays unchanged. The fault activates only when 24 otherwise free
inputs all equal 1, forcing two AXI next-state bits high.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from lec_onehot_boolean import ROOT, DAG, case_conditions, enforce_process_memory, sha
from lec_onehot_sat import decide_sat
from lec_reset_base import read_aig_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--controls", required=True)
    args = parser.parse_args()
    out, controls = Path(args.out).resolve(), Path(args.controls).resolve()
    if not out.is_relative_to(ROOT) or out.exists() or not controls.is_relative_to(ROOT):
        raise ValueError("New research control output and existing receipt required")
    memory = enforce_process_memory()
    ctrl = json.loads(controls.read_text())
    if ctrl["status"] != "PASS_BOUNDED_CNF_CHECKER_CONTROLS":
        raise ValueError("Current successful checker controls required")
    for rel, digest in ctrl["source_sha256"].items():
        if sha(ROOT / rel) != digest:
            raise ValueError("Current checker differs from controls")
    paths = [ROOT / p for p in ("asic/equiv/lec/gold_god_r14.aig",
                               "asic/equiv/lec/pairsAR14.json", "asic/equiv/lec/AR14_spec.json",
                               "scripts/verification/lec_reset_base.py",
                               "scripts/verification/lec_onehot_boolean.py",
                               "scripts/verification/lec_onehot_sat.py",
                               "scripts/verification/check_lec_onehot_sat_model_fault.py")]
    paths.append(controls)
    hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    graph = read_aig_bytes(paths[0].read_bytes())
    pairs, spec = json.loads(paths[1].read_text()), json.loads(paths[2].read_text())
    group = next(g for g in spec["onehot_gold"] if g["name"] == "axi_last_grant")
    conditions = case_conditions(graph, pairs, group, 0,
                                 {"reset_n": 1, "lec_q_p19088": 1, "lec_q_p19089": 1})
    dag = DAG(graph["inputs"], time.monotonic() + 10)
    outputs = dag.cofactor(graph, conditions)
    dnames = {i: f"lec_d_p{k:05d}" for k, (i, _) in enumerate(pairs["pairs"])}
    values = [outputs[dnames[i]] for i in group["gold"]]
    baseline = decide_sat(dag, dag.onehot_violation(values))
    if baseline["status"] != "PROVED_BOOLEAN_CNF":
        raise ValueError("Semantic fault control needs an actually proved exact baseline")
    free = [i for i, name in enumerate(graph["input_names"]) if name not in conditions][:24]
    if len(free) != 24:
        raise ValueError("Missing distinct unrestricted trigger inputs")
    trigger = 1
    for i in free:
        trigger = dag.AND(trigger, 2 * (i + 1))
    mutated = [dag.OR(values[0], trigger), dag.OR(values[1], trigger), *values[2:]]
    negative = decide_sat(dag, dag.onehot_violation(mutated))
    if negative["status"] != "DISPROVED_UNDER_RECORDED_ASSUMPTIONS":
        raise ValueError("Missing output, timeout or UNKNOWN is not a negative-control pass")
    witness = negative["counterexample"]
    if any(witness.get(i) != 1 for i in free):
        raise ValueError("Fault witness must activate all 24 trigger inputs")
    complete = {i: 0 for i in range(graph["inputs"])}
    complete.update(witness)
    original_code = [dag.evaluate(value, complete) for value in values]
    faulty_code = [dag.evaluate(value, complete) for value in mutated]
    if sum(original_code) != 1 or sum(faulty_code) < 2:
        raise ValueError("Fault must be isolated to mutation with explicit raw-DAG codes")
    negative["counterexample"] = {graph["input_names"][i]: v for i, v in sorted(witness.items())}
    if any(sha(ROOT / rel) != digest for rel, digest in hashes.items()):
        raise ValueError("Pinned model/checker changed during control")
    receipt = {"status": "PASS_ACTUAL_RAW_MODEL_CNF_RARE_ONEHOT_FAULT_CONTROL",
               "scope": "Verifier control only; actual pinned raw Boolean cone, mutation in memory, source/AIG/RTL unchanged. Full sequential LEC OPEN.",
               "memory_enforcement": memory, "input_sha256": hashes,
               "group": group["name"], "active_current_bit": 0, "assignments": conditions,
               "baseline": baseline, "mutation": "D0 := D0 OR rare24; D1 := D1 OR rare24; other D unchanged",
               "trigger_inputs": [graph["input_names"][i] for i in free],
               "fault_activation_fraction_over_unrestricted_trigger_bits": "1 / 16777216",
               "negative": negative, "original_code_at_fault_witness": original_code,
               "mutated_code_at_fault_witness": faulty_code,
               "unassigned_other_free_inputs_at_witness": 0,
               "false_semantic_negative_from_missing_timeout_or_unknown_allowed": False}
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print("PASS: actual CNF baseline UNSAT; rare 24-input model fault SAT with raw-DAG witness")


if __name__ == "__main__":
    main()
