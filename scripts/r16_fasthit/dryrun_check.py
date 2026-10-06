"""R16 dry run (rule D.1: apply by script on a copy first). Simulates the patched copy work_r16_dryrun/:

  (a) FAST_HIT=0 (default): every snapshot field must equal the frozen R15 reference (results/r15_4kb_p1.csv,
      results/coremark_r15_4kb_p1.csv) -- the change must not touch the existing configurations;
  (b) FAST_HIT=1 on the DSE / N-way configurations: the run must pass the harness self-check and invariants, every
      CACHE counter (accesses, hits, victim hits, misses, AXI traffic) and every architectural counter (minstret,
      branches...) must equal the FAST_HIT=0 run -- FAST_HIT only answers earlier, it decides nothing differently --
      and mcycle must not grow.
    python scripts/r16_fasthit/dryrun_check.py [--compile]
"""
import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "work_r16_dryrun"
sys.path.insert(0, str(ROOT / "scripts"))
from snapshot_fields import FIELDS, invariants, parse as parse_snapshot  # noqa: E402

VSIM = r"C:\questasim64_2024.1\win64\vsim.exe"
CFG = {"DM": 0, "SA2": 1, "DM_VC4": 2, "DM_DSE": 3, "SA4": 4}
WLS = ("up_crc32", "up_ud", "up_aha-mont64", "coremark")
# counters FAST_HIT may change: cycle accounting only
TIMING = {"mcycle", "cycle_retire", "load_use", "i_wait", "d_wait", "control", "trap", "mmio", "fill_drain",
          "other", "snap_seq"}

ap = argparse.ArgumentParser()
ap.add_argument("--compile", action="store_true")
a = ap.parse_args()
logs = W / "dryrun_logs"
logs.mkdir(exist_ok=True)
if a.compile:
    log = logs / "compile.log"
    rc = subprocess.run([VSIM, "-c", "-do", "do tb/compile_active_design.do; quit -f", "-l", str(log)], cwd=W,
                        capture_output=True, text=True).returncode
    txt = log.read_text(encoding="utf-8", errors="replace")
    if rc != 0 or "** Error" in txt or "** Fatal" in txt:
        sys.exit("[FAIL] compile, see %s" % log)
    print("[COMPILE] ok", flush=True)


def run(cfg, fast, w):
    mem = "-gIMEM_DEPTH=4096 -gDMEM_DEPTH=4096 " if w == "coremark" else ""
    log = logs / ("%s_f%d_%s.log" % (cfg, fast, w))
    do = ("vsim -onfinish stop -gCACHE_CONFIG=%d -gMEMFILE=fw/%s.hex -gICACHE_LINE_COUNT=256 -gDCACHE_LINE_COUNT=256 "
          "-gCACHE_FAST_HIT=%d -gL0_ENTRIES=8 -gBRANCH_PREDICT_ENABLE=1 %swork.tb_benchmark_snapshot +benchmark=%s "
          "+max_cycles=20000000; run -all; quit -f" % (CFG[cfg], w, fast, mem, w))
    t0 = time.time()
    subprocess.run([VSIM, "-c", "-do", do, "-l", str(log)], cwd=W, capture_output=True, text=True, timeout=7200)
    row, why = parse_snapshot(log)
    bad = invariants(row) if row else [why]
    print("[%s] %-7s FAST_HIT=%d %-14s mcycle=%s (%.0fs)" % ("OK" if row and not bad else "FAIL", cfg, fast, w,
                                                              row["mcycle"] if row else "-", time.time() - t0),
          flush=True)
    return row if row and not bad else None


ref = {}
for r in csv.DictReader(open(ROOT / "results" / "r15_4kb_p1.csv", encoding="utf-8")):
    ref[(r["config"], r["kernel"])] = r
for r in csv.DictReader(open(ROOT / "results" / "coremark_r15_4kb_p1.csv", encoding="utf-8")):
    ref[(r["config"], "coremark")] = r
problems = []
rows = {}
for cfg in CFG:
    for w in WLS:
        r0 = run(cfg, 0, w)
        rows[(cfg, 0, w)] = r0
        if r0 is None:
            problems.append("%s/%s FAST_HIT=0 failed" % (cfg, w))
            continue
        d = [f for f in FIELDS if f in ref[(cfg, w)] and str(r0[f]) != ref[(cfg, w)][f]]
        if d:
            problems.append("%s/%s FAST_HIT=0 differs from R15 in %s" % (cfg, w, d[:8]))
        if cfg == "DM":
            continue
        r1 = run(cfg, 1, w)
        rows[(cfg, 1, w)] = r1
        if r1 is None:
            problems.append("%s/%s FAST_HIT=1 failed" % (cfg, w))
            continue
        d = [f for f in FIELDS if f not in TIMING and str(r1[f]) != str(r0[f])]
        if d:
            problems.append("%s/%s FAST_HIT=1 changes non-timing counters %s" % (cfg, w, d[:8]))
        if int(r1["mcycle"]) > int(r0["mcycle"]):
            problems.append("%s/%s FAST_HIT=1 is slower (%s > %s)" % (cfg, w, r1["mcycle"], r0["mcycle"]))
        print("      %-7s %-14s mcycle %s -> %s (%+.2f %%), DM %s" % (
            cfg, w, r0["mcycle"], r1["mcycle"], 100.0 * (int(r1["mcycle"]) - int(r0["mcycle"])) / int(r0["mcycle"]),
            ref[("DM", w)]["mcycle"]), flush=True)
print("[%s] %d problem(s)" % ("PASS" if not problems else "FAIL", len(problems)))
for p in problems:
    print("   ", p)
sys.exit(1 if problems else 0)
