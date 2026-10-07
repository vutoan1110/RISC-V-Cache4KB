#!/usr/bin/env bash
# Continue one gated flow after a stop that did not show the run cannot sign off: a margin gate with a positive
# slack, a detailed-routing watchdog that was recalibrated afterwards, or a terminal session that ended under the
# job. Same phases and limits as run_gated_pd.sh: detailed routing with drt_watch.sh under the shared slot lock
# (at most 2 detailed routings, >= 12 GB free, fewer than 3 live flows), then the sign-off part, then the signoff
# gate of fp_tools/gate_check.py.
#   bash run_gated_resume.sh <design dir> <tag> <config file> <reason> [from] [to]
#     from: drt  (default) detailed routing, then the sign-off part from OpenROAD.PostRouteHoldECO
#           hold the sign-off part from OpenROAD.PostRouteHoldECO
#           sta  the sign-off part from OpenROAD.STAPostPNR (the run stopped during or after RCX)
#     to:   last step of the sign-off part, default Checker.LVS. Yosys.EQY needs about 13 GB (it was killed by the
#           kernel OOM killer next to two detailed routings on 2026-10-07) and is run on its own afterwards.
# Cooperative stop: touch asic/.abort_gated_pd (checked before each phase).
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/dse_pd.log
GLOG=$A/gated_pd.log
LOCK=$A/.gated_drt_gate.lock
des=$1; tag=$2; CFG=$3; WHY=$4; FROM=${5:-drt}; TO=${6:-Checker.LVS}
cd $A
say () { echo "$(date -Is) $*" | tee -a $GLOG >> $LOG; }
aborted () { [ -e $A/.abort_gated_pd ]; }
avail () { free -m | awk '/Mem/{print $7}'; }
flows () { pgrep -af -- "--run-tag" | grep -oE "run-tag '?[A-Za-z0-9_]+" | tr -d "'" | sort -u | wc -l; }
drts () { pgrep -af "bin/openroad .*-detailedrouting/" | grep -c detailedrouting; }
last_step () { ls $A/$1/runs/$2 2>/dev/null | grep -E '^[0-9]+-' | tail -1; }
gate () {
    local r
    r=$(python3 $A/fp_tools/gate_check.py $A/$1/runs/$2 $3 2>&1 | tail -1)
    say "GATE $2 $r"
    [[ "$r" == PASS* ]]
}
[ -d "$A/$des/runs/$tag" ] || { echo "no run $des/$tag"; exit 2; }
[ -f "$A/$des/$CFG" ] || { echo "no config $des/$CFG"; exit 2; }
say "RESUME $tag ($WHY): from $FROM to $TO"
case $FROM in
    drt)
        while :; do
            aborted && { say "STOP $tag before detailed routing (abort flag)"; exit 0; }
            if [ "$(flows)" -lt 3 ] && mkdir $LOCK 2>/dev/null; then
                if [ "$(drts)" -le 1 ] && [ "$(avail)" -ge 12000 ]; then
                    say "$tag detailed routing start (other detailed routings $(drts), avail $(avail) MB, flows $(flows))"
                    ( RESUME=1 CONFIG=$CFG bash run_pd_mk.sh "$des" "$tag" --from OpenROAD.DetailedRouting --to OpenROAD.DetailedRouting > "$A/${tag}_p3.log" 2>&1 ) &
                    p3=$!
                    sleep 240
                    rmdir $LOCK
                    bash $A/drt_watch.sh "$des" "$tag" &
                    wd=$!
                    wait $p3
                    sleep 70                     # let the watchdog see runtime.txt (normal end) before judging
                    if kill -0 $wd 2>/dev/null; then kill $wd 2>/dev/null; fi
                    wait $wd 2>/dev/null
                    d=$(ls -d $A/$des/runs/$tag/*-openroad-detailedrouting 2>/dev/null | tail -1)
                    if [ -z "$d" ] || [ ! -f "$d/runtime.txt" ]; then
                        say "STOP $tag in detailed routing (drt_convergence abort or crash), last step $(last_step $des $tag)"
                        exit 1
                    fi
                    break
                fi
                rmdir $LOCK
            fi
            sleep 60
        done
        say "$tag detailed routing done, last step $(last_step $des $tag)"
        STEP=OpenROAD.PostRouteHoldECO ;;
    hold) STEP=OpenROAD.PostRouteHoldECO ;;
    sta)  STEP=OpenROAD.STAPostPNR ;;
    *)    echo "from must be drt, hold or sta"; exit 2 ;;
esac
if [ "$FROM" != drt ]; then
    while [ "$(flows)" -ge 3 ]; do aborted && break; sleep 60; done
fi
aborted && { say "STOP $tag before the sign-off part (abort flag)"; exit 0; }
RESUME=1 CONFIG=$CFG bash run_pd_mk.sh "$des" "$tag" --from $STEP --to $TO > "$A/${tag}_p4.log" 2>&1
say "$tag sign-off part done (to $TO), last step $(last_step $des $tag)"
if gate "$des" "$tag" final; then say "SIGNOFF CLEAN $tag"; else say "SIGNOFF FAILED $tag"; fi
