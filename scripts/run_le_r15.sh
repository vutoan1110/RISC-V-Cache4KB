#!/usr/bin/env bash
# R15 Quartus chain (review item M2: four-way set associativity and 8 KiB; NHAT_KY_RTL / FLOW_JOURNAL 2026-10-02).
# Seed 2 only -- the project's pinned seed; the 4-seed sweep of R14 already measured seed noise (LE <= 109) --
# and every fit twice, accepted only when pass 2 reproduces pass 1 on every field. Fits run one at a time.
#   dm_4kb   control: configurations 0-3 elaborate exactly the R14 modules, so this row must reproduce the R14
#            seed-2 row (results/fpga_points_r14_p1.csv, point dm_4kb); a difference is reported, not hidden
#   sa4_4kb, dm_8kb, sa2_8kb, vc4_8kb, dse_8kb, sa4_8kb   the new points
# Cooperative stop: create results/.abort_fpga_sweep (every fit not yet started returns at once).
set -uo pipefail
cd "$(dirname "$0")/.."
TAG=r15
POINTS="dm_4kb sa4_4kb dm_8kb sa2_8kb vc4_8kb dse_8kb sa4_8kb"
fail=0
for PASS in 1 2; do
    OUT=results/fpga_points_${TAG}_p$PASS.csv
    LOG=results/le_${TAG}_p$PASS.log
    : > "$LOG"
    rm -f "$OUT"
    for pt in $POINTS; do
        echo "##### $pt seed=2 pass $PASS  $(date -Is)" | tee -a "$LOG"
        python scripts/run_fpga_points.py --points "$pt" --seed 2 --tag "${TAG}_p$PASS" --out "$OUT" 2>&1 \
            | grep -v '^$' | tee -a "$LOG"
        [ "${PIPESTATUS[0]}" -eq 0 ] || fail=$((fail+1))
    done
done
LOG=results/le_${TAG}_compare.log
echo "##### COMPARE pass 1 vs pass 2 (every field)  $(date -Is)" | tee "$LOG"
python scripts/verify_double.py results/fpga_points_${TAG}_p1.csv results/fpga_points_${TAG}_p2.csv --key point 2>&1 \
    | tail -5 | tee -a "$LOG"
[ "${PIPESTATUS[0]}" -eq 0 ] || fail=$((fail+1))
echo "##### dm_4kb seed 2: R15 vs R14 (every field)" | tee -a "$LOG"
python - <<'PY' 2>&1 | tee -a "$LOG"
import csv, sys
a = {r['point']: r for r in csv.DictReader(open('results/fpga_points_r15_p1.csv'))}.get('dm_4kb')
b = {r['point']: r for r in csv.DictReader(open('results/fpga_points_r14_p1.csv'))}.get('dm_4kb')
if a is None or b is None:
    print('  missing row'); sys.exit(1)
d = [(k, b[k], a.get(k)) for k in b if a.get(k) != b[k]]
print('  dm_4kb R15 vs R14: %s' % ('IDENTICAL on %d fields' % len(b) if not d else 'DIFF %d fields: %s' % (len(d), d[:8])))
sys.exit(1 if d else 0)
PY
[ "${PIPESTATUS[0]}" -eq 0 ] || echo "  (R15 vs R14 differs: reported, see above)" | tee -a "$LOG"
echo "##### done $(date -Is): $fail failure(s)" | tee -a "$LOG"
exit $fail
