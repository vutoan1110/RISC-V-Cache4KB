#!/usr/bin/env bash
# Measure what the L0 hot buffer's depth costs in cycles.
#
# The area side is already measured, on Quartus, seed 2:
#   L0=8  14,596 LE  8,015 regs  0.000 ns
#   L0=4  13,875 LE  7,399 regs  +0.710 ns   -721 LE and better timing
#   L0=2  13,465 LE  7,091 regs  -0.047 ns   -1,131 LE but misses 50 MHz
# Those are one fit each and have to be re-run before they are quoted. This is
# the other axis: a smaller buffer sends more accesses to the main array, and
# until that is counted the table above is half a story.
#
# L0=8 is re-run rather than taken from the existing CSV, so the sweep carries
# its own baseline and the whole matrix gets reproduced on a machine that is
# known to corrupt memory.
set -uo pipefail
cd "$(dirname "$0")/.."
for l0 in 8 4 2; do
  echo "########## L0_ENTRIES=$l0  $(date -Is)"
  python scripts/run_ablation.py --l0 "$l0" --out "results/ablation_l0_$l0.csv" 2>&1 | tail -4
done
echo "########## done $(date -Is)"
