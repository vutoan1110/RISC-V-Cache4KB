#!/usr/bin/env python3
"""Cache-controller ablation matrix.

The published comparison confounds cache organization with controller depth:
CACHE_CONFIG 0 runs the five-state icache_controller, while 1 and 2 run the
ten-state icache_dse_core.  CACHE_CONFIG 3 selects neither IS_SA2 nor IS_VC4,
so the DSE core degenerates to a plain direct-mapped cache.  Comparing 0 with 3
isolates controller cost; comparing 3 with 1 isolates associativity.

    python scripts/run_ablation.py --configs 0,3 --kernels up_crc32
    python scripts/run_ablation.py --compile
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The standard benchmark suite: the upstream Embench-IoT kernels that fit the 16 KiB RAM (fw/up_*.hex).
# The project's own Embench-style kernels were removed on 2026-09-30 (review item A6).
KERNELS = ("up_aha-mont64", "up_crc32", "up_depthconv", "up_edn", "up_huffbench", "up_matmult-int",
           "up_md5sum", "up_nettle-sha256", "up_slre", "up_statemate", "up_tarfind", "up_ud")
CONFIGS = {0: "DM", 1: "SA2", 2: "DM_VC4", 3: "DM_DSE"}
MAX_CYCLES = 5000000
sys.path.insert(0, str(Path(__file__).resolve().parent))
# Every field the harness prints; a run that lacks one is a failed run.
from snapshot_fields import FIELDS, invariants, parse as parse_snapshot  # noqa: E402


def vsim_bin() -> str:
    for cand in (os.environ.get("QUESTA_VSIM"),
                 r"C:\questasim64_2024.1\win64\vsim.exe"):
        if cand and Path(cand).is_file():
            return cand
    found = shutil.which("vsim")
    if found:
        return found
    sys.exit("[FAIL] vsim not found; set QUESTA_VSIM")


def vsim(do: str, log: Path) -> int:
    proc = subprocess.run([vsim_bin(), "-c", "-do", do, "-l", str(log)],
                          cwd=ROOT, capture_output=True, text=True, timeout=7200)
    return proc.returncode


def compile_design(log_dir: Path, asic_view: bool = False, asic_script: str = "tb/compile_asic_view.do") -> None:
    script = asic_script if asic_view else "tb/compile_active_design.do"
    print("[COMPILE] %s" % script)
    log = log_dir / ("compile_asic_view.log" if asic_view else "compile.log")
    if vsim("do %s; quit -f" % script, log) != 0:
        sys.exit("[FAIL] compile failed; see %s" % log)
    txt = log.read_bytes().decode("utf-8", "replace")
    if re.search(r"\*\*\s+(Fatal|Error):", txt) or "[PASS]" not in txt:
        sys.exit("[FAIL] compile transcript reports errors; see %s" % log)
    print("         ok")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", default="0,1,2,3")
    ap.add_argument("--kernels", default=",".join(KERNELS))
    ap.add_argument("--compile", action="store_true",
                    help="recompile the work library first")
    ap.add_argument("--out", default="results/ablation.csv")
    # Cache capacity is LINE_COUNT * LINE_WORDS * 4 bytes. 64 lines is the
    # published 1 KiB; 256 lines is 4 KiB, where each of the four data banks
    # becomes an exact fit for an OpenRAM 32x256 macro.
    ap.add_argument("--lines", type=int, default=64)
    # L0 hot-buffer depth. The LE side is measured (8 -> 4 is -721 LE and
    # +0.710 ns slack); this is the axis that says what it costs in cycles.
    ap.add_argument("--l0", type=int, default=8)
    # Run on the memories the ASIC builds (SRAM macro models and the two
    # macro wrappers) instead of the behavioural RAMs. Only the DM 4 KiB point
    # exists as an ASIC, so this forces CACHE_CONFIG 0 and 256 lines.
    ap.add_argument("--asic-view", action="store_true")
    # FLOW_JOURNAL Incident 93: an experimental RTL copy is compiled by its own script into its own library
    ap.add_argument("--asic-compile", default="tb/compile_asic_view.do")
    ap.add_argument("--asic-lib", default="work_asic")
    # R14 (RAM16K_CHANGES.md): images from another directory, e.g. the upstream Embench suite or a
    # scale-factor probe; the default keeps the frozen fw/ images.
    ap.add_argument("--fw-dir", default="fw")
    # A8 (review): branch predictor off (BRANCH_PREDICT_ENABLE=0) at the same cache points.
    ap.add_argument("--bp", type=int, default=1)
    # Full-iteration upstream images (fw_board/) need more than the default cycle budget.
    ap.add_argument("--max-cycles", type=int, default=MAX_CYCLES)
    # FPGA-view simulation library (work_b: scripts/metrics/compile_active_design_b.do) for a parallel batch.
    ap.add_argument("--lib", default="work")
    args = ap.parse_args()

    configs = [int(c) for c in args.configs.split(",")]
    kernels = args.kernels.split(",")
    # One log directory per output file, so pass 2 does not overwrite the
    # logs pass 1's CSV was read from.
    log_root = "ablation_logs"
    if args.asic_view:
        args.configs, args.lines = "0", 256
        configs = [0]
        log_root = "ablation_logs_asic_view"
    log_dir = ROOT / "results" / log_root / Path(args.out).stem
    log_dir.mkdir(parents=True, exist_ok=True)
    if args.compile:
        compile_design(log_dir, args.asic_view, args.asic_compile)

    rows, failures = [], []
    for cfg in configs:
        for kern in kernels:
            name = CONFIGS[cfg]
            hexfile = "%s/%s.hex" % (args.fw_dir, kern)
            if not (ROOT / hexfile).is_file():
                failures.append("%s: missing %s" % (kern, hexfile))
                continue
            log = log_dir / ("%s_%s.log" % (kern, name))
            do = ("vsim -onfinish stop -gCACHE_CONFIG=%d -gMEMFILE=%s "
                  "-gICACHE_LINE_COUNT=%d -gDCACHE_LINE_COUNT=%d -gL0_ENTRIES=%d -gBRANCH_PREDICT_ENABLE=%d "
                  "%s +benchmark=%s +max_cycles=%d; "
                  "run -all; quit -f"
                  % (cfg, hexfile, args.lines, args.lines, args.l0, args.bp,
                     ("-gVERBOSE=0 %s.tb_benchmark_snapshot %s.asic_view_checker" % (args.asic_lib, args.asic_lib)
                      if args.asic_view else "%s.tb_benchmark_snapshot" % args.lib),
                     kern, args.max_cycles))
            t0 = time.time()
            rc = vsim(do, log)
            row, why = parse_snapshot(log) if rc == 0 else (None, "rc=%d" % rc)
            bad = invariants(row) if row else []
            if row is None or bad:
                failures.append("%s/%s: %s" % (kern, name, why or "; ".join(bad)))
                print("[FAIL] %-11s %-7s  %s  see %s"
                      % (kern, name, why or "; ".join(bad), log))
                continue
            row["kernel"], row["config"], row["config_id"] = kern, name, cfg
            rows.append(row)
            print("[OK]   %-11s %-7s mcycle=%-9d i_wait=%-7s (%.0fs)" %
                  (kern, name, row["mcycle"], row["i_wait"], time.time() - t0))

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = ["kernel", "config", "config_id"] + list(FIELDS)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print("")
    print("[%s] %d run(s) -> %s" %
          ("PASS" if not failures else "PARTIAL", len(rows), out))
    for f in failures:
        print("   failed: %s" % f)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
