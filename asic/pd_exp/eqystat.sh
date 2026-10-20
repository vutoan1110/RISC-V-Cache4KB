#!/usr/bin/env bash
# FLOW_JOURNAL Incident 93: progress of the stock EQY rerun (final3_eqy)
tail -2 /mnt/e/Projects/RISCV-research/asic/x_exps.log
free -g | sed -n 2p
f=$(ls /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/final3_eqy/*yosys-eqy/yosys-eqy.log 2>/dev/null)
[ -n "$f" ] || { echo "no log yet"; exit 0; }
echo "proved: $(grep -a -c 'Proved equivalence' $f)  not proved: $(grep -a -c 'Could not prove' $f)  errors: $(grep -a -c 'encountered an error' $f)  command-not-found: $(grep -a -c 'command not found' $f)"
tail -1 $f | cut -c1-220
