#!/usr/bin/env bash
# R10a k-induction proof (see gen.py). Runs the real RTL at 256 and 8 lines,
# then the negative control (mutant) which must FAIL.
set -u
cd "$(dirname "$0")"
R=/mnt/e/Projects/RISCV-research
Y=$(ls -d /nix/store/*-yosys-*/bin/yosys | grep -v abc | head -1)
prove() { # label dir linecount
  cat > $2/prove_$3.ys <<YS
read_verilog -formal -sv $2/icache_controller_fv.v $2/icache_tag_ram_fv.v $2/fv_top.sv
hierarchy -top fv_top -chparam LINE_COUNT $3
prep -top fv_top
flatten
async2sync
memory_map
opt -fast
sat -tempinduct -prove-asserts -set-at 1 reset_n 0 -maxsteps 8 -timeout 3000
YS
  $Y -q -l $2/prove_$3.log $2/prove_$3.ys > /dev/null 2>&1; local rc=$?
  local verdict=$(grep -E "SUCCESS|FAIL|failed|Induction step proven|proven" $2/prove_$3.log | tail -2 | tr '\n' ' ')
  echo "$1 lines=$3 rc=$rc : $verdict"
}
# harness generated on Windows: python gen.py <root> real ; python gen.py <root> mutant --mutant
prove REAL real 256
prove REAL real 8
prove MUTANT mutant 256
