#!/usr/bin/env bash
# 2026-10-14 21:20 (+07). Owner decision: PD on the newest RTL 6c4ccffd. The acceptance run dm_grid3665x2900_r4 (rtl_r14
# snapshot) was stopped while it waited at its detailed-routing gate (cooperative flag, 14:11 UTC). New DM acceptance run:
#   dm_grid3665x2900_rtl6c4c_r1 = config_R14_FINAL_rtl6c4c.json (the signed DM recipe; VERILOG_FILES read
#   asic/snapshots/rtl_rfbht = manifest 6c4ccffd, checked byte-identical to the live tree), full flow from step 1.
# Its P1 / P2 are light and start now, next to the sa2_..._cts25_r5 sign-off part (sequence d, peak ~13 GB). The new
# queue removes slot locks older than 10 minutes when it starts, i.e. the lock sequence d holds; this script takes the
# lock again at once, so the DM detailed routing still waits until the SA2 sign-off part has ended (sequence d removes
# the lock then and logs "... sign-off part ended"). The SA2 acceptance run on 6c4ccffd is queued separately after the
# E1 / ecomaxmin comparison. Log-based waits only. Cooperative stop: asic/.abort_sequence_20261014e.
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/gated_pd.log
LOCK=$A/.gated_drt_gate.lock
DM=dm_grid3665x2900_rtl6c4c_r1
SA2=sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25_r5
say () { echo "$(date -Is) $*" | tee -a $LOG >> $A/dse_pd.log; }
stop_req () { [ -e $A/.abort_sequence_20261014e ]; }
held=0
release () { [ $held = 1 ] && rmdir $LOCK 2>/dev/null && say "NOTE heavy-phase sequence e released the detailed-routing slot lock"; held=0; }
trap release EXIT
sa2_done () { grep -q "heavy-phase sequence d: $SA2 sign-off part ended" $LOG; }
say "NOTE heavy-phase sequence e: owner decision 2026-10-14, PD on RTL 6c4ccffd; dm_grid3665x2900_r4 (rtl_r14) stopped at its gate; starting $DM (config_R14_FINAL_rtl6c4c.json, snapshot rtl_rfbht = 6c4ccffd)"
( cd $A && G5_UNLIMITED_LATE_PHASE=1 ITEMS="soc_dm_4kb:$DM:config_R14_FINAL_rtl6c4c.json" bash run_gated_pd.sh ) &
q=$!
until grep -q "gated queue start .*$DM" $LOG; do sleep 1; done
if ! sa2_done; then
    until mkdir $LOCK 2>/dev/null; do sleep 1; done
    held=1
    say "NOTE heavy-phase sequence e holds the detailed-routing slot lock until the $SA2 sign-off part has ended"
    until sa2_done; do stop_req && { say "NOTE heavy-phase sequence e aborted while the SA2 sign-off part runs"; exit 0; }; sleep 30; done
    release
fi
say "NOTE heavy-phase sequence e: $DM may enter detailed routing"
wait $q
say "NOTE heavy-phase sequence e done"
