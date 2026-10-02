#!/usr/bin/env bash
# FLOW_JOURNAL Incident 96 (2026-10-03): the double-executed FULL flows (synthesis .. signoff) of the three 4 KiB
# builds on the ring1 floorplan (fp_tools/make_ring_fp.py; die 3200 x 3190 um): <design>/config_ring1.json.
# Order: the three A runs (DM_VC4 first: it is the one the grid floorplans could not route), then the B runs.
#
# Each flow runs in two phases so that detailed routing (~10.5 GB peak per run, DM r14F) never runs three at a
# time -- the wide-floorplan runs sa2F_A / vc4F_A also reach detailed routing on their own schedule:
#   phase 1: synthesis .. OpenROAD.ResizerTimingPostGRT                (--to; ~3-5 GB)
#   gate:    at most ONE other detailed routing running and >= 12 GB free, checked under a lock
#   phase 2: resume --from OpenROAD.DetailedRouting .. signoff        (RESUME=1, same run dir)
# The only step this skips is the third STAMidPNR (a report between post-GRT timing repair and detailed
# routing); A and B runs are executed the same way, so they stay comparable.
# A new flow (phase 1) starts only with fewer than 3 OpenLane processes' run tags live, >= 10 GB free and
# >= 30 minutes after the previous start.
# Cooperative stop (no new starts, no new phase 2; running steps finish): touch asic/.abort_ring_pd
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/dse_pd.log
LOCK=$A/.ring_drt_gate.lock
cd $A
aborted () { [ -e $A/.abort_ring_pd ]; }
avail () { free -m | awk '/Mem/{print $7}'; }
flows () { pgrep -af -- "--run-tag" | grep -oE "run-tag '?[A-Za-z0-9_]+" | tr -d "'" | sort -u | wc -l; }
drts () { pgrep -af "bin/openroad .*-detailedrouting/" | grep -c detailedrouting; }
last_step () { ls $A/$1/runs/$2 2>/dev/null | grep -E '^[0-9]+-' | tail -1; }
one () {   # <design dir> <tag>
    local des=$1 tag=$2
    CONFIG=config_ring1.json bash run_pd_mk.sh "$des" "$tag" --to OpenROAD.ResizerTimingPostGRT > "$A/$tag.log" 2>&1
    echo "$(date -Is) $tag phase 1 done rc=$? last step $(last_step $des $tag)" >> $LOG
    last_step $des $tag | grep -q resizertimingpostgrt || { echo "$(date -Is) end $tag (phase 1 did not reach ResizerTimingPostGRT)" >> $LOG; return; }
    while :; do
        aborted && { echo "$(date -Is) ring queue abort: $tag left after phase 1 (resume with --from OpenROAD.DetailedRouting)" >> $LOG; return; }
        if mkdir $LOCK 2>/dev/null; then
            if [ "$(drts)" -le 1 ] && [ "$(avail)" -ge 12000 ]; then
                echo "$(date -Is) $tag phase 2 start (detailed routing running elsewhere: $(drts), avail $(avail) MB)" >> $LOG
                ( RESUME=1 CONFIG=config_ring1.json bash run_pd_mk.sh "$des" "$tag" --from OpenROAD.DetailedRouting > "$A/${tag}_p2.log" 2>&1
                  echo "$(date -Is) end $tag rc=$? last step $(last_step $des $tag)" >> $LOG ) &
                sleep 240           # the new detailed routing is visible to drts before the lock is released
                rmdir $LOCK
                wait
                return
            fi
            rmdir $LOCK
        fi
        sleep 60
    done
}
rmdir $LOCK 2>/dev/null
echo "$(date -Is) ring queue start" >> $LOG
last=0
for item in ${ITEMS:-soc_vc4_4kb:vc4R1F_A soc_sa2_4kb:sa2R1F_A soc_dm_4kb:dmR1F_A soc_vc4_4kb:vc4R1F_B soc_sa2_4kb:sa2R1F_B soc_dm_4kb:dmR1F_B}; do
    des=${item%%:*}; tag=${item##*:}
    while :; do
        aborted && { echo "$(date -Is) ring queue abort before $tag" >> $LOG; wait; exit 0; }
        now=$(date +%s)
        if [ "$(flows)" -lt 3 ] && [ "$(avail)" -ge 10000 ] && [ $((now - last)) -ge 1800 ]; then
            break
        fi
        sleep 60
    done
    echo "$(date -Is) start $tag ($des/config_ring1.json, full flow in two phases, fresh) avail $(avail) MB, flows running $(flows)" >> $LOG
    one "$des" "$tag" &
    last=$(date +%s)
    sleep 120   # let the new flow's python process appear before the next count
done
wait
echo "$(date -Is) ring queue done" >> $LOG
