#!/usr/bin/env bash
# 2026-10-20 DM_VC4 density-34 recipe (config_..._rszctsall_d34_rtl6c4c.json): the development screen
# vc4_..._d34_rtl6c4c_scr_r1 passed p2 (first DM_VC4 p2 PASS: overflow 0, nom_tt +1.118, hold +0.064) and is held after
# p2 (STOP_AFTER=p2 declared at launch, same as the acceptance runs); r2 is a fresh full flow of the same config with the
# same declared gates. Heavy phases (detailed routing + sign-off part) one at a time: scr_r1 after the SA2 acceptance r2
# sign-off, then r2 after its p2 hold. Same G5 setting as pipeline_acceptance_20261020.sh.
# Cooperative stop: touch asic/.abort_pipeline_vc4_d34 (checked between phases; asic/.abort_gated_pd stops the flows).
set -u
cd /mnt/e/Projects/RISCV-research/asic
CFG=config_corr3800x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rszctsall_d34_rtl6c4c.json
T1=vc4_corr3800x3400_f220_rszctsall_d34_rtl6c4c_scr_r1
T2=vc4_corr3800x3400_f220_rszctsall_d34_rtl6c4c_r2
SA2R2=sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rszctsall_rcrep_rtl6c4c_r2
ABORT=.abort_pipeline_vc4_d34
say () { echo "$(date -u +%FT%T+00:00) $*" >> gated_pd.log; }
say "NOTE pipeline_vc4_d34_20261020 start: $T2 light phase now; heavy $T1 after $SA2R2, then $T2"
( P1_MIN_SETUP=0 P2_MIN_SETUP=0 P2_MIN_HOLD=-0.5 STOP_AFTER=p2 ITEMS="soc_vc4_4kb:$T2:$CFG" bash run_gated_pd.sh \
      > queue_vc4_d34_r2_20261020.out 2>&1 &&
  bash sta_query/ss_proxy.sh soc_vc4_4kb/runs/$T2 /mnt/e/Projects/RISCV-research/results/ss_study_20261015/${T2}_ss_proxy_grt.txt grt \
      >> queue_vc4_d34_r2_20261020.out 2>&1 ) &
LP=$!
until grep -q -E "(SIGNOFF [A-Z]+|STOP) $SA2R2|GATE $SA2R2 (PASS|FAIL) final" gated_pd.log; do
    [ -e $ABORT ] && { say "NOTE pipeline_vc4_d34 aborted before $T1 heavy"; exit 1; }
    sleep 60
done
G5_UNLIMITED_LATE_PHASE=1 bash run_gated_resume.sh soc_vc4_4kb $T1 $CFG \
    "development screen passed p2 (planned pause, STOP_AFTER=p2 declared at launch); heavy phases one at a time" drt \
    > queue_vc4_d34_scr_r1_drt_20261020.out 2>&1
wait $LP
grep -q "HOLD $T2 after P2" gated_pd.log || { say "NOTE pipeline_vc4_d34: $T2 not held after P2, no heavy phase"; exit 0; }
[ -e $ABORT ] && { say "NOTE pipeline_vc4_d34 aborted before $T2 heavy"; exit 1; }
G5_UNLIMITED_LATE_PHASE=1 bash run_gated_resume.sh soc_vc4_4kb $T2 $CFG \
    "acceptance run: planned pause after the p2 gate (STOP_AFTER=p2, same config); heavy phases one at a time" drt \
    > queue_vc4_d34_r2_drt_20261020.out 2>&1
say "NOTE pipeline_vc4_d34_20261020 done"
