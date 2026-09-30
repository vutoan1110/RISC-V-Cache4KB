#!/usr/bin/env bash
# Antenna experiments (FLOW_JOURNAL Incident 73), one after another, each from
# r7r8_358c step 37 (after ResizerTimingPostCTS + STA) through STAPostPNR.
# Each waits for WSL available memory >= 6 GB first (EQY replay holds ~15 GB).
#   bash run_antenna_exps.sh AN1 AN2 [AN3]
A=$(cd "$(dirname "$0")" && pwd)
S=$A/soc_dm_4kb/runs/r7r8_358c/37-openroad-stamidpnr-2/state_out.json
for n in "$@"; do
  [ -f "$A/runs_antenna.abort" ] && { echo "$(date -Is) abort file, stop"; break; }
  while [ "$(free -m | awk '/Mem/{print $7}')" -lt 6000 ]; do sleep 60; done
  echo "$(date -Is) start $n (avail $(free -m | awk '/Mem/{print $7}') MB)"
  CONFIG=config_$n.json bash "$A/run_pd.sh" soc_dm_4kb "ant_$n" --with-initial-state "$S" \
      --from OpenROAD.GlobalRouting --to OpenROAD.STAPostPNR > "$A/antenna_$n.log" 2>&1
  echo "$(date -Is) end $n rc=$?"
done
