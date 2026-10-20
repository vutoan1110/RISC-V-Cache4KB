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
import math
import statistics
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
    ap.add_argument("--seeds", default="1,2,3,4", help="Common comma-separated seeds required for every point")
    ap.add_argument("--points", default="", help="Required comma-separated points; default: points in the CSV")
    args = ap.parse_args()
    seeds_required = tuple(sorted(int(s) for s in args.seeds.split(",")))
    if not seeds_required or len(set(seeds_required)) != len(seeds_required) or min(seeds_required) < 1:
        ap.error("--seeds must contain distinct positive integers")

    rows = list(csv.DictReader(open(args.csv, encoding="utf-8")))
    by_point: dict[str, dict[int, dict]] = {}
    problems = []
    for r in rows:
        base = r["point"].split("@")[0]
        if int(r["seed"]) in by_point.get(base, {}):
            problems.append("%s: duplicate seed %s" % (base, r["seed"]))
        by_point.setdefault(base, {})[int(r["seed"])] = r

    if not rows:
        problems.append("CSV has no rows")
    if args.points and set(by_point) != set(args.points.split(",")):
        problems.append("points %s, expected %s" % (sorted(by_point), sorted(args.points.split(","))))
    for p, seeds in by_point.items():
        if sorted(seeds) != list(seeds_required):
            problems.append("%s: seeds %s, expected %s"
                            % (p, sorted(seeds), list(seeds_required)))
        for s, r in seeds.items():
            empty = [c for c in COLS if c != "seconds" and r.get(c, "") == ""]
            if empty:
                problems.append("%s seed %d: %d empty field(s): %s"
                                % (p, s, len(empty), ", ".join(empty[:8])))

    fields = [c for c in COLS if c not in ID_COLS]
    L = ["# Quartus, %d common seeds: %s\n" % (len(seeds_required), args.csv),
         "Every field `run_fpga_points.py` scrapes. "
         "Required seeds: %s. `spread` = max - min; `sd` is the sample standard deviation.\n" %
         ", ".join(map(str, seeds_required))]
    for p in sorted(by_point):
        seeds = by_point[p]
        L.append("## %s\n" % p)
        L.append("| Field | " + " | ".join("seed %d" % s for s in seeds_required)
                 + " | min | max | mean | sd | spread |")
        L.append("|---|" + "---:|" * (len(seeds_required) + 5))
        for f in fields:
            vals = [seeds.get(s, {}).get(f, "") for s in seeds_required]
            nums = [num(v) for v in vals]
            if all(isinstance(x, (int, float)) and math.isfinite(x) for x in nums):
                lo, hi = min(nums), max(nums)
                mean = sum(nums) / len(nums)
                stats = ["%g" % lo, "%g" % hi, "%.4g" % mean,
                         "%.4g" % (statistics.stdev(nums) if len(nums) > 1 else 0), "%g" % round(hi - lo, 6)]
            else:
                stats = ["", "", "", "", "same" if len(set(vals)) == 1 else "differs"]
            L.append("| %s | %s | %s |" % (f, " | ".join(v or "MISSING" for v in vals),
                                           " | ".join(stats)))
        L.append("")

    # One cross-configuration table of means with the seed spread beside them.
    key = ("le", "regs", "comb", "m9k", "mult9", "setup_s85_slack",
           "setup_s0_slack", "setup_f0_slack", "hold_f0_slack",
           "fmax_restricted_s85", "fmax_restricted_s0", "pow_total_mw",
           "pow_core_dyn_mw", "pow_core_static_mw", "pow_io_mw")
    L.append("## Across configurations (mean of %d common seeds, [min, max])\n" % len(seeds_required))
    L.append("| Field | " + " | ".join(sorted(by_point)) + " |")
    L.append("|---|" + "---:|" * len(by_point))
    for f in key:
        cells = []
        for p in sorted(by_point):
            nums = [num(by_point[p].get(s, {}).get(f, "")) for s in seeds_required]
            if all(isinstance(x, (int, float)) for x in nums):
                cells.append("%.4g [%g, %g]" % (sum(nums) / len(seeds_required), min(nums), max(nums)))
            else:
                cells.append("MISSING")
        L.append("| %s | %s |" % (f, " | ".join(cells)))

    if "dm_4kb" in by_point:
        L.append("\n## Paired differences from DM within the same seed\n")
        L.append("Power is the Quartus default-activity estimate. Timing is Slow 1200 mV 85 C.\n")
        L.append("| seed | point | LE difference | Fmax difference, MHz | total power difference, mW |")
        L.append("|---:|---|---:|---:|---:|")
        for s in seeds_required:
            base = by_point["dm_4kb"].get(s, {})
            for p in sorted(set(by_point) - {"dm_4kb"}):
                row = by_point[p].get(s, {})
                diffs = []
                for f in ("le", "fmax_s85", "pow_total_mw"):
                    a, b = num(row.get(f)), num(base.get(f))
                    diffs.append("%+.6g" % (a - b) if a is not None and b is not None else "MISSING")
                L.append("| %d | %s | %s |" % (s, p, " | ".join(diffs)))
    L.append("\n## Completeness gate\n")
    L.extend(["- FAIL: " + x for x in problems] or
             ["- PASS: %d points x %d seeds, %d fields each, none empty"
              % (len(by_point), len(seeds_required), len([c for c in COLS if c != "seconds"]))])
    Path(args.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    for x in problems:
        print("[FAIL] " + x)
    print("[%s] %d point(s) -> %s" % ("PASS" if not problems else "FAIL",
                                      len(by_point), args.out))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
