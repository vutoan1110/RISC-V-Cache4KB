#!/usr/bin/env bash
# FLOW_JOURNAL Incident 91: PD-only exploration runs, one after another, each from a signed-off
# final_A step state (read only) into a fresh tag, through STAPostPNR.
#   bash run_x_exps.sh <tag> <config> <initial state_out.json (relative to runs/final_A)> <--from step>
# Cooperative stop: touch asic/.abort_x_exps
A=$(cd "$(dirname "$0")" && pwd)
tag=$1 cfg=$2 st=$3 frm=$4
S=$A/soc_dm_4kb/runs/final_A/$st
[ -f "$S" ] || { echo "no state $S"; exit 2; }
[ -e "$A/.abort_x_exps" ] && { echo "$(date -Is) abort before $tag" >> $A/x_exps.log; exit 0; }
while [ "$(free -m | awk '/Mem/{print $7}')" -lt 12000 ]; do sleep 60; done
echo "$(date -Is) start $tag ($cfg from $frm, state $st) avail $(free -m | awk '/Mem/{print $7}') MB" >> $A/x_exps.log
CONFIG=$cfg bash "$A/run_pd_mk.sh" soc_dm_4kb "$tag" --with-initial-state "$S" \
    --from "$frm" --to OpenROAD.STAPostPNR > "$A/$tag.log" 2>&1
echo "$(date -Is) end $tag rc=$?" >> $A/x_exps.log
