#!/usr/bin/env python3
"""Convert objcopy Verilog byte HEX into the SoC word-oriented readmemh image."""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_verilog_bytes(path: Path, ram_bytes: int) -> tuple[bytearray, int]:
    image = bytearray(ram_bytes)
    address = 0
    used_end = 0

    for line_number, raw_line in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
        line = raw_line.split("//", 1)[0].strip()
        if not line:
            continue
        for token in line.split():
            if token.startswith("@"):
                address = int(token[1:], 16)
                if address >= ram_bytes:
                    raise ValueError(
                        f"{path}:{line_number}: address 0x{address:X} exceeds "
                        f"the {ram_bytes}-byte physical RAM"
                    )
                continue
            if len(token) != 2:
                raise ValueError(
                    f"{path}:{line_number}: expected an objcopy byte token, got {token!r}"
                )
            if address >= ram_bytes:
                raise ValueError(
                    f"{path}:{line_number}: firmware exceeds the {ram_bytes}-byte physical RAM"
                )
            image[address] = int(token, 16)
            address += 1
            used_end = max(used_end, address)

    if used_end == 0:
        raise ValueError(f"{path}: no firmware bytes found")
    return image, used_end


def write_words(path: Path, image: bytearray, used_end: int) -> list[int]:
    word_count = (used_end + 3) // 4
    words = []
    for base in range(0, word_count * 4, 4):
        word = (
            image[base]
            | (image[base + 1] << 8)
            | (image[base + 2] << 16)
            | (image[base + 3] << 24)
        )
        words.append(word)

    with path.open("w", encoding="ascii", newline="\n") as output:
        output.write("@00000000\n")
        for index in range(0, len(words), 4):
            output.write(" ".join(f"{word:08x}" for word in words[index:index + 4]))
            output.write("\n")
    return words


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("benchmark.hex"))
    parser.add_argument("--output", type=Path, default=Path("benchmark_rv32.hex"))
    parser.add_argument("--ram-bytes", type=int, default=16384)  # R14: was 8192
    args = parser.parse_args()

    image, used_end = parse_verilog_bytes(args.input, args.ram_bytes)
    words = write_words(args.output, image, used_end)

    print(f"[PASS] wrote {args.output}: {used_end} initialized bytes, {len(words)} words")
    print("[INFO] first 8 little-endian words:")
    for word in words[:8]:
        print(f"{word:08x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
