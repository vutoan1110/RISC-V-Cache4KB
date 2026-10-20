#!/usr/bin/env bash
# FLOW_JOURNAL Incident 89: per-case (alu_ctrl_e one-hot select = v) equivalence of the multiplier
# cone. For each v: miter of cof/g_v.aig vs cof/t_v.aig, every output solved with &sat -a -z.
cd /mnt/e/Projects/RISCV-research/asic/equiv/lec
A=/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys-abc
C=${1:-200000}
echo "$(date -Is) start cof C=$C" >> runs.log
for v in $(seq 0 15); do
  $A -c "&r cof/g_$v.aig; &miter cof/t_$v.aig; &sat -a -z -C $C -v; &w cof/m_$v.aig" > cof/sat_$v.log 2>&1
  printf "case %2d: %s | %s | %s\n" $v "$(grep -h 'Unsat calls' cof/sat_$v.log | awk '{print "unsat="$3}')" "$(grep -h 'Sat   calls' cof/sat_$v.log | awk '{print "sat="$3}')" "$(grep -h 'Undef calls' cof/sat_$v.log | awk '{print "undef="$3}')"
done
echo "$(date -Is) end cof" >> runs.log
