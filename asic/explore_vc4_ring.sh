#!/usr/bin/env bash
# FLOW_JOURNAL Incident 96 (2026-10-03): DM_VC4 ring-floorplan exploration (fp_tools/make_ring_fp.py).
#   bash explore_vc4_ring.sh <ring tag, e.g. ring1>
# (1) <T> = vc4R<n>: config_<ring>.json from the post-synthesis state of vc4F_A (step 12; synthesis is not
#     repeated) through detailed placement; fp_tools/route_proxy.py on the placement -> vc4_explore_proxy.txt.
# (2) <T>g: global routing ONLY, on that detailed placement (before CTS: the clock is still one unbuffered net),
#     with GRT_OVERFLOW_ITERS 15 so a congested variant ends in bounded time (GRT_ALLOW_CONGESTION is on in the
#     config, so it always prints the final congestion report). A screening run, not a flow result.
# Cooperative stop: touch asic/.abort_vc4_explore
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/dse_pd.log
ring=$1
n=${ring#ring}
T=vc4R$n
ST=$A/soc_vc4_4kb/runs/vc4F_A/12-openroad-staprepnr/state_out.json
OR=/nix/store/zzypcxbrgw1qink1l7fwgwpbk7fvdwpg-openroad/bin/openroad
cd $A
[ -e $A/.abort_vc4_explore ] && { echo "$(date -Is) abort vc4 explore before $T" >> $LOG; exit 0; }
echo "$(date -Is) start $T (soc_vc4_4kb/config_$ring.json, from the vc4F_A step-12 state, Floorplan..DetailedPlacement)" >> $LOG
CONFIG=config_$ring.json bash run_pd_mk.sh soc_vc4_4kb $T --with-initial-state $ST \
    --from OpenROAD.Floorplan --to OpenROAD.DetailedPlacement > $A/$T.log 2>&1
dpl=$(ls -d $A/soc_vc4_4kb/runs/$T/*-openroad-detailedplacement 2>/dev/null | tail -1)
echo "$(date -Is) end $T last step $(ls $A/soc_vc4_4kb/runs/$T 2>/dev/null | grep -E '^[0-9]+-' | tail -1)" >> $LOG
[ -n "$dpl" ] || exit 1
$OR -python -exit $A/fp_tools/route_proxy.py $dpl/soc_asic_top.odb $T/dpl 2>&1 | grep tiles >> $A/vc4_explore_proxy.txt
[ -e $A/.abort_vc4_explore ] && { echo "$(date -Is) abort vc4 explore before ${T}g" >> $LOG; exit 0; }
echo "$(date -Is) start ${T}g (GRT only on the $T detailed placement, GRT_OVERFLOW_ITERS 15)" >> $LOG
CONFIG=config_$ring.json bash run_pd_mk.sh soc_vc4_4kb ${T}g --with-initial-state $dpl/state_out.json \
    --from OpenROAD.GlobalRouting --to OpenROAD.GlobalRouting -c GRT_OVERFLOW_ITERS=15 > $A/${T}g.log 2>&1
g=$(ls $A/soc_vc4_4kb/runs/${T}g/*-openroad-globalrouting/openroad-globalrouting.log 2>/dev/null | tail -1)
echo "$(date -Is) end ${T}g: $(grep -E '^Total ' $g 2>/dev/null | tail -1 | tr -s ' ') wire $(grep -o 'Total wirelength: [0-9]* um' $g 2>/dev/null | tail -1)" >> $LOG
