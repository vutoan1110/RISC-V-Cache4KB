#!/usr/bin/env bash
# One queued PD run (FLOW_JOURNAL Incident 76): waits for RAM, then runs.
#   bash run_pd_one.sh <tag> <config> <min_avail_MB> [openlane args...]
# rc is captured right after the flow. Cooperative stop: touch asic/.abort_r10_pd
set -u
cd "$(dirname "$0")"
LOG=r10_pd.log
tag=$1 cfg=$2 mem=$3; shift 3
avail() { free -m | awk '/Mem/{print $7}'; }
while [ "$(avail)" -lt "$mem" ]; do
  [ -e .abort_r10_pd ] && { echo "$(date -Is) abort while waiting for $tag" >> $LOG; exit 0; }
  sleep 60
done
[ -e .abort_r10_pd ] && { echo "$(date -Is) abort before $tag" >> $LOG; exit 0; }
echo "$(date -Is) start $tag ($cfg $*) avail $(avail) MB" >> $LOG
CONFIG=$cfg bash run_pd.sh soc_dm_4kb "$tag" "$@" > "$tag.log" 2>&1
rc=$?
echo "$(date -Is) end $tag rc=$rc" >> $LOG
