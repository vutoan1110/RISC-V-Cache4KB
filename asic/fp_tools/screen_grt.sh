#!/usr/bin/env bash
# Global routing only, with the default 50 overflow iterations, from the STAMidPNR-2 state of a screening run that
# capped global routing at 15 iterations. For the same placement, CTS and repair, the overflow printed here is the
# phase-1 gate value of run_gated_pd.sh (GRT overflow <= 500) for that floorplan.
#   bash fp_tools/screen_grt.sh <design dir> <config file> <screening tag> [more groups of three ...]
# New run tag <screening tag>G50. Summary line in dse_pd.log. A group waits for >= 7 GB free memory.
# Cooperative stop between groups: touch asic/.abort_fp_screen
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
        [ -e $A/.abort_fp_screen ] && { echo "$(date -Is) abort grt50 before $T" >> $LOG; exit 0; }
        sleep 60
    done
    [ -e $A/.abort_fp_screen ] && { echo "$(date -Is) abort grt50 before $T" >> $LOG; exit 0; }
    echo "$(date -Is) start $T ($des/$cfgf, GlobalRouting only, default overflow iterations, from $base STAMidPNR-2)" >> $LOG
    CONFIG=$cfgf bash run_pd_mk.sh $des $T --with-initial-state $ST \
        --from OpenROAD.GlobalRouting --to OpenROAD.GlobalRouting > $A/$T.log 2>&1
    g=$(ls $A/$des/runs/$T/*-openroad-globalrouting/openroad-globalrouting.log 2>/dev/null | tail -1)
    gr="usage $(grep -E '^Total ' $g 2>/dev/null | tail -1 | awk '{print $4" overflow "$NF}') wire $(grep -o 'Total wirelength: [0-9]*' $g 2>/dev/null | tail -1 | awk '{print $3}')"
    echo "$(date -Is) end $T: GRT (50 iterations) $gr" >> $LOG
done
