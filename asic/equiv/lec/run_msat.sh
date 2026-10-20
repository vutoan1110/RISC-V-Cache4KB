#!/usr/bin/env bash
# FLOW_JOURNAL Incident 89: prove every output of the register-mapped LEC miter individually.
# pass a: ABC &sat -a -z with 2,000 conflicts per output (fast, clears almost everything);
# pass b: the residual miter again with 200,000 conflicts. Proved outputs become literal 0.
# usage: run_msat.sh <tag>   (reads gold_lec<tag>.aig, gate_lec<tag>.aig)
cd /mnt/e/Projects/RISCV-research/asic/equiv/lec
T=${1:?tag}
A=/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys-abc
echo "$(date -Is) start msat$T" >> runs.log
$A -c "&r ${G:-gold_lec$T.aig}; &miter ${H:-gate_lec$T.aig}; &ps; &sat -a -z -C 2000 -v; &ps; &w msat${T}_a.aig" > msat${T}_a.log 2>&1
$A -c "&r msat${T}_a.aig; &sat -a -z -C 200000 -v; &ps; &w msat${T}_b.aig" > msat${T}_b.log 2>&1
echo "$(date -Is) end msat$T" >> runs.log
grep -h -E "Unsat calls|Sat   calls|Undef calls" msat${T}_a.log msat${T}_b.log
