#!/usr/bin/env python3
"""Normalize Spike --log-commits output to the retirement CSV.

This parser targets the common textual commit format. It fails loudly when no
commit records are recognized; validate it against the installed Spike revision
before treating the resulting comparison as evidence.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

COMMIT = re.compile(
    r"core\s+\d+:\s+\d+\s+0x([0-9a-fA-F]+)\s+\(0x([0-9a-fA-F]+)\)(.*)"
)
RD = re.compile(r"\bx\s*(\d+)\s+0x([0-9a-fA-F]+)")
MEM = re.compile(r"\bmem\s+0x([0-9a-fA-F]+)\s+0x([0-9a-fA-F]+)")


def normalize(source: Path, output: Path, stop_instr: int) -> int:
    rows: list[dict[str, int]] = []
    with source.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            match = COMMIT.search(line)
            if not match:
                continue
            pc = int(match.group(1), 16) & 0xFFFF_FFFF
            instr = int(match.group(2), 16) & 0xFFFF_FFFF
            if instr == stop_instr:
                break
            tail = match.group(3)
            rd_match = RD.search(tail)
            rd = int(rd_match.group(1)) if rd_match else 0
            rd_we = int(bool(rd_match and rd != 0))
            rd_data = int(rd_match.group(2), 16) & 0xFFFF_FFFF if rd_we else 0

            opcode = instr & 0x7F
            funct3 = (instr >> 12) & 7
            mem_match = MEM.search(tail)
            mem_we = int(opcode == 0x23 and mem_match is not None)
            mem_addr = 0
            mem_wdata = 0
            mem_wstrb = 0
            if mem_we:
                address = int(mem_match.group(1), 16) & 0xFFFF_FFFF
                raw_data = int(mem_match.group(2), 16) & 0xFFFF_FFFF
                width = {0: 1, 1: 2, 2: 4}.get(funct3)
                if width is None:
                    raise ValueError(f"unsupported store funct3={funct3} at pc={pc:08x}")
                offset = address & 3
                mem_addr = address
                mem_wstrb = ((1 << width) - 1) << offset
                mem_wdata = (raw_data & ((1 << (8 * width)) - 1)) << (8 * offset)
                mem_wdata &= 0xFFFF_FFFF

            rows.append({
                "order": len(rows), "pc": pc, "instr": instr,
                "rd": rd, "we": rd_we, "rd_data": rd_data,
                "mem_we": mem_we, "mem_addr": mem_addr,
                "mem_wdata": mem_wdata, "mem_wstrb": mem_wstrb,
            })

    if not rows:
        raise SystemExit("no Spike commit records recognized; check Spike log format")
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["order", "pc", "instr", "rd", "we", "rd_data",
              "mem_we", "mem_addr", "mem_wdata", "mem_wstrb"]
    with output.open("w", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: (f"{value:08x}" if key in
                      {"pc", "instr", "rd_data", "mem_addr", "mem_wdata"}
                      else f"{value:x}" if key == "mem_wstrb" else value)
                for key, value in row.items()
            })
    print(f"normalized_spike_retirements={len(rows)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stop-instr", type=lambda value: int(value, 0),
                        default=0x0000006F)
    args = parser.parse_args()
    return normalize(args.input, args.output, args.stop_instr)


if __name__ == "__main__":
    raise SystemExit(main())
