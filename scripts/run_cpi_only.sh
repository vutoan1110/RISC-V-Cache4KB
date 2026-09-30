#!/usr/bin/env bash
# Just the three CPI matrices. Split out because the FPGA fits from the same
# batch are still running and did not need re-doing -- only the simulations did,
# and only because `work` had been overwritten by the UVM regression.
set -uo pipefail
cd "$(dirname "$0")/.."
first=--compile
for l0 in 8 4 2; do
  echo "##### L0_ENTRIES=$l0  $(date -Is)"
  python scripts/run_ablation.py $first --l0 "$l0" --out "results/ablation_l0_$l0.csv" 2>&1 | tail -3
  first=""
done
echo "##### done $(date -Is)"
