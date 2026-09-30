#!/usr/bin/env bash
# FLOW_JOURNAL Incident 86: double execution of the SEC front end. Rebuilds gold_pre / gate_pre and
# the miter from scratch into pass2/, so the miter can be compared byte for byte with pass 1.
# (sram_cut.py runs on Windows Python afterwards: WSL Python is the part of this machine that faults.)
set -u
S=/mnt/e/Projects/RISCV-research/asic/equiv/sec
Y=/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys
mkdir -p $S/pass2 && cd $S/pass2
cp ../gold_front_end.ys ../gate_front_end.ys ../gold_pre.ys ../gate_pre.ys ../miter.ys ../wrap.v .
echo "$(date -Is) start pass2 pre" >> ../runs.log
$Y -q -l gold_pre.log gold_pre.ys > gold_pre.out 2>&1; echo "gold_pre rc=$?" >> ../runs.log
$Y -q -l gate_pre.log gate_pre.ys > gate_pre.out 2>&1; echo "gate_pre rc=$?" >> ../runs.log
echo "$(date -Is) end pass2 pre" >> ../runs.log
