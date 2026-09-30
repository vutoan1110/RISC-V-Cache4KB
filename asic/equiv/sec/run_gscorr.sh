#!/usr/bin/env bash
# FLOW_JOURNAL Incident 86: sequential equivalence by ABC &scorr with a prefix of G frames (skips the
# reset transient: the prefix itself is covered by BMC inside &scorr) and P concurrent processes.
# The miter is proved when its single output reduces to constant 0.  usage: run_gscorr.sh <aig> <tag> <G> <P>
cd /mnt/e/Projects/RISCV-research/asic/equiv/sec
A=${1:?aig}; T=${2:?tag}; G=${3:-8}; P=${4:-8}
echo "$(date -Is) start gscorr $T G=$G P=$P" >> runs.log
/usr/bin/time -f "%e s %M kB" stdbuf -oL -eL /nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys-abc \
  -c "read_aiger $A; &get -n; &ps; &scorr -v -G $G -P $P; &ps; &put; print_stats; write_aiger gscorr_$T.aig" > gscorr_$T.log 2>&1
echo "$(date -Is) end gscorr $T rc=$?" >> runs.log
