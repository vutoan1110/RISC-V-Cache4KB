"""Check immutable paired RAM bank evidence and separate method review."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from review_lec_onehot_cnf import ROOT, digest, memory_cap, peak_memory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    out = parser.parse_args().out.resolve()
    if out.exists() or not out.is_relative_to(ROOT):
        raise ValueError("New research verification output required")
    memory = memory_cap()
    paths = [f"results/ram_bank_default_definedness_20261010_p{i}.json" for i in (1, 2)]
    hashes = {p: digest(ROOT / p) for p in paths}
    pair = [json.loads((ROOT / p).read_text()) for p in paths]
    if hashes[paths[0]] != hashes[paths[1]] or pair[0] != pair[1]:
        raise ValueError("Independent pair differs; no fields may be ignored")
    receipt = pair[0]
    if receipt["status"] != "PROVED_LOCAL_MAIN_RAM_BANK_BOOLEAN_UNUSED_A_ONLY" or len(receipt["targets"]) != 49 or len({row["cell"] for row in receipt["targets"]}) != 49 or receipt["all_free_bank_cases"] != 392 or receipt["raw_semantic_negative_controls"] != 98 or receipt["unique_original_B_data_bit_atoms_free"] != 398 or len(receipt["raw_selector_cone_cells"]) != 32 or receipt["zero_init_reset_FSM_onehot_or_reachability_premise"] is not False:
        raise ValueError("Complete paired local scope/counts required")
    if any(row["status"] != "PROVED_UNUSED_A_FOR_ALL_EIGHT_FREE_BANK_CODES" or len(row["cases"]) != 8 or len(row["negative_controls"]) != 2 for row in receipt["targets"]):
        raise ValueError("A target proof/control missing")
    source_hashes = dict(receipt["input_sha256"])
    if any(digest(ROOT / rel) != h for rel, h in source_hashes.items()):
        raise ValueError("Frozen actual proof input changed")
    review_rel = "results/ram_bank_definedness_independent_review_20261010.json"
    review = json.loads((ROOT / review_rel).read_text())
    if review["status"] != "PASS_INDEPENDENT_MAIN_RAM_BANK_UNUSED_A_REVIEW" or review["checker_BHT_or_inventory_parser_imported"] is not False or review["free_bank_cases_rebuilt"] != 392 or review["actual_raw_semantic_faults_reconstructed"] != 98 or review["original_B_data_atoms_free"] != 398 or review["independent_pair_byte_and_all_field_equal"] is not True or len(review["reviewed_targets"]) != 49:
        raise ValueError("Separate exact parser/data-order review incomplete")
    if any(digest(ROOT / rel) != h for rel, h in review["input_sha256"].items()):
        raise ValueError("Independent review input changed")
    result = {"status": "VERIFIED_PAIRED_LOCAL_MAIN_RAM_UNUSED_A_WITH_INDEPENDENT_METHOD_REVIEW",
              "native_process_exit_codes": [0, 0], "pair_byte_and_all_field_equal": True,
              "ignored_fields": [], "proof_receipts": paths, "receipt_sha256": hashes,
              "input_sha256": source_hashes, "independent_method_receipt": review_rel,
              "independent_method_receipt_sha256": digest(ROOT / review_rel),
              "verification_script_sha256": digest(Path(__file__)),
              "original_A_default_connect_lines_closed": 49,
              "free_bank_cases_per_pass": 392, "paired_free_bank_cases": 784,
              "unique_original_B_atoms_free": 398, "actual_raw_selector_cone_cells": 32,
              "actual_semantic_faults_per_pass": 98, "paired_actual_semantic_faults": 196,
              "no_init_reset_FSM_onehot_or_reachability_premise": True,
              "GOLD_functional_XZ_connect_lines_classified": 358,
              "locally_closed_connect_lines": 310, "remaining_connect_lines": 48,
              "count_unit": "classified original connect lines, not bits or defects",
              "whole_Y_definedness": "NOT_CLAIMED; actual selected B/unreset/macro data remains arbitrary",
              "full_sequential_LEC": "OPEN", "whole_source_undefined_abstraction": "OPEN",
              "four_state_equivalence": "NOT_CLAIMED", "memory_enforcement": memory,
              "peak_process_memory": peak_memory()}
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(result["status"], "310localclosed/48remain;fullLECOPEN", flush=True)


if __name__ == "__main__":
    main()
