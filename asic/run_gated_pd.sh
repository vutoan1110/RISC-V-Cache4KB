#!/usr/bin/env bash
# Gated full flows: a flow stops as soon as it can no longer reach a clean sign-off (0 DRC, 0 LVS, 0 antenna,
# setup >= 0 at tt and ff, hold >= 0 at every corner; QUY_TRINH.md section D).
#   ITEMS="<design dir>:<tag>:<config file> ..." bash run_gated_pd.sh      (FPCFG=<config> sets a default config)
#   STOP_AFTER=p2 ...   screening: hold every flow after a passed p2 gate (continue it with run_gated_resume.sh ... drt)
# Each flow runs in four phases in ONE run directory (fresh first phase, then RESUME); a phase starts only if the
# previous gate passed (fp_tools/gate_check.py, thresholds in its header / environment):
#   P1  synthesis .. OpenROAD.GlobalRouting                    -> gate p1 (grt_overflow, cts_tt_slack)
#   P2  OpenROAD.CheckAntennas .. OpenROAD.STAMidPNR-3          -> gate p2 (grt_repair_overflow, grt_tt_slack)
#   P3  OpenROAD.DetailedRouting, with drt_watch.sh             -> drt_convergence: stopped when it cannot reach 0 DRC
#   P4  OpenROAD.PostRouteHoldECO .. sign-off                   -> gate final (signoff: DRC/LVS/XOR/overlap/antenna 0,
#                                                                 setup >= 0 at tt and ff, hold >= 0 at every corner)
# (Older log lines name the gates G1 .. G6 in the order above.)
# No step of the Classic flow is skipped. P3 waits for a detailed-routing slot (at most ONE other detailed routing
# running, >= 12 GB free; mkdir lock), so three ~10.5 GB detailed routings never coincide. A new flow (P1) starts only
# with fewer than 3 OpenLane run tags live, >= 10 GB free and >= 30 min after the previous start, under a start lock
# (.gated_drt_gate.lock.p2) shared with run_gated_resume.sh p2 and run_gated_branch.sh, so two queues waiting for the
# same free slot cannot both take it.
# Every gate result goes to dse_pd.log and gated_pd.log as "GATE <PASS|FAIL> <tag> <gate>: <numbers>".
# Cooperative stop (no new flows, no new phases; running steps finish): touch asic/.abort_gated_pd
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/dse_pd.log
GLOG=$A/gated_pd.log
LOCK=$A/.gated_drt_gate.lock
CFG0=${FPCFG:-}
cd $A
say () { echo "$(date -Is) $*" | tee -a $GLOG >> $LOG; }
aborted () { [ -e $A/.abort_gated_pd ]; }
avail () { free -m | awk '/Mem/{print $7}'; }
flows () { pgrep -af -- "--run-tag" | grep -oE "run-tag '?[A-Za-z0-9_]+" | tr -d "'" | sort -u | wc -l; }
drts () { pgrep -af "bin/openroad .*-detailedrouting/" | grep -c detailedrouting; }
last_step () { ls $A/$1/runs/$2 2>/dev/null | grep -E '^[0-9]+-' | tail -1; }
gate () {   # <design> <tag> <gate>; MISSING data counts as FAIL
    local r
    r=$(python3 $A/fp_tools/gate_check.py $A/$1/runs/$2 $3 2>&1 | tail -1)
    say "GATE $2 $r"
    [[ "$r" == PASS* ]]
}
gated_one () {   # <design dir> <tag> <config file>
    local des=$1 tag=$2 CFG=$3
    CONFIG=$CFG bash run_pd_mk.sh "$des" "$tag" --to OpenROAD.GlobalRouting > "$A/${tag}_p1.log" 2>&1
    say "$tag P1 done, last step $(last_step $des $tag)"
    gate "$des" "$tag" p1 || { say "STOP $tag after P1 (gate p1)"; return; }
    aborted && { say "STOP $tag after P1 (abort flag)"; return; }
    RESUME=1 CONFIG=$CFG bash run_pd_mk.sh "$des" "$tag" --from OpenROAD.CheckAntennas --to OpenROAD.STAMidPNR-3 > "$A/${tag}_p2.log" 2>&1
    say "$tag P2 done, last step $(last_step $des $tag)"
    gate "$des" "$tag" p2 || { say "STOP $tag after P2 (gate p2)"; return; }
    [ "${STOP_AFTER:-}" = p2 ] && { say "HOLD $tag after P2 (STOP_AFTER=p2; continue with run_gated_resume.sh ... drt)"; return; }
    while :; do
        aborted && { say "STOP $tag after P2 (abort flag; resume with --from OpenROAD.DetailedRouting)"; return; }
        if mkdir $LOCK 2>/dev/null; then
            if [ "$(drts)" -le 1 ] && [ "$(avail)" -ge 12000 ]; then
                say "$tag P3 detailed routing start (other detailed routings $(drts), avail $(avail) MB)"
                ( RESUME=1 CONFIG=$CFG bash run_pd_mk.sh "$des" "$tag" --from OpenROAD.DetailedRouting --to OpenROAD.DetailedRouting > "$A/${tag}_p3.log" 2>&1 ) &
                local p3=$!
                sleep 240
                rmdir $LOCK
                bash $A/drt_watch.sh "$des" "$tag" &
                local wd=$!
                wait $p3
                sleep 70                     # let the watchdog see runtime.txt (normal end) before judging
                if kill -0 $wd 2>/dev/null; then kill $wd 2>/dev/null; fi
                wait $wd 2>/dev/null
                local d
                d=$(find "$A/$des/runs/$tag" -mindepth 1 -maxdepth 1 -type d -regextype posix-extended -regex '.*/[0-9]+-openroad-detailedrouting' 2>/dev/null | LC_ALL=C sort -V | tail -1)
                if [ -z "$d" ] || [ ! -f "$d/runtime.txt" ]; then
                    say "STOP $tag in P3: detailed routing did not finish (G5 abort or crash), last step $(last_step $des $tag)"
                    return
                fi
                break
            fi
            rmdir $LOCK
        fi
        sleep 60
    done
    say "$tag P3 done, last step $(last_step $des $tag)"
    aborted && { say "STOP $tag after P3 (abort flag; resume with --from OpenROAD.PostRouteHoldECO)"; return; }
    # 2026-10-15: stop at Checker.LVS like run_gated_resume.sh (P4_TO overrides). Without --to the flow ran on into
    # Yosys.EQY (~13 GB, known not to pass on this design, not a sign-off criterion): SA2 6c4ccffd r2 spent 53 min in it.
    RESUME=1 CONFIG=$CFG bash run_pd_mk.sh "$des" "$tag" --from OpenROAD.PostRouteHoldECO --to "${P4_TO:-Checker.LVS}" > "$A/${tag}_p4.log" 2>&1
    say "$tag P4 done, last step $(last_step $des $tag)"
    if gate "$des" "$tag" final; then say "SIGNOFF CLEAN $tag"; else say "SIGNOFF FAILED $tag"; fi
}
find $A -maxdepth 1 -name '.gated_drt_gate.lock*' -mmin +10 -exec rmdir {} + 2>/dev/null   # stale locks only
say "gated queue start (default config ${CFG0:-none}): ${ITEMS:?set ITEMS}"
last=0
for item in $ITEMS; do
    des=${item%%:*}; rest=${item#*:}; tag=${rest%%:*}; cfg=$CFG0
    [ "$rest" != "$tag" ] && cfg=${rest#*:}
    if [ -z "$cfg" ] || [ ! -f "$A/$des/$cfg" ]; then say "SKIP $tag: no config file '$cfg' in $des"; continue; fi
    if [ -d "$A/$des/runs/$tag" ]; then say "SKIP $tag: run directory exists already (a fresh tag is required)"; continue; fi
    while :; do                        # start lock shared with run_gated_resume.sh p2 and run_gated_branch.sh
        aborted && { say "gated queue abort before $tag"; wait; exit 0; }
        now=$(date +%s)
        if [ $((now - last)) -ge 1800 ] && mkdir $LOCK.p2 2>/dev/null; then
            [ "$(flows)" -lt 3 ] && [ "$(avail)" -ge 10000 ] && break
            rmdir $LOCK.p2
        fi
        sleep 60
    done
    say "start $tag ($des/$cfg, gated full flow, fresh) avail $(avail) MB, flows running $(flows)"
    gated_one "$des" "$tag" "$cfg" &
    last=$(date +%s)
    sleep 120
    rmdir $LOCK.p2
done
wait
say "gated queue done"
