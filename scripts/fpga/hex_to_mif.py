#!/usr/bin/env python3
"""Convert a word-oriented Verilog HEX image into four byte-lane Quartus MIFs."""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path


def parse_hex(path: Path, depth: int) -> list[int]:
    words = [0] * depth
    address = 0
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = re.split(r"//|#", raw, maxsplit=1)[0].strip()
        if not line:
            continue
        for token in line.split():
            if token.startswith("@"):
                address = int(token[1:], 16)
                if address >= depth:
                    raise ValueError(f"{path}:{line_number}: address {address:#x} exceeds depth {depth}")
                continue
            value = int(token.replace("_", ""), 16)
            if value > 0xFFFF_FFFF:
                raise ValueError(f"{path}:{line_number}: {token} is wider than 32 bits")
            if address >= depth:
                raise ValueError(f"{path}:{line_number}: image exceeds depth {depth}")
            words[address] = value
            address += 1
    return words


def write_lane(path: Path, values: list[int], lane: int) -> None:
    width = max(3, math.ceil(math.log(max(len(values), 1), 16)))
    lines = [
        "WIDTH=8;",
        f"DEPTH={len(values)};",
        "ADDRESS_RADIX=HEX;",
        "DATA_RADIX=HEX;",
        "CONTENT BEGIN",
    ]
    for address, word in enumerate(values):
        byte = (word >> (8 * lane)) & 0xFF
        lines.append(f"    {address:0{width}X} : {byte:02X};")
    lines.append("END;")
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=root / "hdl" / "riscv_full.hex")
    parser.add_argument("--output-dir", type=Path, default=root / "hdl")
    parser.add_argument("--prefix", default="riscv_full_byte")
    parser.add_argument("--depth", type=int, default=4096)  # R14: was 2048 (16 KiB RAM)
    args = parser.parse_args()

    words = parse_hex(args.input.resolve(), args.depth)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for lane in range(4):
        output = args.output_dir / f"{args.prefix}{lane}.mif"
        write_lane(output, words, lane)
        outputs.append(output)

    print(f"Converted {args.input} into {len(outputs)} byte-lane MIF files")
    for output in outputs:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
