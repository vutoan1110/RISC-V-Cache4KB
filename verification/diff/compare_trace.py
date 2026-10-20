#!/usr/bin/env python3
"""Compare normalized architectural retirement traces with useful context."""

from __future__ import annotations

import argparse
import csv
from collections import deque
from pathlib import Path

FIELDS = ["order", "pc", "instr", "rd", "we", "rd_data",
          "mem_we", "mem_addr", "mem_wdata", "mem_wstrb"]
HEX_FIELDS = {"pc", "instr", "rd_data", "mem_addr", "mem_wdata", "mem_wstrb"}


def read_trace(path: Path) -> list[dict[str, int]]:
    rows = []
    with path.open(newline="", encoding="ascii") as handle:
        for row in csv.DictReader(handle):
            rows.append({key: int(row[key], 16 if key in HEX_FIELDS else 10) for key in FIELDS})
    return rows


def format_row(row: dict[str, int]) -> str:
    return (f"order={row['order']} pc={row['pc']:08x} instr={row['instr']:08x} "
            f"rd=x{row['rd']} we={row['we']} data={row['rd_data']:08x} "
            f"mem_we={row['mem_we']} addr={row['mem_addr']:08x} "
            f"wdata={row['mem_wdata']:08x} wstrb={row['mem_wstrb']:x}")


def compare(dut_path: Path, ref_path: Path, seed: int, label: str) -> int:
    dut = read_trace(dut_path)
    ref = read_trace(ref_path)
    history: deque[str] = deque(maxlen=8)
    for index, (dut_row, ref_row) in enumerate(zip(dut, ref)):
        if dut_row != ref_row:
            print(f"[FAIL] {label} architectural mismatch")
            print(f"Seed: {seed}")
            print(f"Retire order/index: {index}")
            print(f"DUT: {format_row(dut_row)}")
            print(f"REF: {format_row(ref_row)}")
            print("Recent instructions:")
            for item in history:
                print(f"  {item}")
            return 1
        history.append(format_row(dut_row))
    if len(dut) != len(ref):
        print(f"[FAIL] {label} trace length mismatch seed={seed}: DUT={len(dut)} REF={len(ref)}")
        if len(dut) > len(ref):
            print(f"First extra DUT: {format_row(dut[len(ref)])}")
        else:
            print(f"First extra REF: {format_row(ref[len(dut)])}")
        return 1
    print(f"[PASS] {label} seed={seed} retirements={len(dut)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dut", required=True, type=Path)
    parser.add_argument("--ref", required=True, type=Path)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--label", default="DUT/reference")
    args = parser.parse_args()
    return compare(args.dut, args.ref, args.seed, args.label)


if __name__ == "__main__":
    raise SystemExit(main())
