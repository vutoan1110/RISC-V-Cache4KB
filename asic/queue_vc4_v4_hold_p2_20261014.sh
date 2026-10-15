#!/usr/bin/env bash
# 2026-10-14: DM_VC4 V4 = the V2 recipe on the 3800 x 3400 corridor floorplan (config_corr3800x3400_f220_capm20_pad1_
# antgrt10_nogrtt_nogrtd_antcong.json; only DIE_AREA / CORE_AREA / MACRO_PLACEMENT_CFG differ from V2). Development run
# (rule Q revised 2026-10-14): STOP_AFTER=p2 holds it before detailed routing while the V2 detailed-routing replay screening
# holds ~12 GB of the WSL VM; the detailed routing is resumed later with run_gated_resume.sh ... drt under the SAME
# environment as below. Declared at launch for the detailed routing: G5_ANT_ROUND_RULES=1 with the default antenna-call
# limits of drt_watch.sh (iteration 20 > 3000, 30 > 600, 40 > 200, stall rule from 20; no limit after 40 with
# G5_UNLIMITED_LATE_PHASE=1). Acceptance needs a later complete run without hold.
A=/mnt/e/Projects/RISCV-research/asic
cd $A && STOP_AFTER=p2 G5_UNLIMITED_LATE_PHASE=1 G5_ANT_ROUND_RULES=1 P2_MIN_SETUP=0 P2_MIN_HOLD=-0.5 P2_INITIAL_GRT_FALLBACK=1 \
  ITEMS="soc_vc4_4kb:vc4_corr3800x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong_r1:config_corr3800x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong.json" \
  bash run_gated_pd.sh
