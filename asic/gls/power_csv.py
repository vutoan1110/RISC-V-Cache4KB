#!/usr/bin/env python3
"""Activity-based power table of one GLS power run (FLOW_JOURNAL Incidents 83, 91).

    python asic/gls/power_csv.py <tag>          # reads results/gls_power_<tag>/*.power.rpt
                                                #       results/gls_power_<tag>.csv (GLS window)
                                                #       results/asic_view_4kb_p1.csv (minstret)
    -> results/gls_power_<tag>_power.csv

Power is OpenSTA's report_power at nom_tt with the per-kernel SAIF (sta_power.sh). The SAIF window is
exactly the kernel's ASIC-view mcycle (run_gls_power.sh checks window = mcycle), so CPI and energy per
instruction use THAT cycle count: cpi = window_cycles / minstret, epi = P * window_cycles * 20 ns /
minstret. (The first version of this table, for final_A, took CPI from the FPGA-view run
rtlfix_4kb_p1.csv, whose mcycle differs from the ASIC view by 0.2-10.6 %; Incident 91 corrects it.)
"""
import csv
import os
import re
import sys

tag = sys.argv[1]
# FLOW_JOURNAL Incident 96: optional <ref_csv> <config> for the minstret of other designs / kernel sets
# (R14 upstream kernels: results/upstream_asic_r15_p1.csv DM; SA2 / DM_VC4: results/dse_asic_view_p1.csv).
ref_csv = sys.argv[2] if len(sys.argv) > 2 else "asic_view_4kb_p1.csv"
ref_cfg = sys.argv[3] if len(sys.argv) > 3 else "DM"
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
res = os.path.join(R, "results")
gls = {r["kernel"]: r for r in csv.DictReader(open(os.path.join(res, "gls_power_%s.csv" % tag)))}
av = {r["kernel"]: r for r in csv.DictReader(open(os.path.join(res, os.path.basename(ref_csv)))) if r["config"] == ref_cfg}
out = []
for k in sorted(gls):
    g = gls[k]
    rpt = open(os.path.join(res, "gls_power_%s" % tag, "%s.power.rpt" % k)).read()
    grp = {}
    for m in re.finditer(r"^(Sequential|Combinational|Clock|Macro|Pad|Total)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", rpt, re.M):
        grp[m.group(1)] = [float(x) for x in m.group(2, 3, 4, 5)]
    unk = re.search(r"PW_ORIGIN unknown\s+\d+\s+([\d.]+) %", rpt)
    win = int(g["win_cycles"])
    assert g["status"] == "PASS" and g["match"] == "YES" and win == int(g["gls_mcycle"]), (k, g)
    ni = int(av[k]["minstret"])
    tot = grp["Total"]
    p = tot[3]
    out.append({
        "kernel": k, "total_mw": "%.2f" % (1e3 * p), "dynamic_mw": "%.2f" % (1e3 * (tot[0] + tot[1])),
        "leakage_mw": "%.3f" % (1e3 * tot[2]), "seq_mw": "%.2f" % (1e3 * grp["Sequential"][3]),
        "comb_mw": "%.2f" % (1e3 * grp["Combinational"][3]), "clock_mw": "%.2f" % (1e3 * grp["Clock"][3]),
        "macro_mw": "%.2f" % (1e3 * grp["Macro"][3]), "window_cycles": win, "minstret": ni,
        "cpi": "%.4f" % (win / ni), "epi_pj": "%.0f" % (p * win * 20e-9 / ni * 1e12),
        "unknown_pct": unk.group(1) if unk else ""})
dst = os.path.join(res, "gls_power_%s_power.csv" % tag)
with open(dst, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)
print("wrote", dst)
for r in out:
    print("  %-10s %7s mW  cpi %s  epi %s pJ" % (r["kernel"], r["total_mw"], r["cpi"], r["epi_pj"]))
