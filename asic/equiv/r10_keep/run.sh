#!/usr/bin/env bash
# Synthesise both variants with OpenLane's own AREA 0 ABC script and the tt
# liberty, then report the longest path (cells) and the enable->q depth.
set -e
cd $(dirname $0)
LIB=$(ls /home/toanl/.volare/volare/sky130/versions/*/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib | head -1)
Y=$(ls -d /nix/store/*-yosys-*/bin/yosys | grep -v abc | head -1)
for m in cnt_a cnt_b; do
  $Y -q -l $m.log -p "read_verilog cnt_test.v; hierarchy -top $m; synth -flatten -top $m; dfflibmap -liberty $LIB; abc -script /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/r9_ecf4/06-yosys-synthesis/AREA_0.abc -D 20000 -liberty $LIB; opt_clean; stat -liberty $LIB; ltp -noff; write_verilog -noattr $m.nl.v" || true
  echo "$m: $(grep -m1 'Chip area' $m.log) $(grep -m1 'Longest topological path' $m.log)"
done
