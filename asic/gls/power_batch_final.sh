#!/usr/bin/env bash
# Activity-based power of the final netlist (FLOW_JOURNAL Incident 83):
# vectorless first (must reproduce the flow's power.rpt), then one SAIF per kernel.
set -u
R=/mnt/e/Projects/RISCV-research
STEP=$R/asic/soc_dm_4kb/runs/final_A/57-openroad-stapostpnr
O=$R/results/gls_power_final_A
C=nom_tt_025C_1v80
bash $R/asic/gls/sta_power.sh $STEP "" $C > $O/vectorless.power.rpt 2>&1; echo "vectorless rc=$?"
for k in crc32 depthconv edn fdct huffbench insertsort matmult md5sum mont64 sha256 tarfind wikisort; do
  [ -e $R/asic/.abort_final_pd ] && { echo "abort"; exit 0; }
  while [ "$(free -m | awk '/Mem/{print $7}')" -lt 5000 ]; do sleep 60; done
  bash $R/asic/gls/sta_power.sh $STEP $O/$k.pins.saif $C > $O/$k.power.rpt 2>&1
  echo "$k rc=$? $(grep -m1 '^Total' $O/$k.power.rpt | tr -s ' ')"
done
