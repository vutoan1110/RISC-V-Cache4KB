#!/usr/bin/env python3
"""Review items M1 + M2 (danh_gia.txt, 2026-10-03): the cache design-space sweep on the current suite.

M2 asks for a real design space (capacity, line size, associativity, victim depth); M1 asks that controller cost be
separated from organisation. Every point is run on the R15 RTL (frozen manifest) with the 12 upstream Embench-IoT
kernels (fw/up_*.hex) and CoreMark (fw/coremark.hex, 4096+4096-word memories as in run_coremark.py):

  grid A  capacity 256 B .. 8 KiB x {DM (cfg 0, five-state controller), DM_DSE (cfg 3, the DSE core as a plain
          direct-mapped cache), SA2 (cfg 1), VC4 (cfg 2, 4 victim entries), SA4 (cfg 4, N-way core)}, 16 B lines
          -> DM vs DM_DSE is the controller cost, DM_DSE vs SA2 / SA4 / VC4 the organisation effect on ONE controller
  grid B  1 KiB and 4 KiB x line 8 B and 32 B x {DM_DSE, SA2, VC4, SA4}   (the DM controller supports 16 B lines only:
          dcache.v / icache.v $fatal on any other LINE_WORDS)
  grid C  1 KiB and 4 KiB x victim depth 2 and 8 (16 B lines)
Capacity = LINE_COUNT x line bytes for every organisation (same data storage, ways divide the sets).

    python scripts/m2/run_m2_sweep.py --compile --workers 4 --pass 1
    python scripts/m2/run_m2_sweep.py --workers 4 --pass 2          (independent second execution)
    python scripts/m2/run_m2_sweep.py --list                        (the grid only)
Outputs results/m2/sweep_p<pass>.csv (one row per point x workload, every snapshot field) and the logs in
results/m2/logs_p<pass>/. A run whose log already parses with all invariants is not re-run (resume after an
interruption); the two passes never share logs. Cooperative stop: create results/m2/.abort (workers take no new run).
"""
from __future__ import annotations

import argparse
import csv
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from snapshot_fields import FIELDS, invariants, parse as parse_snapshot  # noqa: E402

VSIM = r"C:\questasim64_2024.1\win64\vsim.exe"
KERNELS = ("up_aha-mont64", "up_crc32", "up_depthconv", "up_edn", "up_huffbench", "up_matmult-int",
           "up_md5sum", "up_nettle-sha256", "up_slre", "up_statemate", "up_tarfind", "up_ud")
WORKLOADS = KERNELS + ("coremark",)
ORGS = {"DM": 0, "SA2": 1, "VC": 2, "DM_DSE": 3, "SA4": 4}
OUT = ROOT / "results" / "m2"
# R16 --fast: CACHE_FAST_HIT=1 on the DSE / N-way points, own libraries and output names (set in main)
FAST = False
LIBPFX = "work_m2_"
ABORT = OUT / ".abort"


def point(org, cap, line, vc=4):
    cfg = ORGS[org]
    name = ("VC%d" % vc if org == "VC" else org) + "_%dB_L%d" % (cap, line)
    return {"point": name, "org": "VC%d" % vc if org == "VC" else org, "cfg": cfg, "cap_bytes": cap,
            "line_bytes": line, "lines": cap // line, "line_words": line // 4, "vc": vc if org == "VC" else 0}


def grid():
    pts = []
    for cap in (256, 512, 1024, 2048, 4096, 8192):                       # grid A
        for org in ("DM", "DM_DSE", "SA2", "VC", "SA4"):
            pts.append(point(org, cap, 16))
    for cap in (1024, 4096):                                             # grid B
        for line in (8, 32):
            for org in ("DM_DSE", "SA2", "VC", "SA4"):
                pts.append(point(org, cap, line))
    for cap in (1024, 4096):                                             # grid C
        for vc in (2, 8):
            pts.append(point("VC", cap, 16, vc))
    names = [p["point"] for p in pts]
    assert len(names) == len(set(names)), "duplicate point"
    return pts


def do_cmd(lib, p, w, max_cycles):
    mem = "-gIMEM_DEPTH=4096 -gDMEM_DEPTH=4096 " if w == "coremark" else ""
    return ("vsim -onfinish stop %s-gCACHE_CONFIG=%d -gMEMFILE=fw/%s.hex -gICACHE_LINE_COUNT=%d -gDCACHE_LINE_COUNT=%d "
            "-gCACHE_LINE_WORDS=%d -gVICTIM_ENTRIES=%d -gL0_ENTRIES=8 -gBRANCH_PREDICT_ENABLE=1 %s"
            "%s.tb_benchmark_snapshot +benchmark=%s +max_cycles=%d; run -all; quit -f"
            % ("-gCACHE_FAST_HIT=1 " if FAST else "", p["cfg"], w, p["lines"], p["lines"], p["line_words"], p["vc"] if p["vc"] else 4, mem, lib, w,
               max_cycles))


def good(log):
    if not log.is_file():
        return None
    row, why = parse_snapshot(log)
    if row is None or invariants(row):
        return None
    return row


def worker(k, tasks, results, logdir, max_cycles, lock):
    lib = "%s%d" % (LIBPFX, k)
    while True:
        if ABORT.exists():
            return
        try:
            p, w = tasks.get_nowait()
        except queue.Empty:
            return
        log = logdir / ("%s__%s.log" % (p["point"], w))
        row = good(log)
        status = "reused"
        if row is None:
            t0 = time.time()
            try:
                rc = subprocess.run([VSIM, "-c", "-do", do_cmd(lib, p, w, max_cycles), "-l", str(log)], cwd=ROOT,
                                    capture_output=True, text=True, timeout=4 * 3600).returncode
            except subprocess.TimeoutExpired:
                rc = -9
            row = good(log)
            status = "rc=%d %.0fs" % (rc, time.time() - t0)
        with lock:
            if row is None:
                results.append((p, w, None))
                print("[FAIL] w%d %-18s %-16s %s  %s" % (k, p["point"], w, status, log), flush=True)
            else:
                results.append((p, w, row))
                print("[OK]   w%d %-18s %-16s mcycle=%-9s %s" % (k, p["point"], w, row["mcycle"], status), flush=True)


def main():
    global FAST, LIBPFX, OUT, ABORT
    ap = argparse.ArgumentParser()
    ap.add_argument("--pass", dest="pass_", type=int, default=1)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--compile", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--points", default="", help="comma list of point names (default: the whole grid)")
    ap.add_argument("--workloads", default=",".join(WORKLOADS))
    ap.add_argument("--max-cycles", type=int, default=40000000)
    ap.add_argument("--fast", action="store_true", help="R16 CACHE_FAST_HIT=1 (DSE / N-way points only)")
    ap.add_argument("--out", default=str(OUT),
                    help="result directory (default results/m2); a new directory means no log of an older RTL is "
                         "reused (2026-10-14: re-execution on RTL 6c4ccffd goes to results/m2_6c4ccffd)")
    a = ap.parse_args()
    OUT = Path(a.out) if Path(a.out).is_absolute() else ROOT / a.out
    ABORT = OUT / ".abort"
    FAST = a.fast
    LIBPFX = "work_m2f_" if FAST else "work_m2_"
    pts = grid()
    if FAST:
        pts = [p for p in pts if p["cfg"] != 0]
    if a.points:
        sel = set(a.points.split(","))
        pts = [p for p in pts if p["point"] in sel]
    wls = a.workloads.split(",")
    if a.list:
        for p in pts:
            print("%-18s cfg %d  %5d B  line %2d B  lines %4d  vc %d" % (p["point"], p["cfg"], p["cap_bytes"],
                                                                      p["line_bytes"], p["lines"], p["vc"]))
        print("%d points x %d workloads = %d runs" % (len(pts), len(wls), len(pts) * len(wls)))
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    if a.compile:
        for k in range(1, a.workers + 1):
            log = OUT / ("compile_%s%d.log" % (LIBPFX[5:], k))
            rc = subprocess.run([VSIM, "-c", "-do", "do scripts/m2/compile_%s%d.do; quit -f" % (LIBPFX[5:], k), "-l", str(log)],
                                cwd=ROOT, capture_output=True, text=True).returncode
            txt = log.read_text(encoding="utf-8", errors="replace")
            if rc != 0 or "** Error" in txt or "** Fatal" in txt:
                print("[FAIL] compile work_m2_%d, see %s" % (k, log))
                return 1
            print("[COMPILE] work_m2_%d ok" % k, flush=True)
    # 2026-10-06: a pass started with more workers than compiled libraries had its extra worker fail every run
    # it took (vsim rc=12, no library); refuse to start instead
    missing = [k for k in range(1, a.workers + 1) if not (ROOT / ("%s%d" % (LIBPFX, k))).is_dir()]
    if missing:
        print("[FAIL] no library %s for worker(s) %s; compile with --compile or use fewer --workers"
              % (",".join("%s%d" % (LIBPFX, k) for k in missing), missing))
        return 1
    logdir = OUT / ("logs_%sp%d" % ("fast_" if FAST else "", a.pass_))
    logdir.mkdir(parents=True, exist_ok=True)
    tasks = queue.Queue()
    # CoreMark (the longest run) first, then big-to-small capacities, so the tail of the batch is short runs
    order = sorted(((p, w) for p in pts for w in wls),
                   key=lambda pw: (pw[1] != "coremark", pw[0]["cap_bytes"], pw[0]["point"], pw[1]))
    for t in order:
        tasks.put(t)
    results, lock = [], threading.Lock()
    print("[START] pass %d: %d runs on %d workers" % (a.pass_, tasks.qsize(), a.workers), flush=True)
    th = [threading.Thread(target=worker, args=(k, tasks, results, logdir, a.max_cycles, lock))
          for k in range(1, a.workers + 1)]
    for t in th:
        t.start()
    for t in th:
        t.join()
    out = OUT / ("sweep_%sp%d.csv" % ("fast_" if FAST else "", a.pass_))
    cols = ["point", "org", "cfg", "cap_bytes", "line_bytes", "lines", "vc", "workload"] + list(FIELDS)
    ok = [(p, w, r) for p, w, r in results if r is not None]
    ok.sort(key=lambda x: (x[0]["point"], x[1]))
    with out.open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        wr.writeheader()
        for p, w, r in ok:
            row = dict(r)
            row.update({k: p[k] for k in ("point", "org", "cfg", "cap_bytes", "line_bytes", "lines", "vc")})
            row["workload"] = w
            wr.writerow(row)
    bad = len(results) - len(ok)
    left = tasks.qsize()
    print("[%s] pass %d: %d ok, %d failed, %d not run -> %s" % ("PASS" if not bad and not left else "PARTIAL",
                                                                 a.pass_, len(ok), bad, left, out), flush=True)
    return 0 if not bad and not left else 1


if __name__ == "__main__":
    raise SystemExit(main())
