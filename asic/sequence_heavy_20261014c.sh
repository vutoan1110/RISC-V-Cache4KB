#!/usr/bin/env bash
# 2026-10-14 (owner: shorter tasks first; the V2 replay screening has ended, ~20 GB free). One heavy phase at a time,
# shortest first, and the DM acceptance run protected from any memory overlap:
#   1. resume sa2_..._cts25_r5 (detailed routing + sign-off, ~2.5 h) NOW, while dm_grid3665x2900_r3 is still in its
#      light P1 / P2 phases (synthesis .. global routing, ~3-5 GB);
#   2. once SA2's detailed routing has started and its resume script has released the shared detailed-routing slot
#      lock (asic/.gated_drt_gate.lock, used by run_gated_pd.sh and run_gated_resume.sh), HOLD that lock, so the DM
#      run cannot enter detailed routing while SA2 routes or signs off (P4 has no memory gate of its own: P4 next to a
#      detailed routing exhausted the 24 GB VM once);
#   3. release the lock when SA2 has ended (SIGNOFF CLEAN|FAILED or STOP line): DM's detailed routing then starts through
#      its own gate;
#   4. when DM has ended, resume vc4_corr3800x3400_..._antcong_r1 (V4; environment declared at its launch).
# Log-based waits only (no pgrep -f: it matches its own shell). Cooperative stop between stages:
# asic/.abort_sequence_20261014c (the held lock is released before exiting).
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/gated_pd.log
LOCK=$A/.gated_drt_gate.lock
DM=dm_grid3665x2900_r3
SA2=sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25_r5
V4=vc4_corr3800x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong_r1
say () { echo "$(date -Is) $*" | tee -a $LOG >> $A/dse_pd.log; }
stop_req () { [ -e $A/.abort_sequence_20261014c ]; }
ended () { grep -q -E "(SIGNOFF (CLEAN|FAILED) $1|STOP $1)" $LOG; }
held=0
release () { [ $held = 1 ] && rmdir $LOCK 2>/dev/null && say "NOTE heavy-phase sequence c released the detailed-routing slot lock"; held=0; }
trap release EXIT
say "NOTE heavy-phase sequence c: resuming $SA2 now (shortest first; $DM is in its light phases)"
cd $A && ( G5_UNLIMITED_LATE_PHASE=1 bash run_gated_resume.sh soc_sa2_4kb $SA2 config_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25.json "planned hold after p2 (STOP_AFTER=p2) while the DM_VC4 replay held the WSL memory" drt ) &
# wait for SA2's detailed routing to start (or the run to end early), then take the slot lock once it is free
until grep -q "$SA2 detailed routing start" $LOG || ended $SA2; do sleep 20; done
if ! ended $SA2; then
    until mkdir $LOCK 2>/dev/null; do sleep 5; done
    held=1
    say "NOTE heavy-phase sequence c holds the detailed-routing slot lock while $SA2 routes and signs off ($DM waits at its gate)"
fi
until ended $SA2; do stop_req && { say "NOTE heavy-phase sequence c aborted while $SA2 runs"; exit 0; }; sleep 60; done
release
say "NOTE heavy-phase sequence c: $SA2 ended; $DM may enter detailed routing"
until ended $DM; do stop_req && { say "NOTE heavy-phase sequence c aborted while waiting for $DM"; exit 0; }; sleep 60; done
say "NOTE heavy-phase sequence c: $DM ended; resuming $V4 (detailed routing + sign-off)"
stop_req && { say "NOTE heavy-phase sequence c aborted before $V4"; exit 0; }
cd $A && G5_UNLIMITED_LATE_PHASE=1 G5_ANT_ROUND_RULES=1 bash run_gated_resume.sh soc_vc4_4kb $V4 config_corr3800x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong.json "planned hold after p2 (STOP_AFTER=p2) while the DM_VC4 replay held the WSL memory" drt
until ended $V4; do sleep 60; done
wait
say "NOTE heavy-phase sequence c done"
