#!/usr/bin/env bash
# 2026-10-14 (owner: shorter tasks first): one heavy phase (detailed routing / sign-off) at a time in the 24 GB WSL VM.
# The DM acceptance run dm_grid3665x2900_r3 was started directly (its detailed routing waits for the drt slot of the gated
# driver); this sequence then runs, each stage only after the previous one has written its end line to gated_pd.log:
#   0. wait for the DM_VC4 V2 detailed-routing replay screening to end ("exit N" in its run_screen.out) AND for the DM
#      acceptance run to end ("SIGNOFF CLEAN|FAILED dm_grid3665x2900_r3" or "STOP dm_grid3665x2900_r3")
#   1. sa2_..._cts25_r5   detailed routing + sign-off (held after p2 as planned; environment of its launch)
#   2. vc4_corr3800x3400_..._antcong_r1 (V4) detailed routing + sign-off (held after p2 as planned; environment declared at
#      its launch: G5_UNLIMITED_LATE_PHASE=1 G5_ANT_ROUND_RULES=1, default antenna-call limits) - longest, last
# Log-based waits only (pgrep -f would match its own shell). Cooperative stop between stages: asic/.abort_sequence_20261014b.
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/gated_pd.log
REPLAY=$A/soc_vc4_4kb/screen_drt_replay_v2_20261014/run_screen.out
DM=dm_grid3665x2900_r3
SA2=sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25_r5
V4=vc4_corr3800x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong_r1
say () { echo "$(date -Is) $*" | tee -a $LOG >> $A/dse_pd.log; }
stop_req () { [ -e $A/.abort_sequence_20261014b ]; }
ended () { grep -q -E "(SIGNOFF (CLEAN|FAILED) $1|STOP $1)" $LOG; }
until grep -q "^exit" $REPLAY 2>/dev/null && ended $DM; do
    stop_req && { say "NOTE heavy-phase sequence b aborted while waiting for the replay / $DM"; exit 0; }
    sleep 60
done
say "NOTE heavy-phase sequence b: replay and $DM ended; resuming $SA2 (detailed routing + sign-off)"
stop_req && { say "NOTE heavy-phase sequence b aborted before $SA2"; exit 0; }
cd $A && G5_UNLIMITED_LATE_PHASE=1 bash run_gated_resume.sh soc_sa2_4kb $SA2 config_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25.json "planned hold after p2 (STOP_AFTER=p2) while the DM_VC4 replay held the WSL memory" drt
until ended $SA2; do sleep 60; done
say "NOTE heavy-phase sequence b: $SA2 ended; resuming $V4 (detailed routing + sign-off)"
stop_req && { say "NOTE heavy-phase sequence b aborted before $V4"; exit 0; }
cd $A && G5_UNLIMITED_LATE_PHASE=1 G5_ANT_ROUND_RULES=1 bash run_gated_resume.sh soc_vc4_4kb $V4 config_corr3800x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong.json "planned hold after p2 (STOP_AFTER=p2) while the DM_VC4 replay held the WSL memory" drt
until ended $V4; do sleep 60; done
say "NOTE heavy-phase sequence b done"
