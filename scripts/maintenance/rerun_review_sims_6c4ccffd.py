#!/usr/bin/env python3
"""Re-execute on RTL 6c4ccffd the review experiments that ran on older RTL (owner 2026-10-14: every reported number
from ONE RTL; audit results/rtl_consistency_audit_20261014.md):

  A8  branch predictor off, 12 upstream kernels, 4 KiB, CACHE_CONFIG 0-3     (old: bp0_upstream_r14_4kb, R14)
  A3  cache-model cross-validation, 4 KiB: configs 0-3, N-way 4-5, FAST_HIT 1-5 (old: crossval_r16_*, R16)
  A4  retire-overlap monitor, DM, 12 upstream kernels                         (old: a4_overlap, R14)
  IRQ interrupt latency / context switch, CACHE_CONFIG 0-3                    (old: irq_metrics, R14 / R15)

Every experiment twice; each pass recompiles its libraries from the live hdl/ (manifest 6c4ccffd, checked first).
New outputs carry 6c4ccffd in their names and never overwrite the older-RTL results. One simulator at a time (the
experiments share the work library and the fixed cache-trace file); the whole process tree runs at below-normal
priority so the PD flows keep the CPU. At the end: pass 1 vs pass 2, and 6c4ccffd vs the older results, every field.

    python scripts/maintenance/rerun_review_sims_6c4ccffd.py      (cooperative stop: results/review_sims_6c4ccffd/.abort)
"""
from __future__ import annotations

import csv
import ctypes
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "review_sims_6c4ccffd"
PY = sys.executable
VSIM = r"C:\questasim64_2024.1\win64\vsim.exe"
UP = ("up_aha-mont64,up_crc32,up_depthconv,up_edn,up_huffbench,up_matmult-int,up_md5sum,up_nettle-sha256,up_slre,"
      "up_statemate,up_tarfind,up_ud")
MANIFEST = "6c4ccffd"


def log(msg):
    line = "%s %s" % (time.strftime("%Y-%m-%dT%H:%M:%S"), msg)
    print(line, flush=True)
    with (OUT / "driver.log").open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def aborted():
    return (OUT / ".abort").exists()


def sh(cmd, tag, cwd=ROOT):
    lf = OUT / ("%s.log" % tag)
    with lf.open("w", encoding="utf-8") as f:
        rc = subprocess.run(cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT).returncode
    tail = lf.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-1:] or [""]
    log("%s rc=%d | %s" % (tag, rc, tail[0][:160]))
    return rc


def vsim_do(do, logfile):
    return subprocess.run([VSIM, "-c", "-do", do, "-l", str(logfile)], cwd=ROOT, capture_output=True,
                          text=True).returncode


def a8(p):
    return sh([PY, "scripts/run_ablation.py", "--compile", "--lines", "256", "--bp", "0", "--kernels", UP,
               "--out", "results/bp0_upstream_6c4ccffd_4kb_p%d.csv" % p], "a8_bp0_p%d" % p)


def a3(p):
    rc = 0
    for name, extra in (("4cfg", ["--configs", "0,1,2,3"]), ("nway", ["--configs", "4,5"]),
                        ("fast", ["--fast", "--configs", "1,2,3,4,5"])):
        if aborted():
            return 1
        rc |= sh([PY, "scripts/run_crossval.py", "--lines", "256", "--kernels", UP,
                  "--out", "results/crossval_6c4ccffd_%s_p%d.csv" % (name, p)] + extra, "a3_%s_p%d" % (name, p))
        keep = OUT / ("crossval_logs_%s_p%d" % (name, p))           # run_crossval overwrites its log folder
        if keep.exists():
            shutil.rmtree(keep)
        shutil.copytree(ROOT / "results" / "crossval_logs", keep)
    return rc


OVL = re.compile(r"OVERLAP retire_events=(\d+) charged_elsewhere=(\d+) trap=(\d+) control=(\d+) mmio=(\d+) "
                 r"dcache=(\d+) icache=(\d+) load_use=(\d+)")
SNAP = re.compile(r"BENCHMARK_SNAPSHOT benchmark=(\S+) config=(\d+) mcycle=(\d+) minstret=(\d+) cycle_retire=(\d+)")


def a4(p):
    d = OUT / ("a4_overlap_p%d" % p)
    d.mkdir(parents=True, exist_ok=True)
    if vsim_do("vlib work_mon; vlog -work work_mon -sv scripts/metrics/overlap_mon.sv; quit -f", d / "compile_mon.log"):
        log("a4 p%d: monitor compile failed" % p)
        return 1
    rows, bad = [], 0
    for k in UP.split(","):
        if aborted():
            return 1
        lf = d / ("%s.log" % k)
        vsim_do("vsim -onfinish stop -gCACHE_CONFIG=0 -gMEMFILE=fw/%s.hex -gICACHE_LINE_COUNT=256 "
                "-gDCACHE_LINE_COUNT=256 -gL0_ENTRIES=8 work.tb_benchmark_snapshot work_mon.overlap_mon "
                "+benchmark=%s +max_cycles=5000000; run -all; quit -f" % (k, k), lf)
        t = lf.read_text(encoding="utf-8", errors="replace")
        s, o = SNAP.search(t), OVL.search(t)
        if not (s and o and "[PASS]" in t):
            bad += 1
            rows.append({"kernel": k, "status": "FAIL"})
            continue
        minstret, retire = int(s.group(4)), int(s.group(5))
        elsewhere = int(o.group(2))
        ok = (minstret - retire == elsewhere) and int(o.group(1)) == minstret
        bad += 0 if ok else 1
        rows.append({"kernel": k, "minstret": minstret, "cycle_retire": retire, "diff": minstret - retire,
                     "charged_elsewhere": elsewhere, "control": int(o.group(4)), "load_use": int(o.group(8)),
                     "trap": int(o.group(3)), "mmio": int(o.group(5)), "dcache": int(o.group(6)),
                     "icache": int(o.group(7)), "status": "IDENTITY_OK" if ok else "IDENTITY_FAIL"})
    with (OUT / ("a4_overlap_6c4ccffd_p%d.csv" % p)).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows and len(rows[0]) > 2 else
                           ["kernel", "status"], extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    log("a4 p%d: %d kernels, %d not IDENTITY_OK" % (p, len(rows), bad))
    return 1 if bad else 0


def irq(p):
    d = OUT / "irq_logs"
    d.mkdir(parents=True, exist_ok=True)
    if p == 1:   # firmware rebuilt once from the frozen source (as scripts/metrics/run_irq_metrics.sh does)
        sh(["wsl.exe", "-d", "Ubuntu", "-e", "bash", "-lc",
            "cd /mnt/e/Projects/RISCV-research/sw_metrics/irq && make clean > /dev/null && make 2>&1 | tail -1"],
           "irq_build")
    if vsim_do("do sw_metrics/irq/compile_irq.do; quit -f", d / ("compile_p%d.log" % p)):
        log("irq p%d: compile failed" % p)
        return 1
    rc = 0
    for cfg in (0, 1, 2, 3):
        if aborted():
            return 1
        lf = d / ("cfg%d_p%d.log" % (cfg, p))
        vsim_do("vsim -onfinish stop -gCACHE_CONFIG=%d work_irq.tb_irq_metrics; run -all; quit -f" % cfg, lf)
        ok = "[PASS] IRQ_METRICS" in lf.read_text(encoding="utf-8", errors="replace")
        rc |= 0 if ok else 1
        log("irq p%d cfg %d: %s" % (p, cfg, "PASS" if ok else "FAIL"))
    return rc


def rows_by(path, keys):
    with open(path, newline="", encoding="utf-8") as f:
        return {tuple(r[k] for k in keys): r for r in csv.DictReader(f)}


def cmp_csv(a, b, keys, ignore=()):
    ra, rb = rows_by(a, keys), rows_by(b, keys)
    diffs = [(k, f, ra[k].get(f), rb[k].get(f)) for k in ra if k in rb for f in ra[k]
             if f not in ignore and f in rb[k] and ra[k].get(f) != rb[k].get(f)]
    return {"a": str(Path(a).relative_to(ROOT)), "b": str(Path(b).relative_to(ROOT)), "rows": [len(ra), len(rb)],
            "missing_in_b": len(set(ra) - set(rb)), "missing_in_a": len(set(rb) - set(ra)),
            "field_diffs": len(diffs), "first": [[list(k), f, x, y] for k, f, x, y in diffs[:10]]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)  # BELOW_NORMAL
    chk = subprocess.run([PY, "scripts/rtl_manifest.py", "--check"], cwd=ROOT, capture_output=True, text=True)
    if "IDENTICAL" not in chk.stdout or MANIFEST not in chk.stdout:
        log("manifest check failed, not starting")
        return 1
    log("start: live tree = manifest %s (IDENTICAL); A8, A3, A4, IRQ, two passes each" % MANIFEST)
    for p in (1, 2):
        for step in (a8, a3, a4, irq):
            if aborted():
                log("abort flag: stopped before %s p%d" % (step.__name__, p))
                return 1
            step(p)
    if subprocess.run([PY, "scripts/metrics/irq_metrics_table.py", "--logs", str(OUT / "irq_logs"),
                       "--out", "results/irq_metrics_6c4ccffd.csv"], cwd=ROOT).returncode:
        log("irq table: FAIL (a pass missing or pass 1 != pass 2)")
    R = ROOT / "results"
    res = {}
    pairs = [("a8_p1_vs_p2", R / "bp0_upstream_6c4ccffd_4kb_p1.csv", R / "bp0_upstream_6c4ccffd_4kb_p2.csv", ("kernel", "config")),
             ("a8_old_vs_new", R / "bp0_upstream_r14_4kb_p1.csv", R / "bp0_upstream_6c4ccffd_4kb_p1.csv", ("kernel", "config")),
             ("a4_p1_vs_p2", OUT / "a4_overlap_6c4ccffd_p1.csv", OUT / "a4_overlap_6c4ccffd_p2.csv", ("kernel",)),
             ("irq_old_vs_new", R / "irq_metrics.csv", R / "irq_metrics_6c4ccffd.csv", ("config", "phase"))]
    for name in ("4cfg", "nway", "fast"):
        pairs.append(("a3_%s_p1_vs_p2" % name, R / ("crossval_6c4ccffd_%s_p1.csv" % name),
                      R / ("crossval_6c4ccffd_%s_p2.csv" % name), ("kernel", "config")))
    pairs += [("a3_4cfg_old_vs_new", R / "crossval_r16_4cfg.csv", R / "crossval_6c4ccffd_4cfg_p1.csv", ("kernel", "config")),
              ("a3_fast_old_vs_new", R / "crossval_r16_fast.csv", R / "crossval_6c4ccffd_fast_p1.csv", ("kernel", "config")),
              ("a3_nway_old_vs_new", R / "crossval_r15_nway.csv", R / "crossval_6c4ccffd_nway_p1.csv", ("kernel", "config"))]
    for name, a, b, keys in pairs:
        if a.is_file() and b.is_file():
            res[name] = cmp_csv(a, b, keys)
            log("%s: rows %s, missing %d/%d, field differences %d" % (name, res[name]["rows"], res[name]["missing_in_b"],
                                                                     res[name]["missing_in_a"], res[name]["field_diffs"]))
        else:
            log("%s: input missing (%s / %s)" % (name, a.name, b.name))
    # every cross-validation row must say the RTL counters equal the independent model
    for f in sorted(R.glob("crossval_6c4ccffd_*_p[12].csv")):
        rs = list(csv.DictReader(open(f, newline="", encoding="utf-8")))
        nm = sum(1 for r in rs if r.get("match") != "EXACT")
        res["match_" + f.stem] = {"rows": len(rs), "not_matching": nm}
        log("%s: %d rows, %d not matching the model" % (f.name, len(rs), nm))
    (OUT / "comparison.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    log("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
