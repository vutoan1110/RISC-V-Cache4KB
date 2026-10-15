#!/usr/bin/env bash
# 2026-10-14: one heavy phase (detailed routing / sign-off) at a time in the 24 GB WSL VM, in this order, each stage
# started only after the previous one has written its end line to gated_pd.log:
#   0. wait for the DM_VC4 V2 detailed-routing replay screening to end (its run_screen.out gets "exit N")
#   1. sa2_..._cts25_r5   detailed routing + sign-off (planned hold after p2; same environment as its launch)
#   2. vc4_corr3800x3400_..._antcong_r1 (V4) detailed routing + sign-off (planned hold after p2; environment declared at
#      its launch: G5_UNLIMITED_LATE_PHASE=1 G5_ANT_ROUND_RULES=1 with the default antenna-call limits)
#   3. DM acceptance run dm_grid3665x2900_r3 (queue_dm_clean_run_20261014.sh, complete flow from step 1)
# End of a stage = a "SIGNOFF CLEAN|FAILED <tag>" or "STOP <tag>" line (log based; no pgrep, which matches its own shell).
# Cooperative stop between stages: touch asic/.abort_sequence_20261014.
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/gated_pd.log
REPLAY=$A/soc_vc4_4kb/screen_drt_replay_v2_20261014/run_screen.out
SA2=sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25_r5
V4=vc4_corr3800x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong_r1
say () { echo "$(date -Is) $*" | tee -a $LOG >> $A/dse_pd.log; }
stop_req () { [ -e $A/.abort_sequence_20261014 ]; }
wait_end () {   # <tag>
    until grep -q -E "(SIGNOFF (CLEAN|FAILED) $1|STOP $1)" $LOG; do sleep 60; done
}
until grep -q "^exit" $REPLAY 2>/dev/null; do stop_req && { say "NOTE heavy-phase sequence aborted while waiting for the replay"; exit 0; }; sleep 60; done
say "NOTE heavy-phase sequence: V2 DRT replay screening ended ($(grep '^exit' $REPLAY | tail -1)); resuming $SA2 (detailed routing + sign-off)"
stop_req && { say "NOTE heavy-phase sequence aborted before $SA2"; exit 0; }
cd $A && G5_UNLIMITED_LATE_PHASE=1 bash run_gated_resume.sh soc_sa2_4kb $SA2 config_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25.json "planned hold after p2 (STOP_AFTER=p2) while the DM_VC4 replay held the WSL memory" drt
wait_end $SA2
say "NOTE heavy-phase sequence: $SA2 ended; resuming $V4 (detailed routing + sign-off)"
stop_req && { say "NOTE heavy-phase sequence aborted before $V4"; exit 0; }
cd $A && G5_UNLIMITED_LATE_PHASE=1 G5_ANT_ROUND_RULES=1 bash run_gated_resume.sh soc_vc4_4kb $V4 config_corr3800x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong.json "planned hold after p2 (STOP_AFTER=p2) while the DM_VC4 replay held the WSL memory" drt
wait_end $V4
say "NOTE heavy-phase sequence: $V4 ended; launching the DM acceptance run dm_grid3665x2900_r3"
stop_req && { say "NOTE heavy-phase sequence aborted before the DM acceptance run"; exit 0; }
bash $A/queue_dm_clean_run_20261014.sh
say "NOTE heavy-phase sequence done"
