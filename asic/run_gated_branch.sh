#!/usr/bin/env bash
# Gated screening of a run branched with branch_run.sh: the rest of P1 (when the branch point is before global
# routing) and P2, with the p1 / p2 gates of run_gated_pd.sh, then the run is held (continue it with
# run_gated_resume.sh <design dir> <tag> <config> <reason> drt).
#   bash run_gated_branch.sh <design dir> <tag> <config file> <reason> <from step id>
#     from step id: OpenROAD.RepairDesignPostGPL for knobs that act from the first design repair on (MAX_FANOUT_CONSTRAINT:
#                   only the STA report steps use it earlier); OpenROAD.CheckAntennas for knobs that act after global
#                   routing (GRT_DESIGN_REPAIR_MAX_CAP_PCT).
#                   drt: detailed routing only of a run held after P2 (slot lock and drt_watch.sh as in run_gated_pd.sh),
#                   held again after it, so a screening run's sign-off part is spent only when the run is chosen
#                   (continue with run_gated_resume.sh <design dir> <tag> <config> <reason> hold).
# Starts with fewer than 3 OpenLane run tags live and >= 10 GB free, under the start lock of run_gated_resume.sh p2.
# Cooperative stop: touch asic/.abort_gated_pd (checked before each phase).
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/dse_pd.log
GLOG=$A/gated_pd.log
LOCK=$A/.gated_drt_gate.lock
des=$1; tag=$2; CFG=$3; WHY=$4; FROM=$5
cd $A
say () { echo "$(date -Is) $*" | tee -a $GLOG >> $LOG; }
aborted () { [ -e $A/.abort_gated_pd ]; }
avail () { free -m | awk '/Mem/{print $7}'; }
flows () { pgrep -af -- "--run-tag" | grep -oE "run-tag '?[A-Za-z0-9_]+" | tr -d "'" | sort -u | wc -l; }
last_step () { ls $A/$1/runs/$2 2>/dev/null | grep -E '^[0-9]+-' | tail -1; }
gate () {
    local r
    r=$(python3 $A/fp_tools/gate_check.py $A/$1/runs/$2 $3 2>&1 | tail -1)
    say "GATE $2 $r"
    [[ "$r" == PASS* ]]
}
run () { RESUME=1 CONFIG=$CFG bash run_pd_mk.sh "$des" "$tag" --from $1 --to $2 > "$A/${tag}_$3.log" 2>&1; }
drts () { pgrep -af "bin/openroad .*-detailedrouting/" | grep -c detailedrouting; }
[ -d "$A/$des/runs/$tag" ] || { echo "no run $des/$tag"; exit 2; }
[ -f "$A/$des/$CFG" ] || { echo "no config $des/$CFG"; exit 2; }
if [ "$FROM" = drt ]; then
    say "BRANCH $tag ($WHY): detailed routing only, held after it"
    while :; do
        aborted && { say "STOP $tag before detailed routing (abort flag)"; exit 0; }
        if [ "$(flows)" -lt 3 ] && mkdir $LOCK 2>/dev/null; then
            if [ "$(drts)" -le 1 ] && [ "$(avail)" -ge 12000 ]; then
                say "$tag detailed routing start (other detailed routings $(drts), avail $(avail) MB, flows $(flows))"
                ( run OpenROAD.DetailedRouting OpenROAD.DetailedRouting p3 ) &
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
                say "HOLD $tag after detailed routing (continue with run_gated_resume.sh $des $tag $CFG <reason> hold)"
                exit 0
            fi
            rmdir $LOCK
        fi
        sleep 60
    done
fi
say "BRANCH $tag ($WHY): from $FROM to OpenROAD.STAMidPNR-3, held after the p2 gate"
while :; do
    aborted && { say "STOP $tag before the start (abort flag)"; exit 0; }
    if mkdir $LOCK.p2 2>/dev/null; then
        [ "$(flows)" -lt 3 ] && [ "$(avail)" -ge 10000 ] && break
        rmdir $LOCK.p2
    fi
    sleep 60
done
say "$tag start (avail $(avail) MB, flows running $(flows))"
if [ "$FROM" != OpenROAD.CheckAntennas ]; then
    ( run $FROM OpenROAD.GlobalRouting p1 ) &
    p=$!; sleep 120; rmdir $LOCK.p2; wait $p
    say "$tag P1 done, last step $(last_step $des $tag)"
    gate "$des" "$tag" p1 || { say "STOP $tag after the p1 gate"; exit 1; }
    aborted && { say "STOP $tag after P1 (abort flag)"; exit 0; }
    run OpenROAD.CheckAntennas OpenROAD.STAMidPNR-3 p2
else
    ( run OpenROAD.CheckAntennas OpenROAD.STAMidPNR-3 p2 ) &
    p=$!; sleep 120; rmdir $LOCK.p2; wait $p
fi
say "$tag P2 done, last step $(last_step $des $tag)"
if gate "$des" "$tag" p2; then
    say "HOLD $tag after P2 (continue with run_gated_resume.sh $des $tag $CFG <reason> drt)"
    exit 0
fi
say "STOP $tag after the p2 gate"
exit 1
