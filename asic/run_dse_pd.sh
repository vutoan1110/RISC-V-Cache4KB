#!/usr/bin/env bash
# SA2 / DM_VC4 ASIC builds (2026-09-30, FLOW_JOURNAL: SA2 and DM_VC4 ASIC builds): the double-executed
# FULL flow (synthesis .. signoff) of each, with the chosen DM R14 knobs (config.json in each design dir =
# config_R14_FINAL.json except the cache organisation). Queue: sa2F_A, vc4F_A, sa2F_B, vc4F_B.
# At most two OpenLane flows on the machine at once (the DM r14F_A/B pair counts), a new flow only with
# >= 14 GB free and >= 45 minutes after the previous start, so detailed-routing / signoff peaks do not
# coincide. Nothing starts before r14F_B has started (run_r14_final.sh), so this queue never takes the
# slot that pair was promised.
# Cooperative stop: touch asic/.abort_dse_pd
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/dse_pd.log
cd $A
aborted () { [ -e $A/.abort_dse_pd ]; }
# Distinct run tags among live OpenLane processes (one flow can own several processes).
flows () { pgrep -af -- "--run-tag" | grep -oE "run-tag '?[A-Za-z0-9_]+" | tr -d "'" | sort -u | wc -l; }
echo "$(date -Is) queue start" >> $LOG
while ! grep -qE "start r14F_B|abort" $A/r14_final_pd.log; do
    aborted && { echo "$(date -Is) abort while waiting for r14F_B" >> $LOG; exit 0; }
    sleep 60
done
last=0
one () {   # <design dir> <tag>
    CONFIG=config.json bash run_pd_mk.sh "$1" "$2" > "$A/$2.log" 2>&1
    echo "$(date -Is) end $2 rc=$? last step $(ls $A/$1/runs/$2 | grep -E '^[0-9]+-' | tail -1)" >> $LOG
}
for item in soc_sa2_4kb:sa2F_A soc_vc4_4kb:vc4F_A soc_sa2_4kb:sa2F_B soc_vc4_4kb:vc4F_B; do
    des=${item%%:*}; tag=${item##*:}
    while :; do
        aborted && { echo "$(date -Is) abort before $tag" >> $LOG; wait; exit 0; }
        now=$(date +%s)
        if [ "$(flows)" -lt 2 ] && [ "$(free -m | awk '/Mem/{print $7}')" -ge 14000 ] && [ $((now - last)) -ge 2700 ]; then
            break
        fi
        sleep 60
    done
    echo "$(date -Is) start $tag ($des/config.json, full flow) avail $(free -m | awk '/Mem/{print $7}') MB, flows running $(flows)" >> $LOG
    one "$des" "$tag" &
    last=$(date +%s)
    sleep 120   # let the new flow's python process appear before the next count
done
wait
echo "$(date -Is) queue done" >> $LOG
