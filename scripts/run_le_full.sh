#!/usr/bin/env bash
# Bring every FPGA point up to the constitution: 4 seeds and a measured power
# number, not one fit and an assumption.
#
# Where the gaps were:
#   sa2, dm_vc4, dm_dse   4 seeds + power        complete
#   dm                    1 seed,  NO power      config 0 is the baseline of the
#                                                whole DSE and had neither
#   dm_nopc               1 seed,  no power
#   dm@l0-4, dm@l0-2      1 seed,  no power      the two points a decision rests on
#
# Seed order is 1, 3, 4, then 2. Seed 2 goes last on purpose: all four seeds
# share one Quartus revision, so whatever is fitted last is what sits on disk,
# and power has to be measured on the same seed as every existing power row.
# Refitting seed 2 also re-measures a number already in the CSV, which is a free
# reproducibility check.
#
# Sequential by construction. run_fpga_points.py refuses to start if another
# quartus_ process is alive, so the project's own rule is enforced, not
# remembered.
set -uo pipefail
cd "$(dirname "$0")/.."

sweep () {            # $1 = point name, $2 = L0 depth
  local pt=$1 l0=$2
  for s in 1 3 4 2; do
    echo "##### $pt l0=$l0 seed=$s  $(date -Is)"
    python scripts/run_fpga_points.py --points "$pt" --seed "$s" --l0 "$l0" 2>&1 | tail -3
  done
  echo "##### $pt l0=$l0 POWER (on the seed-2 fit)  $(date -Is)"
  python scripts/run_power.py --points "$pt" --l0 "$l0" 2>&1 | tail -3
}

sweep dm      8    # baseline config 0 -- the weakest row in the main table
sweep dm      4    # the L0 decision
sweep dm      2
sweep dm_nopc 8    # counter-bank overhead control
echo "##### done $(date -Is)"
