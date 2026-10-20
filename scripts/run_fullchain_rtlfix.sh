#!/usr/bin/env bash
# Full verification chain on the frozen RTL (NHAT_KY.md), 4 KiB only.
# The 1 KiB design is out of scope from 2026-09-25.
#
# Every measurement runs twice and the two passes must agree exactly, because
# this machine has been shown to corrupt data silently. Every result that the
# RTL changes are expected NOT to move is also compared against the reference
# taken before the changes:
#   R1 read enable, R3 write-error capture, R4 UART FIFO bits, R5 latch fix and
#   the RXDATA fix are all cycle-neutral for the benchmarks, so the FPGA-view
#   Embench and CoreMark matrices must be byte-identical to the tagfix /
#   coremark references.
# The ASIC view (SRAM macro models and the two macro wrappers) is compared with
# the FPGA view on every architectural field and cache counter.
#
# Progress goes to results/fullchain_rtlfix.log; one line per stage result.
set -uo pipefail
cd "$(dirname "$0")/.."
V=C:/questasim64_2024.1/win64/vsim.exe
LOG=results/fullchain_rtlfix.log
: > "$LOG"
say () { echo "$*" | tee -a "$LOG"; }
fail=0
check () { if [ "$1" -eq 0 ]; then say "  [OK]   $2"; else say "  [FAIL] $2"; fail=$((fail+1)); fi; }

say "######## 0. RTL freeze check  $(date -Is)"
python scripts/rtl_manifest.py --check 2>&1 | tail -3 | tee -a "$LOG"

say "######## 1. static checks (WSL)  $(date -Is)"
wsl.exe -d Ubuntu -e bash -lc 'cd /mnt/e/Projects/RISCV-research && ./scripts/latch_sweep.sh >/dev/null 2>&1'
check $? "latch sweep: 0 latches over 8 combinations"
wsl.exe -d Ubuntu -e bash -lc 'cd /mnt/e/Projects/RISCV-research && ./scripts/lint_rtl.sh 2>&1 | grep -q "\[PASS\] no correctness-class"'
check $? "lint_rtl: 0 correctness warnings, 8 combinations"
wsl.exe -d Ubuntu -e bash -lc 'cd /mnt/e/Projects/RISCV-research && bash scripts/lint_asic.sh soc_dm_4kb 2>&1 | grep -q "\[PASS\]"'
check $? "lint_asic soc_dm_4kb: 0 correctness warnings, 0 elaboration errors"

say "######## 2. directed regression x2  $(date -Is)"
for pass in 1 2; do
  "$V" -c -do "do tb/run_full_regression.do; quit -f" > "results/regression_rtlfix_p$pass.log" 2>&1
  p=$(grep -c '^# \[PASS\]' "results/regression_rtlfix_p$pass.log")
  f=$(grep -cE '\[FAIL\]|\*\* Fatal|\*\* Error' "results/regression_rtlfix_p$pass.log")
  say "  pass $pass: $p PASS, $f FAIL/Fatal/Error"
  [ "$f" -eq 0 ] || fail=$((fail+1))
done
p1=$(grep -c '^# \[PASS\]' results/regression_rtlfix_p1.log); p2=$(grep -c '^# \[PASS\]' results/regression_rtlfix_p2.log)
[ "$p1" = "$p2" ]; check $? "regression passes agree ($p1 = $p2)"

say "######## 3. UVM at 256 lines (4 KiB), x2  $(date -Is)"
for lc in 256; do
  for pass in 1 2; do
    ok=0
    for t in core_smoke_test core_random_test axi_smoke_test soc_directed_test soc_periph_test; do
      "$V" -c -do "do verification/uvm/run_uvm.do $t 1 1 4 $lc; quit -f" > "results/uvm_rtlfix_${lc}_${t}_p$pass.log" 2>&1
      if grep -q 'UVM status: PASS' "results/uvm_rtlfix_${lc}_${t}_p$pass.log"; then ok=$((ok+1)); else say "    FAIL $t lc=$lc p$pass"; fi
    done
    say "  lc=$lc pass $pass: $ok/5 PASS"; [ "$ok" -eq 5 ] || fail=$((fail+1))
  done
done

say "######## 4. UVM AXI at 8 / 32 / 64 B lines, x2  $(date -Is)"
for lw in 2 8 16; do
  for pass in 1 2; do
    "$V" -c -do "do verification/uvm/run_uvm.do axi_smoke_test 1 1 $lw 64; quit -f" > "results/uvm_rtlfix_axi_lw${lw}_p$pass.log" 2>&1
    grep -q 'UVM status: PASS' "results/uvm_rtlfix_axi_lw${lw}_p$pass.log"; check $? "axi_smoke_test line_words=$lw pass $pass"
  done
done

say "######## 5. Embench FPGA view, 4 KiB, x2  $(date -Is)"
python scripts/run_ablation.py --compile --lines 256 --out results/rtlfix_4kb_p1.csv 2>&1 | tail -1 | tee -a "$LOG"
python scripts/run_ablation.py           --lines 256 --out results/rtlfix_4kb_p2.csv 2>&1 | tail -1 | tee -a "$LOG"
python scripts/verify_double.py results/rtlfix_4kb_p1.csv results/rtlfix_4kb_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "Embench 4 KiB: pass 1 = pass 2 (48 runs)"
python scripts/verify_double.py results/tagfix_4kb_p1.csv results/rtlfix_4kb_p1.csv --key kernel --also config >/dev/null 2>&1; check $? "Embench 4 KiB: identical to the pre-change reference (48 runs)"

say "######## 6. CoreMark, 4 KiB, x2  $(date -Is)"
for lc in 256; do
  sz=4kb
  for pass in 1 2; do
    python scripts/run_coremark.py --lines $lc --out results/coremark_rtlfix_${sz}_p$pass.csv 2>&1 | tail -1 | tee -a "$LOG"
  done
  python scripts/verify_double.py results/coremark_rtlfix_${sz}_p1.csv results/coremark_rtlfix_${sz}_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "CoreMark $sz: pass 1 = pass 2"
  python scripts/verify_double.py results/coremark_${sz}.csv results/coremark_rtlfix_${sz}_p1.csv --key kernel --also config >/dev/null 2>&1; check $? "CoreMark $sz: identical to the pre-change reference"
done

say "######## 7. random differential, 50 seeds, x2  $(date -Is)"
[ -f results/random_diff_pre_rtlfix.csv ] || cp results/random_diff.csv results/random_diff_pre_rtlfix.csv
for pass in 1 2; do
  bash scripts/run_random_diff.sh 1 50 2>&1 | tail -1 | tee -a "$LOG"
  cp results/random_diff.csv "results/random_diff_rtlfix_p$pass.csv"
done
cmp -s results/random_diff_rtlfix_p1.csv results/random_diff_rtlfix_p2.csv; check $? "random diff: pass 1 = pass 2"
cmp -s results/random_diff_pre_rtlfix.csv results/random_diff_rtlfix_p1.csv; check $? "random diff: identical to the pre-change reference (hashes included)"
[ "$(grep -c ',MATCH,' results/random_diff_rtlfix_p1.csv)" -eq 50 ]; check $? "random diff: 50/50 MATCH"

say "######## 8. ASIC view: Embench x2 and directed ISA  $(date -Is)"
python scripts/run_ablation.py --asic-view --compile --out results/asic_view_4kb_p1.csv 2>&1 | tail -1 | tee -a "$LOG"
python scripts/run_ablation.py --asic-view           --out results/asic_view_4kb_p2.csv 2>&1 | tail -1 | tee -a "$LOG"
python scripts/verify_double.py results/asic_view_4kb_p1.csv results/asic_view_4kb_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "ASIC view Embench: pass 1 = pass 2"
python - <<'PY' >> "$LOG" 2>&1
import csv, sys
sys.path.insert(0, 'scripts')
from snapshot_fields import FIELDS, CYCLE_FIELDS
A = {r['kernel']: r for r in csv.DictReader(open('results/asic_view_4kb_p1.csv'))}
F = {r['kernel']: r for r in csv.DictReader(open('results/rtlfix_4kb_p1.csv')) if r['config'] == 'DM'}
# Every field except the cycle counts that depend on memory latency, which
# differ by design (the macro wrapper ignores the MISS_PENALTY hooks).
# load_use, control and trap are pipeline-internal and were compared before,
# so they stay in.
same = [f for f in FIELDS if f not in CYCLE_FIELDS] + ['load_use', 'control', 'trap']
bad = [(k, x) for k in A for x in same if A[k][x] != F[k][x]]
print('  ASIC view vs FPGA view, %d kernels x %d fields: %s' % (len(A), len(same), 'IDENTICAL' if not bad else 'DIFF %s' % bad[:5]))
sys.exit(1 if bad or len(A) != 12 else 0)
PY
check $? "ASIC view = FPGA view on every architectural field and cache counter"
"$V" -c -do "do tb/compile_asic_view.do; vsim -onfinish stop -voptargs=+acc -gVERBOSE=0 -gTB_LINE_COUNT=256 work_asic.tb_directed_isa work_asic.asic_view_checker_isa; run -all; quit -f" > results/asic_view_directed_isa_rtlfix.log 2>&1
[ "$(grep -c '^# \[PASS\]' results/asic_view_directed_isa_rtlfix.log)" -ge 6 ] && ! grep -q '\*\* Fatal' results/asic_view_directed_isa_rtlfix.log
check $? "ASIC view directed ISA: all six checks PASS"
# R8: the ASIC wrapper's reset, key1_n and uart_rx synchronisers (the FPGA
# wrapper's are in the directed regression as tb_de2_115_top_sync).
for pass in 1 2; do
  "$V" -c -do "vsim -onfinish stop work_asic.tb_soc_asic_top_sync; run -all; quit -f" > "results/asic_top_sync_rtlfix_p$pass.log" 2>&1
  grep -q '^# \[PASS\] soc_asic_top' "results/asic_top_sync_rtlfix_p$pass.log" && ! grep -qE '\[FAIL\]|\*\* (Fatal|Error)' "results/asic_top_sync_rtlfix_p$pass.log"
  check $? "ASIC wrapper synchronisers (tb_soc_asic_top_sync) pass $pass"
done

say "######## done $(date -Is): $fail failure(s)"
python scripts/rtl_manifest.py --check 2>&1 | tail -2 | tee -a "$LOG"
exit $fail
