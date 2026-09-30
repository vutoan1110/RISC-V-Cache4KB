#!/usr/bin/env bash
# Run a flow up to a target step, retrying past the host's memory fault.
#
#   pd_to_retry.sh <design> <tag> <Step.Id> <success-dir-glob>
#
# Two things this gets right that the previous attempts did not:
#
#  * --overwrite, a fresh tag each time. `RESUME=1` WITHOUT `--from` does not
#    resume -- OpenLane restarts the flow from lint, which is how a run meant to
#    reach global placement instead re-ran synthesis as steps 07-12 and died in
#    ABC again. Resuming needs --from as well, and after a failed step the state
#    chain is not worth trusting anyway.
#
#  * success is a DIRECTORY THAT EXISTS, not an exit code. Exit codes have
#    already misled this project twice today: a truncated run wrote final/ and
#    the retry loop announced "flow complete" with eleven steps unrun.
set -uo pipefail
ASIC=$(cd "$(dirname "$0")" && pwd)
DES=$1; TAG=$2; TO=$3; MARK=$4
MAX=${MAX:-12}
# Ordered tail of the Classic flow, so a retry can resume at the step that died
# instead of starting over. The first version overwrote the run every attempt:
# attempt 1 got as far as global placement -- proving the twelve-macro floorplan
# is accepted -- and attempt 2 wiped it and died in synthesis. Throwing away ten
# minutes of good work to re-roll a two-percent dice is the wrong trade.
STEPS=(
  Yosys.JsonHeader Yosys.Synthesis Checker.YosysUnmappedCells
  Checker.YosysSynthChecks OpenROAD.CheckSDCFiles OpenROAD.STAPrePNR
  OpenROAD.Floorplan Odb.SetPowerConnections Odb.ManualMacroPlacement
  OpenROAD.CutRows OpenROAD.TapEndcapInsertion Odb.AddPDNObstructions
  OpenROAD.GeneratePDN Odb.RemovePDNObstructions OpenROAD.GlobalPlacementSkipIO
  OpenROAD.IOPlacement Odb.CustomIOPlacement Odb.ApplyDEFTemplate
  OpenROAD.GlobalPlacement
)
slug () { printf '%s' "$1" | tr 'A-Z.' 'a-z-'; }

# Where did the run get to? Highest-numbered step directory that HAS a
# state_out.json, i.e. that actually completed.
resume_at () {
  local d n line
  for line in $(ls -1d "$ASIC/$DES/runs/$TAG"/*/ 2>/dev/null | grep -v '/tmp/$' \
                | sed 's|.*/\([^/]*\)/$|\1|' | sort -t- -k1,1nr); do
    [ -f "$ASIC/$DES/runs/$TAG/$line/state_out.json" ] || continue
    d=$(printf '%s' "$line" | sed 's|^[0-9]*-||' | sed 's|-[0-9]*$||')
    for n in "${!STEPS[@]}"; do
      if [ "$(slug "${STEPS[$n]}")" = "$d" ]; then
        printf '%s' "${STEPS[$((n+1))]:-}"; return
      fi
    done
  done
  printf ''
}

for n in $(seq 1 "$MAX"); do
  from=$(resume_at)
  start=$(date +%s)
  if [ -n "$from" ]; then
    RESUME=1 bash "$ASIC/run_pd.sh" "$DES" "$TAG" --from "$from" --to "$TO" >/tmp/pd_to.log 2>&1
  else
    bash "$ASIC/run_pd.sh" "$DES" "$TAG" --to "$TO" >/tmp/pd_to.log 2>&1
  fi
  rc=$?
  el=$(( $(date +%s) - start ))
  if ls -1 "$ASIC/$DES/runs/$TAG"/*-$MARK/state_out.json >/dev/null 2>&1; then
    echo "[$n] rc=$rc ${el}s  reached $TO"
    exit 0
  fi
  why=$(grep -oE "return code [0-9]+|Signal 11|MemoryError|Can't open ABC output file|GRT-[0-9]+|Error while reading|DPL-[0-9]+|ORD-[0-9]+" /tmp/pd_to.log 2>/dev/null | tail -1)
  last=$(ls -1d "$ASIC/$DES/runs/$TAG"/*/ 2>/dev/null | grep -v '/tmp/$' \
         | sed 's|.*/\([^/]*\)/$|\1|' | sort -t- -k1,1nr | head -1)
  printf '[%2d] from=%-26s rc=%-3s %4ds  at %-32s %s\n' \
    "$n" "${from:-<start>}" "$rc" "$el" "${last:-?}" "${why:-}"
done
echo "gave up after $MAX attempts"; exit 1
