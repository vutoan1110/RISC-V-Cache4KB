#!/usr/bin/env bash
# 2026-10-14: DM_VC4 V5 = V2 + DESIGN_REPAIR_MAX_WIRE_LENGTH 500 um (config_corr3600x3400_f220_capm20_pad1_antgrt10_nogrtt_
# nogrtd_antcong_mwl500.json; single change). Development run (rule Q revised 2026-10-14), held after p2 (STOP_AFTER=p2)
# while the V2 detailed-routing replay screening holds ~12 GB. Early indicator: the antenna check after the global-route
# antenna repair (V2 742 nets, V4 821). Detailed routing later with the SAME environment (G5_ANT_ROUND_RULES=1 declared).
A=/mnt/e/Projects/RISCV-research/asic
cd $A && STOP_AFTER=p2 G5_UNLIMITED_LATE_PHASE=1 G5_ANT_ROUND_RULES=1 P2_MIN_SETUP=0 P2_MIN_HOLD=-0.5 P2_INITIAL_GRT_FALLBACK=1 \
  ITEMS="soc_vc4_4kb:vc4_corr3600x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong_mwl500_r1:config_corr3600x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong_mwl500.json" \
  bash run_gated_pd.sh
