#!/usr/bin/env bash
# Re-run a segment of an existing OpenLane run from a given step, retrying
# across host crashes.
#
# ch4kb_run.sh cannot do this: it resumes at the first step that has never
# completed, and after the first pass every step up to CTS has completed once.
# Re-running the floorplan makes a SECOND completed floorplan, so counting
# occurrences from the start of the flow would say the run is further along
# than it is.
#
# This anchors on BASE, the highest step number present before the segment
# starts. Only directories numbered above BASE count, and they are matched in
# order against the flow's steps from FROM onward.
set -uo pipefail
ASIC=$(cd "$(dirname "$0")" && pwd)
DES=${DES:-soc_dm_4kb}; TAG=${TAG:-ch4kb}
FROM=${FROM:-OpenROAD.Floorplan}
TO=${TO:-OpenROAD.CTS}
MAX=${MAX:-40}
R=$ASIC/$DES/runs/$TAG
DES_CFG=$ASIC/$DES/config.json
mapfile -t ALL < "$ASIC/classic_steps.txt"

# Steps gated off in config never produce a state_out.json, so a segment counter
# that waits for one stalls forever. Observed: RUN_HEURISTIC_DIODE_INSERTION was
# set false and the driver spent 295 attempts "resuming from" a step OpenLane
# was skipping. Drop gated-off steps from the segment.
SKIP_STEPS=""
for pair in "Odb.HeuristicDiodeInsertion:RUN_HEURISTIC_DIODE_INSERTION"             "OpenROAD.ResizerTimingPostCTS:RUN_POST_CTS_RESIZER_TIMING"             "OpenROAD.RepairDesignPostGRT:RUN_POST_GRT_DESIGN_REPAIR"             "OpenROAD.IRDropReport:RUN_IRDROP_REPORT"             "Yosys.EQY:RUN_EQY"; do
  step=${pair%%:*}; var=${pair##*:}
  val=$(python3 -c "import json;print(json.load(open('$DES_CFG')).get('$var',''))" 2>/dev/null)
  [ "$val" = "False" ] && SKIP_STEPS="$SKIP_STEPS $step"
done
[ -n "$SKIP_STEPS" ] && echo "[refloor] bo qua buoc bi tat:$SKIP_STEPS"

LOCK=$R/.refloor.lock
if [ -f "$LOCK" ] && kill -0 "$(cat "$LOCK" 2>/dev/null)" 2>/dev/null; then
  echo "[ABORT] another refloor_run.sh is live (pid $(cat "$LOCK"))"; exit 1
fi
mkdir -p "$R"; echo $$ > "$LOCK"; trap 'rm -f "$LOCK"' EXIT

BASE=$(ls -1d "$R"/*/ 2>/dev/null | sed 's|.*/\([^/]*\)/$|\1|' | sed 's|-.*||' \
       | grep -E '^[0-9]+$' | sort -nr | head -1)
BASE=${BASE:-0}
echo "[refloor] BASE=$BASE  FROM=$FROM  TO=$TO"

# The tail of the flow, starting at FROM.
SEG=(); seen=0
for s in "${ALL[@]}"; do
  [ "$s" = "$FROM" ] && seen=1
  case " $SKIP_STEPS " in *" $s "*) continue;; esac
  [ "$seen" = 1 ] && SEG+=("$s")
done
slug () { printf '%s' "$1" | tr 'A-Z.' 'a-z-'; }

# How many of SEG have completed in directories numbered above BASE, matched in
# order. Prints that count.
seg_done () {
  local i=0 d base
  for d in $(ls -1d "$R"/*/ 2>/dev/null | sed 's|.*/\([^/]*\)/$|\1|' \
             | grep -E '^[0-9]+-' | sort -t- -k1,1n); do
    [ "${d%%-*}" -gt "$BASE" ] || continue
    [ -f "$R/$d/state_out.json" ] || continue
    base=${d#*-}; base=${base%%-[0-9]}          # drop the -1 / -2 repeat suffix
    [ "$i" -lt "${#SEG[@]}" ] || break
    if [ "$base" = "$(slug "${SEG[$i]}")" ]; then i=$((i+1)); fi
  done
  echo "$i"
}

target=0
for j in "${!SEG[@]}"; do [ "${SEG[$j]}" = "$TO" ] && target=$((j+1)) && break; done

for attempt in $(seq 1 "$MAX"); do
  done_n=$(seg_done)
  if [ "$done_n" -ge "$target" ]; then
    echo "[DONE] segment reached $TO after $((attempt-1)) attempt(s)"; exit 0
  fi
  nxt=${SEG[$done_n]}
  echo "[$attempt/$MAX] $(date -Is) segment $done_n/$target, resume from $nxt"
  # A --from into a fresh tag has no step state to read, so the first
  # invocation of a brand-new run must carry an explicit initial state.
  # Once any step in the tag has completed, the state belongs to the tag and
  # the flag must not be repeated (it would rewind the run every attempt).
  INIT_ARG=""
  if [ -n "${INIT_STATE:-}" ] && [ "$(seg_done)" = "0" ]; then
    INIT_ARG="--with-initial-state $INIT_STATE"
  fi
  RESUME=1 bash "$ASIC/run_pd.sh" "$DES" "$TAG" $INIT_ARG --from "$nxt" --to "$TO" >/tmp/refloor.log 2>&1
  rc=$?
  after=$(seg_done)
  echo "     rc=$rc  segment: $done_n -> $after"
  if [ "$after" = "$done_n" ] && [ "$rc" != 0 ]; then
    tail -4 /tmp/refloor.log | sed 's/^/       /'
  fi
done
echo "[GIVEUP] $MAX attempts"; exit 1
