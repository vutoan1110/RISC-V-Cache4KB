#!/usr/bin/env bash
# Drive the PD flow to completion on a machine that corrupts memory.
#
# Step 47 fails roughly 98 times in 100, and not because of anything in
# OpenLane: a pure-Python loop with no odb in it fails on this machine too, on
# Windows as well as WSL (see BAO_CAO_LOI_PHAN_CUNG.md). Yosys/ABC has now
# crashed the same way, return code 139. The fault is random, which is the one
# property that makes it survivable: every retry is a fresh draw.
#
# Resuming needs --from as well as the tag. Without it OpenLane restarts the
# flow at Yosys, which is what a first attempt at this script did. So the loop
# tracks where the flow died and points --from at exactly that step, and because
# the tag is reused with no --overwrite, everything already finished is kept.
#
# This gets the flow finished. It does NOT make any single number trustworthy.
# Whatever comes out still has to be reproduced by an independent run before it
# goes in a report, because this machine can also finish and be quietly wrong.
set -uo pipefail
ASIC=$(cd "$(dirname "$0")" && pwd)
DES=${1:-soc_dm_control}
TAG=${2:-sync_final}
MAX=${MAX:-80}
RUNS=$ASIC/$DES/runs/$TAG

# Classic flow, from the first blocked step to the end (openlane/flows/classic.py).
STEPS=(
  Odb.ReportDisconnectedPins Checker.DisconnectedPins Odb.ReportWireLength
  Checker.WireLength OpenROAD.FillInsertion Odb.CellFrequencyTables
  OpenROAD.RCX OpenROAD.STAPostPNR OpenROAD.IRDropReport
  Magic.StreamOut KLayout.StreamOut Magic.WriteLEF
  Odb.CheckDesignAntennaProperties KLayout.XOR Checker.XOR
  Magic.DRC KLayout.DRC Checker.MagicDRC Checker.KLayoutDRC
  Magic.SpiceExtraction Checker.IllegalOverlap Netgen.LVS Checker.LVS
  Yosys.EQY Checker.SetupViolations Checker.HoldViolations
  Checker.MaxSlewViolations Checker.MaxCapViolations
  Misc.ReportManufacturability
)

# "Odb.ReportDisconnectedPins" -> "odb-reportdisconnectedpins", which is how the
# step directory is named.
slug () { printf '%s' "$1" | tr 'A-Z.' 'a-z-'; }

# Which step did the flow stop on? Take the newest step directory, drop its
# number and any -N repeat suffix, and find it in the list.
where () {
  local d n line
  # Sort on the step NUMBER, numerically. `ls` sorts lexicographically, so
  # "99-klayout-xor" came after "126-openroad-stapostpnr"; the name that got
  # picked did not map to any step, the function fell through to its `printf 0`
  # fallback, and the loop re-ran twenty already-finished steps starting at
  # Odb.ReportDisconnectedPins -- including RCX and post-PnR STA.
  #
  # Walk down from the highest-numbered directory and take the first that names
  # a step in the tail of the flow, so an unrecognised directory costs one
  # iteration instead of hours.
  for line in $(ls -1d "$RUNS"/*/ 2>/dev/null | grep -v '/tmp/$' \
                | sed 's|.*/\([^/]*\)/$|\1|' | sort -t- -k1,1nr); do
    d=$(printf '%s' "$line" | sed 's|^[0-9]*-||' | sed 's|-[0-9]*$||')
    for n in "${!STEPS[@]}"; do
      [ "$(slug "${STEPS[$n]}")" = "$d" ] && { printf '%s' "$n"; return; }
    done
  done
  printf '0'
}

# FROM=<StepID> forces the FIRST iteration to start there, whatever the run
# directory suggests. Needed after a config change: `where()` resumes from the
# furthest step reached, so a step that has already "succeeded" is never redone
# and never picks up the new config. Passing --from on this script's command
# line does nothing -- it only reads $1, $2 and MAX -- which is how
# KLayout.StreamOut kept feeding Magic.DRC a design GDS built from the
# unstripped macro for four attempts, forty minutes each.
FORCE_FIRST=${FROM:-}

for n in $(seq 1 "$MAX"); do
  # NOT final/: a truncated run (--to <step>), used to validate the Magic
  # blackbox fix on its own, writes final/ as well. This loop then exited on
  # iteration 1 announcing "flow complete" with eleven sign-off steps still
  # unrun. The flow is done when its LAST step has a directory, nothing else.
  ls -1d "$RUNS"/*-misc-reportmanufacturability >/dev/null 2>&1 \n    && { echo "[$n] Misc.ReportManufacturability present - flow complete"; exit 0; }
  if [ -n "$FORCE_FIRST" ]; then
    from=$FORCE_FIRST
  else
    i=$(where); from=${STEPS[$i]}
  fi
  start=$(date +%s)
  RESUME=1 bash "$ASIC/run_pd.sh" "$DES" "$TAG" --from "$from" >/tmp/pd_attempt.log 2>&1
  rc=$?
  el=$(( $(date +%s) - start ))
  # Keep forcing FROM until the step has actually RUN. A crash from the host's
  # memory fault returns in seconds; a real Magic.StreamOut takes minutes. If we
  # cleared FORCE_FIRST on a four-second SIGSEGV, `where()` would resume from the
  # furthest directory on disk and quietly skip the step whose config changed --
  # exactly the trap that fed Magic.DRC a stale design GDS for four attempts.
  if [ -n "$FORCE_FIRST" ] && [ "$el" -ge 120 ]; then FORCE_FIRST=""; fi
  j=$(where)
  why=$(grep -Eom1 'Signal 11|return code 139|MemoryError|UnboundLocalError|AttributeError|TypeError|NotRenderableError' \
        "$RUNS/error.log" 2>/dev/null | head -1)
  printf '[%2d] from=%-30s -> %-30s rc=%-3s %4ds %s\n' \
    "$n" "$from" "${STEPS[$j]}" "$rc" "$el" "${why:-}"
  # NOT final/: a truncated run (--to <step>), used to validate the Magic
  # blackbox fix on its own, writes final/ as well. This loop then exited on
  # iteration 1 announcing "flow complete" with eleven sign-off steps still
  # unrun. The flow is done when its LAST step has a directory, nothing else.
  ls -1d "$RUNS"/*-misc-reportmanufacturability >/dev/null 2>&1 \n    && { echo "[$n] Misc.ReportManufacturability present - flow complete"; exit 0; }
done
echo "gave up after $MAX attempts"
exit 1
