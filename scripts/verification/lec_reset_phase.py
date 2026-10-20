"""Current raw-gold invariant closure across all reachable sampled reset phases.

Exact scope is completed clock steps of the existing Boolean graph; asynchronous
between-edge source reset/X semantics and full sequential LEC remain OPEN.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from lec_joint_invariant import (alias_cofactor, assess, joint_predicate, nonvacuity,
                                 recheck_counterexample, specification, xor)
from lec_onehot_boolean import ROOT, DAG, BoundReached, enforce_process_memory, sha
from lec_reset_base import read_aig_bytes

PHASES = [(external, meta, sync) for external in (0, 1)
          for meta, sync in ((0, 0), (1, 0), (1, 1))]
SECONDS = 10.0


def relation(meta, sync):
    if type(meta) is not int or type(sync) is not int or meta not in (0, 1) or sync not in (0, 1):
        raise ValueError("Boolean synchronizer phase required")
    return not sync or bool(meta)


def conditions_for(phase):
    if len(phase) != 3 or any(type(v) is not int or v not in (0, 1) for v in phase) or tuple(phase) not in PHASES:
        raise ValueError("Require exactly one of six established reachable phases")
    external, meta, sync = phase
    return {"reset_n": external, "lec_q_p19088": meta, "lec_q_p19089": sync}


def protocol_phase(graph, phase):
    conditions = conditions_for(phase)
    external, meta, sync = phase
    dag = DAG(graph["inputs"], time.monotonic() + SECONDS)
    try:
        outputs = dag.cofactor(graph, conditions)
        actual = [outputs["lec_d_p19088"], outputs["lec_d_p19089"]]
        expected = [external, external & meta]
        status = "PROVED_STRUCTURAL_PHASE_TRANSITION" if actual == expected else "UNKNOWN"
    except (BoundReached, MemoryError, RecursionError) as exc:
        actual, expected, status = str(exc), [external, external & meta], "UNKNOWN"
    return {"phase": list(phase), "assignments": conditions,
            "expected_next_meta_sync": expected, "actual_D_literals": actual,
            "expected_next_relation_R": relation(*expected), "status": status,
            "joint_invariant_assumed_for_protocol": False}


def phase_closures(graph, info, phase):
    constants, aliases = info["constants"], info["duplicate_aliases"]
    phase_conditions = conditions_for(phase)
    assignments = {**constants, **phase_conditions}
    rows = []
    dag = DAG(graph["inputs"], time.monotonic() + SECONDS)
    outputs = alias_cofactor(dag, graph, assignments, aliases, aliases)
    premise = joint_predicate(dag, graph, info, assignments)
    point = nonvacuity(graph, info, phase_conditions)
    for qname, expected in constants.items():
        dag.deadline = time.monotonic() + SECONDS
        dname = qname.replace("lec_q_", "lec_d_")
        row = {"kind": "constant", "Q": qname, "D": dname, "expected": expected,
               "reset_conditions": phase_conditions, "nonvacuity": point}
        row.update(assess(dag, premise, outputs[dname] ^ expected))
        recheck_counterexample(graph, info, phase_conditions, row)
        rows.append(row)
    for qname, partner in aliases.items():
        dag.deadline = time.monotonic() + SECONDS
        dname, pname = qname.replace("lec_q_", "lec_d_"), partner.replace("lec_q_", "lec_d_")
        row = {"kind": "duplicate", "Q": qname, "paired_Q": partner,
               "D": dname, "paired_D": pname, "reset_conditions": phase_conditions, "nonvacuity": point}
        row.update(assess(dag, premise, xor(dag, outputs[dname], outputs[pname])))
        recheck_counterexample(graph, info, phase_conditions, row)
        rows.append(row)
    print("phase", phase, "constant/duplicate", len(rows), flush=True)
    del dag, outputs
    for group in info["onehot_groups"]:
        for active in range(len(group["Q"])):
            conditions = {**phase_conditions, **{name: int(i == active) for i, name in enumerate(group["Q"])}}
            row = {"kind": "onehot", "group": group["name"], "active_current_bit": active,
                   "group_Q": group["Q"], "D": group["D"], "reset_conditions": conditions,
                   "nonvacuity": nonvacuity(graph, info, conditions)}
            dag = DAG(graph["inputs"], time.monotonic() + SECONDS)
            try:
                assignments = {**constants, **conditions}
                outputs = alias_cofactor(dag, graph, assignments, aliases, aliases)
                premise = joint_predicate(dag, graph, info, assignments)
                row.update(assess(dag, premise, dag.onehot_violation([outputs[name] for name in group["D"]])))
                recheck_counterexample(graph, info, conditions, row)
            except (BoundReached, MemoryError, RecursionError) as exc:
                row["decision"] = {"status": "UNKNOWN", "reason": str(exc), "counterexample": None}
            rows.append(row)
            print("phase", phase, group["name"], active, row["decision"]["status"], flush=True)
    if len(rows) != 286:
        raise ValueError("Complete per-phase joint closure population required")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--controls", required=True)
    args = parser.parse_args()
    out, controls = Path(args.out).resolve(), Path(args.controls).resolve()
    if out.exists() or not out.is_relative_to(ROOT) or not controls.is_relative_to(ROOT):
        raise ValueError("New research phase output and current controls required")
    memory = enforce_process_memory()
    ctrl = json.loads(controls.read_text())
    if ctrl["status"] != "PASS_RESET_PHASE_CHECKER_CONTROLS":
        raise ValueError("Successful current phase controls required")
    for rel, digest in ctrl["source_sha256"].items():
        if sha(ROOT / rel) != digest:
            raise ValueError("Frozen phase/CNF checker changed since controls")
    paths = [ROOT / p for p in ("asic/equiv/lec/gold_god_r14.aig", "asic/equiv/lec/pairsAR14.json",
                               "asic/equiv/lec/AR14_spec.json", "results/dm_reset_phase_hypothesis_20261010.md",
                               "scripts/verification/lec_reset_phase.py", "scripts/verification/lec_joint_invariant.py",
                               "scripts/verification/lec_onehot_sat.py", "scripts/verification/lec_onehot_boolean.py",
                               "scripts/verification/lec_reset_base.py",
                               "results/dm_reset_base_structural_20261010_p1.json",
                               "results/dm_reset_base_structural_20261010_p2.json",
                               "results/dm_joint_invariant_20261010_p1.json",
                               "results/dm_joint_invariant_20261010_p2.json",
                               "results/lec_joint_invariant_independent_review_20261010.json",
                               "results/lec_joint_reset_base_independent_review_20261010.json")]
    paths.append(controls)
    hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    bases = [json.loads(p.read_text()) for p in paths[9:11]]
    steps = [json.loads(p.read_text()) for p in paths[11:13]]
    if bases[0] != bases[1] or bases[0]["status"] != "PROVED_GOLD_RESET_SUBOBLIGATIONS_ONLY" or steps[0] != steps[1]:
        raise ValueError("Paired settled reset base and deasserted step prerequisites required")
    reviews = [json.loads(p.read_text()) for p in paths[13:15]]
    if reviews[0]["status"] != "PASS_INDEPENDENT_JOINT_INVARIANT_REVIEW" or \
            reviews[1]["status"] != "PASS_INDEPENDENT_RAW_JOINT_RESET_PREREQUISITE_REVIEW":
        raise ValueError("Independent raw joint/base prerequisite review required")
    for receipt, key in ((bases[0], "inputs"), (steps[0], "input_sha256")):
        for rel, digest in receipt[key].items():
            if sha(ROOT / rel) != digest:
                raise ValueError("Phase prerequisite does not pin current raw inputs")
    graph = read_aig_bytes(paths[0].read_bytes())
    pairs, spec = json.loads(paths[1].read_text()), json.loads(paths[2].read_text())
    info = specification(graph, pairs, spec)
    phases = []
    for phase in PHASES:
        protocol = protocol_phase(graph, phase)
        rows = phase_closures(graph, info, phase)
        counts = {status: sum(row["decision"]["status"] == status for row in rows)
                  for status in ("PROVED_STRUCTURAL_COFACTOR", "PROVED_BOOLEAN_CNF",
                                 "DISPROVED_UNDER_RECORDED_ASSUMPTIONS", "UNKNOWN")}
        phases.append({"phase": list(phase), "phase_relation_R": relation(phase[1], phase[2]),
                       "protocol": protocol, "counts": counts, "obligations": rows})
        print("completed phase", phase, json.dumps(counts), flush=True)
    if any(sha(ROOT / rel) != digest for rel, digest in hashes.items()):
        raise ValueError("Pinned phase inputs changed during execution")
    receipt = {"status": "BOUNDED_REACHABLE_SAMPLED_RESET_PHASE_SUBPROOF_ONLY",
               "memory_enforcement": memory, "input_sha256": hashes,
               "joint_invariant_I_Q": info,
               "phase_relation_R": "(not reset_sync_Q) OR reset_meta_Q; reachable pair codes00,10,11 after established sampled reset protocol",
               "phase_order": [list(p) for p in PHASES], "phase_count": 6,
               "closure_obligations_per_phase": 286, "total_closure_obligations": 1716,
               "establishing_base": "First sampled asserted external reset forces meta/sync D00 regardless of prior synchronizer state; second sampled asserted edge invokes the already universal gold reset base. No unreset memory/register zero axiom.",
               "interrupted_reset_scope": "External reset may change arbitrarily between completed raw-model clock steps; each resulting reachable phase is covered",
               "event_scope": "Existing Boolean graph after recorded frontend transforms; completed clock steps only",
               "between_edge_asynchronous_source_events": "OPEN",
               "source_undefined_zero_abstraction_gap": "OPEN", "raw_N1_final_reset_coupling": "OPEN",
               "full_sequential_LEC": "OPEN", "independent_phase_review": "PENDING_SEPARATE_REVIEW_RECEIPT",
               "limits": {"process_memory_bytes": 512 * 1024 * 1024, "seconds_per_obligation": SECONDS},
               "phases": phases, "external_formal_tools_executed": False}
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print("Completed all six sampled reset phases; source/event/full LEC scopes remain OPEN", flush=True)


if __name__ == "__main__":
    main()
