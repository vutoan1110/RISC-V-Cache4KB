#!/usr/bin/env bash
# 2026-10-14: start the DM_VC4 V2 full flow only after sa2_..._cts25_r3 has ended (sign-off line or STOP/FAIL line in
# gated_pd.log), so that no P4 runs next to another detailed routing (24 GB WSL). Cooperative abort: asic/.abort_gated_pd.
A=/mnt/e/Projects/RISCV-research/asic
T=sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25_r3
until grep -q -E "(SIGNOFF (CLEAN|FAILED) $T|STOP $T)" $A/gated_pd.log; do
  [ -e $A/.abort_gated_pd ] && { echo "$(date -Is) NOTE VC4 V2 queue aborted before launch (abort flag)" >> $A/gated_pd.log; exit 0; }
  sleep 60
done
echo "$(date -Is) NOTE VC4 V2 queue: $T ended; launching vc4_corr3600x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong_r1" >> $A/gated_pd.log
cd $A && G5_UNLIMITED_LATE_PHASE=1 P2_MIN_SETUP=0 P2_MIN_HOLD=-0.5 P2_INITIAL_GRT_FALLBACK=1 \
  ITEMS="soc_vc4_4kb:vc4_corr3600x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong_r1:config_corr3600x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong.json" \
  bash run_gated_pd.sh
