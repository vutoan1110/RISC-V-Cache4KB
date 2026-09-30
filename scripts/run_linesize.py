#!/usr/bin/env python3
"""Line-size sweep at constant capacity.

Capacity is held at 1 KiB so the axis is line size alone, not line size mixed
with capacity: 2 words (8 B) gives 128 lines, 4 words (16 B) gives 64, and
8 words (32 B) gives 32.

Only CACHE_CONFIG 1 and 3 may be swept. Configuration 0 runs
icache_controller.v / dcache_controller.v, which are not parameterised and
assume a four-word line; the shared AXI master's burst length follows
LINE_WORDS, so config 0 is only valid at the default.

    python scripts/run_linesize.py --compile --words 2,4,8
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_ablation import (CONFIGS, FIELDS, KERNELS, MAX_CYCLES,  # noqa: E402
                          compile_design, parse, vsim)

ROOT = Path(__file__).resolve().parents[1]
CAPACITY_BYTES = 1024


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--words", default="2,4,8",
                    help="32-bit words per line; x4 gives the line in bytes")
    ap.add_argument("--configs", default="1,3")
    ap.add_argument("--kernels", default=",".join(KERNELS))
    ap.add_argument("--compile", action="store_true")
    ap.add_argument("--out", default="results/linesize.csv")
    args = ap.parse_args()

    words = [int(x) for x in args.words.split(",")]
    configs = [int(c) for c in args.configs.split(",")]
    kernels = args.kernels.split(",")

    if 0 in configs:
        sys.exit("[FAIL] CACHE_CONFIG 0 is not parameterised on line size; "
                 "see the module docstring")
    for n in words:
        if n & (n - 1):
            sys.exit("[FAIL] words per line must be a power of two: %d" % n)
        lines = CAPACITY_BYTES // (4 * n)
        if lines < 2 or (1 in configs and lines % 2):
            sys.exit("[FAIL] %d words gives %d lines, which SA2 cannot index"
                     % (n, lines))

    log_dir = ROOT / "results" / "linesize_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    if args.compile:
        compile_design(log_dir)

    rows, failures = [], []
    total = len(words) * len(configs) * len(kernels)
    done = 0
    for nwords in words:
        nlines = CAPACITY_BYTES // (4 * nwords)
        for cfg in configs:
            for kern in kernels:
                done += 1
                name = CONFIGS[cfg]
                hexfile = "fw/%s.hex" % kern
                if not (ROOT / hexfile).is_file():
                    failures.append("%s: missing %s" % (kern, hexfile))
                    continue
                log = log_dir / ("%s_%s_w%d.log" % (kern, name, nwords))
                do = ("vsim -onfinish stop -gCACHE_CONFIG=%d "
                      "-gCACHE_LINE_WORDS=%d "
                      "-gICACHE_LINE_COUNT=%d -gDCACHE_LINE_COUNT=%d "
                      "-gMEMFILE=%s work.tb_benchmark_snapshot "
                      "+benchmark=%s +max_cycles=%d; run -all; quit -f"
                      % (cfg, nwords, nlines, nlines, hexfile, kern,
                         MAX_CYCLES))
                t0 = time.time()
                rc = vsim(do, log)
                row = parse(log) if rc == 0 else None
                if row is None:
                    failures.append("%s/%s/%dw (rc=%d)" % (kern, name, nwords, rc))
                    print("[FAIL] %3d/%d %-11s %-7s %dB line  see %s"
                          % (done, total, kern, name, nwords * 4, log.name))
                    continue
                row["kernel"], row["config"], row["config_id"] = kern, name, cfg
                row["line_words"], row["line_bytes"] = nwords, nwords * 4
                row["lines"] = nlines
                rows.append(row)
                print("[OK]   %3d/%d %-11s %-7s %2dB line x%3d lines "
                      "mcycle=%-9d i_miss=%-6s (%.0fs)"
                      % (done, total, kern, name, nwords * 4, nlines,
                         row["mcycle"], row.get("i_miss"), time.time() - t0))

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = (["kernel", "config", "config_id", "line_words", "line_bytes",
             "lines"] + list(FIELDS))
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
