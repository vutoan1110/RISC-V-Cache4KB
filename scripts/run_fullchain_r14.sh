#!/usr/bin/env bash
# R14 (RAM16K_CHANGES.md): full verification chain for the 16 KiB unified RAM, 4 KiB caches.
# Same stages as run_fullchain_rtlfix.sh, every measurement twice (this machine corrupts data silently),
# plus what R14 adds:
#   - the pre-change references are the 8 KiB design's own chain results (results/ref_pre_r14/). The 12
#     kernels' images now differ from the 8 KiB ones in exactly one word (the stack pointer base, 0x2000 ->
#     0x4000), and 0x1C00 and 0x3C00 map to the same set of every cache here, so the Embench, CoreMark,
#     random-differential and ASIC-view results must stay byte-identical to them;
#   - ramsweep, a new RAM test over every free word (all eight SRAM banks of the ASIC RAM wrapper), in
#     the FPGA view (4 configs) and the ASIC view;
#   - the upstream Embench-IoT suite (fw/up_*.hex, 12 kernels): FPGA view 4 configs and ASIC view,
#     pass 1 = pass 2, ASIC view = FPGA view on every architectural field and cache counter.
# Progress: results/fullchain_r14.log, one line per stage result.
set -uo pipefail
cd "$(dirname "$0")/.."
V=C:/questasim64_2024.1/win64/vsim.exe
LOG=results/fullchain_r14.log
REF=results/ref_pre_r14
UP="up_aha-mont64,up_crc32,up_depthconv,up_edn,up_huffbench,up_matmult-int,up_md5sum,up_nettle-sha256,up_slre,up_statemate,up_tarfind,up_ud"
: > "$LOG"
say () { echo "$*" | tee -a "$LOG"; }
fail=0
check () { if [ "$1" -eq 0 ]; then say "  [OK]   $2"; else say "  [FAIL] $2"; fail=$((fail+1)); fi; }
asic_eq_fpga () {   # $1 ASIC-view csv, $2 FPGA-view csv, $3 expected kernel count
python - "$1" "$2" "$3" <<'PY' >> "$LOG" 2>&1
import csv, sys
sys.path.insert(0, 'scripts')
from snapshot_fields import FIELDS, CYCLE_FIELDS
A = {r['kernel']: r for r in csv.DictReader(open(sys.argv[1]))}
F = {r['kernel']: r for r in csv.DictReader(open(sys.argv[2])) if r['config'] == 'DM'}
same = [f for f in FIELDS if f not in CYCLE_FIELDS] + ['load_use', 'control', 'trap']
bad = [(k, x) for k in A for x in same if A[k][x] != F[k][x]]
print('  %s vs %s, %d kernels x %d fields: %s' % (sys.argv[1], sys.argv[2], len(A), len(same),
      'IDENTICAL' if not bad else 'DIFF %s' % bad[:5]))
sys.exit(1 if bad or len(A) != int(sys.argv[3]) else 0)
PY
}
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
  "$V" -c -do "do tb/run_full_regression.do; quit -f" > "results/regression_r14_p$pass.log" 2>&1
  p=$(grep -c '^# \[PASS\]' "results/regression_r14_p$pass.log")
  f=$(grep -cE '\[FAIL\]|\*\* Fatal|\*\* Error' "results/regression_r14_p$pass.log")
  say "  pass $pass: $p PASS, $f FAIL/Fatal/Error"
  [ "$f" -eq 0 ] || fail=$((fail+1))
done
p1=$(grep -c '^# \[PASS\]' results/regression_r14_p1.log); p2=$(grep -c '^# \[PASS\]' results/regression_r14_p2.log)
[ "$p1" = "$p2" ]; check $? "regression passes agree ($p1 = $p2)"
say "######## 3. UVM at 256 lines (4 KiB), x2  $(date -Is)"
for pass in 1 2; do
  ok=0
  for t in core_smoke_test core_random_test axi_smoke_test soc_directed_test soc_periph_test; do
    "$V" -c -do "do verification/uvm/run_uvm.do $t 1 1 4 256; quit -f" > "results/uvm_r14_256_${t}_p$pass.log" 2>&1
    if grep -q 'UVM status: PASS' "results/uvm_r14_256_${t}_p$pass.log"; then ok=$((ok+1)); else say "    FAIL $t p$pass"; fi
  done
  say "  pass $pass: $ok/5 PASS"; [ "$ok" -eq 5 ] || fail=$((fail+1))
done
say "######## 4. UVM AXI at 8 / 32 / 64 B lines, x2  $(date -Is)"
for lw in 2 8 16; do
  for pass in 1 2; do
    "$V" -c -do "do verification/uvm/run_uvm.do axi_smoke_test 1 1 $lw 64; quit -f" > "results/uvm_r14_axi_lw${lw}_p$pass.log" 2>&1
    grep -q 'UVM status: PASS' "results/uvm_r14_axi_lw${lw}_p$pass.log"; check $? "axi_smoke_test line_words=$lw pass $pass"
  done
done
say "######## 5. Embench FPGA view, 4 KiB, x2  $(date -Is)"
python scripts/run_ablation.py --compile --lines 256 --out results/r14_4kb_p1.csv 2>&1 | tail -1 | tee -a "$LOG"
python scripts/run_ablation.py           --lines 256 --out results/r14_4kb_p2.csv 2>&1 | tail -1 | tee -a "$LOG"
python scripts/verify_double.py results/r14_4kb_p1.csv results/r14_4kb_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "Embench 4 KiB: pass 1 = pass 2 (48 runs)"
python scripts/verify_double.py $REF/rtlfix_4kb_p1.csv results/r14_4kb_p1.csv --key kernel --also config >/dev/null 2>&1; check $? "Embench 4 KiB: identical to the 8 KiB design (48 runs)"
say "######## 6. CoreMark, 4 KiB, x2  $(date -Is)"
for pass in 1 2; do
  python scripts/run_coremark.py --lines 256 --out results/coremark_r14_4kb_p$pass.csv 2>&1 | tail -1 | tee -a "$LOG"
done
python scripts/verify_double.py results/coremark_r14_4kb_p1.csv results/coremark_r14_4kb_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "CoreMark: pass 1 = pass 2"
python scripts/verify_double.py $REF/coremark_rtlfix_4kb_p1.csv results/coremark_r14_4kb_p1.csv --key kernel --also config >/dev/null 2>&1; check $? "CoreMark: identical to the 8 KiB design"
say "######## 7. random differential, 50 seeds, x2  $(date -Is)"
for pass in 1 2; do
  bash scripts/run_random_diff.sh 1 50 2>&1 | tail -1 | tee -a "$LOG"
  cp results/random_diff.csv "results/random_diff_r14_p$pass.csv"
done
cmp -s results/random_diff_r14_p1.csv results/random_diff_r14_p2.csv; check $? "random diff: pass 1 = pass 2"
cmp -s $REF/random_diff_rtlfix_p1.csv results/random_diff_r14_p1.csv; check $? "random diff: identical to the 8 KiB design (hashes included)"
[ "$(grep -c ',MATCH,' results/random_diff_r14_p1.csv)" -eq 50 ]; check $? "random diff: 50/50 MATCH"
say "######## 8. ASIC view (8 SRAM banks): Embench x2 and directed ISA  $(date -Is)"
python scripts/run_ablation.py --asic-view --compile --out results/asic_view_r14_4kb_p1.csv 2>&1 | tail -1 | tee -a "$LOG"
python scripts/run_ablation.py --asic-view           --out results/asic_view_r14_4kb_p2.csv 2>&1 | tail -1 | tee -a "$LOG"
python scripts/verify_double.py results/asic_view_r14_4kb_p1.csv results/asic_view_r14_4kb_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "ASIC view Embench: pass 1 = pass 2"
python scripts/verify_double.py $REF/asic_view_4kb_p1.csv results/asic_view_r14_4kb_p1.csv --key kernel --also config >/dev/null 2>&1; check $? "ASIC view Embench: identical to the 4-bank (8 KiB) ASIC view, cycles included"
asic_eq_fpga results/asic_view_r14_4kb_p1.csv results/r14_4kb_p1.csv 12; check $? "ASIC view = FPGA view on every architectural field and cache counter"
"$V" -c -do "do tb/compile_asic_view.do; vsim -onfinish stop -voptargs=+acc -gVERBOSE=0 -gTB_LINE_COUNT=256 work_asic.tb_directed_isa work_asic.asic_view_checker_isa; run -all; quit -f" > results/asic_view_directed_isa_r14.log 2>&1
[ "$(grep -c '^# \[PASS\]' results/asic_view_directed_isa_r14.log)" -ge 6 ] && ! grep -q '\*\* Fatal' results/asic_view_directed_isa_r14.log
check $? "ASIC view directed ISA: all six checks PASS"
for pass in 1 2; do
  "$V" -c -do "vsim -onfinish stop work_asic.tb_soc_asic_top_sync; run -all; quit -f" > "results/asic_top_sync_r14_p$pass.log" 2>&1
  grep -q '^# \[PASS\] soc_asic_top' "results/asic_top_sync_r14_p$pass.log" && ! grep -qE '\[FAIL\]|\*\* (Fatal|Error)' "results/asic_top_sync_r14_p$pass.log"
  check $? "ASIC wrapper synchronisers (tb_soc_asic_top_sync) pass $pass"
done
say "######## 9. ramsweep (new): FPGA view 4 configs x2, ASIC view x2  $(date -Is)"
for pass in 1 2; do
  python scripts/run_ablation.py --lines 256 --kernels ramsweep --out results/ramsweep_r14_p$pass.csv 2>&1 | tail -1 | tee -a "$LOG"
  python scripts/run_ablation.py --asic-view --kernels ramsweep --out results/ramsweep_asic_r14_p$pass.csv 2>&1 | tail -1 | tee -a "$LOG"
done
[ "$(grep -c '^ramsweep,' results/ramsweep_r14_p1.csv)" -eq 4 ] && [ "$(grep -c '^ramsweep,' results/ramsweep_asic_r14_p1.csv)" -eq 1 ]
check $? "ramsweep passes on DM, SA2, DM_VC4, DM_DSE and in the ASIC view"
python scripts/verify_double.py results/ramsweep_r14_p1.csv results/ramsweep_r14_p2.csv --key kernel --also config >/dev/null 2>&1 && \
python scripts/verify_double.py results/ramsweep_asic_r14_p1.csv results/ramsweep_asic_r14_p2.csv --key kernel --also config >/dev/null 2>&1
check $? "ramsweep: pass 1 = pass 2 (FPGA view and ASIC view)"
asic_eq_fpga results/ramsweep_asic_r14_p1.csv results/ramsweep_r14_p1.csv 1; check $? "ramsweep: ASIC view = FPGA view"
say "######## 10. upstream Embench-IoT suite (new, 12 kernels): FPGA view 4 configs x2, ASIC view x2  $(date -Is)"
for pass in 1 2; do
  python scripts/run_ablation.py --lines 256 --kernels "$UP" --out results/upstream_r14_4kb_p$pass.csv 2>&1 | tail -1 | tee -a "$LOG"
  python scripts/run_ablation.py --asic-view --kernels "$UP" --out results/upstream_asic_r14_p$pass.csv 2>&1 | tail -1 | tee -a "$LOG"
done
[ "$(tail -n +2 results/upstream_r14_4kb_p1.csv | wc -l)" -eq 48 ] && [ "$(tail -n +2 results/upstream_asic_r14_p1.csv | wc -l)" -eq 12 ]
check $? "upstream suite: 48/48 FPGA-view runs and 12/12 ASIC-view runs pass verify_benchmark"
python scripts/verify_double.py results/upstream_r14_4kb_p1.csv results/upstream_r14_4kb_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "upstream suite FPGA view: pass 1 = pass 2 (48 runs)"
python scripts/verify_double.py results/upstream_asic_r14_p1.csv results/upstream_asic_r14_p2.csv --key kernel --also config >/dev/null 2>&1; check $? "upstream suite ASIC view: pass 1 = pass 2"
asic_eq_fpga results/upstream_asic_r14_p1.csv results/upstream_r14_4kb_p1.csv 12; check $? "upstream suite: ASIC view = FPGA view"
say "######## done $(date -Is): $fail failure(s)"
python scripts/rtl_manifest.py --check 2>&1 | tail -2 | tee -a "$LOG"
exit $fail
