#!/usr/bin/env python3
"""Cell-type mix of the worst paths in a report_checks -format full file (2026-10-15 ss study).

    python path_cell_mix.py <report> [--top 15]

Per path: data-path delay (launch clock pin to endpoint), and the delay share of every standard-cell family (cell
name without the drive strength, e.g. or4b_1 -> or4b). Over all paths: total delay per family, so the families that
are slow at the corner of the report (e.g. 4-high stacks at ss) stand out.
"""
import argparse
import collections
import re
import sys

ap = argparse.ArgumentParser()
ap.add_argument("report")
ap.add_argument("--top", type=int, default=15)
a = ap.parse_args()
txt = open(a.report, encoding="utf-8", errors="replace").read()
paths = txt.split("Startpoint:")[1:]
tot = collections.Counter()
cnt = collections.Counter()
data_total = 0.0
for p in paths:
    rows = re.findall(r"^\s*(?:\d+\s+)?(?:[\d.]+\s+)?[\d.]+\s+([\d.]+)\s+([\d.]+)\s+[\^v]\s+(\S+)/(\w+)\s+\((sky130_fd_sc_hd__\w+)\)",
                      p, re.M)
    # rows: delay, time, instance, pin, cell; keep output pins only, skip clock tree cells before the launch flop
    outs = [r for r in rows if r[3] in ("X", "Y", "Q", "Q_N")]
    start = next((i for i, r in enumerate(outs) if r[3] in ("Q", "Q_N")), None)
    if start is None:
        continue
    seg = outs[start:]
    for d, _t, _inst, _pin, cell in seg:
        fam = re.sub(r"_\d+$", "", cell.replace("sky130_fd_sc_hd__", ""))
        tot[fam] += float(d)
        cnt[fam] += 1
        data_total += float(d)
print("paths %d, data-path cell delay %.1f ns" % (len(paths), data_total))
print("%-14s %9s %7s %6s" % ("family", "delay ns", "share", "cells"))
for fam, d in tot.most_common(a.top):
    print("%-14s %9.2f %6.1f%% %6d" % (fam, d, 100 * d / data_total if data_total else 0, cnt[fam]))
