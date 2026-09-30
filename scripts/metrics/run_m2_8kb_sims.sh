#!/usr/bin/env bash
# M2 (review): 8 KiB cache points in simulation - 512 lines x 16 B for both caches, the frozen RTL (no change:
# LINE_COUNT is a parameter), all four configurations, the 12 standard Embench-IoT kernels, pass 1 / pass 2.
# Uses its own compiled library work_b so it can run beside a batch that uses work.
# Run from Git Bash on Windows: bash scripts/metrics/run_m2_8kb_sims.sh   (stop: touch results/.abort_m2_sims)
set -u
cd "$(dirname "$0")/../.."
LOG=results/m2_8kb_sims.log
V="C:/questasim64_2024.1/win64/vsim.exe"
echo "$(date -Is) compile work_b" | tee -a "$LOG"
"$V" -c -do "do scripts/metrics/compile_active_design_b.do; quit -f" -l results/m2_compile_work_b.log > /dev/null 2>&1
if grep -q '\*\* \(Error\|Fatal\)' results/m2_compile_work_b.log; then echo "[FAIL] compile, see results/m2_compile_work_b.log" | tee -a "$LOG"; exit 1; fi
for p in 1 2; do
    [ -e results/.abort_m2_sims ] && { echo "$(date -Is) abort before pass $p" | tee -a "$LOG"; exit 0; }
    echo "$(date -Is) start 8kb pass $p" | tee -a "$LOG"
    python scripts/run_ablation.py --lib work_b --lines 512 --out "results/r14_8kb_p$p.csv" 2>&1 | tail -3 | tee -a "$LOG"
done
python scripts/verify_double.py results/r14_8kb_p1.csv results/r14_8kb_p2.csv --key kernel --also config 2>&1 | tail -1 | tee -a "$LOG"
echo "$(date -Is) done" | tee -a "$LOG"
