"""Freeze exact-source/raw-IR UART baud controls before paired proof runs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from check_uart_baud_default_definedness import prove
from review_bht_definedness import sha
from review_lec_onehot_cnf import ROOT, memory_cap, peak_memory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if out.exists() or not out.is_relative_to(ROOT):
        raise ValueError("New control receipt required")
    enforced = memory_cap()
    paths = ["hdl/baudrate_gen_block.sv", "asic/snapshots/rtl_r14/hdl/baudrate_gen_block.sv",
             "hdl/uart_core.sv", "asic/snapshots/rtl_r14/hdl/uart_core.sv",
             "hdl/uart_apb.v", "asic/snapshots/rtl_r14/hdl/uart_apb.v",
             "asic/equiv/lec/gold_flat_r14.il", "scripts/verification/review_bht_definedness.py",
             "scripts/verification/check_uart_baud_default_definedness.py",
             "scripts/verification/check_uart_baud_definedness_controls.py"]
    before = {path: sha(ROOT / path) for path in paths}
    proof = prove()
    if any(sha(ROOT / path) != expected for path, expected in before.items()):
        raise ValueError("A control input changed")
    result = {"status": "PASS_LOCAL_UART_BAUD_ACTUAL_IR_CONTROLS", "input_sha256": before,
              "memory_enforcement": enforced,
              "positive_actual_source_and_IR_codes": 4,
              "raw_semantic_missing_selector_negative_control": proof["negative_controls"]["missing_actual_code3_selector"],
              "raw_semantic_data_bit_order_negative_control": proof["negative_controls"]["reversed_actual_selected_16bit_B_slice"],
              "frozen_checker_before_paired_main_execution": True,
              "full_sequential_LEC": "OPEN", "whole_source_undefined_abstraction": "OPEN",
              "source_or_IR_changed": False, "external_tool_started": False}
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(result["status"], "4positive+2semanticnegative;peak", peak_memory(), flush=True)


if __name__ == "__main__":
    main()
