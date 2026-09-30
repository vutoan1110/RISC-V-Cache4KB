#!/usr/bin/env bash
# Full PD for the 4 KiB design, from the point global placement reached.
#
# One tag, always resumed, never overwritten. On a host that corrupts memory at
# a few percent per run, every --overwrite multiplies the number of dice rolls:
# an earlier attempt threw away 531 seconds of good work to re-roll synthesis.
# Completed steps are kept and only the failed one is retried.
#
# Resume point is the step AFTER OpenROAD.GlobalPlacement, which completed on
# the first attempt once PL_TIME_DRIVEN was turned off (three crashes with it
# on, all in the timing-driven resizer -- see pd_note.txt).
#
# Success is the LAST step of the flow having written state_out.json. Not final/,
# which a truncated run also writes; not an exit code.
set -uo pipefail
ASIC=$(cd "$(dirname "$0")" && pwd)
DES=soc_dm_4kb; TAG=synth4kb
MAX=${MAX:-60}
FORCE_FIRST=${FROM:-}
R=$ASIC/$DES/runs/$TAG

# Refuse to start beside another instance. Two of these ran on the same run
# tag at once because a new one was launched without stopping the old: they
# interleaved attempts into one log and could have fought over step
# directories. The lock is the PID file, checked against a live process.
LOCK=$R/.pd4kb.lock
if [ -f "$LOCK" ] && kill -0 "$(cat "$LOCK" 2>/dev/null)" 2>/dev/null; then
  echo "[ABORT] another pd4kb_run.sh is live (pid $(cat "$LOCK"))"; exit 1
fi
mkdir -p "$R"; echo $$ > "$LOCK"
trap 'rm -f "$LOCK"' EXIT
# Highest step number that exists before this loop starts. A forced step counts
# as done only when it completes with a number ABOVE this, so old completions of
# the same step -- made under a different config -- cannot satisfy it.
FORCE_BASE=$(ls -1d "$R"/*/ 2>/dev/null | grep -v '/tmp/$' | sed 's|.*/\([^/]*\)/$|\1|' | sed 's|-.*||' | sort -nr | head -1)
FORCE_BASE=${FORCE_BASE:-0}

# Ordered flow from just after global placement to the end, so a retry can pick
# up at whatever died rather than starting the tail again.
STEPS=(
  Odb.WriteVerilogHeader Checker.PowerGridViolations OpenROAD.STAMidPNR
  OpenROAD.RepairDesignPostGPL Odb.ManualGlobalPlacement
  OpenROAD.DetailedPlacement OpenROAD.CTS OpenROAD.STAMidPNR
  OpenROAD.ResizerTimingPostCTS OpenROAD.STAMidPNR OpenROAD.GlobalRouting
  OpenROAD.CheckAntennas OpenROAD.RepairDesignPostGRT Odb.DiodesOnPorts
  Odb.HeuristicDiodeInsertion OpenROAD.RepairAntennas
  OpenROAD.ResizerTimingPostGRT OpenROAD.STAMidPNR OpenROAD.DetailedRouting
  Odb.RemoveRoutingObstructions OpenROAD.CheckAntennas Checker.TrDRC
  Odb.ReportDisconnectedPins Checker.DisconnectedPins Odb.ReportWireLength
  Checker.WireLength OpenROAD.FillInsertion Odb.CellFrequencyTables
  OpenROAD.RCX OpenROAD.STAPostPNR OpenROAD.IRDropReport Magic.StreamOut
  KLayout.StreamOut Magic.WriteLEF Odb.CheckDesignAntennaProperties
  KLayout.XOR Checker.XOR Magic.DRC KLayout.DRC Checker.MagicDRC
  Checker.KLayoutDRC Magic.SpiceExtraction Checker.IllegalOverlap Netgen.LVS
  Checker.LVS Yosys.EQY Checker.SetupViolations Checker.HoldViolations
  Checker.MaxSlewViolations Checker.MaxCapViolations
  Misc.ReportManufacturability
)
slug () { printf '%s' "$1" | tr 'A-Z.' 'a-z-'; }

resume_at () {
  # OpenLane names a repeated step `id`, then `id-1`, `id-2`. OpenROAD.STAMidPNR
  # occurs three times in the Classic flow, so matching on name alone always
  # found the FIRST occurrence and returned its successor -- which sent the
  # retry backwards from CTS to RepairDesignPostGPL, redoing eight minutes of
  # work each time. Count the suffix to pick the right occurrence.
  local d n line occ seen
  for line in $(ls -1d "$R"/*/ 2>/dev/null | grep -v '/tmp/$' \
                | sed 's|.*/\([^/]*\)/$|\1|' | sort -t- -k1,1nr); do
    [ -f "$R/$line/state_out.json" ] || continue
    d=$(printf '%s' "$line" | sed 's|^[0-9]*-||')
    occ=0
    case "$d" in
      *-[0-9]|*-[0-9][0-9]) occ=${d##*-}; d=${d%-*} ;;
    esac
    if [ "$d" = "openroad-globalplacement" ]; then printf '%s' "${STEPS[0]}"; return; fi
    seen=0
    for n in "${!STEPS[@]}"; do
      if [ "$(slug "${STEPS[$n]}")" = "$d" ]; then
        if [ "$seen" -eq "$occ" ]; then
          printf '%s' "${STEPS[$((n+1))]:-Misc.ReportManufacturability}"; return
        fi
        seen=$((seen+1))
      fi
    done
  done
  printf '%s' "${STEPS[0]}"
}

for n in $(seq 1 "$MAX"); do
  if ls -1 "$R"/*-misc-reportmanufacturability/state_out.json >/dev/null 2>&1; then
    echo "[$n] FLOW COMPLETE"; exit 0
  fi
  # FROM forces the first iteration to start at a named step. Needed after a
  # config change: a resumed run only applies new settings to steps it actually
  # RE-RUNS, so lowering PL_TARGET_DENSITY_PCT changed nothing while global
  # placement stayed done. The proof was the failure list -- the same three
  # instances, _060918_, wire13141 and _060942_, before and after the change.
  # FORCE_FIRST is held until the forced step ACTUALLY COMPLETES, not just until
  # it has been attempted once. When the floorplan crashed on its first try, the
  # old version dropped the override, resume_at then found a later completed step
  # from the previous die, and the flow carried on routing a floorplan that no
  # longer matched the config -- the GRT-0053 table came back byte-identical,
  # which is how it was caught.
  if [ -n "${FORCE_FIRST:-}" ]; then
    fslug=$(slug "$FORCE_FIRST")
    if ls -1d "$R"/*-"$fslug" >/dev/null 2>&1        && [ -n "$(ls -1 "$R"/*-"$fslug"/state_out.json 2>/dev/null | awk -v b="$FORCE_BASE" -F/ '{split($(NF-1),a,"-"); if (a[1]+0 > b+0) print}')" ]; then
      FORCE_FIRST=""; from=$(resume_at)
    else
      from=$FORCE_FIRST
    fi
  else from=$(resume_at); fi
  start=$(date +%s)
  RESUME=1 bash "$ASIC/run_pd.sh" "$DES" "$TAG" --from "$from" >/tmp/pd4kb.log 2>&1
  rc=$?; el=$(( $(date +%s) - start ))
  last=$(ls -1d "$R"/*/ 2>/dev/null | grep -v '/tmp/$' | sed 's|.*/\([^/]*\)/$|\1|' \
         | sort -t- -k1,1nr | head -1)
  why=$(grep -oE "return code [0-9]+|Signal 11|MemoryError|GRT-[0-9]+|DPL-[0-9]+|ORD-[0-9]+|PSM-[0-9]+|ANT-[0-9]+|DRT-[0-9]+" /tmp/pd4kb.log 2>/dev/null | tail -1)
  printf '[%2d] from=%-30s rc=%-3s %5ds at %-34s %s\n' \
    "$n" "$from" "$rc" "$el" "${last:-?}" "${why:-}"
done
echo "gave up after $MAX attempts"; exit 1
