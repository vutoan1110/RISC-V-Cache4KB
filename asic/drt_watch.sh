#!/usr/bin/env bash
# drt_convergence gate (older logs: G5): watchdog of ONE run's detailed routing (QUY_TRINH.md section D).
#   bash drt_watch.sh <design dir> <run tag>
# Every 60 s it reads "Start Nth optimization iteration" / "Number of violations" from the run's
# *-openroad-detailedrouting log and stops the run when its convergence cannot reach a clean sign-off:
#   after optimization iteration  5: violations > ${G5_IT5:-20000}
#                       iteration 10: violations > ${G5_IT10:-5000}
#                       iteration 20: violations > ${G5_IT20:-600}
#                       iteration 30: violations > ${G5_IT30:-400}
#                       iteration 40: violations > ${G5_IT40:-200}
#   stall: from iteration 12 on, more than 300 violations left and less than a 10 % drop over the last 4 iterations
# Reference trajectories: DM grid3665x2900 2,246 at 5, 153 at 10, 0 at the end; SA2 on the wide grid (failed) 48,353
# at 5; SA2 corr3400x3400_f220 (sa2uB, 64-iteration run of 2026-10-07) 9,414 at 5, 1,424 at 10, 115 at 20, 72 at 30,
# 70 at 40 (flat from 28 to 44), 39 at 50, 0 at 54. Recalibrated 2026-10-07 on that run: the 2026-10-06 limits
# (30: 150, 40: 30, stall above 100) would have stopped it at iteration 23. No limit after iteration 40 (2026-10-08):
# the late iterations change the rip-up strategy and that run fell from 70 to 0 between iterations 44 and 54, so a
# count limit there would be a guess; the late phase runs to the 64-iteration end. The window restarts with each
# detailed_route call (antenna-repair passes renumber from 0).
# G5_UNLIMITED_LATE_PHASE=1 implements the published no-limit-after-40 rule; off by default.
# G5_ANT_ROUND_RULES=1 (2026-10-14, off by default; declare at launch): the post-DRT antenna re-route calls (the 2nd and
# later detailed_route call of the step) get their own limits, because they start from a routed design and follow a
# different trajectory (DM_VC4 V2: 78,513 at 0, 1,389 at 16, a one-iteration bump to 2,063 at 17, the same kind of bump
# the main route showed at 17: 91 -> 283 -> 59). Antenna-call limits: iteration 20 > ${G5_ANT_IT20:-3000}, 30 >
# ${G5_ANT_IT30:-600}, 40 > ${G5_ANT_IT40:-200} (no limit after 40 with G5_UNLIMITED_LATE_PHASE=1); stall rule from
# iteration ${G5_ANT_STALL_FROM:-20}. The main route keeps the limits above. DRT_WATCH_ROOT / DRT_WATCH_LOG: test overrides.
# Stop = SIGTERM to exactly this run's detailed-routing openroad process and its OpenLane python process (matched by
# the run directory path and by "run-tag <tag>"). Exit 0 when detailed routing finished (runtime.txt written), 1 on stop.
set -u
A=${DRT_WATCH_ROOT:-/mnt/e/Projects/RISCV-research/asic}
des=$1; tag=$2
LOG=${DRT_WATCH_LOG:-$A/dse_pd.log}
runs=$A/$des/runs/$tag
while :; do
    d=$(ls -d $runs/*-openroad-detailedrouting 2>/dev/null | tail -1)
    if [ -n "$d" ] && [ -f "$d/runtime.txt" ]; then
        exit 0
    fi
    if [ -n "$d" ] && [ -f "$d/openroad-detailedrouting.log" ]; then
        read call it v v4 < <(awk '/Start 0th optimization iteration/ {call++}
                           /Start [0-9]+(st|nd|rd|th) optimization iteration/ {match($0, /Start [0-9]+/); it = substr($0, RSTART + 6, RLENGTH - 6)}
                           /Number of violations =/ {n = $NF; sub(/\./, "", n); last_it = it; last_v = n; hist[it] = n}
                           END {p = (last_it == "" ? "" : hist[last_it - 4]);
                                print call + 0, (last_it == "" ? -1 : last_it), (last_v == "" ? -1 : last_v), (p == "" ? -1 : p)}' "$d/openroad-detailedrouting.log")
        lim=""
        if [ "${G5_ANT_ROUND_RULES:-0}" = 1 ] && [ "$call" -gt 1 ]; then
            if [ "${G5_UNLIMITED_LATE_PHASE:-0}" = 1 ] && [ "$it" -gt 40 ]; then
                :
            elif [ "$it" -ge 40 ] && [ "$v" -gt "${G5_ANT_IT40:-200}" ]; then lim="antenna call $call, iteration $it: $v > ${G5_ANT_IT40:-200}"
            elif [ "$it" -ge 30 ] && [ "$v" -gt "${G5_ANT_IT30:-600}" ]; then lim="antenna call $call, iteration $it: $v > ${G5_ANT_IT30:-600}"
            elif [ "$it" -ge 20 ] && [ "$v" -gt "${G5_ANT_IT20:-3000}" ]; then lim="antenna call $call, iteration $it: $v > ${G5_ANT_IT20:-3000}"
            elif [ "$it" -ge "${G5_ANT_STALL_FROM:-20}" ] && [ "$v" -gt 300 ] && [ "$v4" -gt 0 ] && [ $((v * 10)) -gt $((v4 * 9)) ]; then
                lim="antenna call $call, iteration $it: stalled, $v violations vs $v4 four iterations earlier (< 10 % drop)"
            fi
        elif [ "${G5_UNLIMITED_LATE_PHASE:-0}" = 1 ] && [ "$it" -gt 40 ]; then
            :  # Published rule: after iteration 40, routing runs to its configured end.
        elif [ "$it" -ge 40 ] && [ "$v" -gt "${G5_IT40:-200}" ];  then lim="iteration $it: $v > ${G5_IT40:-200}"
        elif [ "$it" -ge 30 ] && [ "$v" -gt "${G5_IT30:-400}" ];  then lim="iteration $it: $v > ${G5_IT30:-400}"
        elif [ "$it" -ge 20 ] && [ "$v" -gt "${G5_IT20:-600}" ];  then lim="iteration $it: $v > ${G5_IT20:-600}"
        elif [ "$it" -ge 10 ] && [ "$v" -gt "${G5_IT10:-5000}" ]; then lim="iteration $it: $v > ${G5_IT10:-5000}"
        elif [ "$it" -ge 5 ]  && [ "$v" -gt "${G5_IT5:-20000}" ]; then lim="iteration $it: $v > ${G5_IT5:-20000}"
        elif [ "$it" -ge 12 ] && [ "$v" -gt 300 ] && [ "$v4" -gt 0 ] && [ $((v * 10)) -gt $((v4 * 9)) ]; then
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
