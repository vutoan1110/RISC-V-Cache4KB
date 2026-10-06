#!/usr/bin/env bash
# FLOW_JOURNAL Incident 96 (2026-10-03): floorplan screening up to post-GRT timing repair.
#   bash explore_fp.sh <design dir> <config file> <synthesised A tag> <run tag> [more groups of four ...]
# Each group: <run tag> = <config> from the post-synthesis state of <A tag> (step 12; synthesis is not repeated)
# through OpenROAD.ResizerTimingPostGRT (CTS, post-CTS repair, GRT, post-GRT repair, post-GRT timing repair:
# where the SA2 wide build's setup collapsed to -12 ns), then a summary line in dse_pd.log: STAMidPNR-2 setup
# (placement estimates), GRT overflow / wire, the final setup WNS/TNS of the post-GRT timing repair, and the
# route proxy of the detailed placement (-> fp_explore_proxy.txt). A group waits until >= 9 GB are free.
# Cooperative stop: touch asic/.abort_vc4_explore
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/dse_pd.log
OR=/nix/store/zzypcxbrgw1qink1l7fwgwpbk7fvdwpg-openroad/bin/openroad
cd $A
while [ $# -ge 4 ]; do
    des=$1; cfgf=$2; base=$3; T=$4; shift 4
    ST=$A/$des/runs/$base/12-openroad-staprepnr/state_out.json
    while [ "$(free -m | awk '/Mem/{print $7}')" -lt 9000 ]; do
        [ -e $A/.abort_vc4_explore ] && { echo "$(date -Is) abort fp explore before $T" >> $LOG; exit 0; }
        sleep 60
    done
    [ -e $A/.abort_vc4_explore ] && { echo "$(date -Is) abort fp explore before $T" >> $LOG; exit 0; }
    echo "$(date -Is) start $T ($des/$cfgf, from the $base step-12 state, Floorplan..ResizerTimingPostGRT) avail $(free -m | awk '/Mem/{print $7}') MB" >> $LOG
    CONFIG=$cfgf bash run_pd_mk.sh $des $T --with-initial-state $ST \
        --from OpenROAD.Floorplan --to OpenROAD.ResizerTimingPostGRT > $A/$T.log 2>&1
    rd=$A/$des/runs/$T
    dpl=$(ls -d $rd/*-openroad-detailedplacement 2>/dev/null | tail -1)
    [ -n "$dpl" ] && $OR -python -exit $A/fp_tools/route_proxy.py $dpl/soc_asic_top.odb $T/dpl 2>&1 | grep tiles >> $A/fp_explore_proxy.txt
    s2=$(ls -d $rd/*-openroad-stamidpnr-2 2>/dev/null | tail -1)
    mid=$(python3 -c "import json,sys; m=json.load(open('$s2/state_out.json'))['metrics']; print('%.3f' % m['timing__setup__ws__corner:nom_tt_025C_1v80'])" 2>/dev/null)
    g=$(ls $rd/*-openroad-globalrouting/openroad-globalrouting.log 2>/dev/null | tail -1)
    gr="usage $(grep -E '^Total ' $g 2>/dev/null | tail -1 | awk '{print $4" overflow "$NF}') wire $(grep -o 'Total wirelength: [0-9]*' $g 2>/dev/null | tail -1 | awk '{print $3}')"
    t=$(ls $rd/*-openroad-resizertimingpostgrt/*.log 2>/dev/null | tail -1)
    fin=$(grep -E '^\s+final \|' $t 2>/dev/null | tr -s ' ' | tr '\n' ';')   # setup row (WNS, TNS) then hold row
    echo "$(date -Is) end $T last step $(ls $rd | grep -E '^[0-9]+-' | tail -1): midPnR-2 setup nom_tt ${mid:-?}; GRT $gr; post-GRT repair final rows: ${fin:-?}" >> $LOG
done
