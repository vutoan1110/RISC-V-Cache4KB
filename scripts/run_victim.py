#!/usr/bin/env python3
"""Victim-buffer depth sweep.

`VICTIM_ENTRIES` is already generic in the DSE core: the compare loop, the
replacement pointer and `VC_INDEX_WIDTH` are all derived from it, and the only
guard on the value is a `$display` note, not a check. Depth is therefore a third
design-space axis reachable with no RTL change.

Depth 1 is excluded: `VC_INDEX_WIDTH` floors at 1 bit, so the replacement
pointer can leave the single valid entry.

    python scripts/run_victim.py --victim 2,4,8
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_ablation import (FIELDS, KERNELS, MAX_CYCLES,  # noqa: E402
                          compile_design, parse, vsim)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--victim", default="2,4,8")
    ap.add_argument("--lines", default="64")
    ap.add_argument("--kernels", default=",".join(KERNELS))
    ap.add_argument("--compile", action="store_true")
    ap.add_argument("--out", default="results/victim.csv")
    args = ap.parse_args()

    depths = [int(x) for x in args.victim.split(",")]
    if any(d < 2 for d in depths):
        sys.exit("[FAIL] depth 1 is not supported; see the module docstring")
    nlines = int(args.lines)
    kernels = args.kernels.split(",")
    log_dir = ROOT / "results" / "victim_logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    if args.compile:
        compile_design(log_dir)

    rows, failures = [], []
    total, done = len(depths) * len(kernels), 0
    for depth in depths:
        for kern in kernels:
            done += 1
            hexfile = "fw/%s.hex" % kern
            if not (ROOT / hexfile).is_file():
                failures.append("%s: missing %s" % (kern, hexfile))
                continue
            log = log_dir / ("%s_vc%d.log" % (kern, depth))
            do = ("vsim -onfinish stop -gCACHE_CONFIG=2 "
                  "-gICACHE_LINE_COUNT=%d -gDCACHE_LINE_COUNT=%d "
                  "-gVICTIM_ENTRIES=%d -gMEMFILE=%s "
                  "work.tb_benchmark_snapshot +benchmark=%s +max_cycles=%d; "
                  "run -all; quit -f"
                  % (nlines, nlines, depth, hexfile, kern, MAX_CYCLES))
            t0 = time.time()
            rc = vsim(do, log)
            row = parse(log) if rc == 0 else None
            if row is None:
                failures.append("%s/vc%d (rc=%d)" % (kern, depth, rc))
                print("[FAIL] %3d/%d %-11s vc=%d  see %s"
                      % (done, total, kern, depth, log.name))
                continue
            row["kernel"], row["victim_entries"], row["lines"] = \
                kern, depth, nlines
            rows.append(row)
            print("[OK]   %3d/%d %-11s vc=%-2d mcycle=%-9d "
                  "d_victim=%-6s d_miss=%-6s (%.0fs)"
                  % (done, total, kern, depth, row["mcycle"],
                     row.get("d_victim"), row.get("d_miss"), time.time() - t0))

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = ["kernel", "victim_entries", "lines"] + list(FIELDS)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print("")
    print("[%s] %d run(s) -> %s"
          % ("PASS" if not failures else "PARTIAL", len(rows), out))
    for f in failures:
        print("   failed: %s" % f)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
