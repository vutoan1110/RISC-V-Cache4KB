#!/usr/bin/env bash
# FLOW_JOURNAL Incident 89: algebraic (backward-rewriting) polynomial of a 64-bit-output multiplier AIG.
# usage: run_polyn.sh <x.aig> [timeout_s]
cd /mnt/e/Projects/RISCV-research/asic/equiv/lec/mulproof
S=$(python3 -c 'print("+".join("%d*o%d" % (k, k) for k in range(64)))' 2>/dev/null)
[ -z "$S" ] && S=$(for k in $(seq 0 63); do printf "%d*o%d+" $k $k; done | sed 's/+$//')
timeout ${2:-600} /nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys-abc -c "&r $1; &polyn -s -v -S $S" > polyn_$(basename $1 .aig).log 2>&1
echo "rc=$?"
