#!/usr/bin/env bash
# Review follow-up simulations, second batch (the first, run_review_sims.sh, was stopped with its abort flag
# when the project's own Embench-style kernels were removed on 2026-09-30). Standard kernels only, FPGA view,
# 4 KiB points, all four cache configurations, pass 1 / pass 2:
#   A8  branch predictor off: 12 upstream kernels (pass 1 was completed by the first batch)
#   board reference: the 12 upstream kernels at their original iteration counts (fw_board/upfull_*.hex)
# Waits until the first batch has stopped, so two simulator batches never share the work library (two vsim
# runs creating implicit optimised designs in work/ at once made one fail with vsim-1962).
# Run from Git Bash on Windows: bash scripts/metrics/run_review_sims2.sh   (stop: touch results/.abort_review_sims2)
set -u
cd "$(dirname "$0")/../.."
UP=up_aha-mont64,up_crc32,up_depthconv,up_edn,up_huffbench,up_matmult-int,up_md5sum,up_nettle-sha256,up_slre,up_statemate,up_tarfind,up_ud
UPFULL=$(echo "$UP" | sed 's/up_/upfull_/g')
LOG=results/review_sims.log
until grep -q "abort before\|done$" "$LOG" 2>/dev/null; do sleep 30; done
step () {   # <label> <args...>
    [ -e results/.abort_review_sims2 ] && { echo "$(date -Is) abort before $1" | tee -a "$LOG"; exit 0; }
    local label=$1; shift
    echo "$(date -Is) start $label" | tee -a "$LOG"
    python scripts/run_ablation.py --lines 256 "$@" 2>&1 | tail -3 | tee -a "$LOG"
}
step "upfull p1"       --fw-dir fw_board --max-cycles 80000000 --kernels "$UPFULL" --out results/upfull_r14_4kb_p1.csv
step "bp0 upstream p2" --bp 0 --kernels "$UP" --out results/bp0_upstream_r14_4kb_p2.csv
step "upfull p2"       --fw-dir fw_board --max-cycles 80000000 --kernels "$UPFULL" --out results/upfull_r14_4kb_p2.csv
for f in bp0_upstream_r14_4kb upfull_r14_4kb; do
    python scripts/verify_double.py "results/${f}_p1.csv" "results/${f}_p2.csv" --key kernel --also config 2>&1 | tail -1 | tee -a "$LOG"
done
echo "$(date -Is) batch2 done" | tee -a "$LOG"
