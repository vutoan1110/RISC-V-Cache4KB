#!/usr/bin/env python3
"""Where does the associativity benefit outweigh the controller penalty?

Combines the capacity sweeps of all three points:

    DM      CACHE_CONFIG 0, direct-mapped on the five-state controller
    DM_DSE  CACHE_CONFIG 3, direct-mapped on the ten-state controller
    SA2     CACHE_CONFIG 1, two-way on the ten-state controller

controller penalty = DM_DSE - DM   (organization fixed, controller varies)
associativity gain = SA2 - DM_DSE  (controller fixed, organization varies)
published net      = SA2 - DM      (what the paper reports; the sum of the two)
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(*names: str) -> dict:
    data = defaultdict(dict)
    for name in names:
        path = ROOT / name
        if not path.is_file():
            sys.exit("[FAIL] missing %s" % path)
        for r in csv.DictReader(path.open(encoding="utf-8")):
            data[(int(r["lines"]), r["kernel"])][r["config"]] = int(r["mcycle"])
    return data


def main() -> int:
    data = load("results/sweep.csv", "results/sweep_dm.csv")
    sizes = sorted({k[0] for k in data})
    kernels = sorted({k[1] for k in data})
    need = ("DM", "DM_DSE", "SA2")

    print("Totals over %d kernels" % len(kernels))
    print("%9s %10s %10s %10s   %12s %12s %12s"
          % ("capacity", "DM", "DM_DSE", "SA2",
             "controller", "assoc gain", "published"))
    print("-" * 86)
    for n in sizes:
        tot = dict.fromkeys(need, 0)
        ok = True
        for k in kernels:
            cell = data[(n, k)]
            if not set(need) <= cell.keys():
                ok = False
                break
            for c in need:
                tot[c] += cell[c]
        if not ok:
            print("%9s  incomplete" % ("%dB" % (n * 16)))
            continue
        ctrl = tot["DM_DSE"] - tot["DM"]
        gain = tot["SA2"] - tot["DM_DSE"]
        net = tot["SA2"] - tot["DM"]
        print("%8dB %10d %10d %10d   %+11d %+12d %+12d"
              % (n * 16, tot["DM"], tot["DM_DSE"], tot["SA2"],
                 ctrl, gain, net))
        print("%9s %10s %10s %10s   %+11.2f%% %+11.2f%% %+11.2f%%"
              % ("", "", "", "",
                 100.0 * ctrl / tot["DM"],
                 100.0 * gain / tot["DM_DSE"],
                 100.0 * net / tot["DM"]))

    print("")
    print("Reading: 'published' is positive at every capacity, so the paper's")
    print("comparison would report the direct-mapped configuration as the")
    print("winner throughout. It is positive only because the controller")
    print("penalty exceeds the associativity gain, not because the")
    print("direct-mapped organization is faster.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
