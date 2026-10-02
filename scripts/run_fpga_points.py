#!/usr/bin/env python3
"""Fit the new design-space points on the Cyclone IV E.

The cycle results cover four organizations, four capacities, three victim
depths and four line sizes, but every area and timing number in the paper is
still for the original geometry. This generates a Quartus project per point and
runs map/fit/sta inside research/, so the published output_files_de2_115_*
directories are never touched.

    python scripts/run_fpga_points.py --points dm_dse,sa2_w8
    python scripts/run_fpga_points.py --list
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
LE_BUDGET = 20000

# name -> (CACHE_CONFIG, line words, lines, victim entries,
#          PERF_COUNTERS_ENABLE, what it answers)
POINTS = {
    "dm":        (0, 4, 64, 4, 1,  "frozen baseline, refit here as a control"),
    "sa2":       (1, 4, 64, 4, 1,  "frozen SA2, control"),
    "dm_vc4":    (2, 4, 64, 4, 1,  "frozen DM+VC4, control"),
    "dm_dse":    (3, 4, 64, 4, 1,  "ablation point: DM on the ten-state core"),
    "sa2_w8":    (1, 8, 32, 4, 1,  "SA2 with a 32-byte line"),
    "sa2_w16":   (1, 16, 16, 4, 1, "SA2 with a 64-byte line"),
    "dm_dse_w8": (3, 8, 32, 4, 1,  "DM-DSE with a 32-byte line"),
    "dm_vc8":    (2, 4, 64, 8, 1,  "victim buffer of eight entries"),
    # Same design as "dm" with the counter bank and the APB snapshot
    # removed. The difference between the two is what the
    # instrumentation costs on its own.
    "dm_nopc":   (0, 4, 64, 4, 0, "DM with PERF_COUNTERS_ENABLE=0"),
    # 4 KiB points. 256 lines x 4 words x 4 bytes. This is the capacity the
    # benchmark matrix measures, and on the ASIC side it is the size at which
    # each data bank becomes an exact fit for an OpenRAM 32x256 macro.
    "dm_4kb":    (0, 4, 256, 4, 1, "DM at 4 KiB"),
    "sa2_4kb":   (1, 4, 256, 4, 1, "SA2 at 4 KiB"),
    "vc4_4kb":   (2, 4, 256, 4, 1, "DM+VC4 at 4 KiB"),
    "dse_4kb":   (3, 4, 256, 4, 1, "DM-DSE at 4 KiB"),
    # R15 / review item M2: four-way set associativity (dcache/icache_nway_core) and the 8 KiB capacity.
    "sa4_4kb":   (4, 4, 256, 4, 1, "SA4 at 4 KiB"),
    "dm_8kb":    (0, 4, 512, 4, 1, "DM at 8 KiB"),
    "sa2_8kb":   (1, 4, 512, 4, 1, "SA2 at 8 KiB"),
    "vc4_8kb":   (2, 4, 512, 4, 1, "DM+VC4 at 8 KiB"),
    "dse_8kb":   (3, 4, 512, 4, 1, "DM-DSE at 8 KiB"),
    "sa4_8kb":   (4, 4, 512, 4, 1, "SA4 at 8 KiB"),
}

QSF = """set_global_assignment -name TOP_LEVEL_ENTITY de2_115_top
source quartus/soc_core_common.qsf
source quartus/de2_115/de2_115_common.qsf

# Seed 2 is pinned in the revision .qsf, not only in the sourced common file:
# a SEED arriving through `source` does not take effect.
set_global_assignment -name SEED {seed}

set_global_assignment -name PROJECT_OUTPUT_DIRECTORY output_files_{name}
set_parameter -name CACHE_CONFIG {cfg}
set_parameter -name VICTIM_ENTRIES {victim}
set_parameter -name ICACHE_LINE_COUNT {lines}
set_parameter -name DCACHE_LINE_COUNT {lines}
set_parameter -name CACHE_LINE_WORDS {words}
set_parameter -name BRANCH_PREDICT_ENABLE 1
set_parameter -name PERF_COUNTERS_ENABLE {perf}
set_parameter -name L0_ENTRIES {l0}
set_parameter -name BHT_ENTRIES 256

set_instance_assignment -name PARTITION_HIERARCHY root_partition -to | -section_id Top
set_global_assignment -name PARTITION_NETLIST_TYPE SOURCE -section_id Top
set_global_assignment -name PARTITION_FITTER_PRESERVATION_LEVEL PLACEMENT_AND_ROUTING -section_id Top
set_global_assignment -name PARTITION_COLOR 16764057 -section_id Top
"""


def tool(name: str) -> str:
    root = Path(os.environ.get("QUARTUS_ROOTDIR", r"D:\altera\quartus")) / "bin64"
    found = shutil.which(name) or (root / (name + ".exe"))
    if not (found and Path(found).is_file()):
        sys.exit("[FAIL] %s not found; set QUARTUS_ROOTDIR" % name)
    return str(found)


def run(cmd: list[str], log: Path, retries: int = 3) -> None:
    for attempt in range(1, retries + 1):
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           timeout=7200)
        log.write_bytes(((p.stdout or "") + (p.stderr or "")).encode(
            "utf-8", "replace"))
        if p.returncode == 0:
            return
        # Keep the failed attempt's log: the next attempt overwrites `log`,
        # and a crash that is retried away must still leave its evidence.
        kept = log.with_name("%s.attempt%d.failed%s" % (log.stem, attempt, log.suffix))
        shutil.copy2(log, kept)
        print("        attempt %d failed (rc=%d), log kept as %s"
              % (attempt, p.returncode, kept.name))
        time.sleep(5)
    raise RuntimeError("%s failed; see %s" % (Path(cmd[0]).name, log))


def write_project(name: str, seed: int = 2, l0: int = 8) -> str:
    cfg, words, lines, victim, perf, _ = POINTS[name]
    rev = "point_" + name
    (ROOT / (rev + ".qpf")).write_bytes(
        ('QUARTUS_VERSION = "20.1"\nPROJECT_REVISION = "%s"\n' % rev
         ).encode("utf-8"))
    (ROOT / (rev + ".qsf")).write_bytes(
        QSF.format(name=name, cfg=cfg, victim=victim, perf=perf,
                   seed=seed, l0=l0,
                   lines=lines, words=words).encode("utf-8"))
    return rev


# Everything the map, fit, sta and pow reports give for a point is recorded,
# not a hand-picked subset: a number that is not scraped cannot be compared
# between seeds, passes or configurations afterwards.
CORNERS = (("s85", "Slow 1200mV 85C"), ("s0", "Slow 1200mV 0C"),
           ("f0", "Fast 1200mV 0C"))
CHECKS = (("setup", "Setup"), ("hold", "Hold"), ("recovery", "Recovery"),
          ("removal", "Removal"), ("mpw", "Minimum Pulse Width"))

# Fitter Resource Usage Summary rows: column -> row label.
FIT_ROWS = (
    ("le", "Total logic elements"),
    ("le_comb_only", "-- Combinational with no register"),
    ("le_reg_only", "-- Register only"),
    ("le_comb_reg", "-- Combinational with a register"),
    ("lut4", "-- 4 input functions"),
    ("lut3", "-- 3 input functions"),
    ("lut2", "-- <=2 input functions"),
    ("le_normal", "-- normal mode"),
    ("le_arith", "-- arithmetic mode"),
    ("regs", "-- Dedicated logic registers"),
    ("io_regs", "-- I/O registers"),
    ("labs", "Total LABs:  partially or completely used"),
    ("pins", "I/O pins"),
    ("m9k", "M9Ks"),
    ("mem_bits", "Total block memory bits"),
    ("mem_impl_bits", "Total block memory implementation bits"),
    ("mult9", "Embedded Multiplier 9-bit elements"),
    ("plls", "PLLs"),
    ("global_clocks", "-- Global clocks"),
    ("interconnect_avg_pct", "Average interconnect usage (total/H/V)"),
    ("interconnect_peak_pct", "Peak interconnect usage (total/H/V)"),
    ("fanout_max", "Maximum fan-out"),
    ("fanout_max_nonglobal", "Highest non-global fan-out"),
    ("fanout_total", "Total fan-out"),
    ("fanout_avg", "Average fan-out"),
)

POW_SUMMARY = (
    ("pow_total_mw", "Total Thermal Power Dissipation"),
    ("pow_core_dyn_mw", "Core Dynamic Thermal Power Dissipation"),
    ("pow_core_static_mw", "Core Static Thermal Power Dissipation"),
    ("pow_io_mw", "I/O Thermal Power Dissipation"),
)
POW_BLOCKS = (
    ("pow_blk_m9k_mw", "M9K"),
    ("pow_blk_mult_mw", "Embedded multiplier block"),
    ("pow_blk_mult_out_mw", "Embedded multiplier output"),
    ("pow_blk_comb_mw", "Combinational cell"),
    ("pow_blk_clkctrl_mw", "Clock control block"),
    ("pow_blk_reg_mw", "Register cell"),
    ("pow_blk_io_mw", "I/O"),
)
# Hierarchy totals (this node plus everything below it).
POW_HIER = (
    ("pow_soc_mw", "u_soc"), ("pow_core_mw", "u_core"),
    ("pow_icache_mw", "u_icache"), ("pow_dcache_mw", "u_dcache"),
    ("pow_axi_master_mw", "u_cache_axi_master"),
    ("pow_axi_ram_mw", "u_axi_ram"), ("pow_axil2apb_mw", "u_axil2apb"),
    ("pow_observability_mw", "u_observability"),
    ("pow_perf_counters_mw", "u_perf_counters"),
    ("pow_sysmon_mw", "u_sysmon"), ("pow_uart_mw", "u_uart"),
)
POW_SUPPLIES = ("VCCINT", "VCCIO", "VCCA", "VCCD")

COLS = (["point", "seed", "l0", "cache_config", "line_bytes", "lines",
         "victim_entries", "capacity_bytes", "le", "le_margin", "comb",
         "regs", "mem_bits", "setup_slack", "fmax",
         "map_le", "map_comb", "map_regs"]
        + [k for k, _ in FIT_ROWS if k not in ("le", "regs", "mem_bits")]
        + ["fmax_%s" % c for c, _ in CORNERS if c != "f0"]
        + ["fmax_restricted_%s" % c for c, _ in CORNERS if c != "f0"]
        + ["%s_%s_%s" % (chk, c, v) for c, _ in CORNERS
           for chk, _ in CHECKS for v in ("slack", "tns")]
        + ["mc_%s_%s" % (chk, v) for chk, _ in CHECKS for v in ("slack", "tns")]
        + ["unconstrained", "clocks_constrained"]
        + [k for k, _ in POW_SUMMARY] + ["pow_confidence"]
        + [k for k, _ in POW_BLOCKS]
        + ["pow_clk_dyn_mw", "pow_noclk_dyn_mw"]
        + ["cur_%s_ma" % s.lower() for s in POW_SUPPLIES]
        + [k for k, _ in POW_HIER]
        + ["seconds"])


def _num(s: str):
    s = s.strip().replace(",", "")
    m = re.match(r"-?[\d.]+", s)
    return (float(m.group(0)) if "." in m.group(0) else int(m.group(0))) \
        if m else None


def _read(path: Path) -> str:
    # Quartus writes CRLF reports; the panel patterns below match on LF.
    return path.read_bytes().decode("utf-8", "replace").replace("\r\n", "\n")


def _panel(txt: str, title: str) -> list[list[str]]:
    """Data rows of the report panel whose title line is `title`."""
    m = re.search(r"^; %s\s*;\s*\n\+[-+]+\n;[^\n]*\n\+[-+]+\n((?:;[^\n]*\n)+)"
                  % re.escape(title), txt, re.M)
    if not m:
        return []
    return [[c.strip() for c in r.strip().strip(";").split(";")]
            for r in m.group(1).splitlines()]


def _section(txt: str, title: str) -> str:
    i = txt.find("; %s" % title)
    if i < 0:
        return ""
    j = txt.find("\n\n\n", i)
    return txt[i:j if j > 0 else len(txt)]


def _row_value(sec: str, label: str):
    m = re.search(r"^;\s*%s\s*;\s*([^;\n]*);" % re.escape(label), sec, re.M)
    return _num(m.group(1)) if m else None


def scrape_fit(row: dict, dest: Path, rev: str) -> None:
    rpt = dest / ("%s.map.rpt" % rev)
    if rpt.exists():
        sec = _section(_read(rpt),
                       "Analysis & Synthesis Summary")
        row["map_le"] = _row_value(sec, "Total logic elements")
        row["map_comb"] = _row_value(sec, "Total combinational functions")
        row["map_regs"] = _row_value(sec, "Dedicated logic registers")
    rpt = dest / ("%s.fit.rpt" % rev)
    if not rpt.exists():
        return
    txt = _read(rpt)
    row["comb"] = _row_value(_section(txt, "Fitter Summary"),
                             "Total combinational functions")
    sec = _section(txt, "Fitter Resource Usage Summary")
    for key, label in FIT_ROWS:
        row[key] = _row_value(sec, label)
    if row.get("le"):
        row["le_margin"] = LE_BUDGET - row["le"]


def scrape_sta(row: dict, dest: Path, rev: str) -> None:
    rpt = dest / ("%s.sta.rpt" % rev)
    if not rpt.exists():
        return
    txt = _read(rpt)
    for c, title in CORNERS:
        for chk, name in CHECKS:
            rows = _panel(txt, "%s Model %s Summary" % (title, name))
            sl = [_num(r[1]) for r in rows if len(r) > 2]
            tn = [_num(r[2]) for r in rows if len(r) > 2]
            row["%s_%s_slack" % (chk, c)] = min(sl) if sl else None
            row["%s_%s_tns" % (chk, c)] = sum(tn) if tn else None
        if c != "f0":
            rows = _panel(txt, "%s Model Fmax Summary" % title)
            fm = [_num(r[0]) for r in rows if "MHz" in r[0]]
            rf = [_num(r[1]) for r in rows if len(r) > 1 and "MHz" in r[1]]
            row["fmax_%s" % c] = min(fm) if fm else None
            row["fmax_restricted_%s" % c] = min(rf) if rf else None
    for r in _panel(txt, "Multicorner Timing Analysis Summary"):
        if r[0] in ("Worst-case Slack", "Design-wide TNS"):
            v = "slack" if r[0].startswith("Worst") else "tns"
            for (chk, _), cell in zip(CHECKS, r[1:]):
                row["mc_%s_%s" % (chk, v)] = _num(cell)
    un = _panel(txt, "Unconstrained Paths Summary")
    row["unconstrained"] = sum((_num(r[1]) or 0) + (_num(r[2]) or 0)
                               for r in un if len(r) > 2) if un else None
    cs = _panel(txt, "Clock Status Summary")
    row["clocks_constrained"] = "%d/%d" % (
        sum(1 for r in cs if r[-1] == "Constrained"), len(cs))
    # The two columns the earlier CSVs carried, kept under their old names.
    row["setup_slack"] = row.get("setup_s85_slack")
    row["fmax"] = row.get("fmax_restricted_s85")


def scrape_pow(row: dict, dest: Path, rev: str) -> None:
    rpt = dest / ("%s.pow.rpt" % rev)
    if not rpt.exists():
        return
    txt = _read(rpt)
    sec = _section(txt, "Power Analyzer Summary")
    for key, label in POW_SUMMARY:
        row[key] = _row_value(sec, label)
    m = re.search(r"^; Power Estimation Confidence\s*;\s*([^;\n]*?)\s*;",
                  sec, re.M)
    row["pow_confidence"] = m.group(1) if m else None
    sec = _section(txt, "Thermal Power Dissipation by Block Type")
    for key, label in POW_BLOCKS:
        row[key] = _row_value(sec, label)
    sec = _section(txt, "Core Dynamic Thermal Power Dissipation by Clock Domain")
    for r in re.findall(r"^;\s*([^;\n]+?)\s*;\s*[\d.]+\s*;\s*([\d.]+)\s*;",
                        sec, re.M):
        if r[0] == "clk":
            row["pow_clk_dyn_mw"] = float(r[1])
        elif r[0] == "No clock domain":
            row["pow_noclk_dyn_mw"] = float(r[1])
    sec = _section(txt, "Current Drawn from Voltage Supplies Summary")
    for s in POW_SUPPLIES:
        row["cur_%s_ma" % s.lower()] = _row_value(sec, s)
    sec = _section(txt, "Thermal Power Dissipation by Hierarchy")
    for key, inst in POW_HIER:
        m = re.search(r"^;\s*\|\S+:%s\s*;\s*([\d.]+) mW" % re.escape(inst),
                      sec, re.M)
        row[key] = float(m.group(1)) if m else None


def scrape(name: str, rev: str, dest: Path) -> dict:
    cfg, words, lines, victim, perf, _ = POINTS[name]
    out = ROOT / ("output_files_" + name)
    row = {"point": name, "cache_config": cfg, "line_bytes": words * 4,
           "lines": lines, "victim_entries": victim,
           "capacity_bytes": lines * words * 4}
    for suffix in ("fit.rpt", "sta.rpt", "map.rpt", "pow.rpt",
                   "fit.summary", "map.summary", "sta.summary"):
        src = out / ("%s.%s" % (rev, suffix))
        if src.exists():
            shutil.copy2(src, dest / src.name)
    scrape_fit(row, dest, rev)
    scrape_sta(row, dest, rev)
    scrape_pow(row, dest, rev)
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", default="dm_dse")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--out", default="results/fpga_points.csv")
    # Placement seed. The project pins 2 per revision; a sweep needs the
    # others to say whether a difference is real or a draw.
    ap.add_argument("--seed", type=int, default=2)
    # Depth of the I-cache L0 hot buffer: eight entries is 1,024 flops for
    # 128 bytes, and the D-cache does the same job with two.
    ap.add_argument("--l0", type=int, default=8)
    # Every fit is followed by the assembler and the Power Analyzer, so each
    # seed has its own power numbers. Before this, power was taken once per
    # point after the whole seed loop, i.e. on whichever seed ran last.
    ap.add_argument("--no-power", action="store_true")
    # Reports are archived under results/fpga_points/<tag>/<point>/s<seed>/,
    # so a second pass or another seed never overwrites the first.
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    if args.list:
        for n, (cfg, w, l, v, _perf, why) in POINTS.items():
            print("  %-11s cfg=%d  %2dB line x %3d lines = %5dB  vc=%d   %s"
                  % (n, cfg, w * 4, l, l * w * 4, v, why))
        return 0

    names = args.points.split(",")

    # Cooperative abort for a sweep loop that has to be restarted: every
    # invocation that starts while this file exists returns at once, so the
    # loop runs out without a fit being killed half way.
    if (ROOT / "results" / ".abort_fpga_sweep").exists():
        print("[ABORT] results/.abort_fpga_sweep present; nothing run")
        return 3

    # Two Quartus fits share point_*.qsf and results/fpga_points/<name>/, so
    # running them concurrently corrupts both. That has happened once already:
    # an overlapping sweep produced a fit failure that was misread as the
    # project's known ~8 % random crash. The rule was in the project notes; it
    # is a check now.
    try:
        busy = subprocess.run(["tasklist"], capture_output=True, text=True,
                              timeout=30).stdout.lower().count("quartus_")
    except Exception:
        busy = 0
    if busy:
        sys.exit("[FAIL] %d quartus process(es) already running; fits must be "
                 "sequential. Wait for them, or pass --allow-concurrent if you "
                 "are certain they touch different revisions." % busy)
    for n in names:
        if n not in POINTS:
            sys.exit("[FAIL] unknown point '%s'; try --list" % n)

    bins = {s: tool("quartus_" + s) for s in ("map", "fit", "sta", "asm", "pow")}
    rows, failed = [], []
    for name in names:
        rev = write_project(name, args.seed, args.l0)
        dest = ROOT / "results" / "fpga_points"
        if args.tag:
            dest = dest / args.tag
        dest = dest / name / ("s%d" % args.seed
                              + ("" if args.l0 == 8 else "_l0-%d" % args.l0))
        dest.mkdir(parents=True, exist_ok=True)
        # A report left over from an earlier fit must never be scraped as
        # this one's, so the revision's reports are removed before map.
        for old in (ROOT / ("output_files_" + name)).glob(rev + ".*"):
            if old.suffix in (".rpt", ".summary"):
                old.unlink()
        shutil.copy2(ROOT / (rev + ".qsf"), dest / (rev + ".qsf"))
        cfg, words, lines, victim, perf, why = POINTS[name]
        print("[RUN] %-11s cfg=%d %dB line x %d lines vc=%d seed=%d  (%s)"
              % (name, cfg, words * 4, lines, victim, args.seed, why))
        t0 = time.time()
        try:
            run([bins["map"], rev, "--read_settings_files=on",
                 "--write_settings_files=off", "-c", rev], dest / "map.log")
            run([bins["fit"], rev, "--read_settings_files=off",
                 "--write_settings_files=off", "-c", rev], dest / "fit.log")
            run([bins["sta"], rev, "-c", rev], dest / "sta.log")
            if not args.no_power:
                run([bins["asm"], rev, "-c", rev], dest / "asm.log")
                run([bins["pow"], rev, "-c", rev], dest / "pow.log")
        except RuntimeError as exc:
            print("      [FAIL] %s" % exc)
            failed.append(name)
            continue
        row = scrape(name, rev, dest)
        row["seed"] = args.seed
        row["l0"] = args.l0
        if args.l0 != 8:
            row["point"] = "%s@l0-%d" % (row["point"], args.l0)
        if args.seed != 2:
            # Keep the seed-2 row as the canonical one and let other seeds
            # accumulate beside it rather than replacing it.
            row["point"] = "%s@s%d" % (row["point"], args.seed)
        row["seconds"] = round(time.time() - t0)
        # A field that should have been scraped and was not is a failure,
        # not a blank cell nobody notices.
        want = [c for c in COLS if c not in ("seconds",)]
        if args.no_power:
            want = [c for c in want if not c.startswith(("pow_", "cur_"))]
        if not perf:
            want = [c for c in want if c not in (
                "pow_observability_mw", "pow_perf_counters_mw", "pow_sysmon_mw")]
        missing = [c for c in want if row.get(c) is None]
        if missing:
            print("      [FAIL] fields not found in the reports: %s" % missing)
            failed.append(name)
        rows.append(row)
        over = "" if (row.get("le_margin") or 0) >= 0 else "  OVER BUDGET"
        print("      LE=%s (margin %s)  regs=%s  M9K=%s  mult9=%s  "
              "setup s85/s0/f0=%s/%s/%s ns  hold=%s/%s/%s ns  "
              "Fmax s85/s0=%s/%s MHz  power=%s mW (dyn %s, static %s, io %s)  "
              "[%ss]%s"
              % (row.get("le"), row.get("le_margin"), row.get("regs"),
                 row.get("m9k"), row.get("mult9"),
                 row.get("setup_s85_slack"), row.get("setup_s0_slack"),
                 row.get("setup_f0_slack"), row.get("hold_s85_slack"),
                 row.get("hold_s0_slack"), row.get("hold_f0_slack"),
                 row.get("fmax_restricted_s85"), row.get("fmax_restricted_s0"),
                 row.get("pow_total_mw"), row.get("pow_core_dyn_mw"),
                 row.get("pow_core_static_mw"), row.get("pow_io_mw"),
                 row["seconds"], over))

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = COLS
    existing = []
    if out.is_file():
        existing = [r for r in csv.DictReader(out.open(encoding="utf-8"))
                    if r["point"] not in {r2["point"] for r2 in rows}]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(existing)
        w.writerows(rows)

    print("")
    print("[%s] %d fit(s) -> %s"
          % ("PASS" if not failed else "PARTIAL", len(rows), out))
    for n in failed:
        print("   failed: %s" % n)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
