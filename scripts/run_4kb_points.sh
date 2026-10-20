#!/usr/bin/env bash
# The 4 KiB capacity axis: four configurations, four seeds each, plus power.
#
# These points have been defined in run_fpga_points.py since the capacity sweep
# was set up and have never been fitted. The simulation side already has them --
# results/ablation_4kb.csv is the 48-run matrix at 256 lines -- so this is the
# missing half: what the capacity costs in area, timing and power rather than
# only in cycles.
#
# No RTL change: LINE_COUNT is a parameter. Seed order 1, 3, 4, 2, with power
# measured on the seed-2 fit, matching every other point in the table.
set -uo pipefail
cd "$(dirname "$0")/.."

sweep () {
  local pt="$1"
  for s in 1 3 4 2; do
    echo "##### $pt seed=$s  $(date -Is)"
    python scripts/run_fpga_points.py --points "$pt" --seed "$s" 2>&1 | tail -3
  done
  echo "##### $pt POWER  $(date -Is)"
  python scripts/run_power.py --points "$pt" 2>&1 | tail -3
}

sweep dm_4kb
sweep dse_4kb
sweep sa2_4kb
sweep vc4_4kb
echo "##### all done $(date -Is)"
