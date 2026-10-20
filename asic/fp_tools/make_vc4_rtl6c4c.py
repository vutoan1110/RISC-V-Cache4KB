"""DM_VC4 on RTL 6c4ccffd (2026-10-15 / 2026-10-20, owner: optimise all three configurations): corridor floorplan
(make_u2_fp.py) and the SA2 6c4ccffd recipe, with the DM_VC4-specific settings.

    python make_vc4_rtl6c4c.py <W> <H> [gin=220] [orient=V] [variant=base]

orient: cache orientation of make_u2_fp.py (F = lower row N / upper row FS, V = lower row FS / upper row N).
variant:
  base     the SA2 recipe (post-GRT design and timing repair on, GRT antenna margin 30);
  nogrt    post-GRT design + timing repair off and DRT_ANTENNA_REPAIR_ALLOW_CONGESTION on, the settings of the R14 DM_VC4
           runs that passed p2 and finished their main detailed route (corr3800x3400_f220 ..._nogrtt_nogrtd_antcong_r1);
           the GRT antenna margin stays at the SA2 value 30 (those runs used 10 and left 1,098 post-route antenna nets).
1. make_u2_fp.py soc_vc4_4kb corr<W>x<H>_<o><gin>_rtl6c4c <W> <H> <VC4 R14 base> 100 220 150 <gin> <orient>
   (the R14 base only supplies the 16 macro instance names; its generated config is removed again);
2. the 8 cache macro names get the R15 / R16 generate level (u_soc.u_{i,d}cache.g_dse -> .genblk1.g_dse, as in the
   6c4ccffd netlist; SA2 needed the same rename, 2026-10-14) and the RTL generate labels are checked in the snapshot;
3. config_corr<W>x<H>_<o><gin>_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rszctsall[_nogrtt_nogrtd_antcong]_rtl6c4c.json.
"""
import json
import re
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

A = Path("E:/Projects/RISCV-research/asic")
D = A / "soc_vc4_4kb"
W, H = float(sys.argv[1]), float(sys.argv[2])
gin = float(sys.argv[3]) if len(sys.argv) > 3 else 220.0
orient = sys.argv[4] if len(sys.argv) > 4 else "V"
variant = sys.argv[5] if len(sys.argv) > 5 else "base"
assert orient in ("F", "V") and variant in ("base", "nogrt")
o = orient.lower()
tag = "corr%dx%d_%s%d_rtl6c4c" % (W, H, o, gin)
base = "config_corr3800x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong.json"
subprocess.run([sys.executable, "-B", str(A / "fp_tools/make_u2_fp.py"), "soc_vc4_4kb", tag, str(W), str(H), base,
                "100", "220", "150", str(gin), orient], check=True)
(D / ("config_%s.json" % tag)).unlink()          # generated from the R14 base: not used
mp = D / ("macro_placement_%s.cfg" % tag)
txt = mp.read_text(encoding="utf-8")
txt = re.sub(r"u_soc\.u_(i|d)cache\.g_dse\.", r"u_soc.u_\1cache.genblk1.g_dse.", txt)
txt = ("# DM_VC4 on RTL 6c4ccffd; cache macro names with the R15 / R16 generate level genblk1 "
       "(fp_tools/make_vc4_rtl6c4c.py).\n" + txt)
mp.write_text(txt, encoding="utf-8", newline="\n")
names = [ln.split()[0] for ln in txt.splitlines() if ln.strip() and not ln.startswith("#")]
assert len(names) == 16 and sum("genblk1.g_dse" in n for n in names) == 8, names
snap = A / "snapshots/rtl_rfbht"
dc = (snap / "hdl/cache/dcache.v").read_text(encoding="utf-8")
assert re.search(r"end else if\s*\(CACHE_CONFIG\s*>=\s*4\)\s*begin\s*:\s*g_nway", dc) and "begin:g_dse" in dc.replace(" ", "")
bank = (snap / "asic/dse_sram/cache_dse_data_bank_sram.v").read_text(encoding="utf-8")
assert re.search(r"begin\s*:\s*g_full", bank) and re.search(r"begin\s*:\s*g_bank", bank)

sa2 = json.load(open(A / "soc_sa2_4kb/config_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rszctsall_rtl6c4c.json",
                     encoding="utf-8"), object_pairs_hook=OrderedDict)
c = OrderedDict()
c["//EXPERIMENT"] = (
    "DM_VC4 on RTL 6c4ccffd (owner: optimise DM, SA2 and DM_VC4). Recipe = the SA2 6c4ccffd recipe "
    "(config_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rszctsall_rtl6c4c.json: cap 20, fanout 16, cell "
    "padding, timing-driven GPL, clock met3-met5, resizer tt / ff with the post-CTS timing repair also on ss, two-pass "
    "post-route hold ECO) on the corridor floorplan %dx%d, cache orientation %s (macro_placement_%s.cfg), variant %s."
    % (W, H, orient, tag, variant))
for k, v in sa2.items():
    if k.startswith("//"):
        continue
    c[k] = v
vf = [f.replace("snapshots/rtl_rfbht/asic/soc_sa2_4kb/soc_asic_top.v", "snapshots/rtl_rfbht/asic/soc_vc4_4kb/soc_asic_top.v")
      for f in sa2["VERILOG_FILES"]]
assert sum("soc_vc4_4kb/soc_asic_top.v" in f for f in vf) == 1 and not any("soc_sa2_4kb" in f for f in vf)
for f in vf:
    assert (D / f.replace("dir::", "")).resolve().is_file(), f
c["VERILOG_FILES"] = vf
c["DIE_AREA"] = [0, 0, W, H]
c["CORE_AREA"] = [12, 12, W - 12, H - 12]
c["MACRO_PLACEMENT_CFG"] = "dir::macro_placement_%s.cfg" % tag
c["DRT_SAVE_MAIN_ROUTE"] = True    # keep the main detailed route if the post-route antenna re-route fails (local, 2026-10-13)
# DM_VC4 never writes the way-1 data banks, so synthesis removes those macros while the JSON header still lists them;
# without this (local, 2026-10-02; every R14 DM_VC4 config had it) Odb.SetPowerConnections fails on them.
c["PWR_CONN_SKIP_SYNTH_REMOVED"] = True
suffix = ""
if variant == "nogrt":
    c["//VARIANT"] = (
        "nogrt (2026-10-20): RUN_POST_GRT_DESIGN_REPAIR / RUN_POST_GRT_RESIZER_TIMING off and "
        "DRT_ANTENNA_REPAIR_ALLOW_CONGESTION on, as the R14 DM_VC4 run that passed p2 and finished its main detailed route "
        "at 3800x3400 F (the post-GRT repairs of the 6c4ccffd V run raised the global-route overflow 0 -> 1,066). GRT "
        "antenna margin 30 (SA2) instead of that run's 10: it left 1,098 post-route antenna nets and its diode re-route "
        "diverged; SA2 with 30 left 616 and converged.")
    c["RUN_POST_GRT_DESIGN_REPAIR"] = False
    c["RUN_POST_GRT_RESIZER_TIMING"] = False
    c["DRT_ANTENNA_REPAIR_ALLOW_CONGESTION"] = True
    assert c["GRT_ANTENNA_MARGIN"] == 30
    suffix = "_nogrtt_nogrtd_antcong"
out = D / ("config_corr%dx%d_%s%d_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rszctsall%s_rtl6c4c.json" % (W, H, o, gin, suffix))
out.write_text(json.dumps(c, indent=4, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
print("wrote", mp.name, "and", out.name)
