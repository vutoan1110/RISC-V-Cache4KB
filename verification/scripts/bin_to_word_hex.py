#!/usr/bin/env python3
"""Convert a little-endian RV32 flat binary into one 32-bit word per line."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("hexfile", type=Path)
    parser.add_argument(
        "--base-address",
        type=lambda value: int(value, 0),
        default=0,
        help="prepend words so the first binary byte is loaded at this address",
    )
    parser.add_argument(
        "--fill-word",
        type=lambda value: int(value, 0),
        default=0x00000013,
        help="32-bit fill word used before base-address (default: RV32I NOP)",
    )
    args = parser.parse_args()

    if args.base_address < 0 or args.base_address & 3:
        raise SystemExit("--base-address must be a non-negative, word-aligned value")
    if not 0 <= args.fill_word <= 0xFFFFFFFF:
        raise SystemExit("--fill-word must fit in 32 bits")

    data = args.binary.read_bytes()
    if len(data) % 4:
        data += bytes(4 - (len(data) % 4))
    words = [args.fill_word] * (args.base_address // 4)
    words.extend(int.from_bytes(data[i : i + 4], "little") for i in range(0, len(data), 4))
    args.hexfile.write_text("".join(f"{word:08x}\n" for word in words), encoding="ascii")
    print(f"wrote {len(words)} words to {args.hexfile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
