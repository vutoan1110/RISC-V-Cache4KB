"""Rare synchronizer fault on actual raw GOLD under a reachable interrupted reset.

Only an in-memory Dsync mutation is made; the source model remains unchanged.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from lec_joint_invariant import (alias_cofactor, assess, evaluate_raw, joint_predicate,
                                 nonvacuity, satisfies_joint, specification)
from lec_onehot_boolean import ROOT, DAG, enforce_process_memory, sha
from lec_reset_base import read_aig_bytes
from lec_reset_phase import conditions_for, relation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--controls", required=True)
    args = parser.parse_args()
    out, controls = Path(args.out).resolve(), Path(args.controls).resolve()
    if out.exists() or not out.is_relative_to(ROOT) or not controls.is_relative_to(ROOT):
        raise ValueError("New research semantic fault-control output required")
    memory = enforce_process_memory()
    ctrl = json.loads(controls.read_text())
    if ctrl["status"] != "PASS_RESET_PHASE_CHECKER_CONTROLS":
        raise ValueError("Current successful phase controls required")
    for rel, digest in ctrl["source_sha256"].items():
        if sha(ROOT / rel) != digest:
            raise ValueError("Frozen phase/joint/CNF checker changed")
    paths = [ROOT / p for p in ("asic/equiv/lec/gold_god_r14.aig", "asic/equiv/lec/pairsAR14.json",
                               "asic/equiv/lec/AR14_spec.json", "scripts/verification/check_lec_reset_phase_fault.py",
                               "scripts/verification/lec_reset_phase.py", "scripts/verification/lec_joint_invariant.py",
                               "scripts/verification/lec_onehot_sat.py", "scripts/verification/lec_onehot_boolean.py",
                               "scripts/verification/lec_reset_base.py")]
    paths.append(controls)
    hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    graph = read_aig_bytes(paths[0].read_bytes())
    pairs, spec = json.loads(paths[1].read_text()), json.loads(paths[2].read_text())
    info = specification(graph, pairs, spec)
    phase = (0, 1, 1)
    conditions = conditions_for(phase)
    nonvacuity_witness = nonvacuity(graph, info, conditions)
    raw_dag = DAG(graph["inputs"], time.monotonic() + 10)
    raw_outputs = raw_dag.cofactor(graph, conditions)
    if [raw_outputs["lec_d_p19088"], raw_outputs["lec_d_p19089"]] != [0, 0]:
        raise ValueError("Actual synchronizer baseline needs an unrestricted raw proof")
    del raw_dag, raw_outputs
    assignments = {**info["constants"], **conditions}
    aliases = info["duplicate_aliases"]
    dag = DAG(graph["inputs"], time.monotonic() + 10)
    outputs = alias_cofactor(dag, graph, assignments, aliases, aliases)
    premise = joint_predicate(dag, graph, info, assignments)
    meta, sync = outputs["lec_d_p19088"], outputs["lec_d_p19089"]
    baseline = assess(dag, premise, dag.AND(sync, meta ^ 1))
    if baseline["decision"]["status"] != "PROVED_STRUCTURAL_COFACTOR":
        raise ValueError("Protocol mutation control needs an actual baseline proof")
    excluded = set(assignments) | set(aliases) | {name for g in info["onehot_groups"] for name in g["Q"]}
    free = [i for i, name in enumerate(graph["input_names"]) if name not in excluded][:24]
    if len(free) != 24:
        raise ValueError("Missing independent rare trigger inputs")
    rare = 1
    for i in free:
        rare = dag.AND(rare, 2 * (i + 1))
    mutated_sync = dag.OR(sync, rare)
    negative = assess(dag, premise, dag.AND(mutated_sync, meta ^ 1))
    decision = negative["decision"]
    if decision["status"] != "DISPROVED_UNDER_RECORDED_ASSUMPTIONS":
        raise ValueError("Negative control needs an actual semantic SAT witness, never a tool failure")
    witness = decision["counterexample"]
    if any(witness.get(i) != 1 for i in free):
        raise ValueError("Fault witness must activate every trigger bit")
    full = dict.fromkeys(graph["input_names"], 0)
    full.update({graph["input_names"][i]: value for i, value in witness.items()})
    full.update(info["constants"])
    full.update(conditions)
    for source, target in aliases.items():
        full[source] = full[target]
    if not satisfies_joint(full, info, conditions) or not relation(full["lec_q_p19088"], full["lec_q_p19089"]):
        raise ValueError("Fault witness violates I(Q) or reachable R(Q)")
    original = evaluate_raw(graph, full)
    original_phase = [original["lec_d_p19088"], original["lec_d_p19089"]]
    bad_phase = [original_phase[0], original_phase[1] | 1]
    numeric = {i: full[name] for i, name in enumerate(graph["input_names"])}
    if original_phase != [0, 0] or bad_phase != [0, 1] or not relation(*original_phase) or relation(*bad_phase) or \
            dag.evaluate(negative["conditional_violation_literal"], numeric) != 1:
        raise ValueError("Actual raw-model witness does not isolate a rare phase-relation fault")
    decision["counterexample"] = {graph["input_names"][i]: value for i, value in sorted(witness.items())}
    if any(sha(ROOT / rel) != digest for rel, digest in hashes.items()):
        raise ValueError("Frozen model/source changed during control")
    receipt = {"status": "PASS_ACTUAL_RAW_MODEL_RARE_RESET_PHASE_FAULT_CONTROL",
               "scope": "Semantic checker control only: actual current raw GOLD, reachable reassertion phase and all I(Q) premises, one in-memory Dsync mutation",
               "input_sha256": hashes, "memory_enforcement": memory,
               "joint_invariant_I_Q": info, "phase": list(phase), "assignments": conditions,
               "nonvacuity": nonvacuity_witness, "raw_unrestricted_meta_sync_D": [0, 0],
               "baseline": baseline, "negative": negative,
               "mutation": "Dsync := Dsync OR rare24; Dmeta unchanged",
               "trigger_inputs": [graph["input_names"][i] for i in free], "activation_fraction": "1 / 16777216",
               "original_raw_next_meta_sync": original_phase, "mutated_next_meta_sync": bad_phase,
               "original_next_relation_R": True, "mutated_next_relation_R": False,
               "counterexample_satisfies_every_joint_and_reachable_phase_premise": True,
               "other_free_values_at_witness_only": 0, "unreset_state_zero_axiom_used": False,
               "between_edge_asynchronous_source_events": "OPEN", "full_sequential_LEC": "OPEN",
               "source_undefined_zero_abstraction_gap": "OPEN"}
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print("PASS: actual interrupted-reset baseline; rare fault has premise-valid raw witness 00 -> 01")


if __name__ == "__main__":
    main()
