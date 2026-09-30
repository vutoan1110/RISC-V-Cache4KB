#!/usr/bin/env python3
"""Build the SoC peripheral and interrupt program image.

The UVM SoC environment needs a program that actually touches the APB
peripherals and takes a timer interrupt; verification/directed/directed_isa.hex
does neither. Writing it here instead of in assembly keeps the RISC-V toolchain
out of the loop: the output is a plain hex image the testbench backdoor-loads.

Register and bit definitions come from hdl/apb_timer.v, hdl/uart_apb.v,
hdl/apb_performance_monitor.v and hdl/datapath.v:

    timer  ctrl[0] = enable, ctrl[1] = irq enable
    timer  status[0] = pending, cleared by writing 1 to offset 0x0C
    uart   0x00 = tx_data (pushes the FIFO), 0x08 = cfg, 0x0C = ctrl[0] start
    sysmon 0x00 = ident, reads 0x53380002
    core   irq_enabled = mstatus[3] && mie[7]

Run:  python verification/uvm/seq/gen_soc_periph_irq.py
"""

from __future__ import annotations

from pathlib import Path

HALT = 0x0000_006F   # JAL x0,0
NOP = 0x0000_0013

UART_BASE = 0x4000_0000
TIMER_BASE = 0x4000_0200
SYSMON_BASE = 0x4000_0300
DATA_BASE = 0x0000_1000

SYSMON_IDENT = 0x5338_0002
UART_CFG_8N1 = 0x0000_00C3

# hdl/baudrate_gen_block.sv: count_max = 433 for the 115200 selection, the
# oversample tick period is (433 >> 4) + 1 = 28 clocks and a bit is 16 ticks.
UART_BIT_CYCLES = 448


def u12(value: int) -> int:
    return value & 0xFFF


def lui(rd: int, imm20: int) -> int:
    return ((imm20 & 0xFFFFF) << 12) | (rd << 7) | 0x37


def addi(rd: int, rs1: int, imm: int) -> int:
    return (u12(imm) << 20) | (rs1 << 15) | (0 << 12) | (rd << 7) | 0x13


def sw(rs2: int, rs1: int, imm: int) -> int:
    v = u12(imm)
    return ((v >> 5) << 25) | (rs2 << 20) | (rs1 << 15) | (2 << 12) | ((v & 0x1F) << 7) | 0x23


def lw(rd: int, rs1: int, imm: int) -> int:
    return (u12(imm) << 20) | (rs1 << 15) | (2 << 12) | (rd << 7) | 0x03


def beq(rs1: int, rs2: int, off: int) -> int:
    v = off & 0x1FFF
    return (((v >> 12) & 1) << 31) | (((v >> 5) & 0x3F) << 25) | (rs2 << 20) | \
           (rs1 << 15) | (0 << 12) | (((v >> 1) & 0xF) << 8) | (((v >> 11) & 1) << 7) | 0x63


def jal(rd: int, off: int) -> int:
    v = off & 0x1FFFFF
    return (((v >> 20) & 1) << 31) | (((v >> 1) & 0x3FF) << 21) | (((v >> 11) & 1) << 20) | \
           (((v >> 12) & 0xFF) << 12) | (rd << 7) | 0x6F


def andi(rd: int, rs1: int, imm: int) -> int:
    return (u12(imm) << 20) | (rs1 << 15) | (7 << 12) | (rd << 7) | 0x13


def csrrw(rd: int, csr: int, rs1: int) -> int:
    return ((csr & 0xFFF) << 20) | (rs1 << 15) | (1 << 12) | (rd << 7) | 0x73


MRET = 0x3020_0073

CSR_MSTATUS = 0x300
CSR_MIE = 0x304
CSR_MTVEC = 0x305

# Fixed layout so the handler address is known before the code that installs it.
HANDLER_WORD = 48
DONE_WORD = 60
TOTAL_WORDS = 64


def build() -> list[int]:
    prog = [NOP] * TOTAL_WORDS

    body: list[int] = []

    # x31 is the completion flag the handler sets; x30 is the data base.
    body.append(addi(31, 0, 0))
    body.append(lui(30, DATA_BASE >> 12))

    # ---- UART: configure, queue a byte, start, read status ----
    body.append(lui(5, UART_BASE >> 12))
    # cfg[1:0]=3 selects the 115200 divider, cfg[4]=0 disables parity and
    # cfg[7:6]=3 selects eight data bits: the reset default, i.e. plain 8N1.
    body.append(addi(6, 0, UART_CFG_8N1))
    body.append(sw(6, 5, 0x08))            # cfg
    body.append(addi(6, 0, 0x41))          # 'A'
    body.append(sw(6, 5, 0x00))            # tx_data, pushes the FIFO
    body.append(addi(6, 0, 1))
    body.append(sw(6, 5, 0x0C))            # ctrl[0] = start
    body.append(lw(7, 5, 0x10))            # status, an APB read
    body.append(sw(7, 30, 8))              # keep it in RAM for the checker

    # ---- sysmon: read the identification register ----
    body.append(lui(5, SYSMON_BASE >> 12))
    body.append(addi(5, 5, SYSMON_BASE & 0xFFF))
    body.append(lw(8, 5, 0x00))
    body.append(sw(8, 30, 0))              # RAM[0x1000] = ident

    # ---- timer: compare value and counter ----
    body.append(lui(5, TIMER_BASE >> 12))
    body.append(addi(5, 5, TIMER_BASE & 0xFFF))
    body.append(addi(6, 0, 20))
    body.append(sw(6, 5, 0x04))            # cmp
    body.append(sw(0, 5, 0x08))            # count = 0

    # ---- enable interrupts in the core ----
    body.append(addi(9, 0, HANDLER_WORD * 4))
    body.append(csrrw(0, CSR_MTVEC, 9))
    body.append(addi(9, 0, 8))             # mstatus[3] = MIE
    body.append(csrrw(0, CSR_MSTATUS, 9))
    body.append(addi(9, 0, 0x80))          # mie[7] = timer
    body.append(csrrw(0, CSR_MIE, 9))

    # ---- arm the timer, then spin until the handler sets x31 ----
    body.append(addi(6, 0, 3))             # ctrl: enable + irq enable
    body.append(sw(6, 5, 0x00))
    body.append(beq(31, 0, 0))             # branch to itself while x31 == 0
    body.append(sw(31, 30, 4))             # RAM[0x1004] = flag

    # A UART frame takes about 4480 clocks, far longer than the rest of the
    # program, so wait for status[0] (tx done) before halting. Otherwise the
    # byte never reaches the serial line.
    body.append(lui(5, UART_BASE >> 12))
    body.append(lw(7, 5, 0x10))            # status
    body.append(andi(7, 7, 1))             # tx_done_latched
    body.append(beq(7, 0, -8))             # back to the load while it is clear
    body.append(sw(7, 30, 12))             # RAM[0x100c] = 1

    if len(body) > HANDLER_WORD:
        raise SystemExit(f"body of {len(body)} words overruns the handler at {HANDLER_WORD}")
    body.append(jal(0, (DONE_WORD - (len(body))) * 4))

    for i, word in enumerate(body):
        prog[i] = word

    handler = [
        lui(5, TIMER_BASE >> 12),
        addi(5, 5, TIMER_BASE & 0xFFF),
        addi(6, 0, 1),
        sw(6, 5, 0x0C),                    # write 1 to clear the pending flag
        sw(0, 5, 0x00),                    # disable the timer
        addi(31, 0, 1),                    # completion flag
        MRET,
    ]
    for i, word in enumerate(handler):
        prog[HANDLER_WORD + i] = word

    prog[DONE_WORD] = HALT
    return prog


def main() -> int:
    words = build()
    out = Path(__file__).with_name("soc_periph_irq.hex")
    out.write_text("".join(f"{w:08x}\n" for w in words), encoding="ascii")
    print(f"wrote {len(words)} words to {out}")
    print(f"handler at 0x{HANDLER_WORD * 4:03x}, halt at 0x{DONE_WORD * 4:03x}")
    print(f"expected RAM[0x{DATA_BASE:08x}] = 0x{SYSMON_IDENT:08x}, "
          f"RAM[0x{DATA_BASE + 4:08x}] = 0x00000001")
    print(f"uart cfg = 0x{UART_CFG_8N1:08x}, bit period = {UART_BIT_CYCLES} clocks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
