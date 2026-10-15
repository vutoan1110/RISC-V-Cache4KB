"""Freeze Icache hot exact-source/raw-signal controls before paired runs."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from check_icache_hot_default_definedness import prove
from review_bht_definedness import sha
from review_lec_onehot_cnf import ROOT, memory_cap, peak_memory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    out = Path(parser.parse_args().out).resolve()
    if out.exists() or not out.is_relative_to(ROOT):
        raise ValueError("New control receipt required")
    enforced = memory_cap()
    paths = ["hdl/cache/icache_controller.v", "hdl/cache/icache.v", "hdl/soc_top.v", "asic/soc_dm_4kb/soc_asic_top.v",
             "asic/snapshots/rtl_r14/hdl/cache/icache_controller.v", "asic/snapshots/rtl_r14/hdl/cache/icache.v",
             "asic/snapshots/rtl_r14/hdl/soc_top.v", "asic/snapshots/rtl_r14/asic/soc_dm_4kb/soc_asic_top.v",
             "asic/equiv/lec/gold_flat_r14.il", "scripts/verification/review_bht_definedness.py",
             "scripts/verification/check_icache_hot_default_definedness.py", "scripts/verification/check_icache_hot_definedness_controls.py"]
    hashes = {p: sha(ROOT / p) for p in paths}
    proof = prove()
    if any(sha(ROOT / p) != h for p, h in hashes.items()):
        raise ValueError("Control input changed")
    receipt = {"status": "PASS_LOCAL_ICACHE_HOT_ACTUAL_IR_CONTROLS", "input_sha256": hashes,
               "memory_enforcement": enforced, "positive_free_index_cases": 24,
               "actual_copied_selector_and_B_word_controls": [t["negative_controls"] for t in proof["targets"]],
               "checker_frozen_before_main_paired_execution": True,
               "whole_Y_definedness_or_full_LEC_claimed": False, "source_or_IR_changed": False}
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print(receipt["status"], "24positive/6semanticnegative;peak", peak_memory(), flush=True)


if __name__ == "__main__":
    main()
