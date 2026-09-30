#!/usr/bin/env bash
# R14 (RAM16K_CHANGES.md): full OpenLane flow of the 16 KiB-RAM design, config_R14.json, tag $1 (r14_A / r14_B).
# Random crashes are resumed by hand from the failed step (run_resume_retry.sh); see FLOW_JOURNAL.
# Cooperative stop: touch asic/.abort_x_exps
A=/mnt/e/Projects/RISCV-research/asic
tag=${1:-r14_A}
[ -e $A/.abort_x_exps ] && exit 0
while [ "$(free -m | awk '/Mem/{print $7}')" -lt 12000 ]; do [ -e $A/.abort_x_exps ] && exit 0; sleep 60; done
echo "$(date -Is) start $tag (config_R14.json, full flow) avail $(free -m | awk '/Mem/{print $7}') MB" >> $A/x_exps.log
cd $A && CONFIG=config_R14.json bash run_pd_mk.sh soc_dm_4kb $tag > $A/$tag.log 2>&1
echo "$(date -Is) end $tag rc=$?" >> $A/x_exps.log
