#!/usr/bin/env bash
# FLOW_JOURNAL Incident 89: SAT-sweeping CEC (&cec, fraig-based: merges internal equivalent nodes
# - forwarded operands, partial products, adder-tree sums/carries - before attacking the outputs)
# on one alu_ctrl cofactor of the multiplier cone.  usage: run_cofcec.sh <case> <conflicts>
cd /mnt/e/Projects/RISCV-research/asic/equiv/lec
v=${1:?case}; C=${2:-100000}
echo "$(date -Is) start cofcec $v C=$C" >> runs.log
stdbuf -oL /nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys-abc -c "&cec -v -C $C cof/g_$v.aig cof/t_$v.aig" > cof/cec_$v.log 2>&1
echo "$(date -Is) end cofcec $v" >> runs.log
tail -n 3 cof/cec_$v.log
