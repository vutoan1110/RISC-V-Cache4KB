#!/usr/bin/env python3
"""Cache-capacity sweep with the controller held fixed.

The paper reports one capacity, 1 KiB, at which the direct-mapped organization
wins. The open question is whether that ordering survives a change of capacity,
and if not, where it reverses. This sweeps ICACHE_LINE_COUNT and
DCACHE_LINE_COUNT together at the frozen 16-byte line, so 32/64/128/256 lines
are 512 B / 1 KiB / 2 KiB / 4 KiB.

Compare CACHE_CONFIG 1 (SA2) against 3 (direct-mapped on the same ten-state
controller); comparing against 0 would reintroduce the controller confound.

    python scripts/run_sweep.py --compile --lines 32,64,128,256 --configs 1,3
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_ablation import (CONFIGS, FIELDS, KERNELS, MAX_CYCLES,  # noqa: E402
                          compile_design, parse, vsim)

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lines", default="32,64,128,256",
                    help="cache lines per array; 16-byte line, so x16 bytes")
    ap.add_argument("--configs", default="1,3")
    ap.add_argument("--kernels", default=",".join(KERNELS))
    ap.add_argument("--compile", action="store_true")
    ap.add_argument("--out", default="results/sweep.csv")
    args = ap.parse_args()

    lines = [int(x) for x in args.lines.split(",")]
    configs = [int(c) for c in args.configs.split(",")]
    kernels = args.kernels.split(",")
    log_dir = ROOT / "results" / "sweep_logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    if args.compile:
        compile_design(log_dir)

    for cfg in configs:
        if cfg == 1 and any(n % 2 for n in lines):
            sys.exit("[FAIL] SA2 requires an even line count")

    rows, failures = [], []
    total = len(lines) * len(configs) * len(kernels)
    done = 0
    for nlines in lines:
        for cfg in configs:
            for kern in kernels:
                done += 1
                name = CONFIGS[cfg]
                hexfile = "fw/%s.hex" % kern
                if not (ROOT / hexfile).is_file():
                    failures.append("%s: missing %s" % (kern, hexfile))
                    continue
                log = log_dir / ("%s_%s_%d.log" % (kern, name, nlines))
                do = ("vsim -onfinish stop -gCACHE_CONFIG=%d "
                      "-gICACHE_LINE_COUNT=%d -gDCACHE_LINE_COUNT=%d "
                      "-gMEMFILE=%s work.tb_benchmark_snapshot "
                      "+benchmark=%s +max_cycles=%d; run -all; quit -f"
                      % (cfg, nlines, nlines, hexfile, kern, MAX_CYCLES))
                t0 = time.time()
                rc = vsim(do, log)
                row = parse(log) if rc == 0 else None
                if row is None:
                    failures.append("%s/%s/%d lines (rc=%d)"
                                    % (kern, name, nlines, rc))
                    print("[FAIL] %3d/%d %-11s %-7s %4d lines  see %s"
                          % (done, total, kern, name, nlines, log.name))
                    continue
                row["kernel"], row["config"] = kern, name
                row["config_id"], row["lines"] = cfg, nlines
                row["bytes"] = nlines * 16
                rows.append(row)
                print("[OK]   %3d/%d %-11s %-7s %4d lines (%5d B) "
                      "mcycle=%-9d i_miss=%-6s (%.0fs)"
                      % (done, total, kern, name, nlines, nlines * 16,
                         row["mcycle"], row.get("i_miss"), time.time() - t0))

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = ["kernel", "config", "config_id", "lines", "bytes"] + list(FIELDS)
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
