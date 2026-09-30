#!/usr/bin/env bash
# FLOW_JOURNAL Incident 93 (Task B): full flow of the R13b RTL (R13a + two-stage multiplier) with the final3 PD knobs, after the
# E1/E2 PD experiments (one heavy flow at a time). Cooperative stop: touch asic/.abort_x_exps
A=/mnt/e/Projects/RISCV-research/asic
until grep -q "end r13a_A" $A/x_exps.log 2>/dev/null; do [ -e $A/.abort_x_exps ] && exit 0; sleep 60; done
[ -e $A/.abort_x_exps ] && exit 0
while [ "$(free -m | awk '/Mem/{print $7}')" -lt 14000 ]; do sleep 60; done
echo "$(date -Is) start r13b_A (config_R13b.json, full flow)" >> $A/x_exps.log
cd $A && CONFIG=config_R13b.json bash run_pd_mk.sh soc_dm_4kb r13b_A > r13b_A.log 2>&1
echo "$(date -Is) end r13b_A rc=$?" >> $A/x_exps.log
