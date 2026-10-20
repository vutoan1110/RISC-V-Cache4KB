#!/usr/bin/env python3
"""Testbench side of the register file / BHT move to M9K (review A1, 2026-10-08).

Every hierarchical access to regfile.regs[...] and u_bht.bht_mem[...] in the testbenches becomes a macro of
tb/rf_bht_backdoor.svh (RF_GET / RF_SET / BHT_GET / BHT_SET), which resolves to the old arrays in the ASIC view and
to the M9K copies in the FPGA view; each converted file includes the header after its `timescale line (or at the top).

    python scripts/apply_rf_bht_m9k_tb.py <research root>      # a copy first (dry run), then the live tree
"""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
FILES = ["tb/branch_predictor_core_tb.sv", "tb/branch_predictor_tb.sv", "tb/native_interface_tb.sv",
         "tb/predictor_axi_tb.sv", "tb/random_trace_tb.sv", "tb/soc_integration_tb.sv", "tb/valid_irq_tb.sv",
         "verification/uvm/tb/tb_core_top.sv"]
INC = '`include "tb/rf_bht_backdoor.svh"\n'
PAT = re.compile(r"([A-Za-z_][A-Za-z0-9_.]*)\.(regfile)\.regs\[|([A-Za-z_][A-Za-z0-9_.]*)\.(g_bp_on\.u_bht)\.bht_mem\[")


def close_bracket(s, i):
    """s[i-1] == '['; return the index of the matching ']'."""
    d = 1
    while d:
        if s[i] == "[":
            d += 1
        elif s[i] == "]":
            d -= 1
        i += 1
    return i - 1


def convert(s):
    out, pos, n_get, n_set = [], 0, 0, 0
    while True:
        m = PAT.search(s, pos)
        if not m:
            out.append(s[pos:])
            return "".join(out), n_get, n_set
        path = (m.group(1) or m.group(3)) + "." + (m.group(2) or m.group(4))
        kind = "RF" if m.group(2) else "BHT"
        j = close_bracket(s, m.end())
        idx = s[m.end():j]
        rest = s[j + 1:]
        w = re.match(r"\s*=(?!=)\s*([^;]*);", rest)
        out.append(s[pos:m.start()])
        if w:
            out.append("`%s_SET(%s, %s, %s);" % (kind, path, idx, w.group(1).strip()))
            pos = j + 1 + w.end()
            n_set += 1
        else:
            out.append("`%s_GET(%s, %s)" % (kind, path, idx))
            pos = j + 1
            n_get += 1


total = 0
for f in FILES:
    p = root / f
    s = p.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert "rf_bht_backdoor.svh" not in s, f + " already converted"
    s, g, w = convert(s)
    assert g + w > 0, f
    assert "regfile.regs[" not in s and "bht_mem[" not in s, f
    m = re.search(r"^`timescale[^\n]*\n", s, flags=re.M)
    s = s[:m.end()] + INC + s[m.end():] if m else INC + s
    p.write_text(s, encoding="utf-8", newline="\n")
    total += g + w
    print("%-40s %3d reads, %2d writes" % (f, g, w))
print("converted %d accesses" % total)
