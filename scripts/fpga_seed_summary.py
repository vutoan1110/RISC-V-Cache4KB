#!/usr/bin/env python3
"""All four placement seeds, every measured field, side by side.

    python scripts/fpga_seed_summary.py results/fpga_points_rtlfix_p1.csv \
        --out results/fpga_seed_summary_rtlfix.md

Seed 2 is the seed pinned in the project, but a single seed is one draw of the
placer: every field is reported for seeds 1-4 with min / max / mean / spread,
so a difference between configurations can be weighed against the seed noise
of that same field.

Gate (exit 1): every point must have exactly the seeds 1, 2, 3, 4, and every
field of run_fpga_points.COLS must be filled in for every one of them.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_fpga_points import COLS  # noqa: E402

SEEDS = (1, 2, 3, 4)
ID_COLS = ("point", "seed", "l0", "cache_config", "line_bytes", "lines",
           "victim_entries", "capacity_bytes", "seconds")


def num(v: str):
    try:
        f = float(v)
        return int(f) if f.is_integer() and "." not in v else f
    except (TypeError, ValueError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.csv, encoding="utf-8")))
    by_point: dict[str, dict[int, dict]] = {}
    for r in rows:
        base = r["point"].split("@")[0]
        by_point.setdefault(base, {})[int(r["seed"])] = r

    problems = []
    for p, seeds in by_point.items():
        if sorted(seeds) != list(SEEDS):
            problems.append("%s: seeds %s, expected %s"
                            % (p, sorted(seeds), list(SEEDS)))
        for s, r in seeds.items():
            empty = [c for c in COLS if c != "seconds" and r.get(c, "") == ""]
            if empty:
                problems.append("%s seed %d: %d empty field(s): %s"
                                % (p, s, len(empty), ", ".join(empty[:8])))

    fields = [c for c in COLS if c not in ID_COLS]
    L = ["# Quartus, all four seeds: %s\n" % args.csv,
         "Every field `run_fpga_points.py` scrapes, for seeds 1-4. "
         "`spread` = max - min over the four seeds.\n"]
    for p in sorted(by_point):
        seeds = by_point[p]
        L.append("## %s\n" % p)
        L.append("| Field | " + " | ".join("seed %d" % s for s in SEEDS)
                 + " | min | max | mean | spread |")
        L.append("|---|" + "---:|" * (len(SEEDS) + 4))
        for f in fields:
            vals = [seeds.get(s, {}).get(f, "") for s in SEEDS]
            nums = [num(v) for v in vals]
            if all(isinstance(x, (int, float)) for x in nums):
                lo, hi = min(nums), max(nums)
                mean = sum(nums) / len(nums)
                stats = ["%g" % lo, "%g" % hi, "%.4g" % mean, "%g" % round(hi - lo, 6)]
            else:
                stats = ["", "", "", "same" if len(set(vals)) == 1 else "differs"]
            L.append("| %s | %s | %s |" % (f, " | ".join(v or "MISSING" for v in vals),
                                           " | ".join(stats)))
        L.append("")

    # One cross-configuration table of means with the seed spread beside them.
    key = ("le", "regs", "comb", "m9k", "mult9", "setup_s85_slack",
           "setup_s0_slack", "setup_f0_slack", "hold_f0_slack",
           "fmax_restricted_s85", "fmax_restricted_s0", "pow_total_mw",
           "pow_core_dyn_mw", "pow_core_static_mw", "pow_io_mw")
    L.append("## Across configurations (mean of four seeds, [min, max])\n")
    L.append("| Field | " + " | ".join(sorted(by_point)) + " |")
    L.append("|---|" + "---:|" * len(by_point))
    for f in key:
        cells = []
        for p in sorted(by_point):
            nums = [num(by_point[p].get(s, {}).get(f, "")) for s in SEEDS]
            if all(isinstance(x, (int, float)) for x in nums):
                cells.append("%.4g [%g, %g]" % (sum(nums) / 4, min(nums), max(nums)))
            else:
                cells.append("MISSING")
        L.append("| %s | %s |" % (f, " | ".join(cells)))

    L.append("\n## Completeness gate\n")
    L.extend(["- FAIL: " + x for x in problems] or
             ["- PASS: %d points x 4 seeds, %d fields each, none empty"
              % (len(by_point), len([c for c in COLS if c != "seconds"]))])
    Path(args.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    for x in problems:
        print("[FAIL] " + x)
    print("[%s] %d point(s) -> %s" % ("PASS" if not problems else "FAIL",
                                      len(by_point), args.out))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
