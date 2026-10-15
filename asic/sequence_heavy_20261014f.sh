#!/usr/bin/env bash
# 2026-10-14 22:10 (+07). PD on RTL 6c4ccffd (owner). SA2 acceptance run on 6c4ccffd with the signed SA2 recipe as ONE
# flow (E0): sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rtl6c4c_r1 =
# soc_sa2_4kb/config_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rtl6c4c.json (E0 with VERILOG_FILES on
# snapshot rtl_rfbht = 6c4ccffd + the SA2 wrappers frozen into it), launch thresholds as declared for E1
# (P2_MIN_SETUP=0 P2_MIN_HOLD=-0.5 P2_INITIAL_GRT_FALLBACK=1 G5_UNLIMITED_LATE_PHASE=1).
#   1. wait until the old-RTL sa2_..._cts25_r5 sign-off part has ended (sequence d logs it) and sequence e has
#      released the detailed-routing slot lock (its lines), so no slot lock of d / e is left to race with;
#   2. start the SA2 queue (P1 / P2 are light next to the DM detailed routing);
#   3. one heavy phase at a time: as soon as dm_grid3665x2900_rtl6c4c_r1 has started its detailed routing (its gate
#      releases the slot lock 240 s later), take the lock and hold it until the DM run has ended (sign-off included),
#      so the SA2 detailed routing starts only then.
# Log-based waits only. Cooperative stop: asic/.abort_sequence_20261014f (the held lock is released).
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/gated_pd.log
LOCK=$A/.gated_drt_gate.lock
DM=dm_grid3665x2900_rtl6c4c_r1
SA2=sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rtl6c4c_r1
OLD=sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25_r5
say () { echo "$(date -Is) $*" | tee -a $LOG >> $A/dse_pd.log; }
stop_req () { [ -e $A/.abort_sequence_20261014f ]; }
ended () { grep -q -E "(SIGNOFF (CLEAN|FAILED) $1|STOP $1)" $LOG; }
held=0
release () { [ $held = 1 ] && rmdir $LOCK 2>/dev/null && say "NOTE heavy-phase sequence f released the detailed-routing slot lock"; held=0; }
trap release EXIT
say "NOTE heavy-phase sequence f: SA2 acceptance run on RTL 6c4ccffd ($SA2) queued after the old-RTL $OLD sign-off part; DM and SA2 heavy phases one at a time"
until grep -q "heavy-phase sequence d: $OLD sign-off part ended" $LOG && grep -q "heavy-phase sequence e: $DM may enter detailed routing" $LOG; do
    stop_req && { say "NOTE heavy-phase sequence f aborted before $SA2 started"; exit 0; }
    sleep 30
done
( cd $A && G5_UNLIMITED_LATE_PHASE=1 P2_MIN_SETUP=0 P2_MIN_HOLD=-0.5 P2_INITIAL_GRT_FALLBACK=1 \
    ITEMS="soc_sa2_4kb:$SA2:config_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rtl6c4c.json" bash run_gated_pd.sh ) &
q=$!
until grep -q "$DM P3 detailed routing start" $LOG || ended $DM; do sleep 5; done
if ! ended $DM; then
    until mkdir $LOCK 2>/dev/null || ended $DM; do sleep 1; done
    if ! ended $DM; then
        held=1
        say "NOTE heavy-phase sequence f holds the detailed-routing slot lock until $DM has ended ($SA2 waits at its gate)"
        until ended $DM; do stop_req && { say "NOTE heavy-phase sequence f aborted while $DM runs"; exit 0; }; sleep 60; done
        release
    fi
fi
say "NOTE heavy-phase sequence f: $DM ended; $SA2 may enter detailed routing"
wait $q
say "NOTE heavy-phase sequence f done"
