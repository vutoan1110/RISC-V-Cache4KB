#!/usr/bin/env bash
# 2026-10-14 18:20 (+07), state found after the previous session ended:
#  - dm_grid3665x2900_r3 (DM acceptance run) ended in P2: the OpenLane process segfaulted right after step 40
#    (CheckAntennas itself completed, report complete), so STAMidPNR-3 never ran and the p2 gate read MISSING data.
#    Rule Q: the acceptance run is ONE complete flow from step 1 -> new tag dm_grid3665x2900_r4 (same recipe
#    config_R14_FINAL.json, same default gates, same G5_UNLIMITED_LATE_PHASE=1).
#  - sa2_..._cts25_r5 (SA2 E1, development run): detailed routing done, then step 51 Odb.ReportDisconnectedPins was
#    interrupted by SIGSEGV, so no sign-off data (SIGNOFF FAILED line). Rule Q (revised 2026-10-14): a development run may
#    be resumed from the failing step: the crashed step directory is renamed and the sign-off part re-runs from step 51.
#  - sequence c resumed V4 (vc4_corr3800x3400_..._antcong_r1) at 10:33 UTC because r3 had ended; V4 is in detailed
#    routing and its sign-off part follows without any memory gate. V4 is not stopped (owner decision only).
# Measured peaks (process_stats.json of r14F_A / SA2 ecomaxmin_r2): detailed routing ~10 GiB (V2 12.4 GB), Magic WriteLEF
# 12-13 GiB, KLayout XOR 7-8 GiB, KLayout DRC 8 GiB, Magic SPICE extraction 4-5 GiB: a sign-off part next to a detailed
# routing does not fit in the 24 GB VM, so both waiting jobs wait for V4.
# Order (owner: shorter tasks first):
#   1. start DM r4 now: P1 / P2 are light next to V4's detailed routing; as soon as its queue has started (the queue
#      removes stale slot locks at start) take the detailed-routing slot lock and HOLD it, so DM r4 waits at its
#      detailed-routing gate;
#   2. when V4 has ended: SA2 r5 sign-off part from step 51 (~2 h), lock still held;
#   3. then release the lock: DM r4 detailed routing + sign-off (~3 h).
# Log-based waits only (no pgrep -f). Cooperative stop: asic/.abort_sequence_20261014d (the held lock is released).
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/gated_pd.log
LOCK=$A/.gated_drt_gate.lock
DM=dm_grid3665x2900_r4
SA2=sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25_r5
SA2CFG=config_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25.json
V4=vc4_corr3800x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong_r1
say () { echo "$(date -Is) $*" | tee -a $LOG >> $A/dse_pd.log; }
stop_req () { [ -e $A/.abort_sequence_20261014d ]; }
ended () { grep -q -E "(SIGNOFF (CLEAN|FAILED) $1|STOP $1)" $LOG; }
held=0
release () { [ $held = 1 ] && rmdir $LOCK 2>/dev/null && say "NOTE heavy-phase sequence d released the detailed-routing slot lock"; held=0; }
trap release EXIT
say "NOTE heavy-phase sequence d: dm_grid3665x2900_r3 ended in P2 (OpenLane process segfault after step 40; no design or gate fault) -> acceptance run $DM; $SA2 step 51 SIGSEGV -> sign-off part re-run from step 51 after $V4 (sign-off next to a detailed routing exceeds the 24 GB VM)"
( cd $A && G5_UNLIMITED_LATE_PHASE=1 ITEMS="soc_dm_4kb:$DM:config_R14_FINAL.json" bash run_gated_pd.sh ) &
q=$!
until grep -q "gated queue start .*$DM" $LOG; do sleep 2; done
sleep 5
until mkdir $LOCK 2>/dev/null; do sleep 1; done
held=1
say "NOTE heavy-phase sequence d holds the detailed-routing slot lock: $DM waits at its detailed-routing gate until $V4 and the $SA2 sign-off part have ended"
until ended $V4; do stop_req && { say "NOTE heavy-phase sequence d aborted while $V4 runs"; exit 0; }; sleep 60; done
stop_req && { say "NOTE heavy-phase sequence d aborted before the $SA2 sign-off part"; exit 0; }
R=$A/soc_sa2_4kb/runs/$SA2
if [ -d $R/51-odb-reportdisconnectedpins ] && [ ! -e $R/crashed-51-odb-reportdisconnectedpins ]; then
    mv $R/51-odb-reportdisconnectedpins $R/crashed-51-odb-reportdisconnectedpins
fi
say "NOTE heavy-phase sequence d: $V4 ended; $SA2 sign-off part from step 51 (Odb.ReportDisconnectedPins)"
cd $A && G5_UNLIMITED_LATE_PHASE=1 bash run_gated_resume.sh soc_sa2_4kb $SA2 $SA2CFG "random SIGSEGV in step 51 Odb.ReportDisconnectedPins; development run resumed from the failing step (rule Q revised 2026-10-14)" step:Odb.ReportDisconnectedPins
release
say "NOTE heavy-phase sequence d: $SA2 sign-off part ended; $DM may enter detailed routing"
wait $q
say "NOTE heavy-phase sequence d done"
