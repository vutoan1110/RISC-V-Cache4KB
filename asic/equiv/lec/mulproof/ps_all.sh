#!/usr/bin/env bash
# FLOW_JOURNAL Incident 89: AND/level statistics of every pure multiplier AIG.
cd /mnt/e/Projects/RISCV-research/asic/equiv/lec
A=/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys-abc
for f in mulproof/mulA.aig mulproof/mulB.aig mulproof/mulC.aig mulproof/mulG.aig mulproof/mulN.aig mulproof/rtl_pure.aig mulproof/t0_pure.aig mulproof/n1_pure.aig mul_pure_gold.aig mul_pure_gate.aig; do
  printf "%-26s %s\n" $f "$($A -c "&r $f; &ps" 2>&1 | grep -a 'and =' | sed 's/\x1b\[[0-9;]*m//g' | tr -s ' ' | cut -c1-110)"
done
