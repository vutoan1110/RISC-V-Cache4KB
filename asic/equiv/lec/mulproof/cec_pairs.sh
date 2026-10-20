#!/usr/bin/env bash
# FLOW_JOURNAL Incident 89: &cec on pairs of pure multiplier AIGs; usage: cec_pairs.sh a1 b1 [a2 b2 ...]
cd /mnt/e/Projects/RISCV-research/asic/equiv/lec
A=/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys-abc
while [ $# -ge 2 ]; do
  r=$(timeout ${CEC_T:-300} $A -c "&cec -v $1 $2" 2>&1 | grep -a -E "Networks are|NOT EQUIV|UNDECIDED" | tail -n 1)
  printf "%-34s %-34s %s\n" "$1" "$2" "${r:-NO VERDICT (timeout)}"
  shift 2
done
