#!/usr/bin/env bash
# Floorplan screening. Each group runs one candidate floorplan from an existing post-synthesis state through
# OpenROAD.GlobalRouting (floorplan, placement, CTS, post-CTS timing repair, STAMidPNR-2, global routing with the
# default 50 overflow iterations), so its numbers are the phase-1 gate values of run_gated_pd.sh: STAMidPNR-2
# setup/hold nom_tt and the GRT overflow. A 15-iteration cap misranks candidates near the routability edge. The run
# stops before the post-GRT repair, which takes hours on a congested floorplan.
#   bash fp_tools/screen_floorplan.sh <design dir> <config file> <synthesised tag> <run tag> [more groups of four ...]
# <run tag> starts from the step-12 (OpenROAD.STAPrePNR) state of <synthesised tag>, so nothing is re-synthesised.
# Summary line in dse_pd.log; route proxy of the detailed placement in fp_explore/route_proxy.txt. A group waits for
# >= 7 GB free memory. Cooperative stop between groups: touch asic/.abort_fp_screen
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/dse_pd.log
OR=/nix/store/zzypcxbrgw1qink1l7fwgwpbk7fvdwpg-openroad/bin/openroad
cd $A
while [ $# -ge 4 ]; do
    des=$1; cfgf=$2; base=$3; T=$4; shift 4
    ST=$A/$des/runs/$base/12-openroad-staprepnr/state_out.json
    while [ "$(free -m | awk '/Mem/{print $7}')" -lt 7000 ]; do
        [ -e $A/.abort_fp_screen ] && { echo "$(date -Is) abort fp explore before $T" >> $LOG; exit 0; }
        sleep 60
    done
    [ -e $A/.abort_fp_screen ] && { echo "$(date -Is) abort fp explore before $T" >> $LOG; exit 0; }
    echo "$(date -Is) start $T ($des/$cfgf, from the $base step-12 state, Floorplan..GlobalRouting, GRT default 50 overflow iterations) avail $(free -m | awk '/Mem/{print $7}') MB" >> $LOG
    CONFIG=$cfgf bash run_pd_mk.sh $des $T --with-initial-state $ST \
        --from OpenROAD.Floorplan --to OpenROAD.GlobalRouting  > $A/$T.log 2>&1
    rd=$A/$des/runs/$T
    dpl=$(ls -d $rd/*-openroad-detailedplacement 2>/dev/null | tail -1)
    [ -n "$dpl" ] && $OR -python -exit $A/fp_tools/route_proxy.py $dpl/soc_asic_top.odb $T/dpl 2>&1 | grep tiles >> $A/fp_explore/route_proxy.txt
    s2=$(ls -d $rd/*-openroad-stamidpnr-2 2>/dev/null | tail -1)
    mid=$(python3 -c "import json; m=json.load(open('$s2/state_out.json'))['metrics']; print('setup %.3f hold %.3f' % (m['timing__setup__ws__corner:nom_tt_025C_1v80'], m['timing__hold__ws__corner:nom_tt_025C_1v80']))" 2>/dev/null)
    g=$(ls $rd/*-openroad-globalrouting/openroad-globalrouting.log 2>/dev/null | tail -1)
    gr="usage $(grep -E '^Total ' $g 2>/dev/null | tail -1 | awk '{print $4" overflow "$NF}') wire $(grep -o 'Total wirelength: [0-9]*' $g 2>/dev/null | tail -1 | awk '{print $3}')"
    echo "$(date -Is) end $T last step $(ls $rd | grep -E '^[0-9]+-' | tail -1): midPnR-2 nom_tt ${mid:-?}; GRT50 $gr" >> $LOG
done
