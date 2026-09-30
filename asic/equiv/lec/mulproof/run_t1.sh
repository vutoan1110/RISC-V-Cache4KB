#!/usr/bin/env bash
# FLOW_JOURNAL Incident 89: t1 snapshot multiplier -> AIG -> pure multiplier -> &cec against n1_pure (N1 in context).
cd /mnt/e/Projects/RISCV-research/asic/equiv/lec/mulproof
/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys -q -l t1_pure.log t1_pure.ys > /dev/null 2>&1; echo "yosys rc=$?"
