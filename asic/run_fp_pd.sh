#!/usr/bin/env bash
# FLOW_JOURNAL Incident 96 (2026-10-03): double-executed FULL flows of the 4 KiB builds on one chosen floorplan.
# Same logic as run_ring_pd.sh (which is still running and therefore not edited), with the config file name a
# parameter:
#   FPCFG=config_u2a.json ITEMS="soc_vc4_4kb:vc4U2F_A soc_sa2_4kb:sa2U2F_A ..." bash run_fp_pd.sh
# Each flow runs in two phases so that detailed routing (~10.5 GB peak per run) never runs three at a time:
#   phase 1: synthesis .. OpenROAD.STAMidPNR-3 (--to; includes the post-GRT timing report)
#   gate:    at most ONE other detailed routing running and >= 12 GB free, checked under a lock
#   phase 2: resume --from OpenROAD.DetailedRouting .. signoff (RESUME=1, same run dir)
# No step is skipped (phase 1 ends with the third STAMidPNR). A new flow (phase 1) starts only with fewer than 3
# OpenLane run tags live, >= 10 GB free and >= 30 minutes after the previous start.
# Cooperative stop (no new starts, no new phase 2; running steps finish): touch asic/.abort_fp_pd
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/dse_pd.log
LOCK=$A/.fp_drt_gate.lock
CFG=${FPCFG:?set FPCFG to the config file name}
cd $A
aborted () { [ -e $A/.abort_fp_pd ]; }
avail () { free -m | awk '/Mem/{print $7}'; }
flows () { pgrep -af -- "--run-tag" | grep -oE "run-tag '?[A-Za-z0-9_]+" | tr -d "'" | sort -u | wc -l; }
drts () { pgrep -af "bin/openroad .*-detailedrouting/" | grep -c detailedrouting; }
last_step () { ls $A/$1/runs/$2 2>/dev/null | grep -E '^[0-9]+-' | tail -1; }
one () {   # <design dir> <tag>
    local des=$1 tag=$2
    CONFIG=$CFG bash run_pd_mk.sh "$des" "$tag" --to OpenROAD.STAMidPNR-3 > "$A/$tag.log" 2>&1
    echo "$(date -Is) $tag phase 1 done rc=$? last step $(last_step $des $tag)" >> $LOG
    last_step $des $tag | grep -q stamidpnr-3 || { echo "$(date -Is) end $tag (phase 1 did not reach STAMidPNR-3)" >> $LOG; return; }
    while :; do
        aborted && { echo "$(date -Is) fp queue abort: $tag left after phase 1 (resume with --from OpenROAD.DetailedRouting)" >> $LOG; return; }
        if mkdir $LOCK 2>/dev/null; then
            if [ "$(drts)" -le 1 ] && [ "$(avail)" -ge 12000 ]; then
                echo "$(date -Is) $tag phase 2 start (detailed routing running elsewhere: $(drts), avail $(avail) MB)" >> $LOG
                ( RESUME=1 CONFIG=$CFG bash run_pd_mk.sh "$des" "$tag" --from OpenROAD.DetailedRouting > "$A/${tag}_p2.log" 2>&1
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
echo "$(date -Is) fp queue start ($CFG): ${ITEMS:?set ITEMS}" >> $LOG
last=0
for item in $ITEMS; do
    des=${item%%:*}; tag=${item##*:}
    while :; do
        aborted && { echo "$(date -Is) fp queue abort before $tag" >> $LOG; wait; exit 0; }
        now=$(date +%s)
        if [ "$(flows)" -lt 3 ] && [ "$(avail)" -ge 10000 ] && [ $((now - last)) -ge 1800 ]; then
            break
        fi
        sleep 60
    done
    echo "$(date -Is) start $tag ($des/$CFG, full flow in two phases, fresh) avail $(avail) MB, flows running $(flows)" >> $LOG
    one "$des" "$tag" &
    last=$(date +%s)
    sleep 120   # let the new flow's python process appear before the next count
done
wait
echo "$(date -Is) fp queue done ($CFG)" >> $LOG
