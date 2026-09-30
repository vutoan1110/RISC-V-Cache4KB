#!/usr/bin/env bash
# FLOW_JOURNAL Incident 91: the double-executed FULL flow (step 1 .. signoff) of the chosen PD config,
# two independent runs, one after the other.  bash run_final2.sh <config> <tagA> <tagB>
# Cooperative stop: touch asic/.abort_final2
set -u
cd "$(dirname "$0")"
LOG=final2_pd.log
cfg=$1; shift
for tag in "$@"; do
  [ -e .abort_final2 ] && { echo "$(date -Is) abort before $tag" >> $LOG; exit 0; }
  while [ "$(free -m | awk '/Mem/{print $7}')" -lt 14000 ]; do
    [ -e .abort_final2 ] && { echo "$(date -Is) abort while waiting for $tag" >> $LOG; exit 0; }
    sleep 60
  done
  echo "$(date -Is) start $tag ($cfg) avail $(free -m | awk '/Mem/{print $7}') MB" >> $LOG
  CONFIG=$cfg bash run_pd_mk.sh soc_dm_4kb "$tag" > "$tag.log" 2>&1
  echo "$(date -Is) end $tag rc=$?" >> $LOG
done
