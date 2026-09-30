#!/usr/bin/env python3
"""Workspace cleanup mandated by the user on 2026-09-26 (PD_metrics.pdf, item 4).

    python scripts/cleanup_20260926b.py            # dry run: list + sizes
    python scripts/cleanup_20260926b.py --do       # delete, manifest in results/

Rules: delete failed/corrupted/superseded OpenLane runs, false or superseded
verification outputs, empty files, temporary material; for every deleted run a
small evidence archive is written first (results/pd_run_archive/<run>/:
resolved.json, last metrics, error/warning logs, gzipped flow.log, step list).
KEEP: markdown reports and logs, double-executed canonical CSVs, the 1 KiB
post-route baseline (asic/soc_dm_control/runs/sync_final), the Magic namespace
collision evidence (PD_incident_report.md B3, openlane-local, asic/evidence,
prove_magicsafe_equivalence.py, strip_macro_annotation_layers.py,
list_gds_cells.py, macros/*.magicsafe.gds), runs that are valid for the final
RTL 8b163675 (r10A..r10E, byte-identical netlist) and the running r12b_* samples.
"""
import glob
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
MANIFEST = os.path.join(R, r"results\cleanup_20260926b_deleted.txt")

KEEP_FULL = {"r10A", "r10E"}                 # signoff run + density-40 sample of the final netlist
KEEP_TRIM = {"r10B", "r10C", "r10D"}         # valid knob experiments: keep logs/reports/metrics
RUNNING = {"r12b_d38", "r12b_d42"}
BULK = re.compile(r"\.(odb|def|gds|mag|spef|sdf|spice|ext|lib|vcd|il|lef|gz|v|sv|xml|ids|guide|dot|blif)$", re.I)

plan = []   # (kind, path, bytes)


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
    last = None
    for d in reversed(steps):
        so = os.path.join(src, d, "state_out.json")
        if os.path.isfile(so):
            last = (d, so)
            break
    if last:
        try:
            m = json.load(open(last[1])).get("metrics", {})
            json.dump({"last_step": last[0], "metrics": m}, open(os.path.join(dst, "last_metrics.json"), "w"), indent=1)
        except Exception as e:
            open(os.path.join(dst, "last_metrics.json"), "w").write('{"error": "%s"}' % e)


# 1. runs
for run in sorted(os.listdir(RUNS)):
    p = os.path.join(RUNS, run)
    if not os.path.isdir(p) or run in KEEP_FULL or run in RUNNING:
        continue
    if run in KEEP_TRIM:
        for d, _, fs in os.walk(p):
            for f in fs:
                if BULK.search(f):
                    add("trim", os.path.join(d, f))
        continue
    add("run", p)
add("dir", os.path.join(RUNS, "r10A", "73-yosys-eqy", "scratch"))   # partition of the superseded EQY script

# 2. snapshots of rejected / superseded RTL
for s in ("rtl_358cb660", "rtl_r11cand", "rtl_r12"):
    add("dir", os.path.join(R, "asic", "snapshots", s))

# 3. configs whose runs are deleted (their resolved.json is archived) and rejected EQY scripts
d = os.path.join(R, r"asic\soc_dm_4kb")
for pat in ("config_S_*.json", "config_AN?.json", "config_E?.json", "config_SS?.json", "config_clk22.json",
            "config_R10p12.json", "config_R11cand.json", "config_R12_d??.json", "config_R12b_syn.json",
            "config_R10A2.json", "eqy_soc_asic_top_hide_r12_mm.eqy"):
    for f in glob.glob(os.path.join(d, pat)):
        add("file", f)

# 4. temporary probe inputs
add("file", os.path.join(R, r"asic\equiv\r12_abc\input.blif"))
add("file", os.path.join(R, r"asic\equiv\r12_abc\stdcells.genlib"))
add("file", os.path.join(R, r"asic\equiv\r12_abc\abc.script"))

# 5. superseded / flawed verification outputs (copies of anything cited live in results/archive_*)
for f in ("fpga_points_r10_p1.csv", "le_r10_p1.log", "le_r10_p1.stdout", "fpga_seed_summary_r10_p1.md",
          "fpga_points_r10f2_p1.csv", "le_r10f2_p1.log", "le_r10f2_p1.stdout", "fpga_seed_summary_r10f2_p1.md",
          "fpga_points_r12_p1.csv", "le_r12_p1.log", "le_r12_p1.stdout", "fpga_seed_summary_r12_p1.md"):
    add("file", os.path.join(R, "results", f))
add("dir", os.path.join(R, r"results\archive_b56fbd4e"))           # iteration with the checker bug
for g in ("gls_power_r7r8_358c", "gls_r8_a0c4", "gls_r8_clk215", "gls_power_r8_a0c4"):
    add("dir", os.path.join(R, "results", g))                       # old-netlist SAIF/logs; CSVs stay
add("dir", os.path.join(R, "work_glsp_r7r8_358c"))                  # regenerable Questa library

# 6. empty files in results/ and asic/ (outside running runs)
for base in (os.path.join(R, "results"), os.path.join(R, "asic")):
    for dd, _, fs in os.walk(base):
        if any(x in dd for x in RUNNING) or "openlane-local" in dd:
            continue
        for f in fs:
            fp = os.path.join(dd, f)
            try:
                if os.path.getsize(fp) == 0 and not f.startswith("."):
                    add("empty", fp)
            except OSError:
                pass

# safety: never touch these
PROTECT = ("soc_dm_control", "openlane-local", "evidence", "magicsafe", "PD_incident_report",
           "prove_magicsafe", "strip_macro_annotation", "list_gds_cells", "RISCV-AHB-APB-UART")
plan = [x for x in plan if not any(k in x[1] for k in PROTECT)]
# a trimmed/deleted path must not be inside a kept run except the r10A EQY scratch and trims
tot = sum(b for _, _, b in plan)
by = {}
for k, _, b in plan:
    by[k] = by.get(k, 0) + b
print("planned: %d items, %.1f GB  %s" % (len(plan), tot / 2**30,
      {k: "%.1f GB" % (v / 2**30) for k, v in by.items()}))
for k, p, b in plan:
    if k in ("run", "dir"):
        print("  %-5s %8.1f MB  %s" % (k, b / 2**20, p))
if not DO:
    print("(dry run)")
    sys.exit(0)

os.makedirs(ARCH, exist_ok=True)
with open(MANIFEST, "a", newline="\n") as mf:
    mf.write("# cleanup 2026-09-26b (user rule 4, PD_metrics.pdf): <kind>\\t<bytes>\\t<path>\n")
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
