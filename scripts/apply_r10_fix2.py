#!/usr/bin/env python3
"""R10 fix 2 (NHAT_KY.md 2026-09-26): make the R10b (* keep *) cut points ASIC-only.

Measured: with the unconditional attribute, Quartus kept every increment as its
own LCELL boundary and the DM 4 KiB fit grew from 15,425 LE (r7r8, seed 2) to
18,063 LE (+17 %), which would push sa2_4kb (19,346) and vc4_4kb (19,798) past
the 20,000 LE budget. The cut exists only for Yosys/ABC, so the attribute is
now emitted only when __openlane__ is defined (OpenLane lint, synthesis and EQY
all define it; Quartus, Questa and the project's Verilator lint do not). A
file-local macro keeps it to one line per counter and is #undef'd at once, so
nothing leaks into later files. Logic function: unchanged everywhere. The
OpenLane view is textually identical after preprocessing, which is checked by
re-synthesising and diffing against the R10A netlist.

    python scripts/apply_r10_fix2.py [root]
"""
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
DEF = ("`ifdef __openlane__\n"
       "`define R10B_KEEP (* keep *)\n"
       "`else\n"
       "`define R10B_KEEP\n"
       "`endif\n")
UNDEF = "`undef R10B_KEEP\n"
NOTE = ("// R10 fix 2: the cut is for Yosys/ABC only. Quartus honours keep too and paid\n"
        "// +17 % LE for it (15,425 -> 18,063 on dm_4kb), so it is ASIC-only.\n")


def fix(path, expect):
    p = os.path.join(ROOT, path)
    s = open(p, newline="").read()
    if "\r\n" in s:
        sys.exit("[FAIL] %s is CRLF" % path)
    lines = s.split("\n")
    idx = [i for i, l in enumerate(lines) if l.startswith("(* keep *) wire [31:0] ")]
    if len(idx) != expect or idx != list(range(idx[0], idx[0] + expect)):
        sys.exit("[FAIL] %s: expected %d contiguous kept increments, found %d" % (path, expect, len(idx)))
    for i in idx:
        lines[i] = "`R10B_KEEP " + lines[i][len("(* keep *) "):]
    lines.insert(idx[-1] + 1, UNDEF.rstrip("\n"))
    for k, l in enumerate((NOTE + DEF).rstrip("\n").split("\n")):
        lines.insert(idx[0] + k, l)
    open(p, "w", newline="").write("\n".join(lines))
    print("[OK] %s: %d increments now `R10B_KEEP" % (path, expect))


fix("hdl/perf_counters.v", 36)
fix("hdl/datapath.v", 1)
