#!/usr/bin/env python3
"""Line-size axis at constant 1 KiB capacity.

Both configurations run the ten-state controller, so the difference between
them is organization alone. Capacity is fixed, so line size and line count
co-vary: the axis is line length together with the set count it implies, not
line length in isolation.
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    path = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "results/linesize.csv")
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    if not rows:
        sys.exit("[FAIL] no rows in %s" % path)

    data = defaultdict(dict)
    lines_for = {}
    for r in rows:
        key = (int(r["line_bytes"]), r["kernel"])
        data[key][r["config"]] = r
        lines_for[int(r["line_bytes"])] = int(r["lines"])

    sizes = sorted({k[0] for k in data})
    kernels = sorted({k[1] for k in data})

    print("Totals over %d kernels, 1 KiB capacity throughout" % len(kernels))
    print("%7s %7s %11s %11s %10s %9s   %s"
          % ("line", "lines", "DM_DSE", "SA2", "delta", "delta%", "SA2 wins"))
    print("-" * 80)
    for b in sizes:
        tot = {"DM_DSE": 0, "SA2": 0}
        wins = ties = losses = 0
        ok = True
        for k in kernels:
            cell = data[(b, k)]
            if not {"DM_DSE", "SA2"} <= cell.keys():
                ok = False
                continue
            for c in tot:
                tot[c] += int(cell[c]["mcycle"])
            d = int(cell["SA2"]["mcycle"]) - int(cell["DM_DSE"]["mcycle"])
            wins += d < 0
            ties += d == 0
            losses += d > 0
        if not ok or not tot["DM_DSE"]:
            print("%6dB  incomplete" % b)
            continue
        delta = tot["SA2"] - tot["DM_DSE"]
        print("%6dB %7d %11d %11d %+10d %+8.2f%%   %d/%d (%d tie, %d lose)"
              % (b, lines_for[b], tot["DM_DSE"], tot["SA2"], delta,
                 100.0 * delta / tot["DM_DSE"], wins, len(kernels),
                 ties, losses))

    for label, field in (("Total cycles, DM_DSE", "mcycle"),
                         ("I-cache misses, DM_DSE", "i_miss"),
                         ("External reads, DM_DSE", "axi_read")):
        print("")
        print(label)
        print("%-11s %s" % ("kernel",
                            " ".join("%10s" % ("%dB" % b) for b in sizes)))
        print("-" * (12 + 11 * len(sizes)))
        for k in kernels:
            cells = []
            for b in sizes:
                cell = data[(b, k)].get("DM_DSE")
                cells.append("%10s" % (cell[field] if cell else "-"))
            print("%-11s %s" % (k, " ".join(cells)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
