#!/usr/bin/env python3
"""Workspace cleanup after the final PD + equivalence work (user rule 4, PD_metrics.pdf;
FLOW_JOURNAL Incidents 86-87).

    python scripts/cleanup_20260927.py            # dry run: list + sizes
    python scripts/cleanup_20260927.py --do       # delete, manifest in results/

Deleted, with an evidence archive written first for every whole run
(results/pd_run_archive/<run>/: resolved.json, last metrics, error/warning logs, gzipped
flow.log, step list):
  * superseded PD runs of the final RTL: r10A..r10E (density/knob samples of the R10 netlist,
    replaced by the R12b final), r12b_d38 (density sample, not selected);
  * r12b_d42 is trimmed, not deleted: it is the first run of config_FINAL.json and is
    bit-identical to final_A / final_B (a third execution) - logs, reports and metrics stay;
  * scratch of the failed EQY steps: final_A/73 (no splitnets, Incident 84) and final_B/75..79
    (the stock EQY dying after combine, Incidents 85-86) - their logs stay;
  * asic/eqy_standalone/fh1 (plugin-path failure, Incident 86) and the bulky intermediate
    files of fh2 (gold/gate/combined .il, .ids, partitions/); fh2's logs, status files, the
    diagnostic make log and the pdr_dbg traces stay;
  * regenerable intermediates of the proofs: asic/equiv/fsm_recode/gold_fsm.il,
    asic/equiv/sec/{gold,gate}_{pre,cut}*.il and pass2/*.il (hashes are in FLOW_JOURNAL;
    the scripts rebuild them bit-identically, which pass 2 showed). The proof objects
    (miter*.aig), all logs, scripts and the negative-control RTL copies stay.
KEEP untouched: final_A, final_B (apart from the failed EQY scratch above), every markdown
report and log, the double-executed canonical CSVs, the 1 KiB post-route baseline
(asic/soc_dm_control/runs/sync_final) and the Magic namespace collision evidence.
"""
import gzip
import json
import os
import re
import shutil
import sys

DO = "--do" in sys.argv
R = r"E:\Projects\RISCV-research"
RUNS = os.path.join(R, r"asic\soc_dm_4kb\runs")
ARCH = os.path.join(R, r"results\pd_run_archive")
MANIFEST = os.path.join(R, r"results\cleanup_20260927_deleted.txt")

DELETE_RUNS = ["r10A", "r10B", "r10C", "r10D", "r10E", "r12b_d38"]
TRIM_RUNS = ["r12b_d42"]
BULK = re.compile(r"\.(odb|def|gds|mag|spef|sdf|spice|ext|lib|vcd|il|lef|gz|v|sv|xml|ids|guide|dot|blif)$", re.I)

plan = []


def size(p):
    if os.path.isfile(p):
        return os.path.getsize(p)
    t = 0
    for d, _, fs in os.walk(p):
        for f in fs:
            try:
                t += os.path.getsize(os.path.join(d, f))
            except OSError:
                pass
    return t


def add(kind, p):
    if os.path.exists(p):
        plan.append((kind, p, size(p)))


def archive_run(run):
    src = os.path.join(RUNS, run)
    dst = os.path.join(ARCH, run)
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
    for d in reversed(steps):
        so = os.path.join(src, d, "state_out.json")
        if os.path.isfile(so):
            try:
                m = json.load(open(so)).get("metrics", {})
                json.dump({"last_step": d, "metrics": m}, open(os.path.join(dst, "last_metrics.json"), "w"), indent=1)
            except Exception as e:
                open(os.path.join(dst, "last_metrics.json"), "w").write('{"error": "%s"}' % e)
            break


# 1. superseded runs (archived first) and the trimmed third execution
for run in DELETE_RUNS:
    add("run", os.path.join(RUNS, run))
for run in TRIM_RUNS:
    for d, _, fs in os.walk(os.path.join(RUNS, run)):
        for f in fs:
            if BULK.search(f):
                add("trim", os.path.join(d, f))

# 2. scratch of the failed EQY steps (logs next to scratch/ stay)
add("dir", os.path.join(RUNS, r"final_A\73-yosys-eqy\scratch"))
for s in range(75, 80):
    add("dir", os.path.join(RUNS, r"final_B\%d-yosys-eqy\scratch" % s))

# 3. standalone EQY attempts
E = os.path.join(R, r"asic\eqy_standalone")
add("dir", os.path.join(E, "fh1"))
F2 = os.path.join(E, "fh2")
for f in ("gold.il", "gate.il", "gate_recoded.il", "combined.il", "gold.ids", "gate_recoded.ids"):
    add("file", os.path.join(F2, f))
add("dir", os.path.join(F2, "partitions"))
add("dir", os.path.join(F2, "fragments"))
add("dir", os.path.join(F2, "modules"))

# 4. regenerable proof intermediates (hashes recorded in FLOW_JOURNAL Incident 86)
add("file", os.path.join(R, r"asic\equiv\fsm_recode\gold_fsm.il"))
S = os.path.join(R, r"asic\equiv\sec")
KEEP_SEC = "--keep-sec" in sys.argv     # the SEC analysis may still rebuild its miter from these
for f in ([] if KEEP_SEC else os.listdir(S)):
    if f.endswith(".il"):
        add("file", os.path.join(S, f))
if not KEEP_SEC and os.path.isdir(os.path.join(S, "pass2")):
    for f in os.listdir(os.path.join(S, "pass2")):
        if f.endswith(".il"):
            add("file", os.path.join(S, "pass2", f))

PROTECT = ("soc_dm_control", "openlane-local", "evidence", "magicsafe", "PD_incident_report",
           "prove_magicsafe", "strip_macro_annotation", "list_gds_cells", "RISCV-AHB-APB-UART",
           "miter", ".aig", ".log")
plan = [x for x in plan if not any(k in os.path.basename(x[1]) or k in x[1].split(os.sep)[-2:-1]
                                   for k in PROTECT[:9]) and not x[1].endswith((".aig", ".log"))]
tot = sum(b for _, _, b in plan)
by = {}
for k, _, b in plan:
    by[k] = by.get(k, 0) + b
print("planned: %d items, %.1f GB  %s" % (len(plan), tot / 2**30, {k: "%.1f GB" % (v / 2**30) for k, v in by.items()}))
for k, p, b in plan:
    if k in ("run", "dir") or b > 100 * 2**20:
        print("  %-5s %9.1f MB  %s" % (k, b / 2**20, p))
if not DO:
    print("(dry run)")
    sys.exit(0)

os.makedirs(ARCH, exist_ok=True)
with open(MANIFEST, "a", newline="\n") as mf:
    mf.write("# cleanup 2026-09-27 (user rule 4, PD_metrics.pdf; FLOW_JOURNAL Incident 87): <kind>\\t<bytes>\\t<path>\n")
    for k, p, b in plan:
        try:
            if k == "run":
                archive_run(os.path.basename(p))
                shutil.rmtree(p)
            elif k == "dir":
                shutil.rmtree(p)
            else:
                os.remove(p)
            mf.write("%s\t%d\t%s\n" % (k, b, p))
        except Exception as e:
            mf.write("FAILED\t%s\t%s\t%s\n" % (k, p, e))
print("done; manifest", MANIFEST)
