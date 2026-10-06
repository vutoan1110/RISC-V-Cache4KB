#!/usr/bin/env bash
# FLOW_JOURNAL Incident 96 (2026-10-06): explore_fp2.sh with the DEFAULT 50 GRT overflow iterations (the 15-iteration
# number proved pessimistic for VC4 and optimistic for SA2), so the screening itself gives the phase-1 G1 value. explore_fp.sh ran on into post-GRT design
# repair after a 233,074-overflow global route (vc4S1, hours of repair that cannot be stopped); this version stops
# right after global routing and caps its overflow iterations, so a congested candidate costs minutes, not hours.
#   bash explore_fp2.sh <design dir> <config file> <synthesised A tag> <run tag> [more groups of four ...]
# Each group: <run tag> = <config> from the post-synthesis state of <A tag> (step 12; no re-synthesis) through
# OpenROAD.GlobalRouting with GRT_OVERFLOW_ITERS 15: CTS, post-CTS timing repair and STAMidPNR-2 (setup nom_tt on
# placement estimates) are included. Summary line in dse_pd.log: STAMidPNR-2 setup/hold nom_tt, GRT usage /
# overflow / wire; route proxy of the detailed placement -> fp_explore_proxy.txt. A group waits for >= 7 GB free.
# Cooperative stop between groups: touch asic/.abort_vc4_explore
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/dse_pd.log
OR=/nix/store/zzypcxbrgw1qink1l7fwgwpbk7fvdwpg-openroad/bin/openroad
cd $A
while [ $# -ge 4 ]; do
    des=$1; cfgf=$2; base=$3; T=$4; shift 4
    ST=$A/$des/runs/$base/12-openroad-staprepnr/state_out.json
    while [ "$(free -m | awk '/Mem/{print $7}')" -lt 7000 ]; do
        [ -e $A/.abort_vc4_explore ] && { echo "$(date -Is) abort fp explore before $T" >> $LOG; exit 0; }
        sleep 60
    done
    [ -e $A/.abort_vc4_explore ] && { echo "$(date -Is) abort fp explore before $T" >> $LOG; exit 0; }
    echo "$(date -Is) start $T ($des/$cfgf, from the $base step-12 state, Floorplan..GlobalRouting, GRT default 50 overflow iterations) avail $(free -m | awk '/Mem/{print $7}') MB" >> $LOG
    CONFIG=$cfgf bash run_pd_mk.sh $des $T --with-initial-state $ST \
        --from OpenROAD.Floorplan --to OpenROAD.GlobalRouting  > $A/$T.log 2>&1
    rd=$A/$des/runs/$T
    dpl=$(ls -d $rd/*-openroad-detailedplacement 2>/dev/null | tail -1)
    [ -n "$dpl" ] && $OR -python -exit $A/fp_tools/route_proxy.py $dpl/soc_asic_top.odb $T/dpl 2>&1 | grep tiles >> $A/fp_explore_proxy.txt
    s2=$(ls -d $rd/*-openroad-stamidpnr-2 2>/dev/null | tail -1)
    mid=$(python3 -c "import json; m=json.load(open('$s2/state_out.json'))['metrics']; print('setup %.3f hold %.3f' % (m['timing__setup__ws__corner:nom_tt_025C_1v80'], m['timing__hold__ws__corner:nom_tt_025C_1v80']))" 2>/dev/null)
    g=$(ls $rd/*-openroad-globalrouting/openroad-globalrouting.log 2>/dev/null | tail -1)
    gr="usage $(grep -E '^Total ' $g 2>/dev/null | tail -1 | awk '{print $4" overflow "$NF}') wire $(grep -o 'Total wirelength: [0-9]*' $g 2>/dev/null | tail -1 | awk '{print $3}')"
    echo "$(date -Is) end $T last step $(ls $rd | grep -E '^[0-9]+-' | tail -1): midPnR-2 nom_tt ${mid:-?}; GRT50 $gr" >> $LOG
done
