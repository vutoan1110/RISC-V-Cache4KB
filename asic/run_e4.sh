#!/usr/bin/env bash
# FLOW_JOURNAL Incident 93: full flow of config_E4 (AREA 3 + REMOVE_BUFFERS on RTL r12b), tag x_E4_A.
# Cooperative stop: touch asic/.abort_x_exps
A=/mnt/e/Projects/RISCV-research/asic
[ -e $A/.abort_x_exps ] && exit 0
while [ "$(free -m | awk '/Mem/{print $7}')" -lt 12000 ]; do [ -e $A/.abort_x_exps ] && exit 0; sleep 60; done
echo "$(date -Is) start x_E4_A (config_E4.json, full flow) avail $(free -m | awk '/Mem/{print $7}') MB" >> $A/x_exps.log
cd $A && CONFIG=config_E4.json bash run_pd_mk.sh soc_dm_4kb x_E4_A > x_E4_A.log 2>&1
echo "$(date -Is) end x_E4_A rc=$?" >> $A/x_exps.log
