#!/usr/bin/env python3
"""Per-module logic-cell breakdown of the Cyclone IV E fits (review item A1).

Reads the "Fitter Resource Utilization by Entity" table of each point's archived fit report
(results/fpga_points/<tag>/<point>/s<seed>/point_<point>.fit.rpt), checks that pass 1 and pass 2 agree on every
row, and writes one table per point plus a comparison table.

    python scripts/le_breakdown.py r16 dm_4kb,sa2_4kb,vc4_4kb,sa2_4kb_fast,vc4_4kb_fast,dse_4kb,sa4_4kb
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG = sys.argv[1] if len(sys.argv) > 1 else "r16"
POINTS = (sys.argv[2] if len(sys.argv) > 2 else "dm_4kb,sa2_4kb,vc4_4kb").split(",")
SEED = "s2"

# Reported groups: (label, entity path relative to soc_top, how), in table order. "own" = the node's own logic only.
GROUPS = [
    ("CPU core, total", "riscv_core_native:u_core", "total"),
    ("  register file (32 x 32; flip-flops in R16, M9K from 6c4ccffd)", "riscv_core_native:u_core|riscv_core:u_pipeline|datapath:datapath|regfile:regfile", "total"),
    ("  branch history table (256 x 2; flip-flops in R16, M9K + valid bits from 6c4ccffd)", "riscv_core_native:u_core|riscv_core:u_pipeline|datapath:datapath|bht_2bit:g_bp_on.u_bht", "total"),
    ("  ALU incl. multiplier", "riscv_core_native:u_core|riscv_core:u_pipeline|datapath:datapath|alu:alu", "total"),
    ("  datapath (pipeline registers, forwarding, CSRs, other)", "riscv_core_native:u_core|riscv_core:u_pipeline|datapath:datapath", "own"),
    ("  control, branch, hazard, extend, wrapper", None, "core_rest"),
    ("I-cache", "icache:u_icache", "total"),
    ("D-cache (incl. victim buffer)", "dcache:u_dcache", "total"),
    ("cache AXI master", "cache_axi_master:u_cache_axi_master", "total"),
    ("observability, total", "performance_observability:u_observability", "total"),
    ("  APB system monitor (snapshot / APB view)", "performance_observability:u_observability|apb_performance_monitor:u_sysmon", "total"),
    ("  hardware performance counters", "performance_observability:u_observability|perf_counters:u_perf_counters", "total"),
    ("main RAM controller (AXI, 16 KiB in M9K)", "axi_ram_32:u_axi_ram", "total"),
    ("buses: AXI-Lite master, AXI-Lite to APB, address decoders", None, "bus"),
    ("UART", "uart_apb:u_uart", "total"),
    ("timer", "apb_timer:u_timer", "total"),
    ("board I/O: display registers, LCD, 7-segment decoders", None, "board"),
    ("SoC glue (soc_top own logic)", "", "own"),
]


def parse(path):
    """{full path relative to de2_115_top: (lc_total, lc_own, regs_total, mem_bits, m9k, dsp)}"""
    txt = open(path, errors="replace").read()
    i = txt.index("; Fitter Resource Utilization by Entity")
    rows, stack = {}, []
    for ln in txt[i:].splitlines()[4:]:
        if ln.startswith("+"):
            break
        f = ln.split(";")
        if len(f) < 10:
            continue
        m = re.match(r"^( *)\|([^|]*?)\|?\s*$", f[1])      # the top row has no closing "|"
        if not m:
            continue
        depth = len(m.group(1)) // 3
        stack = stack[:depth] + [m.group(2)]
        lc = re.match(r"\s*(\d+) \((\d+)\)", f[2])
        reg = re.match(r"\s*(\d+) \((\d+)\)", f[3])
        rows["|".join(stack)] = (int(lc.group(1)), int(lc.group(2)), int(reg.group(1)), int(f[5]), int(f[6]), int(f[7]))
    return rows


def groups(rows):
    soc = [k for k in rows if k.endswith("soc_top:u_soc") and k.count("|") == 1][0]
    get = lambda rel: rows.get(soc + ("|" + rel if rel else ""))
    kids = {k: v for k, v in rows.items() if k.startswith(soc + "|") and k.count("|") == 2}
    out = {}
    for label, rel, how in GROUPS:
        if how == "total":
            v = get(rel)
            out[label] = (v[0], v[2], v[3], v[4], v[5]) if v else (0, 0, 0, 0, 0)
        elif how == "own":
            v = get(rel)
            out[label] = (v[1], 0, 0, 0, 0) if v else (0, 0, 0, 0, 0)
        elif how == "core_rest":
            core = get("riscv_core_native:u_core")
            parts = [out[l][0] for l in out if l.startswith("  ") and l in
                     [g[0] for g in GROUPS[1:5]]]
            out[label] = (core[0] - sum(parts), 0, 0, 0, 0)
        elif how == "bus":
            s = sum(v[0] for k, v in kids.items() if re.search(r"native_axi_lite_master|axi_lite_to_apb|soc_address_decoder", k))
            out[label] = (s, 0, 0, 0, 0)
        elif how == "board":
            s = sum(v[0] for k, v in kids.items() if re.search(r"apb_display_regs|lcd_1602_hex|hex7seg_decoder", k))
            out[label] = (s, 0, 0, 0, 0)
    top = rows[[k for k in rows if k.count("|") == 0][0]]
    covered = sum(v[0] for l, v in out.items() if not l.startswith("  "))
    out["board top own logic"] = (top[1], 0, 0, 0, 0)
    out["TOTAL (fit)"] = (top[0], top[2], top[3], top[4], top[5])
    out["check: groups sum - total"] = (covered + top[1] - top[0], 0, 0, 0, 0)
    return out


base = ROOT / "results" / "fpga_points"
tables, mismatch = {}, []
for pt in POINTS:
    r = []
    for p in (1, 2):
        f = base / ("%s_p%d" % (TAG, p)) / pt / SEED / ("point_%s.fit.rpt" % pt)
        r.append(parse(f))
    if r[0] != r[1]:
        diff = [k for k in set(r[0]) | set(r[1]) if r[0].get(k) != r[1].get(k)]
        mismatch.append((pt, len(diff)))
    tables[pt] = groups(r[0])
labels = [g[0] for g in GROUPS] + ["board top own logic", "TOTAL (fit)", "check: groups sum - total"]
md = ["| module | " + " | ".join(POINTS) + " |", "|---|" + "---:|" * len(POINTS)]
for l in labels:
    md.append("| %s | %s |" % (l.replace("  ", "- "), " | ".join(str(tables[p][l][0]) for p in POINTS)))
md.append("")
md.append("Registers / memory bits / M9K / DSP of the main blocks:")
md.append("")
md.append("| module | " + " | ".join(POINTS) + " |")
md.append("|---|" + "---:|" * len(POINTS))
for l in ["CPU core, total", "I-cache", "D-cache (incl. victim buffer)", "observability, total",
          "main RAM controller (AXI, 16 KiB in M9K)", "TOTAL (fit)"]:
    md.append("| %s | %s |" % (l, " | ".join("%d reg / %d bit / %d M9K / %d DSP" % tables[p][l][1:] for p in POINTS)))
out_md = ROOT / "results" / ("a1_le_breakdown_%s.md" % TAG)
head = ("# A1: logic cells per module, Cyclone IV E (EP4CE115), RTL %s, seed 2\n\n"
        "Source: the archived fit reports results/fpga_points/%s_p1 and _p2 (\"Fitter Resource Utilization by Entity\"). "
        "Logic cells (LE) include each module's children. Pass 1 vs pass 2: %s.\n\n"
        "The groups add up to about 1 %% more than the fit total (last row): Quartus counts a logic cell that packs a LUT "
        "of one module with a register of another module in both modules.\n\n"
        % (TAG, TAG, "identical on every row of every point" if not mismatch else "DIFFERENT: %s" % mismatch))
out_md.write_text(head + "\n".join(md) + "\n", encoding="utf-8")
with open(ROOT / "results" / ("a1_le_breakdown_%s.csv" % TAG), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["module"] + POINTS)
    for l in labels:
        w.writerow([l.strip()] + [tables[p][l][0] for p in POINTS])
print(out_md.read_text(encoding="utf-8"))
