#!/usr/bin/env bash
# FLOW_JOURNAL Incident 95: the double-executed FULL flow (synthesis .. signoff) of the chosen R14 PD config,
# config_R14_FINAL.json (= the knobs of r14_E16: E10 + placement density 55 + hold margins 0.03 / RCX hold ECO
# 0.02 + CTS sink clustering 8), RTL snapshot rtl_r14. Two independent runs, r14F_A and r14F_B; B starts 45
# minutes after A (and only with >= 14 GB free) so their detailed-routing and signoff peaks do not coincide.
# The flow is deterministic, so A must reproduce E16 and B must reproduce A.
# Cooperative stop: touch asic/.abort_r14_final
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/r14_final_pd.log
cd $A
one () {   # <tag>
    [ -e $A/.abort_r14_final ] && { echo "$(date -Is) abort before $1" >> $LOG; return; }
    while [ "$(free -m | awk '/Mem/{print $7}')" -lt 14000 ]; do
        [ -e $A/.abort_r14_final ] && { echo "$(date -Is) abort while waiting for $1" >> $LOG; return; }
        sleep 60
    done
    echo "$(date -Is) start $1 (config_R14_FINAL.json, full flow) avail $(free -m | awk '/Mem/{print $7}') MB" >> $LOG
    CONFIG=config_R14_FINAL.json bash run_pd_mk.sh soc_dm_4kb "$1" > "$A/$1.log" 2>&1
    echo "$(date -Is) end $1 rc=$? last step $(ls $A/soc_dm_4kb/runs/$1 | grep -E '^[0-9]+-' | tail -1)" >> $LOG
}
one r14F_A &
sleep 2700
one r14F_B &
wait
