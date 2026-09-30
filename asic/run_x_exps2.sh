#!/usr/bin/env bash
# FLOW_JOURNAL Incident 91: PD-only exploration run into a fresh tag, through STAPostPNR, starting from
# any existing run's step state (read only).  run_x_exps.sh took states from final_A only; this copy
# takes a path relative to soc_dm_4kb/runs/ (e.g. x2_rc2/40-openroad-repairdesignpostgrt/state_out.json).
#   bash run_x_exps2.sh <tag> <config> <state path under runs/> <--from step> [--to step]
# Cooperative stop: touch asic/.abort_x_exps
A=$(cd "$(dirname "$0")" && pwd)
tag=$1 cfg=$2 st=$3 frm=$4 to=${5:-OpenROAD.STAPostPNR}
S=$A/soc_dm_4kb/runs/$st
[ -f "$S" ] || { echo "no state $S"; exit 2; }
[ -e "$A/.abort_x_exps" ] && { echo "$(date -Is) abort before $tag" >> $A/x_exps.log; exit 0; }
while [ "$(free -m | awk '/Mem/{print $7}')" -lt 12000 ]; do sleep 60; done
echo "$(date -Is) start $tag ($cfg from $frm to $to, state $st) avail $(free -m | awk '/Mem/{print $7}') MB" >> $A/x_exps.log
CONFIG=$cfg bash "$A/run_pd_mk.sh" soc_dm_4kb "$tag" --with-initial-state "$S" \
    --from "$frm" --to "$to" > "$A/$tag.log" 2>&1
echo "$(date -Is) end $tag rc=$?" >> $A/x_exps.log
