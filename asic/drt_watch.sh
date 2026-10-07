#!/usr/bin/env bash
# drt_convergence gate (older logs: G5): watchdog of ONE run's detailed routing (QUY_TRINH.md section D).
#   bash drt_watch.sh <design dir> <run tag>
# Every 60 s it reads "Start Nth optimization iteration" / "Number of violations" from the run's
# *-openroad-detailedrouting log and stops the run when its convergence cannot reach a clean sign-off:
#   after optimization iteration  5: violations > ${G5_IT5:-20000}
#                       iteration 10: violations > ${G5_IT10:-5000}
#                       iteration 20: violations > ${G5_IT20:-600}
#                       iteration 30: violations > ${G5_IT30:-150}
#                       iteration 40: violations > ${G5_IT40:-30}
#   stall: from iteration 12 on, more than 100 violations left and less than a 10 % drop over the last 4 iterations
# Reference trajectories: DM grid3665x2900 2,246 at 5, 153 at 10, 0 at the end; SA2 on the wide grid (failed) 48,353
# at 5. The limits were recalibrated on 2026-10-06 (the first set, taken from one DM run, stopped a converging SA2
# run at iteration 6); the window restarts with each detailed_route call (antenna-repair passes renumber from 0).
# Stop = SIGTERM to exactly this run's detailed-routing openroad process and its OpenLane python process (matched by
# the run directory path and by "run-tag <tag>"). Exit 0 when detailed routing finished (runtime.txt written), 1 on stop.
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
        read it v v4 < <(awk '/Start [0-9]+(st|nd|rd|th) optimization iteration/ {match($0, /Start [0-9]+/); it = substr($0, RSTART + 6, RLENGTH - 6)}
                           /Number of violations =/ {n = $NF; sub(/\./, "", n); last_it = it; last_v = n; hist[it] = n}
                           END {p = (last_it == "" ? "" : hist[last_it - 4]);
                                print (last_it == "" ? -1 : last_it), (last_v == "" ? -1 : last_v), (p == "" ? -1 : p)}' "$d/openroad-detailedrouting.log")
        lim=""
        if   [ "$it" -ge 40 ] && [ "$v" -gt "${G5_IT40:-30}" ];   then lim="iteration $it: $v > ${G5_IT40:-30}"
        elif [ "$it" -ge 30 ] && [ "$v" -gt "${G5_IT30:-150}" ];  then lim="iteration $it: $v > ${G5_IT30:-150}"
        elif [ "$it" -ge 20 ] && [ "$v" -gt "${G5_IT20:-600}" ];  then lim="iteration $it: $v > ${G5_IT20:-600}"
        elif [ "$it" -ge 10 ] && [ "$v" -gt "${G5_IT10:-5000}" ]; then lim="iteration $it: $v > ${G5_IT10:-5000}"
        elif [ "$it" -ge 5 ]  && [ "$v" -gt "${G5_IT5:-20000}" ]; then lim="iteration $it: $v > ${G5_IT5:-20000}"
        elif [ "$it" -ge 12 ] && [ "$v" -gt 100 ] && [ "$v4" -gt 0 ] && [ $((v * 10)) -gt $((v4 * 9)) ]; then
            lim="iteration $it: stalled, $v violations vs $v4 four iterations earlier (< 10 % drop)"
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
