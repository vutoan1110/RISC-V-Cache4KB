#!/usr/bin/env bash
# FLOW_JOURNAL Incident 89: try several ABC CEC engines on one pair (sequentially, 10 min each).
# usage: try_engines.sh <gold.aig> <gate.aig> <tag>
cd /mnt/e/Projects/RISCV-research/asic/equiv/lec
A=/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys-abc
G=$1; T=$2; X=$3
for e in "cec -v" "dcec -v" "&cec -x -v -C 1000000" "iprove -v"; do
  n=$(echo "$e" | tr -d '&-' | tr ' ' '_' | cut -c1-12)
  case "$e" in
    "&"*) cmd="$e $G $T" ;;
    "iprove"*) cmd="miter -m $G $T; $e" ;;
    *) cmd="$e $G $T" ;;
  esac
  echo "$(date -Is) start $X $e" >> runs.log
  timeout 600 $A -c "$cmd" > cof/eng_${X}_${n}.log 2>&1
  echo "$(date -Is) end $X $e rc=$?" >> runs.log
  printf "%-26s %s\n" "$e" "$(grep -a -E "equivalent|NOT EQUIV|UNDECIDED|UNSAT|SAT|proved|Networks" cof/eng_${X}_${n}.log | tail -n 1 | cut -c1-100)"
done
