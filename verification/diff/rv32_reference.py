#!/usr/bin/env python3
"""Small deterministic RV32I-computational + Zmmul reference model.

It intentionally excludes traps, privileged behavior and unsupported opcodes.
It is not Spike and is not presented as an ISA-compliance oracle.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
from pathlib import Path

MASK32 = 0xFFFF_FFFF
HALT = 0x0000_006F  # JAL x0,0, consumed by the harness rather than traced


def u32(value: int) -> int:
    return value & MASK32


def sext(value: int, bits: int) -> int:
    sign = 1 << (bits - 1)
    return (value & (sign - 1)) - (value & sign)


def s32(value: int) -> int:
    return sext(value & MASK32, 32)


@dataclass
class Machine:
    words: list[int]
    regs: list[int] = field(default_factory=lambda: [0] * 32)
    memory: dict[int, int] = field(default_factory=dict)
    pc: int = 0
    order: int = 0

    def load_u8(self, addr: int) -> int:
        return self.memory.get(addr & MASK32, 0)

    def store(self, addr: int, data: int, width: int) -> None:
        for lane in range(width):
            self.memory[u32(addr + lane)] = (data >> (8 * lane)) & 0xFF

    def fetch(self) -> int:
        index = self.pc >> 2
        if index >= len(self.words):
            raise RuntimeError(f"PC escaped generated program: 0x{self.pc:08x}")
        return self.words[index]

    def step(self) -> dict[str, int] | None:
        instr = self.fetch()
        if instr == HALT:
            return None

        pc = self.pc
        opcode = instr & 0x7F
        rd = (instr >> 7) & 0x1F
        funct3 = (instr >> 12) & 7
        rs1 = (instr >> 15) & 0x1F
        rs2 = (instr >> 20) & 0x1F
        funct7 = (instr >> 25) & 0x7F
        a = self.regs[rs1]
        b = self.regs[rs2]
        next_pc = u32(pc + 4)
        rd_we = False
        rd_value = 0
        mem_we = False
        mem_addr = 0
        mem_wdata = 0
        mem_wstrb = 0

        if opcode == 0x33:  # register ALU and Zmmul
            rd_we = True
            shamt = b & 31
            if funct7 == 0x01:
                if funct3 == 0:
                    rd_value = u32(s32(a) * s32(b))
                elif funct3 == 1:
                    rd_value = u32((s32(a) * s32(b)) >> 32)
                elif funct3 == 2:
                    rd_value = u32((s32(a) * (b & MASK32)) >> 32)
                elif funct3 == 3:
                    rd_value = u32(((a & MASK32) * (b & MASK32)) >> 32)
                else:
                    raise RuntimeError(f"unsupported M funct3 {funct3}")
            elif funct3 == 0:
                rd_value = u32(a - b if funct7 == 0x20 else a + b)
            elif funct3 == 1:
                rd_value = u32(a << shamt)
            elif funct3 == 2:
                rd_value = int(s32(a) < s32(b))
            elif funct3 == 3:
                rd_value = int((a & MASK32) < (b & MASK32))
            elif funct3 == 4:
                rd_value = a ^ b
            elif funct3 == 5:
                rd_value = u32(s32(a) >> shamt) if funct7 == 0x20 else a >> shamt
            elif funct3 == 6:
                rd_value = a | b
            else:
                rd_value = a & b

        elif opcode == 0x13:  # immediate ALU
            rd_we = True
            imm = sext(instr >> 20, 12)
            shamt = (instr >> 20) & 31
            if funct3 == 0:
                rd_value = u32(a + imm)
            elif funct3 == 1:
                rd_value = u32(a << shamt)
            elif funct3 == 2:
                rd_value = int(s32(a) < imm)
            elif funct3 == 3:
                rd_value = int((a & MASK32) < u32(imm))
            elif funct3 == 4:
                rd_value = u32(a ^ imm)
            elif funct3 == 5:
                rd_value = u32(s32(a) >> shamt) if funct7 == 0x20 else a >> shamt
            elif funct3 == 6:
                rd_value = u32(a | imm)
            else:
                rd_value = u32(a & imm)

        elif opcode == 0x03:  # loads
            rd_we = True
            mem_addr = u32(a + sext(instr >> 20, 12))
            if funct3 in (0, 4):
                value = self.load_u8(mem_addr)
                rd_value = u32(sext(value, 8)) if funct3 == 0 else value
            elif funct3 in (1, 5):
                value = self.load_u8(mem_addr) | (self.load_u8(mem_addr + 1) << 8)
                rd_value = u32(sext(value, 16)) if funct3 == 1 else value
            elif funct3 == 2:
                rd_value = sum(self.load_u8(mem_addr + i) << (8 * i) for i in range(4))
            else:
                raise RuntimeError(f"unsupported load funct3 {funct3}")

        elif opcode == 0x23:  # stores
            imm = ((instr >> 25) << 5) | ((instr >> 7) & 0x1F)
            mem_addr = u32(a + sext(imm, 12))
            mem_we = True
            if funct3 == 0:
                width = 1
                mem_wstrb = 1 << (mem_addr & 3)
                mem_wdata = (b & 0xFF) << (8 * (mem_addr & 3))
            elif funct3 == 1:
                width = 2
                mem_wstrb = 3 << (mem_addr & 3)
                mem_wdata = (b & 0xFFFF) << (8 * (mem_addr & 3))
            elif funct3 == 2:
                width = 4
                mem_wstrb = 0xF
                mem_wdata = b
            else:
                raise RuntimeError(f"unsupported store funct3 {funct3}")
            self.store(mem_addr, b, width)

        elif opcode == 0x63:  # conditional branches
            imm = (((instr >> 31) & 1) << 12) | (((instr >> 7) & 1) << 11)
            imm |= ((instr >> 25) & 0x3F) << 5
            imm |= ((instr >> 8) & 0xF) << 1
            offset = sext(imm, 13)
            taken = {
                0: a == b,
                1: a != b,
                4: s32(a) < s32(b),
                5: s32(a) >= s32(b),
                6: (a & MASK32) < (b & MASK32),
                7: (a & MASK32) >= (b & MASK32),
            }.get(funct3)
            if taken is None:
                raise RuntimeError(f"unsupported branch funct3 {funct3}")
            if taken:
                next_pc = u32(pc + offset)

        elif opcode == 0x6F:  # JAL
            imm = (((instr >> 31) & 1) << 20) | (((instr >> 12) & 0xFF) << 12)
            imm |= (((instr >> 20) & 1) << 11) | (((instr >> 21) & 0x3FF) << 1)
            rd_we = True
            rd_value = u32(pc + 4)
            next_pc = u32(pc + sext(imm, 21))

        elif opcode == 0x67:  # JALR
            rd_we = True
            rd_value = u32(pc + 4)
            next_pc = u32(a + sext(instr >> 20, 12)) & ~1

        elif opcode == 0x37:  # LUI
            rd_we = True
            rd_value = instr & 0xFFFFF000

        elif opcode == 0x17:  # AUIPC
            rd_we = True
            rd_value = u32(pc + (instr & 0xFFFFF000))

        elif opcode == 0x0F:  # FENCE is a no-op in this single-hart harness
            pass
        else:
            raise RuntimeError(f"unsupported opcode 0x{opcode:02x} at pc=0x{pc:08x}")

        if rd_we and rd != 0:
            self.regs[rd] = u32(rd_value)
        else:
            rd_we = False
            rd_value = 0
        self.regs[0] = 0
        self.pc = next_pc

        row = {
            "order": self.order,
            "pc": pc,
            "instr": instr,
            "rd": rd,
            "we": int(rd_we),
            "rd_data": u32(rd_value),
            "mem_we": int(mem_we),
            "mem_addr": mem_addr,
            "mem_wdata": u32(mem_wdata),
            "mem_wstrb": mem_wstrb & 0xF,
        }
        self.order += 1
        return row


def load_words(path: Path) -> list[int]:
    return [int(line.strip(), 16) for line in path.read_text().splitlines() if line.strip()]


def run(hex_path: Path, trace_path: Path, max_steps: int) -> tuple[int, Machine]:
    machine = Machine(load_words(hex_path))
    rows: list[dict[str, int]] = []
    for _ in range(max_steps):
        row = machine.step()
        if row is None:
            break
        rows.append(row)
    else:
        raise RuntimeError(f"reference watchdog exceeded {max_steps} instructions")

    trace_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["order", "pc", "instr", "rd", "we", "rd_data",
              "mem_we", "mem_addr", "mem_wdata", "mem_wstrb"]
    with trace_path.open("w", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: (f"{row[key]:08x}" if key in {"pc", "instr", "rd_data", "mem_addr", "mem_wdata"}
                      else f"{row[key]:x}" if key == "mem_wstrb" else row[key])
                for key in fields
            })
    return len(rows), machine


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hex", required=True, type=Path)
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--max-steps", type=int, default=10000)
    args = parser.parse_args()
    count, machine = run(args.hex, args.trace, args.max_steps)
    print(f"reference_retirements={count} final_pc=0x{machine.pc:08x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
