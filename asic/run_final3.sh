#!/usr/bin/env bash
# FLOW_JOURNAL Incident 91: the double-executed FULL flow (step 1 .. signoff) of the chosen PD config,
# two independent runs, one after the other.  bash run_final3.sh <config> <tagA> <tagB>
# Cooperative stop: touch asic/.abort_final3
set -u
cd "$(dirname "$0")"
LOG=final3_pd.log
cfg=$1; shift
# wait for the rejected final2_A to finish its signoff steps (one heavy flow at a time)
until grep -q "end final2_A" final2_pd.log 2>/dev/null; do [ -e .abort_final3 ] && exit 0; sleep 60; done
for tag in "$@"; do
  [ -e .abort_final3 ] && { echo "$(date -Is) abort before $tag" >> $LOG; exit 0; }
  while [ "$(free -m | awk '/Mem/{print $7}')" -lt 14000 ]; do
    [ -e .abort_final3 ] && { echo "$(date -Is) abort while waiting for $tag" >> $LOG; exit 0; }
    sleep 60
  done
  echo "$(date -Is) start $tag ($cfg) avail $(free -m | awk '/Mem/{print $7}') MB" >> $LOG
  CONFIG=$cfg bash run_pd_mk.sh soc_dm_4kb "$tag" > "$tag.log" 2>&1
  echo "$(date -Is) end $tag rc=$?" >> $LOG
done
