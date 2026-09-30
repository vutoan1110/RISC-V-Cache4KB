#!/usr/bin/env bash
# The fits still missing after run_after_l0fix.sh died: dm@l0-2 and dm_nopc.
#
# It died because I edited it while bash was running it -- bash reads a script
# incrementally by byte offset, so an in-place patch shifts everything it has
# not read yet and the next line parses as garbage. dm@l0-4 had already
# finished all four seeds and its power measurement, so only these two points
# are outstanding. Written as a NEW file for the same reason.
#
# Waits for the CPI matrices to finish first. Quartus and Questa do not
# conflict, but they compete: a fit measured at 334 s took 1,959 s while a
# simulation matrix was running. Waiting costs less than overlapping.
set -uo pipefail
cd "$(dirname "$0")/.."

echo "waiting for the CPI matrices  $(date -Is)"
for i in $(seq 1 240); do
  grep -q '^##### done' results/cpi_only.log 2>/dev/null && break
  sleep 30
done
echo "proceeding  $(date -Is)"

sweep () {
  local pt="$1" l0="$2"
  for s in 1 3 4 2; do
    echo "##### $pt l0=$l0 seed=$s  $(date -Is)"
    python scripts/run_fpga_points.py --points "$pt" --seed "$s" --l0 "$l0" 2>&1 | tail -3
  done
  echo "##### $pt l0=$l0 POWER  $(date -Is)"
  python scripts/run_power.py --points "$pt" --l0 "$l0" 2>&1 | tail -3
}

sweep dm      2
sweep dm_nopc 8
echo "##### all done $(date -Is)"
