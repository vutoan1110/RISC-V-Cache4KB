"""Freeze exact main-RAM unused-A checker after finite/raw controls."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import check_ram_bank_default_definedness as checker
from review_bht_definedness import bits
from review_lec_onehot_cnf import ROOT, digest, memory_cap, peak_memory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    out = parser.parse_args().out.resolve()
    if out.exists() or not out.is_relative_to(ROOT):
        raise ValueError("New research control output required")
    guard = memory_cap()
    proof = checker.prove()
    if len(proof["targets"]) != 49 or sum(len(row["cases"]) for row in proof["targets"]) != 392:
        raise ValueError("Actual positive control completeness differs")
    raw_faults = [row["negative_controls"] for row in proof["targets"]]
    if len(raw_faults) != 49 or any(len(row) != 2 for row in raw_faults):
        raise ValueError("Actual semantic fault-control completeness differs")
    widths = {"\\idx": 3, "\\word": 8, "\\bit": 1}
    finite = []
    valid = [("\\idx", [("\\idx", i) for i in range(3)]),
             ("{ \\idx 2'10 }", [0, 1, *( ("\\idx", i) for i in range(3))]),
             ("\\word [5:2]", [("\\word", i) for i in range(2, 6)]),
             ("{ 1'1 \\bit 1'0 }", [0, ("\\bit", 0), 1]),
             ("9'x", [("UNDEFINED", "x", i) for i in range(9)])]
    for expression, expected in valid:
        if bits(expression, widths) != expected:
            raise ValueError("SigSpec finite data-order control failed")
        finite.append({"expression": expression, "status": "PASS"})
    invalid = ["\\missing", "\\word [8]", "\\word [2:5]", "{ \\idx", "\\idx }", "{ \\idx } \\bit", "3'xx", "\\idx [3:0]"]
    for expression in invalid:
        try:
            bits(expression, widths)
        except ValueError:
            finite.append({"malformed_expression_rejected": expression, "status": "PASS"})
        else:
            raise ValueError("Malformed SigSpec was accepted")
    declarations, cells, unused, unused_rows = checker.parse(ROOT / checker.RAW)
    widths = {name: row["width"] for name, row in declarations.items()}
    baseline = checker.RawSelectors(widths, cells)
    cell = cells["$procmux$24571_CMP0"]
    mutant = copy.deepcopy(cell)
    mutant["parameters"]["\\A_SIGNED"] = "1"
    changed = dict(cells)
    changed[cell["name"]] = mutant
    try:
        checker.RawSelectors(widths, changed).vector("$procmux$24571_CMP", checker.WRITE_BANK, 0)
    except ValueError:
        finite.append({"malformed_actual_signed_decoder_rejected": cell["name"], "status": "PASS"})
    else:
        raise ValueError("Signed actual decoder change was not rejected")
    changed_widths = dict(widths)
    changed_widths[checker.WRITE_BANK] = 4
    try:
        checker.RawSelectors(changed_widths, cells).vector("$procmux$24571_CMP", checker.WRITE_BANK, 0)
    except ValueError:
        finite.append({"malformed_actual_bank_width_rejected": 4, "status": "PASS"})
    else:
        raise ValueError("Changed raw input width was not rejected")
    hashes = dict(proof["input_sha256"])
    own = Path(__file__).relative_to(ROOT).as_posix()
    hashes[own] = digest(Path(__file__))
    if any(digest(ROOT / rel) != expected for rel, expected in hashes.items()):
        raise ValueError("Control input changed")
    receipt = {"status": "PASS_MAIN_RAM_BANK_DEFINEDNESS_PRE_RUN_CONTROLS",
               "source_sha256": hashes, "frozen_checker_before_main_pair": True,
               "actual_positive_cases": 392, "actual_raw_faults": 98,
               "finite_data_order_and_fail_closed_controls": finite,
               "actual_raw_negative_controls": raw_faults, "memory_enforcement": guard,
               "peak_process_memory": peak_memory(), "no_original_mutation": True,
               "whole_Y_init_full_LEC_claimed": False}
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print(receipt["status"], "392positive/98rawnegative; finite", len(finite), flush=True)


if __name__ == "__main__":
    main()
