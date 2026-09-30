#!/usr/bin/env bash
# Quartus chain on the frozen RTL (NHAT_KY_RTL.md), 4 KiB only.
#
#   bash scripts/run_le_rtlfix.sh 1     # pass 1
#   bash scripts/run_le_rtlfix.sh 2     # pass 2, then compared with pass 1
#   TAG=r7r8 bash scripts/run_le_rtlfix.sh 1   # another RTL freeze, own files
#   (default TAG=rtlfix: the a0c425f8 results; a new freeze must not overwrite them)
#
# Every 4 KiB point is fitted at the four seeds, and every fit is followed by
# the assembler and the Power Analyzer, so each point x seed row carries the
# full set: resources, timing at all three corners and power. Earlier versions
# took power once per point after the seed loop, which measured whichever seed
# ran last. Each fit runs twice: this machine has been shown to corrupt data
# silently, so a fit is only accepted when a second, independent run
# reproduces every field exactly. Quartus fits run one at a time.
#
# To stop a running sweep, create results/.abort_fpga_sweep: every fit that
# has not started yet returns at once. Killing the loop's shell instead left
# the running python unable to start quartus_sta (three empty-log failures,
# 2026-09-25, NHAT_KY_RTL.md).
set -uo pipefail
cd "$(dirname "$0")/.."
PASS=${1:-1}
TAG=${TAG:-rtlfix}
OUT=results/fpga_points_${TAG}_p$PASS.csv
LOG=results/le_${TAG}_p$PASS.log
: > "$LOG"
rm -f "$OUT"
POINTS="dm_4kb sa2_4kb vc4_4kb dse_4kb"   # 4 KiB only from 2026-09-25
fail=0
for pt in $POINTS; do
  for s in 2 1 3 4; do
    echo "##### $pt seed=$s  $(date -Is)" | tee -a "$LOG"
    python scripts/run_fpga_points.py --points "$pt" --seed "$s" \
        --tag "${TAG}_p$PASS" --out "$OUT" 2>&1 | grep -v '^$' | tee -a "$LOG"
    [ "${PIPESTATUS[0]}" -eq 0 ] || fail=$((fail+1))
  done
done
# Every field for all four seeds, with the completeness gate: each point must
# have seeds 1-4 and every field filled in.
echo "##### FOUR-SEED SUMMARY" | tee -a "$LOG"
python scripts/fpga_seed_summary.py "$OUT" --out "results/fpga_seed_summary_${TAG}_p$PASS.md" 2>&1 | tail -3 | tee -a "$LOG"
[ "${PIPESTATUS[0]}" -eq 0 ] || fail=$((fail+1))
if [ "$PASS" = 2 ]; then
  echo "##### COMPARE pass 1 vs pass 2 (every field)" | tee -a "$LOG"
  python scripts/verify_double.py results/fpga_points_${TAG}_p1.csv "$OUT" --key point 2>&1 | tail -5 | tee -a "$LOG"
  [ "${PIPESTATUS[0]}" -eq 0 ] || fail=$((fail+1))
fi
echo "##### done $(date -Is): $fail failure(s)" | tee -a "$LOG"
exit $fail
