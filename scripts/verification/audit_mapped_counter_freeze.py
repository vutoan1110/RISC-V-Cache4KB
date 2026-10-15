"""Verify paired local freeze audit receipts and unchanged source provenance.

This rereads evidence; it does not execute a third proof or simulation.
Independent cone/certificate review has its own separate receipt.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lec_onehot_boolean import ROOT, enforce_process_memory, sha


def verify_pair(folder, design):
    folder = folder.resolve()
    left, right = [folder / f"{design.lower()}_p{number}.json" for number in (1, 2)]
    if left.read_bytes() != right.read_bytes():
        raise ValueError(f"{design}: paired receipts differ in bytes")
    record = json.loads(left.read_text(encoding="utf-8"))
    expected_expression = "~dut._029058_" if design == "DM" else "~dut._031249_"
    if record.get("status") != "VERIFIED_COUNTER_FREEZE_ALIAS" or record.get("design") != design or \
            record.get("expression") != expected_expression or record.get("MCYCLE_width") != 32 or \
            record.get("counter_hold_increment_bridge_verified") is not True or record.get("assumptions") != []:
        raise ValueError("Incomplete or wrong local mapping contract")
    if sha(ROOT / record["netlist"]) != record["netlist_sha256"]:
        raise ValueError("Changed frozen netlist")
    current_inputs = {name: sha(ROOT / name) for name in record["source_inputs"]}
    if current_inputs != record["source_inputs"] or sha(ROOT / "asic/soc_dm_4kb/formal_pdk.v") != record["PDK_sha256"] or \
            sha(ROOT / "scripts/verification/mapped_counter_freeze.py") != record["script_sha256"]:
        raise ValueError("Changed source/checker/PDK provenance")
    expected = {"total_counter_freeze_source_decode"} | \
               {f"MCYCLE_increment_bit_{i:02d}_modulo_2pow32" for i in range(32)} | \
               {f"MCYCLE_D_bit_{i:02d}_clear_hold_increment" for i in range(32)}
    rows = record["proofs"]
    if len(rows) != 65 or len({r["label"] for r in rows}) != 65 or {r["label"] for r in rows} != expected:
        raise ValueError("Incomplete/duplicate proof obligations")
    counts = {"structural": 0, "certificate_CNF": 0}
    for row in rows:
        decision = row["decision"]
        if decision.get("counterexample") is not None:
            raise ValueError("Positive obligation has a counterexample")
        if decision["status"] == "PROVED_STRUCTURAL_BOOLEAN":
            if row["violation_literal"] != 0:
                raise ValueError("Structural status without an exact zero literal")
            counts["structural"] += 1
        elif decision["status"] == "PROVED_BOOLEAN_CNF":
            if not isinstance(decision.get("terminal_empty_clause_derivation"), dict) or \
                    not isinstance(decision.get("resolution_certificate"), list):
                raise ValueError("CNF closure lacks a replayable saved certificate")
            counts["certificate_CNF"] += 1
        else:
            raise ValueError("Positive obligation remains unproved")
    drows = [r for r in rows if r["label"].startswith("MCYCLE_D")]
    if len({r["flop"]["cell"] for r in drows}) != 32 or {r["bit"] for r in drows} != set(range(32)):
        raise ValueError("Counter D consumers are not 32 unique real flops")
    negatives = record["negative_controls"]
    if len(negatives) != 3 or {r["label"] for r in negatives} != {
            "negative_freeze_q_only", "negative_wrong_polarity", "negative_omit_request_acceptance"}:
        raise ValueError("Incomplete semantic wrong-observer controls")
    for row in negatives:
        decision = row["decision"]
        if decision["status"] != "DISPROVED_UNDER_RECORDED_ASSUMPTIONS" or \
                not isinstance(decision.get("counterexample"), dict) or \
                decision.get("counterexample_original_DAG_evaluation") != 1 or \
                row["actual_at_witness"] == row["wrong_expression_at_witness"]:
            raise ValueError("Fault control lacks its actual saved Boolean witness")
    return {"design": design, "pair_equal_all_fields_and_bytes": True,
            "receipt_paths": [p.relative_to(ROOT).as_posix() for p in (left, right)],
            "receipt_sha256": sha(left), "netlist_sha256": record["netlist_sha256"],
            "expression": expected_expression, "positive_obligations": 65,
            "positive_method_counts": counts, "actual_negative_controls": 3,
            "source_checker_PDK_netlist_hashes_match_now": True,
            "proof_checker_sha256": record["script_sha256"], "source_inputs": current_inputs,
            "certificate_replay_here": "NOT_REPEATED: independent review receipt is separate"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    memory = enforce_process_memory()
    result = {"status": "VERIFIED_TWO_INDEPENDENT_LOCAL_COUNTER_FREEZE_PROOF_EXECUTIONS",
              "memory_guard": memory, "results": [verify_pair(args.folder, d) for d in ("DM", "SA2")],
              "receipt_checker_sha256": sha(Path(__file__)),
              "native_execution": [
                  {"case": "DM p1", "chunk": "a51fa4", "exit_code": 0, "wall_seconds": 3.2827955},
                  {"case": "DM p2", "chunk": "696b36", "exit_code": 0, "wall_seconds": 3.8082651},
                  {"case": "SA2 p1", "chunk": "88ad2b", "exit_code": 0, "wall_seconds": 3.0775077},
                  {"case": "SA2 p2", "chunk": "332c6c", "exit_code": 0, "wall_seconds": 3.0406196}],
              "prior_checker_diagnostic": {
                  "preserved_path": "results/mapped_counter_freeze_20261010/dm_p1.json",
                  "status": "UNVERIFIED_COUNTER_FREEZE_ALIAS",
                  "reason": "Original checker treated mapped bit0 increment as an independent symbol on one side. Expanding its actual !Q0 driver on both sides closed the exact algebraic relation; no design input changed."},
              "scope": "Local Boolean observer alias and 32-bit MCYCLE increment/D-consumer cones only. Full SoC LEC, asynchronous event/delay behavior and initialization remain outside this proof."}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "out": str(args.out)}))


if __name__ == "__main__":
    main()
