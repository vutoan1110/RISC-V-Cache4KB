#!/usr/bin/env bash
# 2026-10-14: start sa2_..._cts25_r4 (fresh full flow, same config) only after the DM_VC4 V2 flow has ended (sign-off
# line or STOP line in gated_pd.log), so that no P4 runs next to another detailed routing. Abort: asic/.abort_gated_pd.
A=/mnt/e/Projects/RISCV-research/asic
T=vc4_corr3600x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong_r1
until grep -q -E "(SIGNOFF (CLEAN|FAILED) $T|STOP $T)" $A/gated_pd.log; do
  [ -e $A/.abort_gated_pd ] && { echo "$(date -Is) NOTE SA2 E1 r4 queue aborted before launch (abort flag)" >> $A/gated_pd.log; exit 0; }
  sleep 60
done
echo "$(date -Is) NOTE SA2 E1 r4 queue: $T ended; launching sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25_r4" >> $A/gated_pd.log
cd $A && G5_UNLIMITED_LATE_PHASE=1 P2_MIN_SETUP=0 P2_MIN_HOLD=-0.5 P2_INITIAL_GRT_FALLBACK=1 \
  ITEMS="soc_sa2_4kb:sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25_r4:config_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25.json" \
  bash run_gated_pd.sh
