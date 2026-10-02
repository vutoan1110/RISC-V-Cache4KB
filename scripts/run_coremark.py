# -*- coding: utf-8 -*-
"""Run CoreMark across the cache configurations.

Review item 4 asks for a standard benchmark alongside the Embench-style
kernels. CoreMark is already built (`fw/coremark.hex`), but it does not fit the
SoC as taped out:

    fw/coremark.hex   1,027 data lines x 4 words = 4,108 words = 16.4 KiB
    SoC main memory   IMEM_DEPTH + DMEM_DEPTH = 1024 + 1024 = 2,048 words = 8 KiB

The first attempt through `run_ablation.py` failed on all four configurations
with QuestaSim reporting "Too many data words read on line 514" -- word 2,048 is
reached on data line 512, which is line 513 of the file -- followed by
FAIL_TIMEOUT, because a truncated image never reaches the end marker.

So CoreMark is run here with main memory enlarged, and that difference is the
point of this being a separate script rather than a flag on the canonical one:

- `run_ablation.py` produces the published matrices and is not touched
- the memory depth is identical across all four configurations, so the
  comparison between them stays controlled
- what is under study is cache organisation, which is unchanged; only the
  backing store behind the caches is larger

The 8 KiB figure is a property of this SoC, not of the caches, and the fact that
CoreMark does not fit it is itself a result worth reporting.
"""
import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# 4 = SA4, 5 = the N-way core at two ways (must reproduce SA2); see run_ablation.py (R15).
CONFIGS = {0: "DM", 1: "SA2", 2: "DM_VC4", 3: "DM_DSE", 4: "SA4", 5: "SA2N"}
VSIM = "C:/questasim64_2024.1/win64/vsim.exe"
sys.path.insert(0, str(Path(__file__).resolve().parent))
# Every field the harness prints, parsed as key=value pairs (zipping raw
# tokens against a field list once gave mcycle="benchmark=coremark"); a run
# that lacks one, or breaks a counter identity, is a failed run.
from snapshot_fields import FIELDS, invariants, parse as parse_snapshot  # noqa: E402


ap = argparse.ArgumentParser()
ap.add_argument("--lines", type=int, default=64)
ap.add_argument("--l0", type=int, default=8)
ap.add_argument("--imem", type=int, default=4096)
ap.add_argument("--dmem", type=int, default=4096)
ap.add_argument("--max-cycles", type=int, default=200000000)
ap.add_argument("--out", required=True)
# The default keeps the four configurations every earlier run used.
ap.add_argument("--configs", default="0,1,2,3")
ap.add_argument("--lib", default="work")
args = ap.parse_args()

# One log directory per output file, so pass 2 keeps pass 1's logs.
log_dir = ROOT / "results" / "coremark_logs" / Path(args.out).stem
log_dir.mkdir(parents=True, exist_ok=True)
rows, failures = [], []

for cfg in [int(c) for c in args.configs.split(",")]:
    name = CONFIGS[cfg]
    log = log_dir / ("coremark_%s_lc%d.log" % (name, args.lines))
    do = ("vsim -onfinish stop -gCACHE_CONFIG=%d -gMEMFILE=fw/coremark.hex "
          "-gICACHE_LINE_COUNT=%d -gDCACHE_LINE_COUNT=%d -gL0_ENTRIES=%d "
          "-gIMEM_DEPTH=%d -gDMEM_DEPTH=%d "
          "%s.tb_benchmark_snapshot +benchmark=coremark +max_cycles=%d; "
          "run -all; quit -f"
          % (cfg, args.lines, args.lines, args.l0, args.imem, args.dmem,
             args.lib, args.max_cycles))
    t0 = time.time()
    rc = subprocess.call([VSIM, "-c", "-do", do], cwd=str(ROOT),
                         stdout=open(log, "w"), stderr=subprocess.STDOUT)
    row, why = parse_snapshot(log) if rc == 0 else (None, "rc=%d" % rc)
    bad = invariants(row) if row else []
    if row is None or bad:
        failures.append("%s: %s" % (name, why or "; ".join(bad)))
        print("[FAIL] %-8s %s  see %s" % (name, why or "; ".join(bad), log))
        continue
    row["kernel"], row["config"], row["config_id"] = "coremark", name, cfg
    rows.append(row)
    print("[ok]   %-8s mcycle=%-12s minstret=%-10s  %.0fs"
          % (name, row["mcycle"], row["minstret"], time.time() - t0))

if rows:
    import csv
    cols = ["kernel", "config", "config_id"] + list(FIELDS)
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("[PASS] %d run(s) -> %s" % (len(rows), args.out))
if failures:
    print("   failed: %s" % ", ".join(failures))
sys.exit(0 if rows and not failures else 1)
