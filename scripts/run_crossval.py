#!/usr/bin/env python3
"""Cross-validate the RTL cache counters against the independent model.

For each kernel and configuration this runs the harness with +trace_cache,
replays the resulting access trace through scripts/cache_model.py, and requires
every counter to agree exactly. A single mismatched event fails the run.

    python scripts/run_crossval.py --kernels up_crc32,up_matmult-int,up_nettle-sha256
"""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_ablation import CONFIGS, MAX_CYCLES, vsim  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
COUNTERS = ("i_access", "i_main", "i_victim", "i_miss",
            "d_read", "d_write", "d_main", "d_victim", "d_miss")


def rtl_counts(log: Path) -> dict | None:
    txt = log.read_bytes().decode("utf-8", "replace")
    m = re.search(r"BENCHMARK_SNAPSHOT (.*)", txt)
    if not m:
        return None
    line = m.group(1)
    out = {}
    for k in COUNTERS:
        mm = re.search(r"\b" + k + r"=(\d+)\b", line)
        if not mm:
            return None
        out[k] = int(mm.group(1))
    return out


def model_counts(trace: Path, cfg: int) -> dict | None:
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / "cache_model.py"),
                        str(trace), "--config", str(cfg)],
                       cwd=ROOT, capture_output=True, text=True)
    if p.returncode:
        return None
    out = {}
    for k in COUNTERS:
        m = re.search(r"^\s*" + k + r"\s*=\s*(\d+)", p.stdout, re.M)
        if not m:
            return None
        out[k] = int(m.group(1))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kernels", default="up_crc32,up_matmult-int,up_nettle-sha256,up_md5sum,up_edn")
    ap.add_argument("--configs", default="0,1,2")
    ap.add_argument("--out", default="results/crossval.csv")
    args = ap.parse_args()

    log_dir = ROOT / "results" / "crossval_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    trace = ROOT / "results" / "cache_trace.txt"

    rows, bad = [], []
    for kern in args.kernels.split(","):
        for cfg in [int(c) for c in args.configs.split(",")]:
            name = CONFIGS[cfg]
            hexfile = "fw/%s.hex" % kern
            if not (ROOT / hexfile).is_file():
                bad.append("%s: missing firmware" % kern)
                continue
            log = log_dir / ("%s_%s.log" % (kern, name))
            do = ("vsim -onfinish stop -voptargs=+acc -gCACHE_CONFIG=%d "
                  "-gMEMFILE=%s work.tb_benchmark_snapshot +benchmark=%s "
                  "+max_cycles=%d +trace_cache; run -all; quit -f"
                  % (cfg, hexfile, kern, MAX_CYCLES))
            t0 = time.time()
            if vsim(do, log) != 0:
                bad.append("%s/%s: simulation failed" % (kern, name))
                print("[FAIL] %-11s %-7s simulation" % (kern, name))
                continue
            rtl = rtl_counts(log)
            mdl = model_counts(trace, cfg)
            if not rtl or not mdl:
                bad.append("%s/%s: could not read counts" % (kern, name))
                print("[FAIL] %-11s %-7s counts unreadable" % (kern, name))
                continue
            diff = {k: (rtl[k], mdl[k]) for k in COUNTERS if rtl[k] != mdl[k]}
            row = {"kernel": kern, "config": name,
                   "match": "EXACT" if not diff else "MISMATCH"}
            row.update({k + "_rtl": rtl[k] for k in COUNTERS})
            row.update({k + "_model": mdl[k] for k in COUNTERS})
            rows.append(row)
            if diff:
                bad.append("%s/%s: %s" % (kern, name, diff))
                print("[DIFF] %-11s %-7s %s (%.0fs)"
                      % (kern, name, diff, time.time() - t0))
            else:
                print("[OK]   %-11s %-7s all %d counters exact (%.0fs)"
                      % (kern, name, len(COUNTERS), time.time() - t0))

    out = ROOT / args.out
    cols = (["kernel", "config", "match"]
            + [k + "_rtl" for k in COUNTERS] + [k + "_model" for k in COUNTERS])
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    exact = sum(1 for r in rows if r["match"] == "EXACT")
    print("")
    print("[%s] %d/%d run(s) exact -> %s"
          % ("PASS" if not bad else "FAIL", exact, len(rows), out))
    for b in bad:
        print("   %s" % b)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
