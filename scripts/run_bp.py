#!/usr/bin/env python3
"""Branch predictor on/off, which the paper builds but never evaluates.

Review item A8: the design carries a BRANCH_PREDICT_ENABLE build option and the
paper describes the 256-entry two-bit predictor, but reports no result that
uses it. Either the feature is cut from the paper or it is measured; this
measures it.

    python scripts/run_bp.py --compile
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", default="0")
    ap.add_argument("--kernels", default=",".join(KERNELS))
    ap.add_argument("--compile", action="store_true")
    ap.add_argument("--out", default="results/bp.csv")
    args = ap.parse_args()

    configs = [int(c) for c in args.configs.split(",")]
    kernels = args.kernels.split(",")
    log_dir = ROOT / "results" / "bp_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    if args.compile:
        compile_design(log_dir)

    rows, failures = [], []
    total = 2 * len(configs) * len(kernels)
    done = 0
    for bp in (0, 1):
        for cfg in configs:
            for kern in kernels:
                done += 1
                name = CONFIGS[cfg]
                hexfile = "fw/%s.hex" % kern
                if not (ROOT / hexfile).is_file():
                    failures.append("%s: missing %s" % (kern, hexfile))
                    continue
                log = log_dir / ("%s_%s_bp%d.log" % (kern, name, bp))
                do = ("vsim -onfinish stop -gCACHE_CONFIG=%d "
                      "-gBRANCH_PREDICT_ENABLE=%d -gMEMFILE=%s "
                      "work.tb_benchmark_snapshot +benchmark=%s +max_cycles=%d; "
                      "run -all; quit -f" % (cfg, bp, hexfile, kern, MAX_CYCLES))
                t0 = time.time()
                rc = vsim(do, log)
                row = parse(log) if rc == 0 else None
                if row is None:
                    failures.append("%s/%s/bp%d (rc=%d)" % (kern, name, bp, rc))
                    print("[FAIL] %3d/%d %-11s %-7s bp=%d  see %s"
                          % (done, total, kern, name, bp, log.name))
                    continue
                row["kernel"], row["config"], row["bp"] = kern, name, bp
                rows.append(row)
                print("[OK]   %3d/%d %-11s %-7s bp=%d mcycle=%-9d "
                      "mispredict=%-7s control=%-7s (%.0fs)"
                      % (done, total, kern, name, bp, row["mcycle"],
                         row.get("mispredict"), row.get("control"),
                         time.time() - t0))

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = ["kernel", "config", "bp"] + list(FIELDS)
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
