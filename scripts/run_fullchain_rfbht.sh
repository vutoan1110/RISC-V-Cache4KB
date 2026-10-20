#!/usr/bin/env bash
# Register file and BHT into M9K on the FPGA (2026-10-08, review A1; manifest 6c4ccffd = c09143ea + this change).
# FPGA-only change: every simulation of the FPGA view must reproduce R16 (c09143ea) field for field; the ASIC view is
# checked by token identity and synthesis (asic/run_rf_bht_m9k_asic_checks.sh); the new logic has its own tests
# (tb_regfile, tb_bht BHT-7..10, k-induction proofs with negative controls in asic/equiv/rf_bht_m9k, checker
# liveness). Every measurement twice. Lanes run in parallel, one simulation library each (two batches in one library
# collide: vsim-1962):
#   S       static checks (WSL): latch sweep, lint_rtl, lint_asic
#   W       work: regression x2, random differential x2, checker liveness, UVM x2, AXI line sizes x2
#   A       work_asic: ASIC view x2, directed ISA, synchronisers x2, ramsweep ASIC view x2
#   M1..M6  work_m2_1..6 = configurations 0..5: Embench x2, FAST_HIT x2 (1..5), ramsweep x2, CoreMark x2
#   T       work_act4: ACT4 x2, signatures against the previous run
# The cache model cross-check of R16 is not repeated: the cache RTL is unchanged and every cache counter of every run
# must equal R16's, which the model already matched counter for counter.
# Progress: results/fullchain_rfbht.log, lane logs results/fullchain_rfbht_<lane>.log. Run from Git Bash on Windows.
set -uo pipefail
cd "$(dirname "$0")/.."
V=C:/questasim64_2024.1/win64/vsim.exe
LOG=results/fullchain_rfbht.log
UP="up_aha-mont64,up_crc32,up_depthconv,up_edn,up_huffbench,up_matmult-int,up_md5sum,up_nettle-sha256,up_slre,up_statemate,up_tarfind,up_ud"
CMP=scripts/metrics/compare_cfg.py
ALL6=DM=DM,SA2=SA2,DM_VC4=DM_VC4,DM_DSE=DM_DSE,SA4=SA4,SA2N=SA2N
FAST5=SA2=SA2,DM_VC4=DM_VC4,DM_DSE=DM_DSE,SA4=SA4,SA2N=SA2N
: > "$LOG"
say () { echo "$*" | tee -a "$LOG"; }
fail=0
check () { if [ "$1" -eq 0 ]; then say "  [OK]   $2"; else say "  [FAIL] $2"; fail=$((fail+1)); fi; }
cmpq () { python $CMP "$@" 2>&1 | tail -1 >> "$LOG"; return ${PIPESTATUS[0]}; }
coremark_call () {
  local case_id=$1; shift
  python scripts/run_coremark.py "$@" 2>&1 | tail -1
  local rc=${PIPESTATUS[0]}
  echo "coremark $case_id rc=$rc"
  return "$rc"
}
coremark_status_gate () {
  local k c pass case_id lane_log
  for k in 1 2 3 4 5 6; do
    c=$((k - 1)); lane_log="results/fullchain_rfbht_M$k.log"
    for pass in 1 2; do
      case_id="p${pass}_c$c"
      [ "$(grep -c "^coremark $case_id rc=" "$lane_log")" -eq 1 ] &&
        grep -qx "coremark $case_id rc=0" "$lane_log"
      check $? "CoreMark $case_id: CRC-gated runner exit 0"
      if [ "$c" -ge 1 ]; then
        case_id="fast_p${pass}_c$c"
        [ "$(grep -c "^coremark $case_id rc=" "$lane_log")" -eq 1 ] &&
          grep -qx "coremark $case_id rc=0" "$lane_log"
        check $? "CoreMark $case_id: CRC-gated runner exit 0"
      fi
    done
  done
}
merge () { python - "$@" <<'PY'
import csv, sys
out, ins = sys.argv[1], sys.argv[2:]
rows, head = [], None
for f in ins:
    r = list(csv.reader(open(f, newline="")))
    head = head or r[0]
    assert r[0] == head, f
    rows += r[1:]
w = csv.writer(open(out, "w", newline=""))
w.writerow(head); w.writerows(rows)
PY
}

say "######## 0. RTL manifest (must be the frozen 6c4ccffd)  $(date -Is)"
python scripts/rtl_manifest.py --check 2>&1 | tail -2 | tee -a "$LOG"; check ${PIPESTATUS[0]} "manifest IDENTICAL at start"
grep -q '"aggregate": "6c4ccffd' results/rtl_manifest.json; check $? "frozen manifest is 6c4ccffd"

say "######## 1. libraries work_m2_1..6 from the current tb/compile_active_design.do  $(date -Is)"
python scripts/m2/make_compile_do.py 6 > /dev/null
for k in 1 2 3 4 5 6; do
  "$V" -c -do "do scripts/m2/compile_m2_$k.do; quit -f" > "results/fullchain_rfbht_compile_m2_$k.log" 2>&1 &
done
wait
for k in 1 2 3 4 5 6; do
  grep -q '\[PASS\] Active RTL' "results/fullchain_rfbht_compile_m2_$k.log" && ! grep -qE '\*\* (Error|Fatal)' "results/fullchain_rfbht_compile_m2_$k.log"
  check $? "library work_m2_$k compiled"
done
[ $fail -eq 0 ] || { say "stop: setup failed"; exit $fail; }

say "######## 2. lanes start  $(date -Is)"
lane_S () {
  wsl.exe -d Ubuntu -e bash -lc 'cd /mnt/e/Projects/RISCV-research && ./scripts/latch_sweep.sh >/dev/null 2>&1'; echo "latch_sweep rc=$?"
  wsl.exe -d Ubuntu -e bash -lc 'cd /mnt/e/Projects/RISCV-research && ./scripts/lint_rtl.sh 2>&1 | grep -q "\[PASS\] no correctness-class"'; echo "lint_rtl rc=$?"
  wsl.exe -d Ubuntu -e bash -lc 'cd /mnt/e/Projects/RISCV-research && bash scripts/lint_asic.sh soc_dm_4kb 2>&1 | grep -q "\[PASS\]"'; echo "lint_asic rc=$?"
}
lane_W () {
  "$V" -c -do "do tb/run_full_regression.do; quit -f" > results/regression_rfbht_p1.log 2>&1
  for pass in 1 2; do
    bash scripts/run_random_diff.sh 1 50 "$pass" 2>&1 | tail -1
    local random_rc=${PIPESTATUS[0]}
    echo "random_diff p$pass rc=$random_rc"
    cp results/random_diff.csv "results/random_diff_rfbht_p$pass.csv"
  done
  bash scripts/rf_bht_m9k/checker_mutation.sh work; echo "checker_mutation rc=$?"
  "$V" -c -do "do tb/run_full_regression.do; quit -f" > results/regression_rfbht_p2.log 2>&1
  for pass in 1 2; do
    for t in core_smoke_test core_random_test axi_smoke_test soc_directed_test soc_periph_test; do
      "$V" -c -do "do verification/uvm/run_uvm.do $t 1 1 4 256; quit -f" > "results/uvm_rfbht_256_${t}_p$pass.log" 2>&1
    done
  done
  for lw in 2 8 16; do
    for pass in 1 2; do
      "$V" -c -do "do verification/uvm/run_uvm.do axi_smoke_test 1 1 $lw 64; quit -f" > "results/uvm_rfbht_axi_lw${lw}_p$pass.log" 2>&1
    done
  done
}
lane_A () {
  python scripts/run_ablation.py --asic-view --compile --kernels "$UP" --out results/upstream_asic_rfbht_p1.csv 2>&1 | tail -1
  python scripts/run_ablation.py --asic-view           --kernels "$UP" --out results/upstream_asic_rfbht_p2.csv 2>&1 | tail -1
  "$V" -c -do "vsim -onfinish stop -voptargs=+acc -gVERBOSE=0 -gTB_LINE_COUNT=256 work_asic.tb_directed_isa work_asic.asic_view_checker_isa; run -all; quit -f" > results/asic_view_directed_isa_rfbht.log 2>&1
  for pass in 1 2; do
    "$V" -c -do "vsim -onfinish stop work_asic.tb_soc_asic_top_sync; run -all; quit -f" > "results/asic_top_sync_rfbht_p$pass.log" 2>&1
    python scripts/run_ablation.py --asic-view --kernels ramsweep --out results/ramsweep_asic_rfbht_p$pass.csv 2>&1 | tail -1
  done
}
lane_M () {   # $1 = library index k, configuration k-1
  local k=$1 c=$(( $1 - 1 )) lib=work_m2_$1
  for pass in 1 2; do
    python scripts/run_ablation.py --lib $lib --lines 256 --configs $c --out results/rfbht_4kb_p${pass}_c$c.csv 2>&1 | tail -1
    python scripts/run_ablation.py --lib $lib --lines 256 --configs $c --kernels ramsweep --out results/ramsweep_rfbht_p${pass}_c$c.csv 2>&1 | tail -1
    coremark_call "p${pass}_c$c" --lib "$lib" --lines 256 --configs "$c" --out "results/coremark_rfbht_4kb_p${pass}_c$c.csv" || return $?
    if [ $c -ge 1 ]; then
      python scripts/run_ablation.py --lib $lib --fast --lines 256 --configs $c --out results/rfbhtf_4kb_p${pass}_c$c.csv 2>&1 | tail -1
      python scripts/run_ablation.py --lib $lib --fast --lines 256 --configs $c --kernels ramsweep --out results/ramsweep_rfbhtf_p${pass}_c$c.csv 2>&1 | tail -1
      coremark_call "fast_p${pass}_c$c" --lib "$lib" --fast --lines 256 --configs "$c" --out "results/coremark_rfbhtf_4kb_p${pass}_c$c.csv" || return $?
    fi
  done
}
lane_T () {
  rm -rf results/act4_signatures_before_rfbht
  cp -r verification/results/act4/dut_p1/signatures results/act4_signatures_before_rfbht
  python scripts/metrics/run_act4.py 2>&1 | tail -3; echo "run_act4 rc=${PIPESTATUS[0]}"
}
lane_S > results/fullchain_rfbht_S.log 2>&1 &
lane_W > results/fullchain_rfbht_W.log 2>&1 &
lane_A > results/fullchain_rfbht_A.log 2>&1 &
for k in 1 2 3 4 5 6; do lane_M $k > results/fullchain_rfbht_M$k.log 2>&1 & done
lane_T > results/fullchain_rfbht_T.log 2>&1 &
wait
say "######## 3. lanes done  $(date -Is)"

say "######## 4. static checks"
grep -q "latch_sweep rc=0" results/fullchain_rfbht_S.log; check $? "latch sweep: 0 latches, every combination elaborates"
grep -q "lint_rtl rc=0" results/fullchain_rfbht_S.log; check $? "lint_rtl: 0 correctness warnings"
grep -q "lint_asic rc=0" results/fullchain_rfbht_S.log; check $? "lint_asic soc_dm_4kb: 0 correctness warnings, 0 elaboration errors"

say "######## 5. directed regression x2"
for pass in 1 2; do
  p=$(grep -c '^# \[PASS\]' "results/regression_rfbht_p$pass.log")
  f=$(grep -cE '\[FAIL\]|\*\* Fatal|\*\* Error' "results/regression_rfbht_p$pass.log")
  say "  pass $pass: $p PASS, $f FAIL/Fatal/Error"
  [ "$f" -eq 0 ] || fail=$((fail+1))
done
p1=$(grep -c '^# \[PASS\]' results/regression_rfbht_p1.log); p2=$(grep -c '^# \[PASS\]' results/regression_rfbht_p2.log)
[ "$p1" = "$p2" ]; check $? "regression passes agree ($p1 = $p2; R16 had $(grep -c '^# \[PASS\]' results/regression_r16_p1.log))"
grep -q '^# \[PASS\] Complete active RTL regression' results/regression_rfbht_p1.log && \
  grep -q '^# \[PASS\] Register file: ' results/regression_rfbht_p1.log && \
  grep -q 'First update after reset starts from 01' results/regression_rfbht_p1.log
check $? "regression complete, incl. tb_regfile and tb_bht BHT-7..10"

say "######## 6. UVM x2, AXI line sizes x2"
for pass in 1 2; do
  ok=0
  for t in core_smoke_test core_random_test axi_smoke_test soc_directed_test soc_periph_test; do
    grep -q 'UVM status: PASS' "results/uvm_rfbht_256_${t}_p$pass.log" && ok=$((ok+1))
  done
  [ "$ok" -eq 5 ]; check $? "UVM pass $pass: $ok/5 PASS"
done
for lw in 2 8 16; do for pass in 1 2; do
  grep -q 'UVM status: PASS' "results/uvm_rfbht_axi_lw${lw}_p$pass.log"; check $? "axi_smoke_test line_words=$lw pass $pass"
done; done

say "######## 7. Embench 12 kernels x 6 configurations, FAST_HIT x 5, x2: identical to R16"
for pass in 1 2; do
  merge results/rfbht_4kb_p$pass.csv results/rfbht_4kb_p${pass}_c{0,1,2,3,4,5}.csv
  merge results/rfbhtf_4kb_p$pass.csv results/rfbhtf_4kb_p${pass}_c{1,2,3,4,5}.csv
done
[ "$(tail -n +2 results/rfbht_4kb_p1.csv | wc -l)" -eq 72 ] && [ "$(tail -n +2 results/rfbht_4kb_p2.csv | wc -l)" -eq 72 ]
check $? "Embench: 72 + 72 runs pass verify_benchmark and the counter identities"
python scripts/verify_double.py results/rfbht_4kb_p1.csv results/rfbht_4kb_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "Embench: pass 1 = pass 2"
cmpq results/rfbht_4kb_p1.csv results/r16_4kb_p1.csv --map $ALL6; check $? "Embench: identical to R16 (72 runs, every field)"
[ "$(tail -n +2 results/rfbhtf_4kb_p1.csv | wc -l)" -eq 60 ] && [ "$(tail -n +2 results/rfbhtf_4kb_p2.csv | wc -l)" -eq 60 ]
check $? "Embench FAST_HIT: 60 + 60 runs pass"
python scripts/verify_double.py results/rfbhtf_4kb_p1.csv results/rfbhtf_4kb_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "Embench FAST_HIT: pass 1 = pass 2"
cmpq results/rfbhtf_4kb_p1.csv results/r16f_4kb_p1.csv --map $FAST5; check $? "Embench FAST_HIT: identical to R16 (60 runs, every field)"

say "######## 8. CoreMark x2: identical to R16"
coremark_status_gate
for pass in 1 2; do
  merge results/coremark_rfbht_4kb_p$pass.csv results/coremark_rfbht_4kb_p${pass}_c{0,1,2,3,4,5}.csv
  merge results/coremark_rfbhtf_4kb_p$pass.csv results/coremark_rfbhtf_4kb_p${pass}_c{1,2,3,4,5}.csv
done
python scripts/verify_double.py results/coremark_rfbht_4kb_p1.csv results/coremark_rfbht_4kb_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "CoreMark: pass 1 = pass 2"
cmpq results/coremark_rfbht_4kb_p1.csv results/coremark_r16_4kb_p1.csv --map $ALL6; check $? "CoreMark: identical to R16"
python scripts/verify_double.py results/coremark_rfbhtf_4kb_p1.csv results/coremark_rfbhtf_4kb_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "CoreMark FAST_HIT: pass 1 = pass 2"
cmpq results/coremark_rfbhtf_4kb_p1.csv results/coremark_r16f_4kb_p1.csv --map $FAST5; check $? "CoreMark FAST_HIT: identical to R16"

say "######## 9. random differential, 50 seeds, x2: identical to R16 incl. hashes"
for pass in 1 2; do
  grep -q "^random_diff p$pass rc=0$" results/fullchain_rfbht_W.log
  check $? "random diff: pass $pass process/completion/trace gates passed"
done
cmp -s results/random_diff_rfbht_p1.csv results/random_diff_rfbht_p2.csv; check $? "random diff: pass 1 = pass 2"
cmp -s results/random_diff_r16_p1.csv results/random_diff_rfbht_p1.csv; check $? "random diff: identical to R16"
[ "$(grep -c ',MATCH,' results/random_diff_rfbht_p1.csv)" -eq 50 ]; check $? "random diff: 50/50 MATCH"

say "######## 10. ASIC view x2, directed ISA, synchronisers"
python scripts/verify_double.py results/upstream_asic_rfbht_p1.csv results/upstream_asic_rfbht_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "ASIC view: pass 1 = pass 2"
cmpq results/upstream_asic_rfbht_p1.csv results/upstream_asic_r16_p1.csv --map DM=DM; check $? "ASIC view: identical to R16 (12 kernels, every field)"
[ "$(grep -c '^# \[PASS\]' results/asic_view_directed_isa_rfbht.log)" -ge 6 ] && ! grep -q '\*\* Fatal' results/asic_view_directed_isa_rfbht.log
check $? "ASIC view directed ISA: all six checks PASS"
for pass in 1 2; do
  grep -q '^# \[PASS\] soc_asic_top' "results/asic_top_sync_rfbht_p$pass.log" && ! grep -qE '\[FAIL\]|\*\* (Fatal|Error)' "results/asic_top_sync_rfbht_p$pass.log"
  check $? "ASIC wrapper synchronisers pass $pass"
done

say "######## 11. ramsweep x2: identical to R16"
for pass in 1 2; do
  merge results/ramsweep_rfbht_p$pass.csv results/ramsweep_rfbht_p${pass}_c{0,1,2,3,4,5}.csv
  merge results/ramsweep_rfbhtf_p$pass.csv results/ramsweep_rfbhtf_p${pass}_c{1,2,3,4,5}.csv
done
python scripts/verify_double.py results/ramsweep_rfbht_p1.csv results/ramsweep_rfbht_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "ramsweep: pass 1 = pass 2"
cmpq results/ramsweep_rfbht_p1.csv results/ramsweep_r16_p1.csv --map $ALL6; check $? "ramsweep: identical to R16"
python scripts/verify_double.py results/ramsweep_asic_rfbht_p1.csv results/ramsweep_asic_rfbht_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "ramsweep ASIC view: pass 1 = pass 2"
cmpq results/ramsweep_asic_rfbht_p1.csv results/ramsweep_asic_r16_p1.csv --map DM=DM; check $? "ramsweep ASIC view: identical to R16"
python scripts/verify_double.py results/ramsweep_rfbhtf_p1.csv results/ramsweep_rfbhtf_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "ramsweep FAST_HIT: pass 1 = pass 2"
cmpq results/ramsweep_rfbhtf_p1.csv results/ramsweep_r16f_p1.csv --map $FAST5; check $? "ramsweep FAST_HIT: identical to R16"

say "######## 12. checker liveness, ACT4, checker silence"
grep -q "checker_mutation rc=0" results/fullchain_rfbht_W.log; check $? "checker mutation: regfile and BHT checkers fire on a forced wrong read"
grep -q "run_act4 rc=0" results/fullchain_rfbht_T.log && python -c "
import json,sys; d=json.load(open('results/act4_summary.json'))
sys.exit(0 if d['pass1']==d['pass2']==d['signatures_identical_p1_p2']==d['elfs']==43 else 1)"
check $? "ACT4: 43/43 x2, signatures pass 1 = pass 2"
diff -rq results/act4_signatures_before_rfbht verification/results/act4/dut_p1/signatures > /dev/null; check $? "ACT4: signatures identical to the previous run"
n=$(grep -rl "M9K checker" results/ablation_logs/rfbht*_p* results/ablation_logs/ramsweep_rfbht* results/ablation_logs_asic_view/*rfbht* results/coremark_logs/coremark_rfbht* results/regression_rfbht_p*.log results/uvm_rfbht_* results/random_diff 2>/dev/null | wc -l)
[ "$n" -eq 0 ]; check $? "no M9K checker message in any simulation log ($n files)"

say "######## 13. RTL manifest at the end  $(date -Is)"
python scripts/rtl_manifest.py --check 2>&1 | tail -1 | tee -a "$LOG"; check ${PIPESTATUS[0]} "manifest IDENTICAL at the end"
say "######## 14. supplemental cache UVM, UART RX and complete architecture memory window"
supplement_date=$(date +%Y%m%d_%H%M%S)
python scripts/verification/run_uvm_matrix.py --run --tag "uvm_cache_uart_$supplement_date" 2>&1 | tail -1
check ${PIPESTATUS[0]} "UVM: four cache configurations, three seeds, AXI stress, UART RX, independent paired cases"
python scripts/verification/run_architecture_window.py --run --tag "architecture_window_$supplement_date" 2>&1 | tail -1
check ${PIPESTATUS[0]} "ACT4: complete 1 MiB adapter, upper-half instruction/data and alias negative control"
say "######## done  $(date -Is): $fail failure(s)"
exit $fail
