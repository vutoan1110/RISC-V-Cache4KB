#!/usr/bin/env bash
# FLOW_JOURNAL Incident 89: gold-context split techmap runs (rtl_t2.ys, rtl_t3.ys), sequential.
cd /mnt/e/Projects/RISCV-research/asic/equiv/lec/mulproof
for n in 2 3; do
  /nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys -q -l rtl_t$n.log rtl_t$n.ys > /dev/null 2>&1; echo "rtl_t$n yosys rc=$?"
  echo "  \$macc cells: $(grep -c 'cell \$macc' rtl_t$n.il)  \$fa cells: $(grep -c 'cell \$fa' rtl_t$n.il)"
done
