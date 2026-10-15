#!/usr/bin/env bash
# Register file / BHT in M9K (see gen.py): k-induction proofs of the FPGA versions against the previous arrays, and of
# the read-ahead protocol in the datapath. The real RTL must prove all three, the mutant must fail all three.
#   python gen.py <root> real ; python gen.py <root> mutant --mutant      (Windows side)
#   bash run.sh <root as seen from WSL>
cd "$(dirname "$0")"
H=${1:-/mnt/e/Projects/RISCV-research}/hdl
Y=$(ls -d /nix/store/*-yosys-*/bin/yosys | grep -v abc | head -1)
SUB="$H/alu.v $H/aludec.v $H/branch.v $H/predictor/bht_2bit.v $H/extend.v $H/hazard_unit.v $H/regfile.v"
for v in real mutant; do
  for p in rf bht dp; do
    case $p in
      rf)  SRC="$v/rf_old.v $v/rf_new.v $v/fv_rf.sv"; TOP=fv_rf; N=6 ;;
      bht) SRC="$v/bht_old.v $v/bht_new.v $v/fv_bht.sv"; TOP=fv_bht; N=6 ;;
      dp)  SRC="$SUB $v/datapath_fv.v"; TOP=datapath; N=8 ;;
    esac
    cat > $v/prove_$p.ys <<YS
read_verilog -formal -sv $SRC
prep -top $TOP
flatten
async2sync
memory_map
opt -fast
sat -tempinduct -prove-asserts -set-init-zero -set-at 1 reset_n 0 -maxsteps $N -timeout 3000
YS
    $Y -q -l $v/prove_$p.log $v/prove_$p.ys > /dev/null 2>&1
    echo "$v $p rc=$? : $(grep -E 'Induction step proven|SUCCESS|proof failed|failed' $v/prove_$p.log | tail -2 | tr '\n' ' ') asserts=$(grep -cE '^\s+[0-9]+/[0-9]+: \$assert' $v/prove_$p.log)"
  done
done
