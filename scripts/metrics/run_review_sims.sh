#!/usr/bin/env bash
# Review follow-up simulations (NHAT_KY.md 2026-09-30, requirement of 2026-09-30), FPGA view, R14 frozen RTL
# 3ea52396, 4 KiB points (256 lines), all four cache configurations, each run twice (pass 1 / pass 2):
#   A8  branch predictor off (BRANCH_PREDICT_ENABLE=0): 12 project kernels and 12 upstream kernels
#   board reference: the 12 upstream kernels at their original iteration counts (fw_board/upfull_*.hex), the
#       expected MCYCLE for the board's full-iteration runs
# Run from Git Bash on Windows: bash scripts/metrics/run_review_sims.sh   (stop: touch results/.abort_review_sims)
set -u
cd "$(dirname "$0")/../.."
OLD=crc32,depthconv,edn,fdct,huffbench,insertsort,matmult,md5sum,mont64,sha256,tarfind,wikisort
UP=up_aha-mont64,up_crc32,up_depthconv,up_edn,up_huffbench,up_matmult-int,up_md5sum,up_nettle-sha256,up_slre,up_statemate,up_tarfind,up_ud
UPFULL=$(echo "$UP" | sed 's/up_/upfull_/g')
LOG=results/review_sims.log
step () {   # <label> <args...>
    [ -e results/.abort_review_sims ] && { echo "$(date -Is) abort before $1" | tee -a "$LOG"; exit 0; }
    local label=$1; shift
    echo "$(date -Is) start $label" | tee -a "$LOG"
    python scripts/run_ablation.py --lines 256 "$@" 2>&1 | tail -3 | tee -a "$LOG"
}
for p in 1 2; do
    step "bp0 old p$p"      --bp 0 --kernels "$OLD" --out "results/bp0_r14_4kb_p$p.csv"
    step "bp0 upstream p$p" --bp 0 --kernels "$UP"  --out "results/bp0_upstream_r14_4kb_p$p.csv"
    step "upfull p$p"       --fw-dir fw_board --max-cycles 80000000 --kernels "$UPFULL" --out "results/upfull_r14_4kb_p$p.csv"
done
for f in bp0_r14_4kb bp0_upstream_r14_4kb upfull_r14_4kb; do
    python scripts/verify_double.py "results/${f}_p1.csv" "results/${f}_p2.csv" --key kernel --also config 2>&1 | tail -1 | tee -a "$LOG"
done
echo "$(date -Is) done" | tee -a "$LOG"
