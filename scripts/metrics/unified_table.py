"""Unified metric table (rulebook K / directive 2026-09-30 "Embench metrics expansion").

One row per cache configuration (4 KiB caches, branch predictor on, FPGA view unless stated), built only from
result files on disk -- nothing typed in -- and every source named in the output:

  workload (12 upstream Embench-IoT kernels, results/r15_4kb_p1.csv = R14, verified x2 by the R15 chain)
    CPI            sum(mcycle) / sum(minstret) over the 12 kernels
    I$ hit %       sum(i_hit_ev) / sum(i_access)
    D$ read hit %  sum(d_rd_hit) / sum(d_read)
    BP mispredict % sum(mispredict) / sum(predictions)
  Embench-IoT score (full original iteration counts, results/upfull_r14_4kb_p1.csv; reference = baseline
    speed.json of embench-iot 09c2ed8c, ms at 1 MHz -> reference cycles = ms x 1000)
    speed/MHz GM, GSD   per kernel ref_cycles / mcycle; geometric mean and geometric standard deviation
  code size (results/code_size_r14.csv; reference size.json .text) -- the same binaries for every configuration
    size GM, GSD        per kernel kernel-text / reference text (benchmark sources only: harness, support
                        code and libgcc are excluded, as Embench excludes its own support code)
  interrupts (results/irq_metrics.csv, steady state = median of the samples)
    IRQ entry           timer line -> first handler instruction retired, minimal handler, register work
    IRQ total           whole interruption with the minimal handler
    ctx switch          whole interruption with the full context switch (31 GPRs + mepc saved and restored)
  FPGA (results/fpga_points_r14_p1.csv, seed 2): LE, Fmax Slow 85C
  MCYCLE match: FPGA view vs ASIC view (results/upstream_asic_r15_p1.csv, results/dse_asic_view_p1.csv)
    -- the documented difference: the RAM macro wrapper ignores the MISS_PENALTY hooks; GLS and board columns
    are filled when those runs exist (board: none, no board available).
  ASIC area / timing / GLS->SAIF power: pending the R14 / SA2 / DM_VC4 full flows (FLOW_JOURNAL Incident 95-97).

    python scripts/metrics/unified_table.py  -> results/unified_metrics.csv and results/unified_metrics.md
"""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "results"
BASE = ROOT / "scripts" / "metrics" / "embench_baseline_09c2ed8c"
CONFIGS = ["DM", "SA2", "DM_VC4", "DM_DSE"]
FPGA_POINT = {"DM": "dm_4kb", "SA2": "sa2_4kb", "DM_VC4": "vc4_4kb", "DM_DSE": "dse_4kb"}


def rows(path):
    p = R / path
    return list(csv.DictReader(open(p, encoding="utf-8"))) if p.is_file() else []


def gm_gsd(vals):
    logs = [math.log(v) for v in vals]
    m = sum(logs) / len(logs)
    sd = math.sqrt(sum((x - m) ** 2 for x in logs) / len(logs))   # population, as Embench reports
    return math.exp(m), math.exp(sd)


def ksum(rs, f):
    return sum(int(r[f]) for r in rs)


def main():
    speed = json.load(open(BASE / "speed.json"))
    size = json.load(open(BASE / "size.json"))
    std = [r for r in rows("r15_4kb_p1.csv")]
    full = rows("upfull_r14_4kb_p1.csv")
    cs = {r["image"]: r for r in rows("code_size_r14.csv")}
    irq = {(r["config"], int(r["phase"])): r for r in rows("irq_metrics.csv")}
    fpga = {r["point"]: r for r in rows("fpga_points_r14_p1.csv")}
    asic_dm = {r["kernel"]: r for r in rows("upstream_asic_r15_p1.csv")}
    asic_dse = {(r["kernel"], r["config"]): r for r in rows("dse_asic_view_p1.csv")}
    # CoreMark: ITERATIONS = 1 (sw/coremark/core_portme.h) -- a cycle count, explicitly NOT an official score
    cmk = {r["config"]: r for r in rows("coremark_r15_4kb_p1.csv")}

    # code size: identical binaries for every configuration
    ratios = []
    for img, r in cs.items():
        if not img.startswith("up_"):
            continue
        k = img[3:]
        ratios.append(int(r["text_kernel"]) / size[k]["text"])
    size_gm, size_gsd = gm_gsd(ratios) if ratios else (float("nan"), float("nan"))

    out = []
    for cfg in CONFIGS:
        s = [r for r in std if r["config"] == cfg]
        f = [r for r in full if r["config"] == cfg]
        row = {"config": cfg, "kernels": len(s)}
        if s:
            row["cpi"] = ksum(s, "mcycle") / ksum(s, "minstret")
            row["icache_hit_pct"] = 100.0 * ksum(s, "i_hit_ev") / ksum(s, "i_access")
            row["dcache_read_hit_pct"] = 100.0 * ksum(s, "d_rd_hit") / ksum(s, "d_read")
            row["bp_mispredict_pct"] = 100.0 * ksum(s, "mispredict") / ksum(s, "predictions")
        if f:
            sc = [speed[r["kernel"].replace("upfull_", "")] * 1000.0 / int(r["mcycle"]) for r in f]
            row["embench_speed_per_mhz_gm"], row["embench_speed_gsd"] = gm_gsd(sc)
            row["embench_kernels"] = len(sc)
        row["size_gm"], row["size_gsd"] = size_gm, size_gsd
        if cfg in cmk:
            row["coremark_1iter_mcycle"] = int(cmk[cfg]["mcycle"])
        for name, ph, fld in (("irq_entry", 1, "entry_median"), ("irq_total", 1, "total_median"),
                              ("ctx_switch_total", 2, "total_median"), ("irq_entry_cold", 1, "entry_first")):
            if (cfg, ph) in irq:
                row[name] = float(irq[(cfg, ph)][fld])
        p = fpga.get(FPGA_POINT[cfg])
        if p:
            row["fpga_le"], row["fpga_fmax_mhz"] = int(p["le"]), float(p["fmax"])
        # MCYCLE: FPGA view vs ASIC view (kernels whose mcycle is identical / total)
        av = [(r, asic_dm.get(r["kernel"])) if cfg == "DM" else (r, asic_dse.get((r["kernel"], cfg))) for r in s]
        av = [(a, b) for a, b in av if b is not None]
        if av:
            row["asic_view_mcycle_sum_pct_vs_fpga"] = 100.0 * (sum(int(b["mcycle"]) for _, b in av)
                                                                / sum(int(a["mcycle"]) for a, _ in av) - 1.0)
            row["asic_view_kernels"] = len(av)
        # GLS / activity-based power of the signed-off final netlist (FLOW_JOURNAL Incidents 95-96)
        tag = {"DM": "r14F_A", "SA2": "sa2F_A", "DM_VC4": "vc4F_A"}.get(cfg)
        g = rows("gls_power_%s.csv" % tag) if tag else []
        p = rows("gls_power_%s_power.csv" % tag) if tag else []
        if g:
            ok = sum(1 for r in g if r["match"] == "YES")
            row["gls_mcycle_match"] = "%d/%d kernels = ASIC-view RTL (%s)" % (ok, len(g), tag)
        else:
            row["gls_mcycle_match"] = "pending (after PD)" if tag else "N/A (no ASIC build)"
        row["board_mcycle_match"] = "N/A (no board)"
        if p:
            tot = [float(r["total_mw"]) for r in p]
            epi = [float(r["epi_pj"]) for r in p]
            row["asic_power_saif"] = "%.1f-%.1f mW (mean %.1f), nom_tt, %d kernels" % (min(tot), max(tot), sum(tot) / len(tot), len(p))
            row["asic_epi_pj"] = "%.0f-%.0f pJ (GM %.0f)" % (min(epi), max(epi), gm_gsd(epi)[0])
        else:
            row["asic_power_saif"] = "pending (after PD + GLS)" if tag else "N/A (no ASIC build)"
        out.append(row)

    cols = []
    for r in out:
        for k in r:
            if k not in cols:
                cols.append(k)
    with open(R / "unified_metrics.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(out)

    def fmt(v, nd=3):
        return ("%.*f" % (nd, v)) if isinstance(v, float) else str(v)

    md = ["# Unified metrics (4 KiB caches, BP on)", "",
          "Generated by scripts/metrics/unified_table.py from result files; see its docstring for every source.", "",
          "| metric | " + " | ".join(CONFIGS) + " |", "|---|" + "---:|" * len(CONFIGS)]
    labels = [("cpi", "CPI (12 Embench-IoT kernels)", 4), ("icache_hit_pct", "I$ hit %", 2),
              ("dcache_read_hit_pct", "D$ read hit %", 2), ("bp_mispredict_pct", "branch mispredict %", 2),
              ("embench_speed_per_mhz_gm", "Embench speed / MHz, GM", 3), ("embench_speed_gsd", "Embench speed, GSD", 3),
              ("size_gm", "code size vs reference, GM", 3), ("size_gsd", "code size, GSD", 3),
              ("coremark_1iter_mcycle", "CoreMark 1 iteration, mcycle (not an official score)", 0),
              ("irq_entry", "IRQ entry, cycles (steady)", 0), ("irq_entry_cold", "IRQ entry, cycles (first, cold)", 0),
              ("irq_total", "IRQ total, minimal handler", 0), ("ctx_switch_total", "context switch total, cycles", 0),
              ("fpga_le", "FPGA LE (seed 2)", 0), ("fpga_fmax_mhz", "FPGA Fmax Slow 85C, MHz", 2),
              ("asic_view_mcycle_sum_pct_vs_fpga", "ASIC-view mcycle vs FPGA view, %", 3),
              ("gls_mcycle_match", "GLS mcycle = ASIC-view RTL", 0), ("board_mcycle_match", "board mcycle", 0),
              ("asic_power_saif", "ASIC power (GLS->SAIF, OpenSTA nom_tt)", 0),
              ("asic_epi_pj", "ASIC energy per instruction", 0)]
    byc = {r["config"]: r for r in out}
    for key, lab, nd in labels:
        md.append("| %s | %s |" % (lab, " | ".join(fmt(byc[c].get(key, "-"), nd) for c in CONFIGS)))
    (R / "unified_metrics.md").write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
