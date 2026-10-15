#!/usr/bin/env bash
# 2026-10-15 07:40 (+07). PD on RTL 6c4ccffd, second attempts (rule Q: fresh tags, full flows from step 1, thresholds
# declared at launch):
#  - dm_grid3665x2900_rtl6c4c_r1 stopped at the p1 gate: the 6c4ccffd netlist (71,006 cells, +565 vs R14) leaves the
#    half-cycle RAM bank -> D$ refill path at +0.307 ns after CTS (R14: worst path +2.164 ns elsewhere), below the
#    P1_MIN_SETUP margin of +0.5 ns. r2 declares P1_MIN_SETUP=0 and P2_MIN_SETUP=0 at launch; the sign-off gate
#    (setup >= 0 at tt / ff, hold >= 0 at every corner) decides.
#  - sa2_..._eco2_rtl6c4c_r1 stopped in step 16: the 6c4ccffd netlist names the cache macros
#    u_soc.u_{i,d}cache.genblk1.g_dse.* (R14: ...g_dse.*). r2 uses macro_placement_u2fg_rtl6c4c.cfg (names only;
#    coordinates equal; checked 16/16 against the netlist). Thresholds declared as for E1 / E0, plus P1_MIN_SETUP=0.
# One heavy phase at a time in the 24 GB VM: whichever run starts its detailed routing first keeps the slot (this script
# takes the slot lock after that run's own 240 s hold and keeps it until that run has ended, sign-off included).
# Log-based waits only. Cooperative stop: asic/.abort_sequence_20261015g (the held lock is released).
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/gated_pd.log
LOCK=$A/.gated_drt_gate.lock
DM=dm_grid3665x2900_rtl6c4c_r2
SA2=sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rtl6c4c_r2
say () { echo "$(date -Is) $*" | tee -a $LOG >> $A/dse_pd.log; }
stop_req () { [ -e $A/.abort_sequence_20261015g ]; }
ended () { grep -q -E "(SIGNOFF (CLEAN|FAILED) $1|STOP $1)" $LOG; }
drt_started () { grep -q "$1 P3 detailed routing start" $LOG; }
held=0
release () { [ $held = 1 ] && rmdir $LOCK 2>/dev/null && say "NOTE heavy-phase sequence g released the detailed-routing slot lock"; held=0; }
trap release EXIT
say "NOTE heavy-phase sequence g: RTL 6c4ccffd second attempts $DM (P1/P2 setup >= 0 declared) and $SA2 (renamed cache macros in the placement file)"
( cd $A && G5_UNLIMITED_LATE_PHASE=1 P1_MIN_SETUP=0 P2_MIN_SETUP=0 \
    ITEMS="soc_dm_4kb:$DM:config_R14_FINAL_rtl6c4c.json" bash run_gated_pd.sh ) &
q1=$!
until grep -q "gated queue start .*$DM" $LOG; do sleep 2; done
( cd $A && G5_UNLIMITED_LATE_PHASE=1 P1_MIN_SETUP=0 P2_MIN_SETUP=0 P2_MIN_HOLD=-0.5 P2_INITIAL_GRT_FALLBACK=1 \
    ITEMS="soc_sa2_4kb:$SA2:config_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rtl6c4c.json" bash run_gated_pd.sh ) &
q2=$!
first=""
until [ -n "$first" ]; do
    stop_req && { say "NOTE heavy-phase sequence g aborted before any detailed routing"; exit 0; }
    if drt_started $DM; then first=$DM; other=$SA2
    elif drt_started $SA2; then first=$SA2; other=$DM
    elif ended $DM && ended $SA2; then first=none
    fi
    [ -z "$first" ] && sleep 5
done
if [ "$first" != none ] && ! ended $other; then
    until mkdir $LOCK 2>/dev/null || ended $first; do sleep 1; done
    if ! ended $first; then
        held=1
        say "NOTE heavy-phase sequence g holds the detailed-routing slot lock until $first has ended ($other waits at its gate)"
        until ended $first; do stop_req && { say "NOTE heavy-phase sequence g aborted while $first runs"; exit 0; }; sleep 60; done
    fi
    release
    say "NOTE heavy-phase sequence g: $first ended; $other may enter detailed routing"
fi
wait $q1 $q2
say "NOTE heavy-phase sequence g done"
