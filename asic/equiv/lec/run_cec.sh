#!/usr/bin/env bash
# FLOW_JOURNAL Incident 89: ABC combinational equivalence of the register-mapped LEC pair.
# usage: run_cec.sh <tag> "<abc commands>"
cd /mnt/e/Projects/RISCV-research/asic/equiv/lec
T=${1:?tag}; C=${2:?cmds}
echo "$(date -Is) start $T : $C" >> runs.log
/usr/bin/time -f "%e s %M kB" stdbuf -oL -eL /nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys-abc -c "$C" > $T.log 2>&1
echo "$(date -Is) end $T rc=$?" >> runs.log
