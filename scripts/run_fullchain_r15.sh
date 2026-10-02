#!/usr/bin/env bash
# R15 (2026-09-30, review item M2): four-way set associativity. The change adds hdl/cache/dcache_nway_core.v and
# icache_nway_core.v and one generate branch in dcache.v / icache.v for CACHE_CONFIG >= 4 (4 = SA4, 5 = the same
# core at two ways, which exists only to be checked against SA2). Configurations 0-3 elaborate exactly the
# modules they did in R14, so every one of their results must stay byte-identical to the R14 chain's; the new
# core must reproduce SA2 at two ways and agree with the independent cache model at four. Standard benchmarks
# only (the project's own Embench-style kernels were removed on 2026-09-30). Every measurement twice.
# Quartus (x2) and the ASIC netlist identity check are separate steps (scripts/run_le_r15.sh, FLOW_JOURNAL).
# Progress: results/fullchain_r15.log. Run from Git Bash on Windows.
set -uo pipefail
cd "$(dirname "$0")/.."
V=C:/questasim64_2024.1/win64/vsim.exe
LOG=results/fullchain_r15.log
UP="up_aha-mont64,up_crc32,up_depthconv,up_edn,up_huffbench,up_matmult-int,up_md5sum,up_nettle-sha256,up_slre,up_statemate,up_tarfind,up_ud"
CMP=scripts/metrics/compare_cfg.py
OLD4=DM=DM,SA2=SA2,DM_VC4=DM_VC4,DM_DSE=DM_DSE
: > "$LOG"
say () { echo "$*" | tee -a "$LOG"; }
fail=0
check () { if [ "$1" -eq 0 ]; then say "  [OK]   $2"; else say "  [FAIL] $2"; fail=$((fail+1)); fi; }
cmpq () { python $CMP "$@" 2>&1 | tail -1 >> "$LOG"; return ${PIPESTATUS[0]}; }

# The review batch uses the work library; recompiling it under that batch would break it.
until grep -q "batch2 done" results/review_sims.log 2>/dev/null; do sleep 60; done

say "######## 0. RTL manifest  $(date -Is)"
python scripts/rtl_manifest.py 2>&1 | tail -1 | tee -a "$LOG"
say "######## 1. static checks (WSL): 6 configurations x 64/256/512 lines  $(date -Is)"
wsl.exe -d Ubuntu -e bash -lc 'cd /mnt/e/Projects/RISCV-research && ./scripts/latch_sweep.sh >/dev/null 2>&1'
check $? "latch sweep: 0 latches over 18 combinations"
wsl.exe -d Ubuntu -e bash -lc 'cd /mnt/e/Projects/RISCV-research && ./scripts/lint_rtl.sh 2>&1 | grep -q "\[PASS\] no correctness-class"'
check $? "lint_rtl: 0 correctness warnings, 18 combinations"
wsl.exe -d Ubuntu -e bash -lc 'cd /mnt/e/Projects/RISCV-research && bash scripts/lint_asic.sh soc_dm_4kb 2>&1 | grep -q "\[PASS\]"'
check $? "lint_asic soc_dm_4kb: 0 correctness warnings, 0 elaboration errors"
say "######## 2. directed regression x2  $(date -Is)"
for pass in 1 2; do
  "$V" -c -do "do tb/run_full_regression.do; quit -f" > "results/regression_r15_p$pass.log" 2>&1
  p=$(grep -c '^# \[PASS\]' "results/regression_r15_p$pass.log")
  f=$(grep -cE '\[FAIL\]|\*\* Fatal|\*\* Error' "results/regression_r15_p$pass.log")
  say "  pass $pass: $p PASS, $f FAIL/Fatal/Error"
  [ "$f" -eq 0 ] || fail=$((fail+1))
done
p1=$(grep -c '^# \[PASS\]' results/regression_r15_p1.log); p2=$(grep -c '^# \[PASS\]' results/regression_r15_p2.log)
[ "$p1" = "$p2" ]; check $? "regression passes agree ($p1 = $p2)"
say "######## 3. UVM at 256 lines, x2; AXI at 8 / 32 / 64 B lines, x2  $(date -Is)"
for pass in 1 2; do
  ok=0
  for t in core_smoke_test core_random_test axi_smoke_test soc_directed_test soc_periph_test; do
    "$V" -c -do "do verification/uvm/run_uvm.do $t 1 1 4 256; quit -f" > "results/uvm_r15_256_${t}_p$pass.log" 2>&1
    if grep -q 'UVM status: PASS' "results/uvm_r15_256_${t}_p$pass.log"; then ok=$((ok+1)); else say "    FAIL $t p$pass"; fi
  done
  say "  pass $pass: $ok/5 PASS"; [ "$ok" -eq 5 ] || fail=$((fail+1))
done
for lw in 2 8 16; do
  for pass in 1 2; do
    "$V" -c -do "do verification/uvm/run_uvm.do axi_smoke_test 1 1 $lw 64; quit -f" > "results/uvm_r15_axi_lw${lw}_p$pass.log" 2>&1
    grep -q 'UVM status: PASS' "results/uvm_r15_axi_lw${lw}_p$pass.log"; check $? "axi_smoke_test line_words=$lw pass $pass"
  done
done
say "######## 4. Embench-IoT (12 standard kernels), 4 KiB, configurations 0-5, x2  $(date -Is)"
python scripts/run_ablation.py --compile --lines 256 --configs 0,1,2,3,4,5 --out results/r15_4kb_p1.csv 2>&1 | tail -1 | tee -a "$LOG"
python scripts/run_ablation.py           --lines 256 --configs 0,1,2,3,4,5 --out results/r15_4kb_p2.csv 2>&1 | tail -1 | tee -a "$LOG"
[ "$(tail -n +2 results/r15_4kb_p1.csv | wc -l)" -eq 72 ]; check $? "Embench: 72/72 runs pass verify_benchmark and the counter identities"
python scripts/verify_double.py results/r15_4kb_p1.csv results/r15_4kb_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "Embench: pass 1 = pass 2 (72 runs)"
cmpq results/r15_4kb_p1.csv results/upstream_r14_4kb_p1.csv --map $OLD4; check $? "Embench configs 0-3: identical to R14 (48 runs, every field)"
cmpq results/r15_4kb_p1.csv results/r15_4kb_p1.csv --map SA2N=SA2; check $? "Embench: the N-way core at two ways = SA2 (12 kernels, every field)"
say "######## 5. CoreMark, configurations 0-5, x2  $(date -Is)"
for pass in 1 2; do
  python scripts/run_coremark.py --lines 256 --configs 0,1,2,3,4,5 --out results/coremark_r15_4kb_p$pass.csv 2>&1 | tail -1 | tee -a "$LOG"
done
python scripts/verify_double.py results/coremark_r15_4kb_p1.csv results/coremark_r15_4kb_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "CoreMark: pass 1 = pass 2"
cmpq results/coremark_r15_4kb_p1.csv results/coremark_r14_4kb_p1.csv --map $OLD4; check $? "CoreMark configs 0-3: identical to R14"
cmpq results/coremark_r15_4kb_p1.csv results/coremark_r15_4kb_p1.csv --map SA2N=SA2; check $? "CoreMark: N-way at two ways = SA2"
say "######## 6. random differential, 50 seeds, x2  $(date -Is)"
for pass in 1 2; do
  bash scripts/run_random_diff.sh 1 50 2>&1 | tail -1 | tee -a "$LOG"
  cp results/random_diff.csv "results/random_diff_r15_p$pass.csv"
done
cmp -s results/random_diff_r15_p1.csv results/random_diff_r15_p2.csv; check $? "random diff: pass 1 = pass 2"
cmp -s results/random_diff_r14_p1.csv results/random_diff_r15_p1.csv; check $? "random diff: identical to R14 (hashes included)"
[ "$(grep -c ',MATCH,' results/random_diff_r15_p1.csv)" -eq 50 ]; check $? "random diff: 50/50 MATCH"
say "######## 7. ASIC view (8 SRAM banks, DM), x2  $(date -Is)"
python scripts/run_ablation.py --asic-view --compile --kernels "$UP" --out results/upstream_asic_r15_p1.csv 2>&1 | tail -1 | tee -a "$LOG"
python scripts/run_ablation.py --asic-view           --kernels "$UP" --out results/upstream_asic_r15_p2.csv 2>&1 | tail -1 | tee -a "$LOG"
python scripts/verify_double.py results/upstream_asic_r15_p1.csv results/upstream_asic_r15_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "ASIC view: pass 1 = pass 2"
cmpq results/upstream_asic_r15_p1.csv results/upstream_asic_r14_p1.csv --map DM=DM; check $? "ASIC view: identical to R14 (12 kernels, every field)"
"$V" -c -do "do tb/compile_asic_view.do; vsim -onfinish stop -voptargs=+acc -gVERBOSE=0 -gTB_LINE_COUNT=256 work_asic.tb_directed_isa work_asic.asic_view_checker_isa; run -all; quit -f" > results/asic_view_directed_isa_r15.log 2>&1
[ "$(grep -c '^# \[PASS\]' results/asic_view_directed_isa_r15.log)" -ge 6 ] && ! grep -q '\*\* Fatal' results/asic_view_directed_isa_r15.log
check $? "ASIC view directed ISA: all six checks PASS"
for pass in 1 2; do
  "$V" -c -do "vsim -onfinish stop work_asic.tb_soc_asic_top_sync; run -all; quit -f" > "results/asic_top_sync_r15_p$pass.log" 2>&1
  grep -q '^# \[PASS\] soc_asic_top' "results/asic_top_sync_r15_p$pass.log" && ! grep -qE '\[FAIL\]|\*\* (Fatal|Error)' "results/asic_top_sync_r15_p$pass.log"
  check $? "ASIC wrapper synchronisers pass $pass"
done
say "######## 8. ramsweep, configurations 0-5 and the ASIC view, x2  $(date -Is)"
for pass in 1 2; do
  python scripts/run_ablation.py --lines 256 --configs 0,1,2,3,4,5 --kernels ramsweep --out results/ramsweep_r15_p$pass.csv 2>&1 | tail -1 | tee -a "$LOG"
  python scripts/run_ablation.py --asic-view --kernels ramsweep --out results/ramsweep_asic_r15_p$pass.csv 2>&1 | tail -1 | tee -a "$LOG"
done
python scripts/verify_double.py results/ramsweep_r15_p1.csv results/ramsweep_r15_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "ramsweep: pass 1 = pass 2"
cmpq results/ramsweep_r15_p1.csv results/ramsweep_r14_p1.csv --map $OLD4; check $? "ramsweep configs 0-3: identical to R14"
cmpq results/ramsweep_r15_p1.csv results/ramsweep_r15_p1.csv --map SA2N=SA2; check $? "ramsweep: N-way at two ways = SA2"
cmpq results/ramsweep_asic_r15_p1.csv results/ramsweep_asic_r14_p1.csv --map DM=DM; check $? "ramsweep ASIC view: identical to R14"
say "######## 9. independent cache model, 12 kernels: configurations 0-3, then SA4 and the two-way N-way core  $(date -Is)"
# Configurations 0-3 added for the rerun on the lint-fixed RTL (2026-09-30): the model now carries the DM
# D-cache L0 (class DmL0), which explained the one R14 mismatch (up_matmult-int/DM), so all 48 must be exact.
python scripts/run_crossval.py --lines 256 --configs 0,1,2,3 --kernels "$UP" --out results/crossval_r15_4cfg.csv > results/crossval_r15_4cfg.log 2>&1
check $? "cache model: every counter EXACT for DM (with its L0), SA2, DM_VC4, DM_DSE (48 runs)"
python scripts/run_crossval.py --lines 256 --configs 4,5 --kernels "$UP" --out results/crossval_r15_nway.csv > results/crossval_r15_nway.log 2>&1
check $? "cache model: every counter EXACT for SA4 and SA2N (24 runs)"
say "######## done  $(date -Is): $fail failure(s)"
exit $fail
