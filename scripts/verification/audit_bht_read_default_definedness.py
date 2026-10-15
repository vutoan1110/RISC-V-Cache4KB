"""Check paired local BHT read receipts and original source line provenance.

This audit re-reads saved independent executions. It starts no solver or
frontend and does not replace the separate review of the proof method.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
from review_lec_onehot_cnf import ROOT, digest, memory_cap, peak_memory


def raw_source_lines(path):
    text = path.read_text(encoding="ascii")
    evidence = {}
    expressions = {"table_declaration": r"reg\s+\[1:0\]\s+bht_mem\s*\[0:BHT_ENTRIES-1\]\s*;",
                   "fetch_index": r"assign\s+fetch_index\s*=\s*fetch_pc\[BHT_INDEX_BITS\+1:2\]\s*;",
                   "ASIC_fetch_state": r"assign\s+fetch_state\s*=\s*bht_mem\[fetch_index\]\s*;"}
    for name, pattern in expressions.items():
        found = list(re.finditer(pattern, text))
        if len(found) != 1:
            raise ValueError("Exactly one original source line required: " + name)
        evidence[name] = {"original_source_line": text[:found[0].start()].count("\n") + 1,
                          "matched_original_text": found[0][0]}
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if out.exists() or not out.is_relative_to(ROOT):
        raise ValueError("New research audit output required")
    enforced = memory_cap()
    pair = ["results/bht_read_default_definedness_20261010_p1.json",
            "results/bht_read_default_definedness_20261010_p2.json"]
    hashes = {path: digest(ROOT / path) for path in pair}
    receipts = [json.loads((ROOT / path).read_text(encoding="ascii")) for path in pair]
    if hashes[pair[0]] != hashes[pair[1]] or receipts[0] != receipts[1]:
        raise ValueError("Pair byte/field comparison failed; no field may be ignored")
    proof = receipts[0]
    if proof["status"] != "PROVED_LOCAL_BHT_READ_BOOLEAN_DEFAULT_DEFINEDNESS_ONLY" \
            or proof["actual_read_selector_count"] != 256 \
            or proof["actual_selector_index_support_bits"] != 8 \
            or proof["symbolic_memory_data_bits"] != 512 \
            or proof["symbolic_undefined_default_bits"] != 2 \
            or proof["IR_undefined_default_connect_lines_closed"] != 1 \
            or proof["reset_or_invariant_or_zero_initial_state_premise_used"] \
            or proof["source_or_IR_mutation_written"] \
            or proof["external_frontend_simulator_or_solver_executed"]:
        raise ValueError("Local proof count or premise scope differs")
    for path, expected in proof["input_sha256"].items():
        if digest(ROOT / path) != expected:
            raise ValueError("Proof input changed: " + path)
        hashes[path] = expected
    rows = proof["actual_selector_rows_MSB_first"]
    cases = proof["exhaustive_address_truth_cases"]
    if len(rows) != 256 or {r["decoded_index"] for r in rows} != set(range(256)) \
            or len(cases) != 256 or {r["raw_eight_bit_index"] for r in cases} != set(range(256)):
        raise ValueError("Proof records do not cover the complete actual read domain")
    for row in rows:
        code = row["decoded_index"]
        if row["driver_parameters"]["\\A_WIDTH"] != "8" \
                or row["driver_parameters"]["\\A_SIGNED"] != "0" \
                or row["driver_ports"]["\\A"] != r"\u_soc.u_core.u_pipeline.datapath.pc_f [9:2]" \
                or not row["data_word"].endswith(".bht_mem[" + str(code) + "]"):
            raise ValueError("Raw selector/data contract differs")
    for case in cases:
        if case["active_selector_count"] != 1 or case["default_selected"] \
                or len(case["output_symbolic_bits_LSB_first"]) != 2:
            raise ValueError("Default or an overlapping decoder case remains")
    negative = proof["negative_controls"]
    if negative["IR_semantic_missing_selector"]["observed_mutated_outputs"] != [0, 3] \
            or negative["exact_source_missing_last_entry"]["mutated_declared_last_entry"] != 254 \
            or len(negative["malformed_selector_or_data_controls"]) != 4 \
            or any(r["status"] != "REJECTED" for r in negative["malformed_selector_or_data_controls"]):
        raise ValueError("Required semantic or malformed-input controls are incomplete")
    lines = {contract["path"]: raw_source_lines(ROOT / contract["path"]) for contract in proof["source_contracts"]}
    hashes["scripts/verification/audit_bht_read_default_definedness.py"] = digest(Path(__file__).resolve())
    if any(digest(ROOT / path) != expected for path, expected in hashes.items()):
        raise ValueError("An audited input changed")
    receipt = {"status": "VERIFIED_PAIRED_LOCAL_BHT_READ_BOOLEAN_DEFAULT_DEFINEDNESS",
               "paired_native_process_exit_codes": [0, 0],
               "pair_byte_and_all_field_equal": True, "ignored_receipt_fields": [],
               "proof_receipts": pair, "input_sha256": hashes,
               "actual_selector_count": 256, "address_truth_cases_per_pass": 256,
               "address_truth_cases_two_independent_passes": 512,
               "free_table_data_bits": 512, "free_default_data_bits": 2,
               "semantic_negative_controls_per_pass": 2,
               "malformed_input_negative_controls_per_pass": 4,
               "actual_original_source_line_evidence": lines,
               "proof_source_read_lines_scope": "Line positions in selected/uncommented local source view; original file locations are provided separately above",
               "GOLD_functional_XZ_connect_lines_classified": 358,
               "BHT_update_and_read_connect_lines_locally_closed": 257,
               "remaining_GOLD_functional_XZ_connect_lines": 101,
               "count_scope": "Connect lines, not bit count or whole-chip defect count",
               "reset_initial_state_or_invariant_assumptions_used": False,
               "full_sequential_LEC": "OPEN", "whole_source_undefined_abstraction": "OPEN",
               "four_state_equivalence": "NOT_CLAIMED",
               "external_tools_started": False,
               "proof_method_independent_review_status": "SEPARATE_REVIEW_PENDING",
               "memory_enforcement": enforced}
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print(receipt["status"], "all fields/bytes equal; source hashes match; peak", peak_memory(), flush=True)


if __name__ == "__main__":
    main()
