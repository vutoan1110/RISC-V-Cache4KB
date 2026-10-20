#!/usr/bin/env bash
# FLOW_JOURNAL Incident 96 (2026-10-03): byte-exact replay of an R14-era OpenLane synthesis step (06) with the
# CURRENT openlane-local synthesize.py (incl. the SYNTH_OPT_DFF_SAT patch) plus the four Incident 89 snapshot
# hooks (synthesize.py here = openlane-local + 4 write_rtlil lines, nothing else). The replayed netlist must be
# byte-identical to the step's own; the snapshots then are OpenLane's exact intermediate states:
#   s_pre_techmap.il, n1_pre_abc_fast.il (N1), n1b_pre_abc_lib.il, n2a_post_abc_lib.il
#   bash run_replay_r14.sh <design dir> <run tag> <out subdir>      (pairs may repeat: d1 t1 o1 d2 t2 o2 ...)
R=/mnt/e/Projects/RISCV-research/asic
D=$R/equiv/lec/synth_replay_r14
PY=${SYNTH_PY:-$D/synthesize.py}   # SYNTH_PY=$D/synthesize_n1only.py: only the N1 hook
Y=/nix/store/zdhr86kv5rxlp0s58rzxk1aki1igankx-yosys-with-plugins-python3-3.11.9-env/bin/yosys
while [ $# -ge 3 ]; do
    des=$1; tag=$2; o=$D/$3; shift 3
    S=$R/$des/runs/$tag/06-yosys-synthesis
    mkdir -p $o && cd $o
    export SYNTH_SNAP=$o
    echo "$(date -Is) start replay $des/$tag -> $o ($(basename $PY))" >> $D/runs.log
    $Y -y $PY -- --config-in $S/config.json --extra-in $S/extra.json --output $o/soc_asic_top.nl.v > $o/replay.log 2>&1
    rc=$?
    if cmp -s $S/soc_asic_top.nl.v $o/soc_asic_top.nl.v; then v="REPLAY NETLIST BYTE-IDENTICAL TO STEP 06"; else v="REPLAY NETLIST DIFFERS FROM STEP 06"; fi
    echo "$(date -Is) end replay $des/$tag rc=$rc: $v; $(ls $o/*.il 2>/dev/null | wc -l) snapshots" >> $D/runs.log
done
