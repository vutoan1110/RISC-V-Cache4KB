#!/usr/bin/env bash
# R12 invariant proof (see gen.py): real RTL must prove, the mutant must not.
cd "$(dirname "$0")"
H=/mnt/e/Projects/RISCV-research/hdl
Y=$(ls -d /nix/store/*-yosys-*/bin/yosys | grep -v abc | head -1)
SUB="$H/alu.v $H/aludec.v $H/branch.v $H/predictor/bht_2bit.v $H/controller.v $H/extend.v $H/hazard_unit.v $H/maindec.v $H/regfile.v"
for v in real mutant; do
  cat > $v/prove.ys <<YS
read_verilog -formal -sv -D__openlane__ $SUB $v/datapath_fv.v $v/riscv_core_fv.v $v/fv_top.sv
prep -top fv_top
flatten
async2sync
memory_map
opt -fast
sat -tempinduct -prove-asserts -set-at 1 reset_n 0 -maxsteps 6 -timeout 3000
YS
  $Y -q -l $v/prove.log $v/prove.ys > /dev/null 2>&1
  echo "$v rc=$? : $(grep -E 'Induction step proven|SUCCESS|proof failed|failed' $v/prove.log | tail -2 | tr '\n' ' ') asserts=$(grep -cE '^\s+[0-9]+/[0-9]+: \$assert' $v/prove.log)"
done
