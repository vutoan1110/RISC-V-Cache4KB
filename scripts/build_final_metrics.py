#!/usr/bin/env python3
"""Final metric tables for RTL 8b163675 (QUY_TRINH_VA_RANG_BUOC.md, section G).

    python scripts/build_final_metrics.py [--pd <run> [--pd-repeat <run>]] [--gls <gls_power csv>]
                                          [--equiv <equivalence summary json>] [--handoff <section md>]

Writes results/FINAL_METRICS.md. Every table states its source file, its corner
or measurement condition and whether it was double-executed:
  1. architecture per configuration (Embench 12 kernels + CoreMark, 4 KiB):
     CPI/IPC, I$/D$ hit rates, branch misprediction, cycle shares (wait-share);
  2. FPGA per point (Quartus, 4 seeds, pass 1 vs pass 2): LE, registers, M9K,
     mult9, Fmax / slack at Slow-85C, power (Quartus Power Analyzer);
  3. ASIC (DM 4 KiB, OpenLane 2 / sky130): signoff gate first (DRC, LVS, XOR,
     antenna, EQY), then timing per corner, area, cells, power (flow estimate
     vs switching activity from gate-level simulation when available).
"""
import csv
import glob
import json
import math
import os
import sys

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RES = os.path.join(R, "results")
args = sys.argv[1:]
PD = args[args.index("--pd") + 1] if "--pd" in args else None
PD2 = args[args.index("--pd-repeat") + 1] if "--pd-repeat" in args else None
GLS = args[args.index("--gls") + 1] if "--gls" in args else None
EQV = args[args.index("--equiv") + 1] if "--equiv" in args else None   # JSON: {"rows": [[label, value]...], "note": str}
HANDOFF = args[args.index("--handoff") + 1] if "--handoff" in args else None   # markdown appended as section 4
out = []


def rows(p):
    with open(p) as f:
        return list(csv.DictReader(f))


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def gmean(v):
    v = [x for x in v if x > 0]
    return math.exp(sum(math.log(x) for x in v) / len(v)) if v else float("nan")


# ------------------------------------------------------------------ 1. architecture
emb1, emb2 = os.path.join(RES, "rtlfix_4kb_p1.csv"), os.path.join(RES, "rtlfix_4kb_p2.csv")
cm1, cm2 = os.path.join(RES, "coremark_rtlfix_4kb_p1.csv"), os.path.join(RES, "coremark_rtlfix_4kb_p2.csv")
e1, e2 = rows(emb1), rows(emb2)
same = e1 == e2 and rows(cm1) == rows(cm2)
out.append("# Final metrics — RTL 8b163675\n")
out.append("## 1. Architecture per configuration (Embench-IoT 12 kernels, 4 KiB caches, 50 MHz clock)\n")
av1, av2 = os.path.join(RES, "asic_view_4kb_p1.csv"), os.path.join(RES, "asic_view_4kb_p2.csv")
ea = rows(av1)
same_av = os.path.isfile(av2) and ea == rows(av2)
out.append("Source: `results/rtlfix_4kb_p{1,2}.csv` (FPGA-view RTL simulation: the SoC with the FPGA memories). "
           "Double execution: pass 1 %s pass 2.\n" % ("==" if same else "!= (CHECK)"))
out.append("The last row is the ASIC view of DM (`results/asic_view_4kb_p{1,2}.csv`, pass 1 %s pass 2): the RTL "
           "of the ASIC netlist, whose memories are the SRAM macros. It retires the same instructions with identical "
           "counts on 40 of 43 fields, but mcycle, I-wait and D-wait are lower (0.2-10.6 %% per kernel), so the "
           "CPI of the chip is the ASIC-view value; the FPGA-view rows are the FPGA/DSE comparison. (Corrected in "
           "NHAT_KY.md 2026-09-27: an earlier version called the views identical.)\n" % ("==" if same_av else "!= (CHECK)"))
out.append("| Config | Cycles (sum) | Instr (sum) | CPI (sum) | CPI geomean | I$ hit | D$ read hit | D$ write hit "
           "| Branch mispredict | I-wait | D-wait | Load-use | Control | MMIO |")
out.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
cfgs = [(c, [r for r in e1 if r["config"] == c]) for c in
        sorted({r["config"] for r in e1}, key=lambda c: int([r for r in e1 if r["config"] == c][0]["config_id"]))]
cfgs.append(("DM (ASIC view)", [r for r in ea if r["config"] == "DM"]))
for cfg, rs in cfgs:
    s = lambda k: sum(fnum(r[k]) for r in rs)
    cyc, ins = s("mcycle"), s("minstret")
    ia, im = s("i_access"), s("i_miss")
    drh, drm, dwh, dwm = s("d_rd_hit"), s("d_rd_miss"), s("d_wr_hit"), s("d_wr_miss")
    pred, corr = s("predictions"), s("correct")
    out.append("| %s | %d | %d | %.4f | %.4f | %.2f %% | %.2f %% | %.2f %% | %.2f %% | %.1f %% | %.1f %% | %.1f %% | %.1f %% | %.1f %% |" % (
        cfg, cyc, ins, cyc / ins, gmean([fnum(r["mcycle"]) / fnum(r["minstret"]) for r in rs]),
        100 * (1 - im / ia), 100 * drh / (drh + drm), 100 * dwh / (dwh + dwm) if dwh + dwm else float("nan"),
        100 * (1 - corr / pred), 100 * s("i_wait") / cyc, 100 * s("d_wait") / cyc, 100 * s("load_use") / cyc,
        100 * s("control") / cyc, 100 * s("mmio") / cyc))
cm = rows(cm1)
out.append("\nCoreMark (`results/coremark_rtlfix_4kb_p{1,2}.csv`):\n")
out.append("| Config | Cycles | Instr | CPI | I$ hit | Branch mispredict |")
out.append("|---|---:|---:|---:|---:|---:|")
for r in cm:
    out.append("| %s | %s | %s | %.4f | %.2f %% | %.2f %% |" % (
        r["config"], r["mcycle"], r["minstret"], fnum(r["mcycle"]) / fnum(r["minstret"]),
        100 * (1 - fnum(r["i_miss"]) / fnum(r["i_access"])), 100 * (1 - fnum(r["correct"]) / fnum(r["predictions"]))))

# ------------------------------------------------------------------ 2. FPGA
q1, q2 = os.path.join(RES, "fpga_points_r12b_p1.csv"), os.path.join(RES, "fpga_points_r12b_p2.csv")
out.append("\n## 2. FPGA (Cyclone IV EP4CE115, Quartus 20.1, 50 MHz, 4 seeds per point)\n")
if os.path.isfile(q1):
    a = rows(q1)
    b = rows(q2) if os.path.isfile(q2) else None
    out.append("Source: `%s`%s. Timing corner: Slow 1200 mV 85 C (signoff) and Slow 0 C. Power: Quartus Power "
               "Analyzer at the default toggle rate (vectorless estimate, not switching activity).\n" % (
                   os.path.basename(q1), (", pass 2 `%s`: %s" % (os.path.basename(q2), "identical" if b and
                    [{k: v for k, v in r.items() if k != "seconds"} for r in a] ==
                    [{k: v for k, v in r.items() if k != "seconds"} for r in b] else "DIFFERS or incomplete"))
                   if b is not None else ", pass 2 pending"))
    out.append("| Point | LE (min–max) | Registers | M9K | mult9 | Fmax S85C MHz (min–max) | Setup S85C ns (min) "
               "| Hold S85C ns (min) | Power total / core dyn / static mW (seed 2) |")
    out.append("|---|---|---:|---:|---:|---|---:|---:|---|")
    for pt in ("dm_4kb", "sa2_4kb", "vc4_4kb", "dse_4kb"):
        rs = [r for r in a if r["point"].split("@")[0] == pt]
        if not rs:
            continue
        le = [int(fnum(r["le"])) for r in rs]
        fm = [fnum(r["fmax_s85"]) for r in rs]
        s2 = [r for r in rs if "@" not in r["point"]][0]
        out.append("| %s | %d–%d | %s | %s | %s | %.2f–%.2f | %+.3f | %+.3f | %s / %s / %s |" % (
            pt, min(le), max(le), s2["regs"], s2["m9k"], s2["mult9"], min(fm), max(fm),
            min(fnum(r["setup_s85_slack"]) for r in rs), min(fnum(r["hold_s85_slack"]) for r in rs),
            s2["pow_total_mw"], s2["pow_core_dyn_mw"], s2["pow_core_static_mw"]))
else:
    out.append("_pending: Quartus pass 1 on 8b163675_\n")

# ------------------------------------------------------------------ 3. ASIC
out.append("\n## 3. ASIC (DM 4 KiB, sky130A / sky130_fd_sc_hd, OpenLane 2.3.10, CLOCK_PERIOD 20 ns)\n")
if PD:
    base = os.path.join(R, "asic", "soc_dm_4kb", "runs", PD)
    m = {}
    for so in sorted(glob.glob(os.path.join(base, "*", "state_out.json"))):
        try:
            m.update(json.load(open(so)).get("metrics", {}))
        except Exception:
            pass
    g = lambda k: m.get(k, "n/a")
    out.append("Run `%s`%s.\n" % (PD, (" (repeat `%s`)" % PD2) if PD2 else ""))
    out.append("### 3.1 Signoff gate\n")
    out.append("| Check | Result |")
    out.append("|---|---|")
    for lab, k in (("Magic DRC", "magic__drc_error__count"), ("KLayout DRC", "klayout__drc_error__count"),
                   ("Route DRC", "route__drc_errors"), ("LVS errors", "design__lvs_error__count"),
                   ("XOR differences", "design__xor_difference__count"),
                   ("Illegal overlaps", "magic__illegal_overlap__count"),
                   ("Antenna violating nets / pins", None), ("Hold violations (all corners)", "timing__hold_vio__count")):
        v = ("%s / %s" % (g("antenna__violating__nets"), g("antenna__violating__pins"))) if k is None else g(k)
        out.append("| %s | %s |" % (lab, v))
    if EQV:
        q = json.load(open(EQV))
        for lab, v in q["rows"]:
            out.append("| %s | %s |" % (lab, v))
    else:
        eqy = glob.glob(os.path.join(base, "*-yosys-eqy"))
        out.append("| EQY (RTL vs final netlist) | %s |" % ("see NHAT_KY.md" if eqy else "not run"))
    if PD2:
        m2 = {}
        for so in sorted(glob.glob(os.path.join(R, "asic", "soc_dm_4kb", "runs", PD2, "*", "state_out.json"))):
            try:
                m2.update(json.load(open(so)).get("metrics", {}))
            except Exception:
                pass
        shared = [k for k in m if k in m2 and not k.startswith(("runtime", "flow__"))]
        diff = [k for k in shared if m[k] != m2[k]]
        out.append("\nDouble execution: `%s` vs `%s` on %d shared flow metrics: %s.\n" % (
            PD, PD2, len(shared), "identical" if not diff else "%d differ: %s" % (len(diff), ", ".join(diff[:12]))))
    if EQV:
        out.append(q.get("note", "") + "\n")
    out.append("\n### 3.2 Timing per corner (setup / hold worst slack, ns; Fmax = 1/(20 - WNS))\n")
    out.append("| Corner | Setup WS | Setup TNS | Setup violators | Hold WS | Fmax MHz |")
    out.append("|---|---:|---:|---:|---:|---:|")
    for c in ("nom_tt_025C_1v80", "min_tt_025C_1v80", "max_tt_025C_1v80", "nom_ss_100C_1v60",
              "min_ss_100C_1v60", "max_ss_100C_1v60", "nom_ff_n40C_1v95", "min_ff_n40C_1v95", "max_ff_n40C_1v95"):
        ws = fnum(m.get("timing__setup__ws__corner:" + c))
        fmax = 1000.0 / (20.0 - min(ws, 0.0)) if not math.isnan(ws) else float("nan")
        out.append("| %s | %+.3f | %.1f | %s | %+.3f | %s |" % (
            c, ws, fnum(m.get("timing__setup__tns__corner:" + c)), m.get("timing__setup_vio__count__corner:" + c, "n/a"),
            fnum(m.get("timing__hold__ws__corner:" + c)), ">= 50" if ws >= 0 else "%.1f" % fmax))
    out.append("\nSRAM macros are characterised at TT only (no ss/ff liberty exists for "
               "sky130_sram_1kbyte_1rw1r_32x256_8 in the PDK); ss/ff numbers use TT macro timing and are optimistic "
               "on paths through the SRAMs.\n")
    out.append("### 3.3 Area and power\n")
    out.append("| Quantity | Value |")
    out.append("|---|---|")
    for lab, k in (("Die area (um^2)", "design__die__area"), ("Core area (um^2)", "design__core__area"),
                   ("Std-cell area (um^2)", "design__instance__area__stdcell"),
                   ("Macro area (um^2)", "design__instance__area__macros"),
                   ("Std-cell count", "design__instance__count__stdcell"),
                   ("Utilization", "design__instance__utilization"), ("Wirelength (um)", "route__wirelength"),
                   ("Flow power metric `power__total` (W) — this is the max_ff_n40C_1v95 corner", "power__total")):
        out.append("| %s | %s |" % (lab, g(k)))
    # vectorless power per corner, read from the step's own power.rpt files
    sta = sorted(glob.glob(os.path.join(base, "*-openroad-stapostpnr")))
    if sta:
        for c in ("nom_tt_025C_1v80", "nom_ss_100C_1v60", "nom_ff_n40C_1v95"):
            p = os.path.join(sta[-1], c, "power.rpt")
            if os.path.isfile(p):
                for ln in open(p):
                    if ln.startswith("Total"):
                        f = ln.split()
                        out.append("| Vectorless power at %s: total / internal / switching / leakage (mW) "
                                   "| %.2f / %.2f / %.2f / %.3f |" % (c, 1e3 * float(f[4]), 1e3 * float(f[1]),
                                                                     1e3 * float(f[2]), 1e3 * float(f[3])))
                        break
    out.append("\nVectorless = OpenSTA with default activity (combinational logic ~0 mW); the activity-based "
               "figure below uses the switching measured in gate-level simulation of each kernel.\n")
else:
    out.append("_pending: final PD run_\n")

if GLS and os.path.isfile(GLS):
    out.append("### 3.4 Activity-based power (gate-level simulation of the final netlist -> SAIF -> OpenSTA, nom_tt)\n")
    out.append("Source: `%s`.\n" % os.path.basename(GLS))
    out.append("| Kernel | Total mW | Dynamic mW | Leakage mW | Energy / instruction pJ |")
    out.append("|---|---:|---:|---:|---:|")
    for r in rows(GLS):
        out.append("| %s | %s | %s | %s | %s |" % (r.get("kernel"), r.get("total_mw"), r.get("dynamic_mw"),
                                                    r.get("leakage_mw"), r.get("epi_pj")))
else:
    out.append("_activity-based power: pending (GLS + SAIF of the final netlist)_\n")

if HANDOFF and os.path.isfile(HANDOFF):
    out.append("")
    out.append(open(HANDOFF, encoding="utf-8").read().rstrip("\n"))

open(os.path.join(RES, "FINAL_METRICS.md"), "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print("wrote results/FINAL_METRICS.md")
