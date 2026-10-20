#!/usr/bin/env bash
# R11 candidate: sequential equivalence of icache_controller before/after, at
# three index widths (6, 8 = the 4 KiB ASIC, 3 = INDEX_WIDTH == L0 bits).
cd "$(dirname "$0")"
Y=$(ls -d /nix/store/*-yosys-*/bin/yosys | grep -v abc | head -1)
for iw in 6 8 3; do
  tw=$((28 - iw))
  cat > eq_$iw.ys <<YS
read_verilog -sv -D__openlane__ icache_controller_old.v
hierarchy -top icache_controller -chparam INDEX_WIDTH $iw -chparam TAG_WIDTH $tw
proc; flatten; rename -top gold
design -stash gold
read_verilog -sv -D__openlane__ icache_controller_new.v
hierarchy -top icache_controller -chparam INDEX_WIDTH $iw -chparam TAG_WIDTH $tw
proc; flatten; rename -top gate
design -stash gate
design -copy-from gold -as gold gold
design -copy-from gate -as gate gate
proc; opt_clean; memory_map; opt_clean
async2sync
equiv_make gold gate eq
hierarchy -top eq
flatten
equiv_simple -seq 2
equiv_induct -seq 2
equiv_status -assert
YS
  $Y -q -l eq_$iw.log eq_$iw.ys > /dev/null 2>&1
  echo "INDEX_WIDTH=$iw rc=$? : $(grep -E 'Of those cells|successfully proven|unproven \$equiv cells in' eq_$iw.log | tail -2 | tr '\n' ' ')"
done
