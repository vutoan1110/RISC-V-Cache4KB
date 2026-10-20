"""Independent raw reset-base prerequisite review for the joint subproof.

No invariant constants/duplicate equalities are assumed while checking reset.
Only the existing explicit reset protocol is cofactered; all other Q/input
symbols remain free. This does not prove arbitrary reset-sequence closure.
"""
from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
from review_lec_onehot_cnf import ROOT, digest, memory_cap, peak_memory, read_graph
from review_lec_joint_invariant import AliasModel, independent_spec


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if out.exists() or not out.is_relative_to(ROOT):
        raise ValueError("New research reset-prerequisite review output required")
    enforcement = memory_cap()
    started = time.monotonic()
    inputs = ["asic/equiv/lec/gold_god_r14.aig", "asic/equiv/lec/pairsAR14.json",
              "asic/equiv/lec/AR14_spec.json", "results/dm_reset_base_structural_20261010_p1.json",
              "results/dm_reset_base_structural_20261010_p2.json",
              "results/lec_joint_invariant_independent_review_20261010.json",
              "scripts/verification/review_lec_onehot_cnf.py",
              "scripts/verification/review_lec_joint_invariant.py",
              "scripts/verification/review_lec_joint_reset_base.py"]
    hashes = {rel: digest(ROOT / rel) for rel in inputs}
    graph = read_graph(ROOT / inputs[0])
    pairs, spec = [json.loads((ROOT / rel).read_text()) for rel in inputs[1:3]]
    info = independent_spec(graph, pairs, spec)
    saved = [json.loads((ROOT / rel).read_text()) for rel in inputs[3:5]]
    if saved[0] != saved[1] or hashes[inputs[3]] != hashes[inputs[4]]:
        raise ValueError("Reset-base independent pair differs")
    protocol = AliasModel(graph, {"reset_n": 0}, {})
    actual_protocol = [protocol.outputs["lec_d_p19088"], protocol.outputs["lec_d_p19089"]]
    if actual_protocol != [0, 0]:
        raise ValueError("Reset protocol does not universally establish synchronizer0")
    del protocol
    gc.collect()
    conditions = {"reset_n": 0, "lec_q_p19088": 0, "lec_q_p19089": 0}
    if saved[0]["assignments_after_reset_edge"] != conditions:
        raise ValueError("Recorded reset base uses a different phase")
    model = AliasModel(graph, conditions, {})
    constants = []
    for name, expected in info["constants"].items():
        actual = model.outputs[name.replace("lec_q_", "lec_d_")]
        if actual != expected:
            raise ValueError("Raw reset constant not exact at " + name)
        constants.append({"Q": name, "D": name.replace("lec_q_", "lec_d_"),
                          "expected": expected, "actual_raw_literal": actual, "status": "PASS"})
    duplicates = []
    for name, partner in info["duplicate_aliases"].items():
        a, b = [model.outputs[x.replace("lec_q_", "lec_d_")] for x in (name, partner)]
        if a != b:
            raise ValueError("Raw reset duplicate equality not exact at " + name)
        duplicates.append({"Q": name, "paired_Q": partner, "D": name.replace("lec_q_", "lec_d_"),
                           "paired_D": partner.replace("lec_q_", "lec_d_"),
                           "actual_raw_D_literals": [a, b], "status": "PASS"})
    groups = []
    for group in info["onehot_groups"]:
        code = [model.outputs[name] for name in group["D"]]
        row = next(r for r in saved[0]["onehot_reset"] if r["name"] == group["name"])
        if any(x not in (0, 1) for x in code) or sum(code) != 1 or code != row["reset_code"]:
            raise ValueError("Raw one-hot reset code not exact at " + group["name"])
        groups.append({"name": group["name"], "D": group["D"], "actual_raw_reset_code": code,
                       "status": "PASS"})
    if any(digest(ROOT / rel) != value for rel, value in hashes.items()):
        raise ValueError("Reset-prerequisite review input changed")
    receipt = {"status": "PASS_INDEPENDENT_RAW_JOINT_RESET_PREREQUISITE_REVIEW",
               "full_sequential_LEC": "OPEN", "source_undefined_zero_abstraction_gap": "OPEN",
               "interrupted_or_arbitrary_reset_phase_invariant_closure": "OPEN",
               "scope": "Exact recorded reset-base Boolean prerequisites only, with external reset asserted; synchronizer0 follows its checked raw protocol. No invariant premise or unreset-state tie is assumed.",
               "input_sha256": hashes, "memory_enforcement": enforcement, "peak_memory": peak_memory(),
               "elapsed_seconds": round(time.monotonic() - started, 3),
               "unrestricted_external_asserted_reset_synchronizer_D": actual_protocol,
               "subsequent_explicit_reset_phase": conditions,
               "other_unassigned_raw_inputs": graph["inputs"] - len(conditions),
               "constant_invariant_assumptions_applied": 0, "duplicate_alias_substitutions_applied": 0,
               "unreset_state_zero_axiom_used": False,
               "independent_parser_cofactor": True, "external_or_SAT_tools_executed": False,
               "constant_targets": constants, "duplicate_targets": duplicates, "onehot_group_targets": groups,
               "counts": {"constant": len(constants), "duplicate": len(duplicates), "onehot_group": len(groups)}}
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print(receipt["status"], receipt["counts"], flush=True)


if __name__ == "__main__":
    main()
