#!/usr/bin/env bash
# Full verification chain at the 4 KiB cache configuration, run to the
# Double-Execution Protocol: every measurement twice, only exact matches
# accepted. 4 KiB is the configuration being taken to silicon, so this is the
# chain that has to be clean before PD is worth starting.
#
# Lint is run separately (scripts/lint_rtl.sh now sweeps LINE_COUNT 64 and 256;
# 8 combinations, 0 correctness warnings).
#
# Questa is single-instance per work library, so these run in sequence. They
# share the machine with the Quartus fits, which is tolerable now that the 1 KiB
# PD flow has been stopped.
set -uo pipefail
cd "$(dirname "$0")/.."
V=C:/questasim64_2024.1/win64/vsim.exe

echo "######## 1. directed regression  $(date -Is)"
# run_full_regression.do already sweeps capacity: `foreach lc {128 256}`.
for pass in 1 2; do
  "$V" -c -do "do tb/run_full_regression.do; quit -f" \
       > "results/regression_4kb_pass$pass.log" 2>&1
  p=$(grep -c '^# \[PASS\]' "results/regression_4kb_pass$pass.log")
  f=$(grep -c '\[FAIL\]'    "results/regression_4kb_pass$pass.log")
  echo "  pass $pass: $p PASS, $f FAIL"
done

echo "######## 2. UVM at CACHE_LINE_COUNT=256  $(date -Is)"
# run_uvm.do argument 5 is line_count; argument 4 is line_words.
for pass in 1 2; do
  ok=0; tot=0
  for t in core_smoke_test core_random_test axi_smoke_test soc_directed_test soc_periph_test; do
    tot=$((tot+1))
    "$V" -c -do "do verification/uvm/run_uvm.do $t 1 1 4 256; quit -f" \
         > "results/uvm_4kb_${t}_pass$pass.log" 2>&1
    grep -q 'UVM status: PASS' "results/uvm_4kb_${t}_pass$pass.log" && ok=$((ok+1)) \
      || echo "    FAIL $t"
  done
  echo "  pass $pass: $ok/$tot PASS"
done

echo "######## 3. Embench matrix at 256 lines, twice  $(date -Is)"
python scripts/run_ablation.py --compile --lines 256 --out results/ablation_4kb_p1.csv 2>&1 | tail -2
python scripts/run_ablation.py            --lines 256 --out results/ablation_4kb_p2.csv 2>&1 | tail -2
echo "######## 4. verify  $(date -Is)"
python scripts/verify_double.py results/ablation_4kb_p1.csv results/ablation_4kb_p2.csv \
       --key kernel --also config
echo "######## fullchain done $(date -Is)"
