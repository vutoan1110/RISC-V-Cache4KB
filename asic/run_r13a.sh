#!/usr/bin/env bash
# FLOW_JOURNAL Incident 93 (Task B): full flow of the cycle-exact R13a RTL with the final3 PD knobs, after the
# E1/E2 PD experiments (one heavy flow at a time). Cooperative stop: touch asic/.abort_x_exps
A=/mnt/e/Projects/RISCV-research/asic
until grep -q "end x_E2" $A/x_exps.log 2>/dev/null; do [ -e $A/.abort_x_exps ] && exit 0; sleep 60; done
[ -e $A/.abort_x_exps ] && exit 0
while [ "$(free -m | awk '/Mem/{print $7}')" -lt 14000 ]; do sleep 60; done
echo "$(date -Is) start r13a_A (config_R13a.json, full flow)" >> $A/x_exps.log
cd $A && CONFIG=config_R13a.json bash run_pd_mk.sh soc_dm_4kb r13a_A > r13a_A.log 2>&1
echo "$(date -Is) end r13a_A rc=$?" >> $A/x_exps.log
