#!/usr/bin/env bash
# FLOW_JOURNAL Incident 93 (Task A): the stock OpenLane Yosys.EQY step on the final3 netlist, alone, with GNU grep
# on PATH (run_pd_mk2.sh). Fresh tag; final3_A's post-LVS state is only read. Cooperative stop: touch asic/.abort_x_exps
A=$(cd "$(dirname "$0")" && pwd)
S=$A/soc_dm_4kb/runs/final3_A/71-checker-lvs/state_out.json
[ -e "$A/.abort_x_exps" ] && exit 0
echo "$(date -Is) start final3_eqy (Yosys.EQY only, grep on PATH) avail $(free -m | awk '/Mem/{print $7}') MB" >> $A/x_exps.log
CONFIG=config_FINAL3.json bash "$A/run_pd_mk2.sh" soc_dm_4kb final3_eqy --with-initial-state "$S" \
    --from Yosys.EQY --to Yosys.EQY > "$A/final3_eqy.log" 2>&1
echo "$(date -Is) end final3_eqy rc=$?" >> $A/x_exps.log
