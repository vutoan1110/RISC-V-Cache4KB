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
#   run_random_diff.sh [first_seed] [last_seed]
set -uo pipefail
cd "$(dirname "$0")/.."
V=C:/questasim64_2024.1/win64/vsim.exe
FIRST=${1:-1}; LAST=${2:-50}
OUT=results/random_diff
mkdir -p "$OUT"
SUM=results/random_diff.csv
echo "seed,length,result,off_hash,on_hash" > "$SUM"

pass=0; fail=0
for s in $(seq "$FIRST" "$LAST"); do
  hex="$OUT/rand_$s.hex"; man="$OUT/rand_$s.json"
  python verification/random/gen_rv32.py --seed "$s" --length 160 \
         --output "$hex" --manifest "$man" >/dev/null 2>&1 || {
    echo "seed $s: GEN-FAIL"; echo "$s,160,GEN-FAIL,," >> "$SUM"; fail=$((fail+1)); continue; }
  off="$OUT/trace_${s}_off.txt"; on="$OUT/trace_${s}_on.txt"
  VERIFY_HEX="$hex" VERIFY_TRACE_OFF="$off" VERIFY_TRACE_ON="$on" VERIFY_SEED="$s" \
    "$V" -c -do "do tb/run_random_trace.do; quit -f" > "$OUT/sim_$s.log" 2>&1
  if [ ! -s "$off" ] || [ ! -s "$on" ]; then
    echo "seed $s: NO-TRACE"; echo "$s,160,NO-TRACE,," >> "$SUM"; fail=$((fail+1)); continue
  fi
  ho=$(sha256sum "$off" | cut -c1-16); hn=$(sha256sum "$on" | cut -c1-16)
  if [ "$ho" = "$hn" ]; then
    pass=$((pass+1)); echo "$s,160,MATCH,$ho,$hn" >> "$SUM"
  else
    fail=$((fail+1)); echo "seed $s: MISMATCH"; echo "$s,160,MISMATCH,$ho,$hn" >> "$SUM"
  fi
done
echo "random-diff seeds $FIRST..$LAST : $pass match, $fail not"
