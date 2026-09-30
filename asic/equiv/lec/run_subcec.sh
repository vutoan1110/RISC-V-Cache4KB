#!/usr/bin/env bash
# FLOW_JOURNAL Incident 89: final step-A closure - &cec of the 34 multiplier-cone outputs after the
# proven-multiplier substitution (mulsub.py subst).  usage: run_subcec.sh <gold.aig> <gate.aig> <tag>
cd /mnt/e/Projects/RISCV-research/asic/equiv/lec
echo "$(date -Is) start subcec $3" >> runs.log
/usr/bin/time -f "%e s %M kB" /nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys-abc -c "&cec -v $1 $2" > $3.log 2>&1
echo "$(date -Is) end subcec $3" >> runs.log
grep -a -E "Networks are|NOT EQUIV|UNDECIDED|s .* kB" $3.log | tail -n 3
