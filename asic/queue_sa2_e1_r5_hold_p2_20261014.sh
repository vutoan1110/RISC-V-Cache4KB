#!/usr/bin/env bash
# 2026-10-14: sa2_..._cts25_r5 = E1 retried from step 1 (rule Q) after r4 died at random in step 34 DetailedPlacement
# (Tcl panic "TclParseNumber: bad acceptState 10 parsing '2720'", 6.5 s into the step). Same config and launch
# environment as r1-r4, plus STOP_AFTER=p2: a PLANNED hold after the p2 gate, so its detailed routing does not run
# beside the DM_VC4 detailed-routing replay screening (asic/soc_vc4_4kb/screen_drt_replay_v2_20261014); continue with
# run_gated_resume.sh soc_sa2_4kb <tag> <config> '<reason>' drt once that screening has ended.
A=/mnt/e/Projects/RISCV-research/asic
cd $A && STOP_AFTER=p2 G5_UNLIMITED_LATE_PHASE=1 P2_MIN_SETUP=0 P2_MIN_HOLD=-0.5 P2_INITIAL_GRT_FALLBACK=1 \
  ITEMS="soc_sa2_4kb:sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25_r5:config_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25.json" \
  bash run_gated_pd.sh
