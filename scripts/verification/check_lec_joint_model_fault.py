"""Actual raw-model rare-fault control under every explicit joint premise.

Only an in-memory next-state mutation is introduced; every pinned source stays
unchanged. A SAT counterexample must satisfy the entire current I(Q).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from lec_joint_invariant import (RESET, alias_cofactor, assess, evaluate_raw,
                                 joint_predicate, nonvacuity, satisfies_joint,
                                 specification)
from lec_onehot_boolean import ROOT, DAG, enforce_process_memory, sha
from lec_reset_base import read_aig_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--controls", required=True)
    args = parser.parse_args()
    out, controls = Path(args.out).resolve(), Path(args.controls).resolve()
    if out.exists() or not out.is_relative_to(ROOT) or not controls.is_relative_to(ROOT):
        raise ValueError("New research fault-control output required")
    memory = enforce_process_memory()
    ctrl = json.loads(controls.read_text())
    if ctrl["status"] != "PASS_JOINT_INVARIANT_CHECKER_CONTROLS":
        raise ValueError("Successful joint checker controls required")
    for rel, digest in ctrl["source_sha256"].items():
        if sha(ROOT / rel) != digest:
            raise ValueError("Frozen joint/CNF checker changed")
    paths = [ROOT / p for p in ("asic/equiv/lec/gold_god_r14.aig", "asic/equiv/lec/pairsAR14.json",
                               "asic/equiv/lec/AR14_spec.json", "scripts/verification/lec_joint_invariant.py",
                               "scripts/verification/check_lec_joint_model_fault.py",
                               "scripts/verification/lec_reset_base.py",
                               "scripts/verification/lec_onehot_boolean.py",
                               "scripts/verification/lec_onehot_sat.py")]
    paths.append(controls)
    hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    graph = read_aig_bytes(paths[0].read_bytes())
    pairs, spec = json.loads(paths[1].read_text()), json.loads(paths[2].read_text())
    info = specification(graph, pairs, spec)
    group = info["onehot_groups"][0]
    conditions = {**RESET, **{name: int(i == 0) for i, name in enumerate(group["Q"])}}
    nonvacuity_witness = nonvacuity(graph, info, conditions)
    assignments = {**info["constants"], **conditions}
    dag = DAG(graph["inputs"], time.monotonic() + 10)
    outputs = alias_cofactor(dag, graph, assignments, info["duplicate_aliases"], info["duplicate_aliases"])
    premise = joint_predicate(dag, graph, info, assignments)
    values = [outputs[name] for name in group["D"]]
    baseline = assess(dag, premise, dag.onehot_violation(values))
    if baseline["decision"]["status"] not in ("PROVED_STRUCTURAL_COFACTOR", "PROVED_BOOLEAN_CNF"):
        raise ValueError("Fault control requires an actual baseline proof under all joint premises")
    excluded = set(assignments) | set(info["duplicate_aliases"]) | \
        {name for g in info["onehot_groups"] for name in g["Q"]}
    free = [i for i, name in enumerate(graph["input_names"]) if name not in excluded][:24]
    if len(free) != 24:
        raise ValueError("Missing 24 independently free trigger inputs")
    trigger = 1
    for i in free:
        trigger = dag.AND(trigger, 2 * (i + 1))
    mutated = [dag.OR(values[0], trigger), dag.OR(values[1], trigger), *values[2:]]
    dag.deadline = time.monotonic() + 10
    negative = assess(dag, premise, dag.onehot_violation(mutated))
    if negative["decision"]["status"] != "DISPROVED_UNDER_RECORDED_ASSUMPTIONS":
        raise ValueError("Missing, timeout or UNKNOWN is not a semantic negative-control PASS")
    witness = negative["decision"]["counterexample"]
    if any(witness.get(i) != 1 for i in free):
        raise ValueError("Rare witness must activate all trigger inputs")
    full = dict.fromkeys(graph["input_names"], 0)
    full.update({graph["input_names"][i]: value for i, value in witness.items()})
    full.update(info["constants"])
    full.update(conditions)
    for source, target in info["duplicate_aliases"].items():
        full[source] = full[target]
    if not satisfies_joint(full, info, conditions):
        raise ValueError("Fault witness fails an explicit joint premise")
    original = evaluate_raw(graph, full)
    original_code = [original[name] for name in group["D"]]
    mutated_code = [original_code[0] | 1, original_code[1] | 1, *original_code[2:]]
    numeric = {i: full[name] for i, name in enumerate(graph["input_names"])}
    if sum(original_code) != 1 or sum(mutated_code) < 2 or \
            [dag.evaluate(v, numeric) for v in mutated] != mutated_code or \
            dag.evaluate(negative["conditional_violation_literal"], numeric) != 1:
        raise ValueError("Fault does not reproduce on original raw graph with every premise satisfied")
    negative["decision"]["counterexample"] = {
        graph["input_names"][i]: value for i, value in sorted(witness.items())}
    if any(sha(ROOT / rel) != digest for rel, digest in hashes.items()):
        raise ValueError("Frozen source/model changed during control")
    receipt = {"status": "PASS_ACTUAL_RAW_MODEL_JOINT_PREMISE_RARE_FAULT_CONTROL",
               "scope": "Actual current-gold Boolean model with a mutation only in memory; every constant/duplicate/one-hot premise satisfied, no hardware defect claim",
               "full_sequential_LEC": "OPEN", "source_undefined_zero_abstraction_gap": "OPEN",
               "memory_enforcement": memory, "input_sha256": hashes,
               "joint_invariant_I_Q": info, "reset_and_own_code_conditions": conditions,
               "nonvacuity": nonvacuity_witness, "group": group["name"],
               "baseline": baseline, "negative": negative,
               "trigger_inputs": [graph["input_names"][i] for i in free],
               "activation_fraction": "1 / 16777216",
               "mutation": "D0 := D0 OR rare24; D1 := D1 OR rare24; other D unchanged",
               "original_raw_D_code_at_witness": original_code,
               "mutated_D_code_at_witness": mutated_code,
               "counterexample_satisfies_every_joint_premise": True,
               "other_unassigned_free_values_at_witness_only": 0,
               "unreset_state_zero_axiom_used": False}
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print("PASS: joint baseline proved; rare raw-model mutation has a premise-valid SAT witness")


if __name__ == "__main__":
    main()
