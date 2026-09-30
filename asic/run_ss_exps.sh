#!/usr/bin/env bash
# ss-corner PD experiments (FLOW_JOURNAL Incident 74), one after another, full
# flow from step 1 to STAPostPNR on the frozen RTL. Each waits for WSL
# available memory >= 9 GB (EQY replay and antenna experiments share the box).
#   bash run_ss_exps.sh SS1 SS2
A=$(cd "$(dirname "$0")" && pwd)
for n in "$@"; do
  [ -f "$A/runs_ss.abort" ] && { echo "$(date -Is) abort file, stop"; break; }
  while [ "$(free -m | awk '/Mem/{print $7}')" -lt 9000 ]; do sleep 60; done
  echo "$(date -Is) start $n (avail $(free -m | awk '/Mem/{print $7}') MB)"
  CONFIG=config_$n.json bash "$A/run_pd.sh" soc_dm_4kb "ss_$n" --to OpenROAD.STAPostPNR > "$A/ss_$n.log" 2>&1
  echo "$(date -Is) end $n rc=$?"
done
