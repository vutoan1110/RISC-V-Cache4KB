#!/usr/bin/env bash
# Random differential test across many seeds.
#
# Review item A7: the paper reports a random-differential run at one seed and
# does not keep the log. One seed proves almost nothing about a differential
# test -- the point of the method is coverage across programs.
#
# For each seed: generate a random RV32 program, run it with the branch
# predictor off and on, and require the two architectural traces to match. A
# disagreement is a real design bug; the predictor must not change results.
#
#   run_random_diff.sh [first_seed] [last_seed] [pass=1|2|unspecified]
# Each invocation has a fresh raw-evidence directory; random_diff.csv remains
# the compatibility summary copied by the full-chain driver after each pass.
set -uo pipefail
cd "$(dirname "$0")/.."
V=${QUESTA_VSIM:-C:/questasim64_2024.1/win64/vsim.exe}
PY=${PYTHON:-python}
FIRST=${1:-1}; LAST=${2:-50}
PASS=${3:-unspecified}
if ! [[ "$FIRST" =~ ^[0-9]+$ && "$LAST" =~ ^[0-9]+$ ]] ||
   (( FIRST < 1 || LAST < FIRST )) || ! [[ "$PASS" =~ ^(1|2|unspecified)$ ]]; then
  echo "[FAIL] require positive ordered seeds and pass 1, 2 or unspecified" >&2
  exit 2
fi
mkdir -p results/random_diff_runs || exit 1
OUT=$(mktemp -d "results/random_diff_runs/$(date -u +%Y%m%dT%H%M%SZ)_pass${PASS}_XXXXXX") || exit 1
SUM="$OUT/summary.csv"
echo "seed,length,result,off_hash,on_hash" > "$SUM"
"$PY" -B scripts/rtl_manifest.py --check > "$OUT/manifest_start.log" 2>&1 || {
  cat "$OUT/manifest_start.log"; exit 1; }
"$PY" -B - "$OUT" "$FIRST" "$LAST" "$PASS" <<'PY'
import hashlib, json, sys
from pathlib import Path
out = Path(sys.argv[1])
sources = ['scripts/run_random_diff.sh', 'scripts/verify_random_diff_case.py',
           'verification/random/gen_rv32.py', 'tb/run_random_trace.do', 'tb/random_trace_tb.sv',
           'results/rtl_manifest.json']
(out / 'inputs.json').write_text(json.dumps({'first_seed': int(sys.argv[2]), 'last_seed': int(sys.argv[3]),
    'pass': sys.argv[4], 'sources': {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources}},
    indent=2) + '\n', encoding='ascii')
PY
[ "$?" -eq 0 ] || exit 1

pass=0; fail=0
for s in $(seq "$FIRST" "$LAST"); do
  hex="$OUT/rand_$s.hex"; man="$OUT/rand_$s.json"
  "$PY" -B verification/random/gen_rv32.py --seed "$s" --length 160 \
         --output "$hex" --manifest "$man" > "$OUT/gen_$s.log" 2>&1 || {
    echo "seed $s: GEN-FAIL"; echo "$s,160,GEN-FAIL,," >> "$SUM"; fail=$((fail+1)); continue; }
  off="$OUT/trace_${s}_off.txt"; on="$OUT/trace_${s}_on.txt"
  rc=0
  VERIFY_HEX="$hex" VERIFY_TRACE_OFF="$off" VERIFY_TRACE_ON="$on" VERIFY_SEED="$s" \
    "$V" -c -do "do tb/run_random_trace.do; quit -f" > "$OUT/sim_$s.log" 2>&1 || rc=$?
  if ! "$PY" -B scripts/verify_random_diff_case.py --seed "$s" --rc "$rc" \
       --log "$OUT/sim_$s.log" --off "$off" --on "$on" --hex "$hex" --manifest "$man" \
       --out "$OUT/verified_$s.json" > "$OUT/check_$s.log" 2>&1; then
    echo "seed $s: SIM-FAIL (see $OUT/check_$s.log)"
    echo "$s,160,SIM-FAIL,," >> "$SUM"; fail=$((fail+1)); continue
  fi
  if ! ho=$(sha256sum "$off" | cut -c1-16) || ! hn=$(sha256sum "$on" | cut -c1-16) ||
     ! [[ "$ho" =~ ^[0-9a-f]{16}$ && "$hn" =~ ^[0-9a-f]{16}$ ]]; then
    echo "seed $s: HASH-FAIL"; echo "$s,160,HASH-FAIL,," >> "$SUM"
    fail=$((fail+1)); continue
  fi
  if [ "$ho" = "$hn" ]; then
    pass=$((pass+1)); echo "$s,160,MATCH,$ho,$hn" >> "$SUM"
  else
    fail=$((fail+1)); echo "seed $s: MISMATCH"; echo "$s,160,MISMATCH,$ho,$hn" >> "$SUM"
  fi
done
"$PY" -B scripts/rtl_manifest.py --check > "$OUT/manifest_end.log" 2>&1 || fail=$((fail+1))
"$PY" -B - "$OUT/inputs.json" <<'PY'
import hashlib, json, sys
from pathlib import Path
data = json.loads(Path(sys.argv[1]).read_text())
changed = [p for p, h in data['sources'].items() if hashlib.sha256(Path(p).read_bytes()).hexdigest() != h]
if changed:
    raise SystemExit('[FAIL] random-diff sources changed during execution: ' + ', '.join(changed))
PY
[ "$?" -eq 0 ] || fail=$((fail+1))
"$PY" -B - "$SUM" "$FIRST" "$LAST" <<'PY'
import csv, sys
with open(sys.argv[1], newline='') as f:
    rows = list(csv.DictReader(f))
expected = {str(s) for s in range(int(sys.argv[2]), int(sys.argv[3]) + 1)}
if len(rows) != len(expected) or {r['seed'] for r in rows} != expected:
    raise SystemExit('[FAIL] summary seed set incomplete or duplicated')
if any(r['result'] != 'MATCH' for r in rows):
    raise SystemExit('[FAIL] summary contains failed cases')
PY
[ "$?" -eq 0 ] || fail=$((fail+1))
cp "$SUM" results/random_diff.csv || fail=$((fail+1))
echo "raw evidence: $OUT (pass $PASS)"
echo "random-diff seeds $FIRST..$LAST : $pass match, $fail not"
[ "$fail" -eq 0 ] && [ "$pass" -eq "$(( LAST - FIRST + 1 ))" ]
