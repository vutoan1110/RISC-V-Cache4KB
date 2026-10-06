#!/usr/bin/env bash
# FLOW_JOURNAL Incident 96 (2026-10-06): the decisive routability number for a floorplan candidate. A screening run
# (explore_fp2.sh) stops global routing after 15 overflow iterations; the real flow (run_gated_pd.sh phase 1) runs
# the default 50 and its gate G1 wants overflow <= 500. This re-runs ONLY OpenROAD.GlobalRouting, with the run's own
# config and the default iterations, from the screening run's STAMidPNR-2 state (the same placement / CTS / repair
# the real phase 1 would produce), so the overflow printed here is the G1 value of that floorplan.
#   bash explore_grt50.sh <design dir> <config file> <screening tag> [more groups of three ...]
# New run tag <screening tag>G50. Summary in dse_pd.log. Waits for >= 7 GB free; stop between groups:
# touch asic/.abort_vc4_explore
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/dse_pd.log
cd $A
while [ $# -ge 3 ]; do
    des=$1; cfgf=$2; base=$3; shift 3
    T=${base}G50
    ST=$(ls -d $A/$des/runs/$base/*-openroad-stamidpnr-2 2>/dev/null | tail -1)/state_out.json
    [ -f "$ST" ] || { echo "$(date -Is) grt50 $T: no STAMidPNR-2 state in $base" >> $LOG; continue; }
    while [ "$(free -m | awk '/Mem/{print $7}')" -lt 7000 ]; do
        [ -e $A/.abort_vc4_explore ] && { echo "$(date -Is) abort grt50 before $T" >> $LOG; exit 0; }
        sleep 60
    done
    [ -e $A/.abort_vc4_explore ] && { echo "$(date -Is) abort grt50 before $T" >> $LOG; exit 0; }
    echo "$(date -Is) start $T ($des/$cfgf, GlobalRouting only, default overflow iterations, from $base STAMidPNR-2)" >> $LOG
    CONFIG=$cfgf bash run_pd_mk.sh $des $T --with-initial-state $ST \
        --from OpenROAD.GlobalRouting --to OpenROAD.GlobalRouting > $A/$T.log 2>&1
    g=$(ls $A/$des/runs/$T/*-openroad-globalrouting/openroad-globalrouting.log 2>/dev/null | tail -1)
    it=$(grep -cE '^\[INFO GRT-0101\]|Running extra iterations|iteration' $g 2>/dev/null)
    gr="usage $(grep -E '^Total ' $g 2>/dev/null | tail -1 | awk '{print $4" overflow "$NF}') wire $(grep -o 'Total wirelength: [0-9]*' $g 2>/dev/null | tail -1 | awk '{print $3}')"
    echo "$(date -Is) end $T: GRT (50 iterations) $gr" >> $LOG
done
