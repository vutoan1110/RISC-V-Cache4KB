#!/usr/bin/env python3
"""Constrained deterministic RV32I/Zmmul random program generator."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

HALT = 0x0000006F
NOP = 0x00000013
WRITABLE = list(range(1, 28))  # x28-x31 are harness-reserved


def r_type(f7: int, rs2: int, rs1: int, f3: int, rd: int) -> int:
    return (f7 << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | 0x33


def i_type(imm: int, rs1: int, f3: int, rd: int, opcode: int = 0x13) -> int:
    return ((imm & 0xFFF) << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | opcode


def s_type(imm: int, rs2: int, rs1: int, f3: int) -> int:
    value = imm & 0xFFF
    return ((value >> 5) << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | ((value & 31) << 7) | 0x23


def b_type(offset: int, rs2: int, rs1: int, f3: int) -> int:
    value = offset & 0x1FFF
    return (((value >> 12) & 1) << 31) | (((value >> 5) & 0x3F) << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | (((value >> 1) & 0xF) << 8) | (((value >> 11) & 1) << 7) | 0x63


def u_type(imm20: int, rd: int, opcode: int) -> int:
    return ((imm20 & 0xFFFFF) << 12) | (rd << 7) | opcode


def j_type(offset: int, rd: int) -> int:
    value = offset & 0x1FFFFF
    return (((value >> 20) & 1) << 31) | (((value >> 1) & 0x3FF) << 21) | (((value >> 11) & 1) << 20) | (((value >> 12) & 0xFF) << 12) | (rd << 7) | 0x6F


def generate(seed: int, length: int) -> list[int]:
    rng = random.Random(seed)
    program = [i_type(0x400, 0, 0, 30)]  # safe data base for split test memory
    for reg in range(1, 11):
        program.append(i_type(rng.randint(-1024, 1023), 0, 0, reg))

    while len(program) < length:
        remaining = length - len(program)
        kind = rng.choices(
            ["r", "i", "mul", "load", "store", "branch", "jal", "jalr", "upper"],
            weights=[20, 20, 12, 10, 10, 12, 6, 4, 6],
        )[0]
        rd = rng.choice(WRITABLE)
        rs1 = rng.choice(WRITABLE)
        rs2 = rng.choice(WRITABLE)

        if kind == "r":
            f3 = rng.randrange(8)
            f7 = 0x20 if f3 in (0, 5) and rng.randrange(2) else 0
            program.append(r_type(f7, rs2, rs1, f3, rd))
        elif kind == "i":
            f3 = rng.randrange(8)
            if f3 == 1:
                imm = rng.randrange(32)
            elif f3 == 5:
                imm = rng.randrange(32) | (0x400 if rng.randrange(2) else 0)
            else:
                imm = rng.randint(-2048, 2047)
            program.append(i_type(imm, rs1, f3, rd))
        elif kind == "mul":
            program.append(r_type(1, rs2, rs1, rng.randrange(4), rd))
        elif kind == "load":
            f3 = rng.choice([0, 1, 2, 4, 5])
            align = 4 if f3 == 2 else 2 if f3 in (1, 5) else 1
            offset = rng.randrange(0, 256 // align) * align
            program.append(i_type(offset, 30, f3, rd, 0x03))
        elif kind == "store":
            f3 = rng.choice([0, 1, 2])
            align = 1 << f3
            offset = rng.randrange(0, 256 // align) * align
            program.append(s_type(offset, rs2, 30, f3))
        elif kind == "branch" and remaining >= 2:
            program.append(b_type(8, rs2, rs1, rng.choice([0, 1, 4, 5, 6, 7])))
            program.append(i_type(rng.randint(-8, 7), rd, 0, rd))
        elif kind == "jal" and remaining >= 2:
            program.append(j_type(8, 27))
            program.append(i_type(rng.randint(-8, 7), rd, 0, rd))
        elif kind == "jalr" and remaining >= 4:
            program.extend([
                u_type(0, 28, 0x17),
                i_type(16, 28, 0, 28),
                i_type(0, 28, 0, 27, 0x67),
                i_type(rng.randint(-8, 7), rd, 0, rd),
            ])
        elif kind == "upper":
            program.append(u_type(rng.randrange(1 << 20), rd, rng.choice([0x17, 0x37])))
        else:
            program.append(NOP)

    return program[:length] + [HALT]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--length", type=int, default=160)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    if not 100 <= args.length <= 500:
        raise SystemExit("--length must be in the requested 100..500 range")

    words = generate(args.seed, args.length)
    text = "".join(f"{word:08x}\n" for word in words)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="ascii")
    digest = hashlib.sha256(text.encode("ascii")).hexdigest()
    manifest = {
        "seed": args.seed,
        "static_instruction_words": len(words),
        "requested_length_before_halt": args.length,
        "sha256": digest,
        "hex": str(args.output),
        "scope": "RV32I computational/control/load-store subset + Zmmul",
    }
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"SEED={args.seed} words={len(words)} sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

