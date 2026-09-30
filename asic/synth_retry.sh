#!/usr/bin/env bash
# Retry synthesis until it survives the host's memory fault.
#
# The 4 KiB run reached ABC technology mapping and died with return code 139 --
# SIGSEGV, the same fault that hits every tool on this machine (incident A1).
# Yosys had already extracted the full netlist by then, so the design is fine
# and the failure is a fresh draw each time.
#
# --overwrite each attempt: synthesis has no partial state worth resuming, and
# a half-written netlist is worse than none.
set -uo pipefail
ASIC=$(cd "$(dirname "$0")" && pwd)
DES=${1:-soc_dm_4kb}
TAG=${2:-synth4kb}
MAX=${MAX:-15}
for n in $(seq 1 "$MAX"); do
  start=$(date +%s)
  bash "$ASIC/run_pd.sh" "$DES" "$TAG" --to Yosys.Synthesis >/tmp/synth.log 2>&1
  rc=$?
  el=$(( $(date +%s) - start ))
  nl=$(ls -1 "$ASIC/$DES/runs/$TAG"/*-yosys-synthesis/*.nl.v 2>/dev/null | head -1)
  if [ -n "$nl" ] && [ -s "$nl" ]; then
    echo "[$n] rc=$rc ${el}s  netlist written: $(basename "$nl")"
    exit 0
  fi
  why=$(grep -oE 'return code [0-9]+|Signal 11|MemoryError' /tmp/synth.log 2>/dev/null | tail -1)
  echo "[$n] rc=$rc ${el}s  ${why:-no netlist}"
done
echo "gave up after $MAX attempts"
exit 1
