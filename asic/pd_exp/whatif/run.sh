#!/usr/bin/env bash
# FLOW_JOURNAL Incident 93: what-if STA on final3_A at max_ss; usage: run.sh <cuts file> <tag>
cd /mnt/e/Projects/RISCV-research/asic
export SQ_OUT=/tmp SQ_CUTS=/mnt/e/Projects/RISCV-research/asic/pd_exp/whatif/$1
bash sta_query/sta_query.sh soc_dm_4kb/runs/final3_A/56-openroad-stapostpnr max_ss_100C_1v60 sta_query/q_whatif.tcl > pd_exp/whatif/$2.rpt 2>&1
echo "rc=$?"; grep -a "WHATIF" pd_exp/whatif/$2.rpt; grep -a -m1 "slack (VIOLATED)" pd_exp/whatif/$2.rpt; grep -a -A3 "^Endpoint " pd_exp/whatif/$2.rpt | tail -3
