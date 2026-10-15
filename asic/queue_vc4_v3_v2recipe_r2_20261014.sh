#!/usr/bin/env bash
# 2026-10-14: DM_VC4 V3 = the V2 recipe (config_corr3600x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong.json, unchanged)
# as a complete run from step 1 without hold (rule Q revised 2026-10-14: development by resume, acceptance by one complete
# run; the flow is deterministic - the standalone replay of V2's detailed routing reproduced V2 iteration by iteration -
# and the only change is a launch-time setting, so this run is test and acceptance at once).
# Launch-time setting (declared here): drt_watch.sh antenna-call limits G5_ANT_ROUND_RULES=1, iteration 20 > 3000,
# 30 > 600, 40 > 400 (G5_ANT_IT40=400), stall rule from 20, no limit after 40 (G5_UNLIMITED_LATE_PHASE=1). Calibrated on the
# replay screening: antenna re-route 2,063 (17) -> 703 (20) -> 353 (30) -> 293 (34), still falling; V2 itself was stopped
# at iteration 17 by the main-route stall rule. Detailed routing waits for the drt slot (>= 12 GB free) while the replay runs.
A=/mnt/e/Projects/RISCV-research/asic
cd $A && G5_UNLIMITED_LATE_PHASE=1 G5_ANT_ROUND_RULES=1 G5_ANT_IT40=400 P2_MIN_SETUP=0 P2_MIN_HOLD=-0.5 P2_INITIAL_GRT_FALLBACK=1 \
  ITEMS="soc_vc4_4kb:vc4_corr3600x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong_r2:config_corr3600x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong.json" \
  bash run_gated_pd.sh
