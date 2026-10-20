#!/usr/bin/env bash
# R16 Quartus chain (review item M1, FAST_HIT; NHAT_KY.md 2026-10-06). Seed 2 only (the pinned seed; seed noise was
# measured on R14: LE <= 109), every fit twice, accepted only when pass 2 reproduces pass 1 on every field. One fit
# at a time.
#   dm_4kb sa2_4kb vc4_4kb dse_4kb sa4_4kb   FAST_HIT 0 controls: the RTL is formally equivalent to R15 at these
#            points, so each row is compared with its R14 / R15 seed-2 row; a difference is reported, not hidden
#            (Quartus maps the source text, which changed)
#   sa2_4kb_fast vc4_4kb_fast dse_4kb_fast sa4_4kb_fast   the cost of FAST_HIT: LE, Fmax / slack at all corners, power
# Cooperative stop: create results/.abort_fpga_sweep (every fit not yet started returns at once).
set -uo pipefail
cd "$(dirname "$0")/.."
TAG=r16
POINTS="dm_4kb sa2_4kb vc4_4kb dse_4kb sa4_4kb sa2_4kb_fast vc4_4kb_fast dse_4kb_fast sa4_4kb_fast"
fail=0
# A fit needs several GB; wait (checking every 2 min) until Windows has >= 6 GB available, so a fit never starts
# into memory pressure (other jobs and other programs share this machine).
avail () { powershell -NoProfile -Command "[int](Get-Counter '\Memory\Available MBytes').CounterSamples.CookedValue" 2>/dev/null | tr -d '\r'; }
memgate () { while :; do [ -e results/.abort_fpga_sweep ] && return 0; a=$(avail); [ "${a:-0}" -ge 6000 ] && return 0; sleep 120; done; }
for PASS in 1 2; do
    OUT=results/fpga_points_${TAG}_p$PASS.csv
    LOG=results/le_${TAG}_p$PASS.log
    : > "$LOG"
    rm -f "$OUT"
    for pt in $POINTS; do
        memgate
        echo "##### $pt seed=2 pass $PASS  $(date -Is)  (Windows available $(avail) MB)" | tee -a "$LOG"
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
echo "##### FAST_HIT 0 controls vs the R14 / R15 seed-2 rows (every field), and the FAST_HIT cost" | tee -a "$LOG"
python - <<'PY' 2>&1 | tee -a "$LOG"
import csv
new = {r['point']: r for r in csv.DictReader(open('results/fpga_points_r16_p1.csv'))}
ref = {r['point']: r for r in csv.DictReader(open('results/fpga_points_r14_p1.csv'))}
ref.update({r['point']: r for r in csv.DictReader(open('results/fpga_points_r15_p1.csv'))})
for p in ('dm_4kb', 'sa2_4kb', 'vc4_4kb', 'dse_4kb', 'sa4_4kb'):
    a, b = new.get(p), ref.get(p)
    if a is None or b is None:
        print('  %-8s missing row' % p); continue
    d = [k for k in b if a.get(k) != b[k]]
    print('  %-8s R16 vs reference: %s' % (p, 'IDENTICAL on %d fields' % len(b) if not d else
          'DIFF %d fields, e.g. le %s->%s, setup_s85_slack %s->%s' % (len(d), b.get('le'), a.get('le'),
          b.get('setup_s85_slack'), a.get('setup_s85_slack'))))
for p in ('sa2_4kb', 'vc4_4kb', 'dse_4kb', 'sa4_4kb'):
    a, f = new.get(p), new.get(p + '_fast')
    if a and f:
        print('  %-8s FAST_HIT 0 -> 1: le %s -> %s, fmax_s85 %s -> %s, setup_s85_slack %s -> %s' % (
            p, a.get('le'), f.get('le'), a.get('fmax_s85'), f.get('fmax_s85'), a.get('setup_s85_slack'), f.get('setup_s85_slack')))
PY
echo "##### done $(date -Is): $fail failure(s)" | tee -a "$LOG"
exit $fail
