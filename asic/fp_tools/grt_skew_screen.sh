#!/usr/bin/env bash
# Mid-PnR STA with global-route parasitics on the state right after the first global route of earlier runs
# (OpenLane's own STAMidPNR step, --with-initial-state <run>/39-openroad-globalrouting/state_out.json).
# usage: bash grt_skew_screen.sh <design> <source run> <config> <new tag> [...groups of four]
A=/mnt/e/Projects/RISCV-research/asic
cd $A
while [ $# -ge 4 ]; do
    des=$1; src=$2; cfg=$3; tag=$4; shift 4
    ST=$(ls -d $A/$des/runs/$src/*-openroad-globalrouting | head -1)/state_out.json
    echo "$(date -Is) SCREEN $tag: STAMidPNR with global-route parasitics on the state after the first global route of $src" >> $A/gated_pd.log
    CONFIG=$cfg bash run_pd_mk.sh $des $tag --with-initial-state $ST --from OpenROAD.STAMidPNR-3 --to OpenROAD.STAMidPNR-3 > $A/$tag.log 2>&1
    d=$(ls -d $A/$des/runs/$tag/*-openroad-stamidpnr* | tail -1)
    h=$(grep -h "hold skew" $d/skew.min.rpt | head -1 | awk '{print $1}'); s=$(grep -h "setup skew" $d/skew.max.rpt | head -1 | awk '{print $1}')
    m=$(python3 -c "import json;m=json.load(open('$d/state_out.json'))['metrics'];print('setup nom_tt %.3f hold nom_tt %.3f'%(m['timing__setup__ws__corner:nom_tt_025C_1v80'],m['timing__hold__ws__corner:nom_tt_025C_1v80']))" 2>/dev/null)
    echo "$(date -Is) SCREEN $tag done: hold skew $h, setup skew $s, $m" >> $A/gated_pd.log
    echo "$tag: hold skew $h setup skew $s $m"
done
