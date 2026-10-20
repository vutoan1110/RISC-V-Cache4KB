"""Finite controls for the independent BHT review SigSpec interpreter.

Exercises bit/concat ordering, original wire slices, X markers and rejection
of malformed expressions. It does not run a hardware proof or measurement.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from review_bht_definedness import bits, decoder
from review_lec_onehot_cnf import ROOT, memory_cap, peak_memory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if out.exists() or not out.is_relative_to(ROOT):
        raise ValueError("New finite-control receipt required")
    enforced = memory_cap()
    widths = {r"\a": 4, r"\b": 2, r"\s": 1}
    expected = [
        ("4'1010", [0, 1, 0, 1]),
        (r"\a [3:1]", [(r"\a", 1), (r"\a", 2), (r"\a", 3)]),
        (r"\b [0]", [(r"\b", 0)]),
        (r"{ 1'1 \b \a [1:0] }", [(r"\a", 0), (r"\a", 1), (r"\b", 0), (r"\b", 1), 1]),
        (r"{ { 1'0 \b } \a [2] }", [(r"\a", 2), (r"\b", 0), (r"\b", 1), 0]),
        ("2'x", [("UNDEFINED", "x", 0), ("UNDEFINED", "x", 1)]),
    ]
    controls = []
    for expression, result in expected:
        if bits(expression, widths) != result:
            raise ValueError("Finite positive SigSpec interpretation failed")
        controls.append({"expression": expression, "status": "PASS"})
    for expression in (r"\a [4]", r"\a [1:3]", "{ 1'0", r"\missing", "3'01", "1'0 1'1", "}"):
        try:
            bits(expression, widths)
        except ValueError:
            controls.append({"expression": expression, "status": "REJECTED"})
        else:
            raise ValueError("Finite malformed SigSpec was accepted")
    selectors = []
    for code in range(4):
        cell = {"type": "$eq", "p": {"\\A_WIDTH": "2", "\\A_SIGNED": "0", "\\Y_WIDTH": "1",
                                      "\\B_WIDTH": "2", "\\B_SIGNED": "0"},
                "c": {"\\A": r"\b", "\\B": "2'" + format(code, "02b"), "\\Y": r"\s"}}
        if decoder(cell, [(r"\b", 0), (r"\b", 1)], widths) != code:
            raise ValueError("Finite exact selector decoding failed")
        selectors.append(code)
    wrong_width = {"type": "$eq", "p": {"\\A_WIDTH": "1", "\\A_SIGNED": "0", "\\Y_WIDTH": "1",
                                          "\\B_WIDTH": "2", "\\B_SIGNED": "0"},
                   "c": {"\\A": r"\b", "\\B": "2'11", "\\Y": r"\s"}}
    try:
        decoder(wrong_width, [(r"\b", 0), (r"\b", 1)], widths)
    except ValueError:
        pass
    else:
        raise ValueError("Width-mismatched selector accepted")
    paths = [Path(__file__).resolve(), ROOT / "scripts/verification/review_bht_definedness.py"]
    receipt = {"status": "PASS_INDEPENDENT_BHT_REVIEW_PARSER_FINITE_CONTROLS",
               "input_sha256": {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
               "positive_bit_expression_cases": 6, "malformed_bit_expression_cases": 7,
               "unsigned_two_bit_selector_cases": 4, "malformed_selector_cases": 1,
               "controls": controls, "decoded_selector_codes": selectors,
               "memory_enforcement": enforced, "hardware_measurement_or_external_tool_started": False}
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print(receipt["status"], "18cases;peak", peak_memory(), flush=True)


if __name__ == "__main__":
    main()
