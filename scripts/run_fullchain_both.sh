#!/usr/bin/env bash
# Full chain after the icache_tag_ram change, at BOTH capacities.
#
# The change makes valid_bits packed instead of an unpacked array with a reset
# loop, matching dcache_tag_ram.v. It is semantically identical, so the 1 KiB
# results must come back byte-for-byte -- that is the check, not a formality.
# 4 KiB is run because it is the configuration heading for silicon and the
# reason the change was needed at all: Verilator will not unroll a 256-iteration
# delayed assignment to an array, so the old form failed OpenLane's own lint.
#
# Double-Execution throughout.
set -uo pipefail
cd "$(dirname "$0")/.."
V=C:/questasim64_2024.1/win64/vsim.exe

echo "######## 1. directed regression x2  $(date -Is)"
for pass in 1 2; do
  "$V" -c -do "do tb/run_full_regression.do; quit -f" \
       > "results/regression_tagfix_pass$pass.log" 2>&1
  echo "  pass $pass: $(grep -c '^# \[PASS\]' results/regression_tagfix_pass$pass.log) PASS, $(grep -c '\[FAIL\]' results/regression_tagfix_pass$pass.log) FAIL"
done

echo "######## 2. UVM at 64 and 256 lines, x2  $(date -Is)"
for lc in 64 256; do
  for pass in 1 2; do
    ok=0
    for t in core_smoke_test core_random_test axi_smoke_test soc_directed_test soc_periph_test; do
      "$V" -c -do "do verification/uvm/run_uvm.do $t 1 1 4 $lc; quit -f" \
           > "results/uvm_tagfix_${lc}_${t}_p$pass.log" 2>&1
      grep -q 'UVM status: PASS' "results/uvm_tagfix_${lc}_${t}_p$pass.log" && ok=$((ok+1)) || echo "    FAIL $t lc=$lc"
    done
    echo "  lc=$lc pass $pass: $ok/5 PASS"
  done
done

echo "######## 3. Embench, 64 and 256 lines, x2 each  $(date -Is)"
python scripts/run_ablation.py --compile --lines 64  --out results/tagfix_1kb_p1.csv 2>&1 | tail -2
python scripts/run_ablation.py           --lines 64  --out results/tagfix_1kb_p2.csv 2>&1 | tail -2
python scripts/run_ablation.py           --lines 256 --out results/tagfix_4kb_p1.csv 2>&1 | tail -2
python scripts/run_ablation.py           --lines 256 --out results/tagfix_4kb_p2.csv 2>&1 | tail -2

echo "######## 4. verify  $(date -Is)"
echo "-- 1 KiB, the two passes against each other"
python scripts/verify_double.py results/tagfix_1kb_p1.csv results/tagfix_1kb_p2.csv --key kernel --also config | tail -2
echo "-- 1 KiB against the canonical matrix (the change must move nothing)"
python scripts/verify_double.py results/ablation_synctag_all.csv results/tagfix_1kb_p1.csv --key kernel --also config | tail -2
echo "-- 4 KiB, the two passes against each other"
python scripts/verify_double.py results/tagfix_4kb_p1.csv results/tagfix_4kb_p2.csv --key kernel --also config | tail -2
echo "-- 4 KiB against this evening's verified matrix"
python scripts/verify_double.py results/ablation_4kb_p1.csv results/tagfix_4kb_p1.csv --key kernel --also config | tail -2
echo "######## done $(date -Is)"
