#!/usr/bin/env python3
"""Workspace cleanup after the Incident 91 PD campaign (user rule 4, PD_metrics.pdf; FLOW_JOURNAL Incident 92).

    python scripts/cleanup_20260928.py            # dry run: list + sizes
    python scripts/cleanup_20260928.py --do       # archive, hash, delete, manifest in results/

Deleted, each whole run archived first (results/pd_run_archive/<run>/: resolved.json, last metrics,
error/warning logs, gzipped flow.log, step list):
  * PD explorations x1_nohd, x2_rc2, x3_fix, x4_hold (their results are in Incident 91 and reproduced by the
    kept runs / configs), and final2_A (rejected candidate: max_ss -9.52, 3 max_ff hold violations);
  * the two crashed step dirs of final3_B (random OpenROAD SIGSEGVs; their logs go to the archive);
  * scratch/ of the failed stock-EQY steps (the logs next to it stay);
  * regenerable intermediates of the step-B LEC reruns and of the RC/antenna experiments (sha256 of every
    file in the manifest; stepB_new.ps1 / the pd_exp scripts rebuild them).
KEEP: final3_A, final3_B (signed off), final_A, final_B (previous signoff, in the Golden Snapshot), every log,
report, markdown, CSV, SAIF and script.
"""
import glob
import gzip
import hashlib
import json
import os
import shutil
import sys

DO = "--do" in sys.argv
R = r"E:\Projects\RISCV-research"
RUNS = os.path.join(R, r"asic\soc_dm_4kb\runs")
ARCH = os.path.join(R, r"results\pd_run_archive")
MANIFEST = os.path.join(R, r"results\cleanup_20260928_deleted.txt")
MB = 1 << 20
DELETE_RUNS = ["x1_nohd", "x2_rc2", "x3_fix", "x4_hold", "final2_A"]
CRASHED_STEPS = [r"final3_B\45-openroad-detailedrouting", r"final3_B\55-odb-cellfrequencytables"]


def size(p):
    if os.path.isfile(p):
        return os.path.getsize(p)
    return sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(p) for f in fs)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def archive_run(run):
    src, dst = os.path.join(RUNS, run), os.path.join(ARCH, run)
    os.makedirs(dst, exist_ok=True)
    steps = sorted(d for d in os.listdir(src) if os.path.isdir(os.path.join(src, d)))
    open(os.path.join(dst, "steps.txt"), "w").write("\n".join(steps) + "\n")
    for f in ("resolved.json", "error.log", "warning.log"):
        if os.path.isfile(os.path.join(src, f)):
            shutil.copy2(os.path.join(src, f), dst)
    fl = os.path.join(src, "flow.log")
    if os.path.isfile(fl):
        with open(fl, "rb") as a, gzip.open(os.path.join(dst, "flow.log.gz"), "wb") as b:
            shutil.copyfileobj(a, b)
    merged = {}
    for d in steps:
        so = os.path.join(src, d, "state_out.json")
        if os.path.isfile(so):
            try:
                merged.update(json.load(open(so)).get("metrics", {}))
            except Exception:
                pass
    json.dump({"cumulative_metrics": merged}, open(os.path.join(dst, "metrics.json"), "w"), indent=1)


dirs, files = [], []
for run in DELETE_RUNS:
    if os.path.isdir(os.path.join(RUNS, run)):
        dirs.append(("run", os.path.join(RUNS, run)))
for s in CRASHED_STEPS:
    if os.path.isdir(os.path.join(RUNS, s)):
        dirs.append(("crashed step", os.path.join(RUNS, s)))
for sc in glob.glob(os.path.join(RUNS, "*", "*-yosys-eqy", "scratch")):
    run = sc.split(os.sep)[-3]
    if run not in DELETE_RUNS:
        dirs.append(("eqy scratch", sc))
EQ = os.path.join(R, r"asic\equiv")
for p in glob.glob(os.path.join(EQ, "**", "*.il"), recursive=True):
    if os.path.getsize(p) > MB:
        files.append(p)
for p in glob.glob(os.path.join(EQ, r"lec\synth_replay\*")):
    if os.path.basename(p) in ("soc_asic_top.nl.v", "soc_asic_top.nl.v.json", "primitive_techmap.dot", "hierarchy.dot"):
        files.append(p)
files += glob.glob(os.path.join(EQ, r"lec\pairsB_*.json"))
PX = os.path.join(R, r"asic\pd_exp")
for n in ("soc_asic_top.odb", "soc_asic_top.def", "soc_asic_top.nl.v", "soc_asic_top.pnl.v"):
    files += glob.glob(os.path.join(PX, r"ant_drt", n))
files += glob.glob(os.path.join(PX, r"rc_corr\after_grt.guide"))
files = sorted(set(f for f in files if os.path.isfile(f)))

tot = 0
for k, p in dirs:
    s = size(p); tot += s
    print("%9.1f MB  %-13s %s" % (s / MB, k, os.path.relpath(p, R)))
for p in files:
    s = os.path.getsize(p); tot += s
    print("%9.1f MB  %-13s %s" % (s / MB, "file", os.path.relpath(p, R)))
print("%d dirs + %d files, %.1f GB%s" % (len(dirs), len(files), tot / (1 << 30), "" if DO else "  (dry run)"))
if not DO:
    sys.exit(0)

lines = ["# cleanup_20260928 (FLOW_JOURNAL Incident 92)", "# directories (runs archived in results/pd_run_archive/<run>/):"]
for k, p in dirs:
    if k == "run":
        archive_run(os.path.basename(p))
    elif k == "crashed step":
        d = os.path.join(ARCH, "final3_B_crashed_steps", os.path.basename(p))
        os.makedirs(d, exist_ok=True)
        for f in os.listdir(p):
            if f.endswith((".log", ".json", "COMMANDS")) or f == "COMMANDS":
                shutil.copy2(os.path.join(p, f), d)
    lines.append("%s  %d  %s" % (k, size(p), os.path.relpath(p, R)))
lines.append("# files: sha256  bytes  path (regenerable)")
for p in files:
    lines.append("%s  %d  %s" % (sha(p), os.path.getsize(p), os.path.relpath(p, R)))
open(MANIFEST, "w", newline="\n").write("\n".join(lines) + "\n")
for k, p in dirs:
    shutil.rmtree(p)
for p in files:
    os.remove(p)
print("deleted; manifest %s" % os.path.relpath(MANIFEST, R))
