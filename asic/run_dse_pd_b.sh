#!/usr/bin/env bash
# FLOW_JOURNAL Incident 96: the B runs of the SA2 / DM_VC4 builds on the wide floorplan (config_wide.json), the
# second execution of each full flow. A B run starts only when (1) its A run has passed detailed routing (a step
# directory after *-openroad-detailedrouting exists), so two detailed routings of ~11 GB never overlap with a
# third flow; (2) at least 14 GB are free; (3) at least 45 minutes have passed since the previous B start.
# Cooperative stop: touch asic/.abort_dse_pd
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/dse_pd.log
cd $A
aborted () { [ -e $A/.abort_dse_pd ]; }
past_drt () {   # <design dir> <tag>: 0 when a step after detailed routing exists
    local d=$A/$1/runs/$2 n
    n=$(ls "$d" 2>/dev/null | grep -E '^[0-9]+-openroad-detailedrouting$' | tail -1 | cut -d- -f1)
    [ -n "$n" ] && ls "$d" | grep -qE "^0*$((10#$n + 1))-|^$((10#$n + 1))-"
}
echo "$(date -Is) B queue start" >> $LOG
last=0
for item in soc_sa2_4kb:sa2F_A:sa2F_B soc_vc4_4kb:vc4F_A:vc4F_B; do
    IFS=: read -r des ta tb <<< "$item"
    while :; do
        aborted && { echo "$(date -Is) abort before $tb" >> $LOG; wait; exit 0; }
        now=$(date +%s)
        if past_drt "$des" "$ta" && [ "$(free -m | awk '/Mem/{print $7}')" -ge 14000 ] && [ $((now - last)) -ge 2700 ]; then
            break
        fi
        sleep 60
    done
    echo "$(date -Is) start $tb wide ($des/config_wide.json, full flow, fresh) avail $(free -m | awk '/Mem/{print $7}') MB" >> $LOG
    ( CONFIG=config_wide.json bash run_pd_mk.sh "$des" "$tb" > "$A/$tb.log" 2>&1
      echo "$(date -Is) end $tb wide last step $(ls $A/$des/runs/$tb | grep -E '^[0-9]+-' | tail -1)" >> $LOG ) &
    last=$(date +%s)
done
wait
echo "$(date -Is) B queue done" >> $LOG
