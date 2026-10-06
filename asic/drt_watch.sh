#!/usr/bin/env bash
# FLOW_JOURNAL Incident 96 (2026-10-03): gate G5 -- watchdog of ONE run's detailed routing.
#   bash drt_watch.sh <design dir> <run tag>
# Every 60 s it reads "Start Nth optimization iteration" / "Number of violations" from the run's
# *-openroad-detailedrouting log and aborts the run when its convergence cannot reach a clean sign-off:
#   after optimization iteration  5: violations > ${G5_IT5:-5000}
#                       iteration 10: violations > ${G5_IT10:-1000}
#                       iteration 20: violations > ${G5_IT20:-200}
#                       iteration 30: violations > ${G5_IT30:-50}
# (reference DM r14F_A: 2,246 at 5, 153 at 10, 0 at the end; SA2 on the wide floorplan: 48,353 at 5.)
# Abort = SIGTERM to exactly this run's detailed-routing openroad process and its OpenLane python process
# (matched by the run directory path and by "run-tag <tag>"), as authorised by the user on 2026-10-03 for runs
# that cannot reach a clean sign-off. Exit 0 when detailed routing finished (runtime.txt written), 1 on abort.
set -u
A=/mnt/e/Projects/RISCV-research/asic
des=$1; tag=$2
LOG=$A/dse_pd.log
runs=$A/$des/runs/$tag
while :; do
    d=$(ls -d $runs/*-openroad-detailedrouting 2>/dev/null | tail -1)
    if [ -n "$d" ] && [ -f "$d/runtime.txt" ]; then
        exit 0
    fi
    if [ -n "$d" ] && [ -f "$d/openroad-detailedrouting.log" ]; then
        read it v < <(awk '/Start [0-9]+(st|nd|rd|th) optimization iteration/ {match($0, /Start [0-9]+/); it = substr($0, RSTART + 6, RLENGTH - 6)}
                           /Number of violations =/ {n = $NF; sub(/\./, "", n); last_it = it; last_v = n}
                           END {print (last_it == "" ? -1 : last_it), (last_v == "" ? -1 : last_v)}' "$d/openroad-detailedrouting.log")
        lim=""
        if   [ "$it" -ge 30 ] && [ "$v" -gt "${G5_IT30:-50}" ];   then lim="iteration $it: $v > ${G5_IT30:-50}"
        elif [ "$it" -ge 20 ] && [ "$v" -gt "${G5_IT20:-200}" ];  then lim="iteration $it: $v > ${G5_IT20:-200}"
        elif [ "$it" -ge 10 ] && [ "$v" -gt "${G5_IT10:-1000}" ]; then lim="iteration $it: $v > ${G5_IT10:-1000}"
        elif [ "$it" -ge 5 ]  && [ "$v" -gt "${G5_IT5:-5000}" ];  then lim="iteration $it: $v > ${G5_IT5:-5000}"
        fi
        if [ -n "$lim" ]; then
            pids=$(pgrep -f "runs/$tag/[0-9]+-openroad-detailedrouting/" ; pgrep -f -- "--run-tag '?$tag'?( |$)")
            echo "$(date -Is) G5 ABORT $tag: detailed routing $lim; SIGTERM to $(echo $pids | tr '\n' ' ')" >> $LOG
            [ -n "$pids" ] && kill -TERM $pids
            exit 1
        fi
    fi
    sleep 60
done
