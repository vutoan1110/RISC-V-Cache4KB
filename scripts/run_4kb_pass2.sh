#!/usr/bin/env bash
# Second independent pass over the 4 KiB points, for the Double-Execution
# Protocol. Waits for pass 1 to finish, snapshots its rows, re-runs every fit at
# the same seeds, and compares field by field.
#
# Same seed, same settings, twice. Random memory corruption cannot repeat itself
# identically, so two passes that agree on every digit are trustworthy and two
# that disagree are not.
set -uo pipefail
cd "$(dirname "$0")/.."
PASS2_LOG=${PASS2_LOG:-results/fpga_4kb_pass2.log}

echo "waiting for pass 1  $(date -Is)"
done_p1=0
for i in $(seq 1 960); do
  if grep -q '^##### all done' results/fpga_4kb.log 2>/dev/null; then done_p1=1; break; fi
  sleep 30
done
# ABORT, do not proceed. The first version ran out after four hours and carried
# on regardless: pass 1 was still fitting, every pass-2 fit was refused by the
# concurrency guard, nothing was measured, and the script still printed
# "[VERIFIED] 11 rows identical" -- because it compared pass 1's snapshot with
# itself. See PD_incident_report.md C10.
if [ "$done_p1" != "1" ]; then
  echo "[ABORT] pass 1 has not finished; refusing to 'verify' unmeasured data"
  exit 1
fi
echo "pass 1 finished, snapshotting  $(date -Is)"

python - <<'PY'
import csv, io
rows=[r for r in csv.DictReader(open('results/fpga_points.csv',encoding='utf-8'))
      if '4kb' in r['point']]
cols=list(rows[0].keys())
with io.open('results/fpga_4kb_pass1.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(rows)
print('pass 1 snapshot: %d rows' % len(rows))
PY

for pt in dm_4kb dse_4kb sa2_4kb vc4_4kb; do
  for s in 1 3 4 2; do
    echo "##### PASS2 $pt seed=$s  $(date -Is)"
    if ! python scripts/run_fpga_points.py --points "$pt" --seed "$s" 2>&1 | tee /tmp/p2.txt | tail -2; then
      echo "[ABORT] fit failed"; exit 1; fi
    # A refused fit is not a measured fit. Without this the pass completes with
    # nothing re-run and the comparison becomes a file against itself.
    if grep -q 'already running\|\[FAIL\]' /tmp/p2.txt; then
      echo "[ABORT] fit was refused or failed; pass 2 is not a second measurement"
      exit 1
    fi
  done
done

python - <<'PY'
import csv, io
rows=[r for r in csv.DictReader(open('results/fpga_points.csv',encoding='utf-8'))
      if '4kb' in r['point']]
cols=list(rows[0].keys())
with io.open('results/fpga_4kb_pass2.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(rows)
print('pass 2 snapshot: %d rows' % len(rows))
PY

echo "##### VERIFY  $(date -Is)"
# NOT a byte-comparison of the snapshots. That guard was added after C10 with
# the reasoning "a real second pass cannot reproduce a byte-identical file". It
# is wrong: the seed column is rewritten with the SAME value, and when all
# sixteen fits reproduce exactly the two files ARE identical. The guard fired on
# the best possible outcome -- a false FAIL produced by a guard against a false
# PASS.
#
# The question is not whether the files differ, it is whether pass 2 measured.
# That is answered by the log: one "[PASS] 1 fit(s)" per fit, and no refusals.
ran=$(grep -c '^\[PASS\] 1 fit' "$PASS2_LOG" 2>/dev/null || echo 0)
refused=$(grep -c 'already running' "$PASS2_LOG" 2>/dev/null || echo 0)
if [ "$ran" -lt 16 ] || [ "$refused" -gt 0 ]; then
  echo "[ABORT] pass 2 completed $ran/16 fits with $refused refusals -- not a second measurement"
  exit 1
fi
echo "pass 2 measured $ran/16 fits, $refused refused"
python scripts/verify_double.py results/fpga_4kb_pass1.csv results/fpga_4kb_pass2.csv --key point
echo "##### pass2 done $(date -Is)"
