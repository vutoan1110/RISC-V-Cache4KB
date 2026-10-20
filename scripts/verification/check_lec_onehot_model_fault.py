"""Negative control on the pinned raw Boolean model, without changing any file.

The proved AXI cone is unchanged unless24 selected free input bits are all1.
Only then two next-state bits are forced high, creating an explicit one-hot fault.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from lec_onehot_boolean import (ROOT, DAG, case_conditions, decide,
                                enforce_process_memory, sha)
from lec_reset_base import read_aig_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if not out.is_relative_to(ROOT) or out.exists():
        raise ValueError("New research control output required")
    memory = enforce_process_memory()
    paths = [ROOT / p for p in ("asic/equiv/lec/gold_god_r14.aig",
                               "asic/equiv/lec/pairsAR14.json", "asic/equiv/lec/AR14_spec.json",
                               "scripts/verification/lec_reset_base.py",
                               "scripts/verification/lec_onehot_boolean.py",
                               "scripts/verification/check_lec_onehot_model_fault.py")]
    hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    graph = read_aig_bytes(paths[0].read_bytes())
    pairs, spec = json.loads(paths[1].read_text()), json.loads(paths[2].read_text())
    group = next(g for g in spec["onehot_gold"] if g["name"] == "axi_last_grant")
    reset = {"reset_n": 1, "lec_q_p19088": 1, "lec_q_p19089": 1}
    conditions = case_conditions(graph, pairs, group, 0, reset)
    dag = DAG(graph["inputs"], time.monotonic() + 10)
    outputs = dag.cofactor(graph, conditions)
    dnames = {i: f"lec_d_p{k:05d}" for k, (i, _) in enumerate(pairs["pairs"])}
    values = [outputs[dnames[i]] for i in group["gold"]]
    baseline = decide(dag, dag.onehot_violation(values))
    if baseline["status"] != "PROVED_BOOLEAN_COFACTOR":
        raise ValueError("Negative control requires an actually proved exact baseline")
    free = [i for i, name in enumerate(graph["input_names"]) if name not in conditions][:24]
    if len(free) != 24:
        raise ValueError("Missing24 distinct unrestricted trigger inputs")
    trigger = 1
    for i in free:
        trigger = dag.AND(trigger, 2 * (i + 1))
    mutated = [dag.OR(values[0], trigger), dag.OR(values[1], trigger), *values[2:]]
    negative = decide(dag, dag.onehot_violation(mutated))
    if negative["status"] != "DISPROVED_UNDER_RECORDED_ASSUMPTIONS":
        raise ValueError("A resource failure/unknown/missing output is not a negative-control PASS")
    witness = negative["counterexample"]
    if any(witness.get(i) != 1 for i in free):
        raise ValueError("Fault witness must activate every one of the24 trigger inputs")
    complete = {i: 0 for i in range(graph["inputs"])}
    complete.update(witness)
    original_code = [dag.evaluate(value, complete) for value in values]
    faulty_code = [dag.evaluate(value, complete) for value in mutated]
    if sum(original_code) != 1 or sum(faulty_code) < 2:
        raise ValueError("Fault must be isolated to the mutation, with an explicit original/faulty code")
    negative["counterexample"] = {graph["input_names"][i]: v for i, v in sorted(witness.items())}
    if any(sha(ROOT / rel) != h for rel, h in hashes.items()):
        raise ValueError("Pinned model or checker changed during negative control")
    j = {"status": "PASS_ACTUAL_RAW_MODEL_RARE_ONEHOT_FAULT_CONTROL",
         "scope": "An in-memory mutation of the raw Boolean transition cone; no source/AIG/RTL file changed. This is a verifier control, not a hardware defect claim.",
         "memory_enforcement": memory, "input_sha256": hashes,
         "group": group["name"], "active_current_bit": 0, "assignments": conditions,
         "baseline": baseline, "mutation": "D0 := D0 OR rare24; D1 := D1 OR rare24; other D unchanged",
         "trigger_inputs": [graph["input_names"][i] for i in free],
         "fault_activation_fraction_over_unrestricted_trigger_bits": "1 /16777216",
         "negative": negative, "original_code_at_fault_witness": original_code,
         "mutated_code_at_fault_witness": faulty_code,
         "unassigned_other_free_inputs_at_witness": 0,
         "false_semantic_negative_from_missing_timeout_or_unknown_allowed": False}
    out.write_text(json.dumps(j, indent=2) + "\n", encoding="ascii")
    print("PASS: exact raw-model baseline proved, rare24 fault has a re-evaluated counterexample")


if __name__ == "__main__":
    main()
