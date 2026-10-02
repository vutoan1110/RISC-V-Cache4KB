#!/usr/bin/env bash
# FLOW_JOURNAL Incident 96 (2026-10-03): ring-floorplan screening for any of the three 4 KiB builds
# (generalises explore_vc4_ring.sh).   bash explore_ring.sh <design dir> <ring> <synthesised A tag> <prefix> ...
# Takes groups of four arguments, run one after the other, e.g.
#   bash explore_ring.sh soc_sa2_4kb ring1 sa2F_A sa2R1  soc_dm_4kb ring1 r14F_A dmR1
# For each: (1) <prefix>: config_<ring>.json from the post-synthesis state of <A tag> (step 12, STAPrePNR;
# synthesis is not repeated) through detailed placement; fp_tools/route_proxy.py -> ring_explore_proxy.txt.
# (2) <prefix>g: global routing ONLY on that placement (before CTS), GRT_OVERFLOW_ITERS 15 (screening).
# Cooperative stop: touch asic/.abort_vc4_explore
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/dse_pd.log
OR=/nix/store/zzypcxbrgw1qink1l7fwgwpbk7fvdwpg-openroad/bin/openroad
cd $A
while [ $# -ge 4 ]; do
    des=$1; ring=$2; base=$3; T=$4; shift 4
    ST=$A/$des/runs/$base/12-openroad-staprepnr/state_out.json
    [ -e $A/.abort_vc4_explore ] && { echo "$(date -Is) abort ring explore before $T" >> $LOG; exit 0; }
    echo "$(date -Is) start $T ($des/config_$ring.json, from the $base step-12 state, Floorplan..DetailedPlacement)" >> $LOG
    CONFIG=config_$ring.json bash run_pd_mk.sh $des $T --with-initial-state $ST \
        --from OpenROAD.Floorplan --to OpenROAD.DetailedPlacement > $A/$T.log 2>&1
    dpl=$(ls -d $A/$des/runs/$T/*-openroad-detailedplacement 2>/dev/null | tail -1)
    echo "$(date -Is) end $T last step $(ls $A/$des/runs/$T 2>/dev/null | grep -E '^[0-9]+-' | tail -1)" >> $LOG
    [ -n "$dpl" ] || continue
    $OR -python -exit $A/fp_tools/route_proxy.py $dpl/soc_asic_top.odb $T/dpl 2>&1 | grep tiles >> $A/ring_explore_proxy.txt
    [ -e $A/.abort_vc4_explore ] && { echo "$(date -Is) abort ring explore before ${T}g" >> $LOG; exit 0; }
    echo "$(date -Is) start ${T}g (GRT only on the $T detailed placement, GRT_OVERFLOW_ITERS 15)" >> $LOG
    CONFIG=config_$ring.json bash run_pd_mk.sh $des ${T}g --with-initial-state $dpl/state_out.json \
        --from OpenROAD.GlobalRouting --to OpenROAD.GlobalRouting -c GRT_OVERFLOW_ITERS=15 > $A/${T}g.log 2>&1
    g=$(ls $A/$des/runs/${T}g/*-openroad-globalrouting/openroad-globalrouting.log 2>/dev/null | tail -1)
    echo "$(date -Is) end ${T}g: $(grep -E '^Total ' $g 2>/dev/null | tail -1 | tr -s ' ') wire $(grep -o 'Total wirelength: [0-9]* um' $g 2>/dev/null | tail -1)" >> $LOG
done
