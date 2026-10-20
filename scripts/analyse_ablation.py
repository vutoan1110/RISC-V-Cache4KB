#!/usr/bin/env python3
"""Decompose the published DM advantage into controller cost and organization.

DM      = direct-mapped on the five-state icache_controller   (published)
DM_DSE  = direct-mapped on the ten-state icache_dse_core       (ablation)
SA2     = two-way set-associative on the ten-state core        (published)
DM_VC4  = direct-mapped + victim buffer on the ten-state core  (published)

DM_DSE - DM    is the cost of controller depth alone.
SA2    - DM_DSE is the effect of associativity alone.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORDER = ("DM", "DM_DSE", "SA2", "DM_VC4")


def load(path: Path) -> dict:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    if not rows:
        sys.exit("[FAIL] no rows in %s" % path)
    data = {}
    for r in rows:
        data.setdefault(r["kernel"], {})[r["config"]] = {
            k: int(v) for k, v in r.items()
            if v not in ("", None) and k not in ("kernel", "config")
        }
    return data


def main() -> int:
    path = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "results/ablation.csv")
    data = load(path)
    have = [c for c in ORDER if any(c in v for v in data.values())]

    print("Cycles per kernel")
    print("%-11s %s  %9s %9s" %
          ("kernel", " ".join("%9s" % c for c in have),
           "ctrl cost", "assoc"))
    print("-" * (12 + 10 * len(have) + 20))

    tot = {c: 0 for c in have}
    inst = 0
    ctrl_wins = assoc_wins = ties = 0
    for kern in sorted(data):
        row = data[kern]
        if not all(c in row for c in have):
            continue
        cells = " ".join("%9d" % row[c]["mcycle"] for c in have)
        for c in have:
            tot[c] += row[c]["mcycle"]
        inst += row[have[0]]["minstret"]
        ctrl = (row["DM_DSE"]["mcycle"] - row["DM"]["mcycle"]
                if {"DM", "DM_DSE"} <= row.keys() else None)
        assoc = (row["SA2"]["mcycle"] - row["DM_DSE"]["mcycle"]
                 if {"SA2", "DM_DSE"} <= row.keys() else None)
        if assoc is not None:
            if assoc < 0:
                assoc_wins += 1
            elif assoc > 0:
                ctrl_wins += 1
            else:
                ties += 1
        print("%-11s %s  %+9s %+9s" %
              (kern, cells,
               "n/a" if ctrl is None else ctrl,
               "n/a" if assoc is None else assoc))

    print("-" * (12 + 10 * len(have) + 20))
    print("%-11s %s" % ("total", " ".join("%9d" % tot[c] for c in have)))
    if inst:
        print("%-11s %s" %
              ("CPI", " ".join("%9.4f" % (tot[c] / inst) for c in have)))

    print("")
    if {"DM", "DM_DSE"} <= set(have):
        d = tot["DM_DSE"] - tot["DM"]
        print("Controller depth alone (DM_DSE - DM) : %+d cycles (%+.2f%%)"
              % (d, 100.0 * d / tot["DM"]))
    if {"SA2", "DM_DSE"} <= set(have):
        d = tot["SA2"] - tot["DM_DSE"]
        print("Associativity alone (SA2 - DM_DSE)   : %+d cycles (%+.2f%%)"
              % (d, 100.0 * d / tot["DM_DSE"]))
        print("  kernels where SA2 beats DM_DSE     : %d" % assoc_wins)
        print("  kernels where SA2 loses            : %d" % ctrl_wins)
        print("  kernels tied                       : %d" % ties)
    if {"DM", "SA2"} <= set(have):
        d = tot["SA2"] - tot["DM"]
        print("Published headline gap (SA2 - DM)    : %+d cycles (%+.2f%%)"
              % (d, 100.0 * d / tot["DM"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
