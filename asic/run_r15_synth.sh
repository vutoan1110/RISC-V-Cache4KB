#!/usr/bin/env bash
# R15 synthesis-identity check: OpenLane up to Yosys.Synthesis with the R15 snapshot, then compare the netlist
# with r14_A's byte for byte.
A=/mnt/e/Projects/RISCV-research/asic
cd $A && CONFIG=config_R15_synth.json bash run_pd_mk.sh soc_dm_4kb r15_synth --to Yosys.Synthesis > $A/r15_synth.log 2>&1
echo "flow rc=$?"
N=$A/soc_dm_4kb/runs/r15_synth/06-yosys-synthesis/soc_asic_top.nl.v
O=$A/soc_dm_4kb/runs/r14_A/06-yosys-synthesis/soc_asic_top.nl.v
sha256sum $O $N
cmp -s $O $N && echo "[IDENTICAL] R15 ASIC netlist == R14" || echo "[DIFF] R15 ASIC netlist differs from R14"
