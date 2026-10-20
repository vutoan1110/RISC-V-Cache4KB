#!/usr/bin/env bash
# FLOW_JOURNAL Incident 86: sequential equivalence of the SEC miter with ABC dprove.
# usage: run_dprove.sh <miter.aig> <tag>
cd /mnt/e/Projects/RISCV-research/asic/equiv/sec
A=${1:?aig}; T=${2:?tag}
echo "$(date -Is) start dprove $T" >> runs.log
/usr/bin/time -f "%e s %M kB" /nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys-abc \
  -c "read_aiger $A; print_stats; dprove -v -T 3600; print_stats" > dprove_$T.log 2>&1
echo "$(date -Is) end dprove $T rc=$?" >> runs.log
