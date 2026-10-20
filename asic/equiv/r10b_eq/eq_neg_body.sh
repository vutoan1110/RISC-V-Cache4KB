#!/usr/bin/env bash
# R10b structural-only claim: old and new modules are sequentially equivalent.
cd "$(dirname "$0")"
Y=$(ls -d /nix/store/*-yosys-*/bin/yosys | grep -v abc | head -1)
H=/mnt/e/Projects/RISCV-research/hdl
eq() { # module oldfile newfile(s...) extra-files
  local m=$1 old=$2 new=$3; shift 3
  cat > eqneg_$m.ys <<YS
read_verilog -sv -D__openlane__ $old $*
hierarchy -top $m
proc
flatten
rename $m ${m}_gold
design -stash gold
read_verilog -sv -D__openlane__ $new $*
hierarchy -top $m
proc
flatten
rename $m ${m}_gate
design -stash gate
design -copy-from gold -as ${m}_gold ${m}_gold
design -copy-from gate -as ${m}_gate ${m}_gate
proc; opt_clean
memory_map; opt_clean
async2sync
equiv_make ${m}_gold ${m}_gate eq
hierarchy -top eq
flatten
equiv_simple -seq 2
equiv_induct -seq 2
equiv_status -assert
YS
  $Y -q -l eqneg_$m.log eqneg_$m.ys > /dev/null 2>&1; echo "$m rc=$? : $(grep -E 'Found [0-9]+ \$equiv|unproven|Equivalence successfully proven' eqneg_$m.log | tr '\n' ' ')"
}
eq perf_counters perf_counters_old.v perf_counters_mutant.v
SUB="$H/alu.v $H/extend.v $H/regfile.v $H/branch.v $H/hazard_unit.v $H/predictor/bht_2bit.v"

