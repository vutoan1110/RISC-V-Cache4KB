#!/usr/bin/env bash
# R16 (2026-10-06, review item M1): FAST_HIT. The DSE and N-way cores get a parameter FAST_HIT (default 0); with 1
# a main-array hit is answered in ST_LOOKUP, one cycle earlier, so the controller's hit latency equals the DM
# controller's and the organisation effect can be measured without the controller confound. With FAST_HIT 0 every
# configuration must reproduce the R15 chain byte for byte (proved formally as well: asic/equiv/r16_eq, 24 module
# checks with negative controls + SoC level); FAST_HIT 1 must decide nothing differently (every cache and
# architectural counter equal, mcycle not larger), agree with the independent cache model, pass the new directed
# tests (tb_cache_configuration FAST variants incl. the SA2 hit latency, DM/SA2/DM_VC4 architectural equivalence)
# and keep the sim-only per-cycle checker silent -- whose liveness is proved by forcing a wrong answer (step 10).
# Manifest c09143ea (hdl = ea3ef852; tb adds the FAST tests). Every measurement twice.
# Quartus x2 (scripts/run_le_rtlfix.sh) and the ASIC side (asic/run_r16_asic_checks.sh) are separate steps.
# Progress: results/fullchain_r16.log. Run from Git Bash on Windows.
set -uo pipefail
cd "$(dirname "$0")/.."
V=C:/questasim64_2024.1/win64/vsim.exe
LOG=results/fullchain_r16.log
UP="up_aha-mont64,up_crc32,up_depthconv,up_edn,up_huffbench,up_matmult-int,up_md5sum,up_nettle-sha256,up_slre,up_statemate,up_tarfind,up_ud"
CMP=scripts/metrics/compare_cfg.py
FC=scripts/r16_fasthit/compare_fast.py
ALL6=DM=DM,SA2=SA2,DM_VC4=DM_VC4,DM_DSE=DM_DSE,SA4=SA4,SA2N=SA2N
: > "$LOG"
say () { echo "$*" | tee -a "$LOG"; }
fail=0
check () { if [ "$1" -eq 0 ]; then say "  [OK]   $2"; else say "  [FAIL] $2"; fail=$((fail+1)); fi; }
cmpq () { python $CMP "$@" 2>&1 | tail -1 >> "$LOG"; return ${PIPESTATUS[0]}; }
fastq () { python $FC "$@" >> "$LOG" 2>&1; }

say "######## 0. RTL manifest (must be the frozen R16, c09143ea)  $(date -Is)"
python scripts/rtl_manifest.py --check 2>&1 | tail -2 | tee -a "$LOG"; check ${PIPESTATUS[0]} "manifest IDENTICAL at start"
say "######## 1. static checks (WSL): 6 configurations x 64/256/512 lines x FAST_HIT 0/1 (33 combinations)  $(date -Is)"
wsl.exe -d Ubuntu -e bash -lc 'cd /mnt/e/Projects/RISCV-research && ./scripts/latch_sweep.sh >/dev/null 2>&1'
check $? "latch sweep: 0 latches, every one of 33 combinations elaborates"
wsl.exe -d Ubuntu -e bash -lc 'cd /mnt/e/Projects/RISCV-research && ./scripts/lint_rtl.sh 2>&1 | grep -q "\[PASS\] no correctness-class"'
check $? "lint_rtl: 0 correctness warnings, 33 combinations"
wsl.exe -d Ubuntu -e bash -lc 'cd /mnt/e/Projects/RISCV-research && bash scripts/lint_asic.sh soc_dm_4kb 2>&1 | grep -q "\[PASS\]"'
check $? "lint_asic soc_dm_4kb: 0 correctness warnings, 0 elaboration errors"
say "######## 2. directed regression x2 (R15 suite + 16 FAST_HIT runs)  $(date -Is)"
for pass in 1 2; do
  "$V" -c -do "do tb/run_full_regression.do; quit -f" > "results/regression_r16_p$pass.log" 2>&1
  p=$(grep -c '^# \[PASS\]' "results/regression_r16_p$pass.log")
  f=$(grep -cE '\[FAIL\]|\*\* Fatal|\*\* Error' "results/regression_r16_p$pass.log")
  say "  pass $pass: $p PASS, $f FAIL/Fatal/Error"
  [ "$f" -eq 0 ] || fail=$((fail+1))
done
p1=$(grep -c '^# \[PASS\]' results/regression_r16_p1.log); p2=$(grep -c '^# \[PASS\]' results/regression_r16_p2.log)
[ "$p1" = "$p2" ]; check $? "regression passes agree ($p1 = $p2)"
[ "$(grep -c 'FAST_HIT=1 request-cycle main-cache hit' results/regression_r16_p1.log)" -eq 15 ] && \
  grep -q '(FAST_HIT=1) retirement traces identical' results/regression_r16_p1.log && \
  grep -q '^# \[PASS\] Complete active RTL regression' results/regression_r16_p1.log
check $? "regression: 15 FAST_HIT tb_cache_configuration runs + the FAST_HIT architectural equivalence PASS, suite complete"
say "######## 3. UVM at 256 lines, x2; AXI at 8 / 32 / 64 B lines, x2  $(date -Is)"
for pass in 1 2; do
  ok=0
  for t in core_smoke_test core_random_test axi_smoke_test soc_directed_test soc_periph_test; do
    "$V" -c -do "do verification/uvm/run_uvm.do $t 1 1 4 256; quit -f" > "results/uvm_r16_256_${t}_p$pass.log" 2>&1
    if grep -q 'UVM status: PASS' "results/uvm_r16_256_${t}_p$pass.log"; then ok=$((ok+1)); else say "    FAIL $t p$pass"; fi
  done
  say "  pass $pass: $ok/5 PASS"; [ "$ok" -eq 5 ] || fail=$((fail+1))
done
for lw in 2 8 16; do
  for pass in 1 2; do
    "$V" -c -do "do verification/uvm/run_uvm.do axi_smoke_test 1 1 $lw 64; quit -f" > "results/uvm_r16_axi_lw${lw}_p$pass.log" 2>&1
    grep -q 'UVM status: PASS' "results/uvm_r16_axi_lw${lw}_p$pass.log"; check $? "axi_smoke_test line_words=$lw pass $pass"
  done
done
say "######## 4. Embench-IoT (12 standard kernels), 4 KiB: configurations 0-5 x2, then FAST_HIT 1-5 x2  $(date -Is)"
python scripts/run_ablation.py --compile --lines 256 --configs 0,1,2,3,4,5 --out results/r16_4kb_p1.csv 2>&1 | tail -1 | tee -a "$LOG"
python scripts/run_ablation.py           --lines 256 --configs 0,1,2,3,4,5 --out results/r16_4kb_p2.csv 2>&1 | tail -1 | tee -a "$LOG"
[ "$(tail -n +2 results/r16_4kb_p1.csv | wc -l)" -eq 72 ]; check $? "Embench: 72/72 runs pass verify_benchmark and the counter identities"
python scripts/verify_double.py results/r16_4kb_p1.csv results/r16_4kb_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "Embench: pass 1 = pass 2 (72 runs)"
cmpq results/r16_4kb_p1.csv results/r15_4kb_p1.csv --map $ALL6; check $? "Embench FAST_HIT 0: identical to R15 (72 runs, every field)"
python scripts/run_ablation.py --fast --lines 256 --configs 1,2,3,4,5 --out results/r16f_4kb_p1.csv 2>&1 | tail -1 | tee -a "$LOG"
python scripts/run_ablation.py --fast --lines 256 --configs 1,2,3,4,5 --out results/r16f_4kb_p2.csv 2>&1 | tail -1 | tee -a "$LOG"
[ "$(tail -n +2 results/r16f_4kb_p1.csv | wc -l)" -eq 60 ]; check $? "Embench FAST_HIT: 60/60 runs pass verify_benchmark and the counter identities"
python scripts/verify_double.py results/r16f_4kb_p1.csv results/r16f_4kb_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "Embench FAST_HIT: pass 1 = pass 2 (60 runs)"
fastq results/r16_4kb_p1.csv results/r16f_4kb_p1.csv --dm results/r16_4kb_p1.csv; check $? "Embench FAST_HIT vs 0: every cache / architectural counter equal, mcycle never larger"
nl=$(ls results/ablation_logs/r16f_4kb_p1/*.log results/ablation_logs/r16f_4kb_p2/*.log 2>/dev/null | grep -vc compile)
nm=$(grep -l "R16 FAST_HIT" results/ablation_logs/r16f_4kb_p1/*.log results/ablation_logs/r16f_4kb_p2/*.log 2>/dev/null | wc -l)
[ "$nl" -ge 120 ] && [ "$nm" -eq 0 ]; check $? "Embench FAST_HIT: no R16 checker message in any of $nl run logs"
say "######## 5. CoreMark: configurations 0-5 x2, FAST_HIT 1-5 x2  $(date -Is)"
for pass in 1 2; do
  python scripts/run_coremark.py --lines 256 --configs 0,1,2,3,4,5 --out results/coremark_r16_4kb_p$pass.csv 2>&1 | tail -1 | tee -a "$LOG"
  python scripts/run_coremark.py --fast --lines 256 --configs 1,2,3,4,5 --out results/coremark_r16f_4kb_p$pass.csv 2>&1 | tail -1 | tee -a "$LOG"
done
python scripts/verify_double.py results/coremark_r16_4kb_p1.csv results/coremark_r16_4kb_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "CoreMark: pass 1 = pass 2"
cmpq results/coremark_r16_4kb_p1.csv results/coremark_r15_4kb_p1.csv --map $ALL6; check $? "CoreMark FAST_HIT 0: identical to R15"
python scripts/verify_double.py results/coremark_r16f_4kb_p1.csv results/coremark_r16f_4kb_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "CoreMark FAST_HIT: pass 1 = pass 2"
fastq results/coremark_r16_4kb_p1.csv results/coremark_r16f_4kb_p1.csv --dm results/coremark_r16_4kb_p1.csv; check $? "CoreMark FAST_HIT vs 0: counters equal, mcycle never larger"
say "######## 6. random differential, 50 seeds, x2 (core only: R16 must not touch it)  $(date -Is)"
for pass in 1 2; do
  bash scripts/run_random_diff.sh 1 50 2>&1 | tail -1 | tee -a "$LOG"
  cp results/random_diff.csv "results/random_diff_r16_p$pass.csv"
done
cmp -s results/random_diff_r16_p1.csv results/random_diff_r16_p2.csv; check $? "random diff: pass 1 = pass 2"
cmp -s results/random_diff_r15_p1.csv results/random_diff_r16_p1.csv; check $? "random diff: identical to R15 (hashes included)"
[ "$(grep -c ',MATCH,' results/random_diff_r16_p1.csv)" -eq 50 ]; check $? "random diff: 50/50 MATCH"
say "######## 7. ASIC view (8 SRAM banks, DM), x2  $(date -Is)"
python scripts/run_ablation.py --asic-view --compile --kernels "$UP" --out results/upstream_asic_r16_p1.csv 2>&1 | tail -1 | tee -a "$LOG"
python scripts/run_ablation.py --asic-view           --kernels "$UP" --out results/upstream_asic_r16_p2.csv 2>&1 | tail -1 | tee -a "$LOG"
python scripts/verify_double.py results/upstream_asic_r16_p1.csv results/upstream_asic_r16_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "ASIC view: pass 1 = pass 2"
cmpq results/upstream_asic_r16_p1.csv results/upstream_asic_r15_p1.csv --map DM=DM; check $? "ASIC view: identical to R15 (12 kernels, every field)"
"$V" -c -do "do tb/compile_asic_view.do; vsim -onfinish stop -voptargs=+acc -gVERBOSE=0 -gTB_LINE_COUNT=256 work_asic.tb_directed_isa work_asic.asic_view_checker_isa; run -all; quit -f" > results/asic_view_directed_isa_r16.log 2>&1
[ "$(grep -c '^# \[PASS\]' results/asic_view_directed_isa_r16.log)" -ge 6 ] && ! grep -q '\*\* Fatal' results/asic_view_directed_isa_r16.log
check $? "ASIC view directed ISA: all six checks PASS"
for pass in 1 2; do
  "$V" -c -do "vsim -onfinish stop work_asic.tb_soc_asic_top_sync; run -all; quit -f" > "results/asic_top_sync_r16_p$pass.log" 2>&1
  grep -q '^# \[PASS\] soc_asic_top' "results/asic_top_sync_r16_p$pass.log" && ! grep -qE '\[FAIL\]|\*\* (Fatal|Error)' "results/asic_top_sync_r16_p$pass.log"
  check $? "ASIC wrapper synchronisers pass $pass"
done
say "######## 8. ramsweep: configurations 0-5 + ASIC view x2, FAST_HIT 1-5 x2  $(date -Is)"
for pass in 1 2; do
  python scripts/run_ablation.py --lines 256 --configs 0,1,2,3,4,5 --kernels ramsweep --out results/ramsweep_r16_p$pass.csv 2>&1 | tail -1 | tee -a "$LOG"
  python scripts/run_ablation.py --asic-view --kernels ramsweep --out results/ramsweep_asic_r16_p$pass.csv 2>&1 | tail -1 | tee -a "$LOG"
  python scripts/run_ablation.py --fast --lines 256 --configs 1,2,3,4,5 --kernels ramsweep --out results/ramsweep_r16f_p$pass.csv 2>&1 | tail -1 | tee -a "$LOG"
done
python scripts/verify_double.py results/ramsweep_r16_p1.csv results/ramsweep_r16_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "ramsweep: pass 1 = pass 2"
cmpq results/ramsweep_r16_p1.csv results/ramsweep_r15_p1.csv --map $ALL6; check $? "ramsweep FAST_HIT 0: identical to R15"
cmpq results/ramsweep_asic_r16_p1.csv results/ramsweep_asic_r15_p1.csv --map DM=DM; check $? "ramsweep ASIC view: identical to R15"
python scripts/verify_double.py results/ramsweep_r16f_p1.csv results/ramsweep_r16f_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "ramsweep FAST_HIT: pass 1 = pass 2"
fastq results/ramsweep_r16_p1.csv results/ramsweep_r16f_p1.csv; check $? "ramsweep FAST_HIT vs 0: counters equal, mcycle never larger"
say "######## 9. independent cache model, 12 kernels: FAST_HIT 0 configurations 0-5, FAST_HIT 1-5  $(date -Is)"
python scripts/run_crossval.py --lines 256 --configs 0,1,2,3 --kernels "$UP" --out results/crossval_r16_4cfg.csv > results/crossval_r16_4cfg.log 2>&1
check $? "cache model: every counter EXACT for DM (with its L0), SA2, DM_VC4, DM_DSE (48 runs)"
python scripts/run_crossval.py --lines 256 --configs 4,5 --kernels "$UP" --out results/crossval_r16_nway.csv > results/crossval_r16_nway.log 2>&1
check $? "cache model: every counter EXACT for SA4 and SA2N (24 runs)"
python scripts/run_crossval.py --fast --lines 256 --configs 1,2,3,4,5 --kernels "$UP" --out results/crossval_r16_fast.csv > results/crossval_r16_fast.log 2>&1
check $? "cache model: every counter EXACT with FAST_HIT for SA2, DM_VC4, DM_DSE, SA4, SA2N (60 runs)"
say "######## 10. R16 checker liveness: a forced wrong answer must stop each of the four FAST_HIT cores  $(date -Is)"
bash scripts/r16_fasthit/checker_mutation.sh work 2>&1 | tee -a "$LOG" | tail -1
check ${PIPESTATUS[0]} "checker mutation: 4/4 checkers fire (I$ / D$ x DSE / N-way)"
say "######## 11. RTL manifest at the end  $(date -Is)"
python scripts/rtl_manifest.py --check 2>&1 | tail -1 | tee -a "$LOG"; check ${PIPESTATUS[0]} "manifest IDENTICAL at the end"
say "######## done  $(date -Is): $fail failure(s)"
exit $fail
