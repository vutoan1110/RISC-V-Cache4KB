#!/usr/bin/env bash
# FLOW_JOURNAL Incident 86: sequential equivalence by signal correspondence (ABC scorr, k-induction
# on candidate equivalences found by simulation). If the miter output reduces to constant 0 the two
# designs are equivalent from the initial (reset) state.  usage: run_scorr.sh <aig> <tag> [F]
cd /mnt/e/Projects/RISCV-research/asic/equiv/sec
A=${1:?aig}; T=${2:?tag}; F=${3:-1}
echo "$(date -Is) start scorr $T F=$F" >> runs.log
/usr/bin/time -f "%e s %M kB" stdbuf -oL -eL /nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys-abc \
  -c "read_aiger $A; print_stats; scorr -v -F $F; print_stats; write_aiger scorr_$T.aig" > scorr_$T.log 2>&1
echo "$(date -Is) end scorr $T rc=$?" >> runs.log
