#!/usr/bin/env bash
# FLOW_JOURNAL Incident 86: deep BMC on a (negative-control) miter.  usage: run_bmc.sh <aig> <tag> <frames>
cd /mnt/e/Projects/RISCV-research/asic/equiv/sec
A=${1:?aig}; T=${2:?tag}; F=${3:-100}
echo "$(date -Is) start bmc $T F=$F" >> runs.log
/usr/bin/time -f "%e s %M kB" /nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys-abc \
  -c "read_aiger $A; print_stats; bmc3 -F $F -T 5400 -v" > bmc_$T.log 2>&1
echo "$(date -Is) end bmc $T rc=$?" >> runs.log
