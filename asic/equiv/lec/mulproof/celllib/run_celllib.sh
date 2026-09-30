#!/usr/bin/env bash
cd /mnt/e/Projects/RISCV-research/asic/equiv/lec/mulproof/celllib
/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys -l prove_cells.log prove_cells.ys > /dev/null 2>&1; echo "prove_cells rc=$?"
grep -a -E "SUCCESS|FAIL|Solving problem|ERROR" prove_cells.log
/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys -l prove_cells_neg.log prove_cells_neg.ys > /dev/null 2>&1; echo "prove_cells_neg rc=$? (must be non-zero)"
grep -a -E "SUCCESS|FAIL|failed|ERROR" prove_cells_neg.log | head -3
