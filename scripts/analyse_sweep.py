#!/usr/bin/env python3
"""Does the associativity benefit depend on capacity, and where does it vanish?

Both configurations run the same ten-state controller, so the difference here is
organization alone. A negative delta means the set-associative cache is faster.
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    path = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "results/sweep.csv")
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    if not rows:
        sys.exit("[FAIL] no rows in %s" % path)

    data = defaultdict(dict)          # (lines, kernel) -> config -> row
    for r in rows:
        data[(int(r["lines"]), r["kernel"])][r["config"]] = r
    sizes = sorted({k[0] for k in data})
    kernels = sorted({k[1] for k in data})

    print("Totals across %d kernels, same controller throughout" % len(kernels))
    print("%7s %9s %11s %11s %10s %9s   %s"
          % ("lines", "capacity", "DM_DSE", "SA2", "delta", "delta%", "SA2 wins"))
    print("-" * 78)
    for n in sizes:
        tot = {"DM_DSE": 0, "SA2": 0}
        inst = 0
        wins = losses = ties = 0
        for k in kernels:
            cell = data[(n, k)]
            if not {"DM_DSE", "SA2"} <= cell.keys():
                continue
            for c in tot:
                tot[c] += int(cell[c]["mcycle"])
            inst += int(cell["DM_DSE"]["minstret"])
            d = int(cell["SA2"]["mcycle"]) - int(cell["DM_DSE"]["mcycle"])
            if d < 0:
                wins += 1
            elif d > 0:
                losses += 1
            else:
                ties += 1
        delta = tot["SA2"] - tot["DM_DSE"]
        print("%7d %8dB %11d %11d %+10d %+8.2f%%   %d/%d (%d tie, %d lose)"
              % (n, n * 16, tot["DM_DSE"], tot["SA2"], delta,
                 100.0 * delta / tot["DM_DSE"], wins, len(kernels), ties, losses))

    print("")
    print("Per-kernel delta (SA2 - DM_DSE); negative means associativity helps")
    print("%-11s %s" % ("kernel", " ".join("%10s" % ("%dB" % (n * 16))
                                           for n in sizes)))
    print("-" * (12 + 11 * len(sizes)))
    for k in kernels:
        cells = []
        for n in sizes:
            cell = data[(n, k)]
            if {"DM_DSE", "SA2"} <= cell.keys():
                d = int(cell["SA2"]["mcycle"]) - int(cell["DM_DSE"]["mcycle"])
                cells.append("%+10d" % d)
            else:
                cells.append("%10s" % "-")
        print("%-11s %s" % (k, " ".join(cells)))

    print("")
    print("I-cache misses, DM_DSE, showing where capacity stops binding")
    print("%-11s %s" % ("kernel", " ".join("%10s" % ("%dB" % (n * 16))
                                           for n in sizes)))
    print("-" * (12 + 11 * len(sizes)))
    for k in kernels:
        cells = []
        for n in sizes:
            cell = data[(n, k)].get("DM_DSE")
            cells.append("%10s" % (cell["i_miss"] if cell else "-"))
        print("%-11s %s" % (k, " ".join(cells)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
