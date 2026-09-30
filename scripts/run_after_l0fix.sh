#!/usr/bin/env bash
# Re-run everything the L0 tag-slice bug invalidated (Entry 32), in one
# sequential job so Quartus and Questa do not fight for the machine -- when they
# ran together earlier a Quartus fit went from 334 s to 1,959 s.
#
# CPI first because it is cheap and it is the axis that decides whether the L0
# depth is worth fitting at all. Then the fits.
set -uo pipefail
cd "$(dirname "$0")/.."

echo "######## CPI matrices $(date -Is)"
# --compile on the first pass, always. The UVM regression compiles its own file
# list into the same `work` library, so whatever ran last owns it: without this
# every run dies with "Failed to find design unit 'tb_benchmark_snapshot'"
# (vopt-13130) and the whole matrix comes out empty in under a minute.
first=--compile
for l0 in 8 4 2; do
  echo "##### L0_ENTRIES=$l0  $(date -Is)"
  python scripts/run_ablation.py $first --l0 "$l0" --out "results/ablation_l0_$l0.csv" 2>&1 | tail -3
  first=""
done

echo "######## FPGA fits, 4 seeds + power $(date -Is)"
sweep () {
  local pt=$1 l0=$2
  for s in 1 3 4 2; do
    echo "##### $pt l0=$l0 seed=$s  $(date -Is)"
    python scripts/run_fpga_points.py --points "$pt" --seed "$s" --l0 "$l0" 2>&1 | tail -3
  done
  echo "##### $pt l0=$l0 POWER  $(date -Is)"
  python scripts/run_power.py --points "$pt" --l0 "$l0" 2>&1 | tail -3
}
# dm at L0=8 already has 4 seeds and power, measured on RTL the fix does not
# change. Not repeated. These are the ones that were void or missing.
sweep dm      4
sweep dm      2
sweep dm_nopc 8
echo "######## done $(date -Is)"
