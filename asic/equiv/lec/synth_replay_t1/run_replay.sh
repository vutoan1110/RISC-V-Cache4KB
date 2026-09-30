#!/usr/bin/env bash
# FLOW_JOURNAL Incident 89 (t1 variant: techmap split as -max_iter 1 + snapshot + techmap): replay OpenLane's synthesis of final_B (step 06) with the SAME script
# (openlane-local copy + 3 write_rtlil snapshots around the two ABC calls), SAME config.json/extra.json,
# SAME yosys; the replayed netlist must be byte-identical to 06-yosys-synthesis/soc_asic_top.nl.v.
R=/mnt/e/Projects/RISCV-research/asic
S=$R/soc_dm_4kb/runs/final_B/06-yosys-synthesis
D=$R/equiv/lec/synth_replay_t1
export SYNTH_SNAP=$D
Y=/nix/store/zdhr86kv5rxlp0s58rzxk1aki1igankx-yosys-with-plugins-python3-3.11.9-env/bin/yosys
cd $D
echo "$(date -Is) start replay_t1" >> ../runs.log
$Y -y $D/synthesize.py -- --config-in $S/config.json --extra-in $S/extra.json --output $D/soc_asic_top.nl.v > replay.log 2>&1
echo "rc=$?"
echo "$(date -Is) end replay_t1" >> ../runs.log
ls -la t1_iter1.il n1*.il soc_asic_top.nl.v
cmp $S/soc_asic_top.nl.v $D/soc_asic_top.nl.v && echo "T1 REPLAY NETLIST BYTE-IDENTICAL TO STEP 06" || echo "T1 replay netlist differs from step 06 (expected possible: split techmap)"
