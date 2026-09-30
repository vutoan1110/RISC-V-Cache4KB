#!/usr/bin/env bash
# R10 PD runs (FLOW_JOURNAL Incident 76).
#   R10A: signoff candidate, full classic flow (DRC/LVS/EQY included).
#   R10B: experiment (setup margins), to STAPostPNR.
# rc is captured on the line right after the flow (the Incident 74 runners
# printed $? of $(date) and so always said rc=0). Cooperative stop:
#   touch asic/.abort_r10_pd   (checked before each run and while waiting for RAM)
set -u
cd "$(dirname "$0")"
LOG=r10_pd.log
avail() { free -m | awk '/Mem/{print $7}'; }
run() { # tag config min_avail_MB [openlane args...]
  local tag=$1 cfg=$2 mem=$3; shift 3
  while [ "$(avail)" -lt "$mem" ]; do
    [ -e .abort_r10_pd ] && { echo "$(date -Is) abort while waiting for $tag" >> $LOG; return; }
    sleep 60
  done
  [ -e .abort_r10_pd ] && { echo "$(date -Is) abort before $tag" >> $LOG; return; }
  echo "$(date -Is) start $tag ($cfg $*) avail $(avail) MB" >> $LOG
  CONFIG=$cfg bash run_pd.sh soc_dm_4kb "$tag" "$@" > "$tag.log" 2>&1
  local rc=$?
  echo "$(date -Is) end $tag rc=$rc" >> $LOG
}
run r10A config_R10A.json 12000 &
sleep 1800
run r10B config_R10B.json 14000 --to OpenROAD.STAPostPNR &
wait
echo "$(date -Is) runner done" >> $LOG
