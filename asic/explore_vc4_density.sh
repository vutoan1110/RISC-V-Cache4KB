#!/usr/bin/env bash
# FLOW_JOURNAL Incident 96 (2026-10-03): DM_VC4 placement-density sweep on the wide floorplan.
# vc4F_A (config_wide.json, density 42) overflows global routing by 34,086. Each variant (config_xd<d>.json =
# config_wide.json with PL_TARGET_DENSITY_PCT <d>, made by fp_tools/make_vc4_variants.py) runs from the
# post-synthesis state of vc4F_A (step 12, STAPrePNR: same netlist, synthesis is not repeated) to detailed
# placement (~8 min), then fp_tools/route_proxy.py measures util / pin density / RUDY / HPWL of the placement.
# One flow at a time (~2-3 GB). Log lines go to dse_pd.log; proxy lines to vc4_explore_proxy.txt.
# Cooperative stop: touch asic/.abort_vc4_explore
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/dse_pd.log
ST=$A/soc_vc4_4kb/runs/vc4F_A/12-openroad-staprepnr/state_out.json
OR=/nix/store/zzypcxbrgw1qink1l7fwgwpbk7fvdwpg-openroad/bin/openroad
cd $A
for d in ${DENS:-36 32 28}; do
    [ -e $A/.abort_vc4_explore ] && { echo "$(date -Is) abort vc4 explore before d$d" >> $LOG; exit 0; }
    t=vc4Xd$d
    echo "$(date -Is) start $t (soc_vc4_4kb/config_xd$d.json, from the vc4F_A step-12 state, Floorplan..DetailedPlacement)" >> $LOG
    CONFIG=config_xd$d.json bash run_pd_mk.sh soc_vc4_4kb $t --with-initial-state $ST \
        --from OpenROAD.Floorplan --to OpenROAD.DetailedPlacement > $A/$t.log 2>&1
    echo "$(date -Is) end $t last step $(ls $A/soc_vc4_4kb/runs/$t 2>/dev/null | grep -E '^[0-9]+-' | tail -1)" >> $LOG
    o=$(ls $A/soc_vc4_4kb/runs/$t/*-openroad-detailedplacement/soc_asic_top.odb 2>/dev/null | tail -1)
    [ -n "$o" ] && $OR -python -exit $A/fp_tools/route_proxy.py $o $t/dpl 2>&1 | grep tiles >> $A/vc4_explore_proxy.txt
done
echo "$(date -Is) vc4 density sweep done" >> $LOG
