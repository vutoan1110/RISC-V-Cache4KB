#!/usr/bin/env bash
# Drive the 4 KiB flow on the channel-corrected floorplan, reconnecting after
# each host crash.
#
# The host segfaults randomly (see BAO_CAO_LOI_PHAN_CUNG.md); a run therefore
# has to be resumable at whatever step died. Three things this gets right that
# earlier loops got wrong:
#
#   * step directories are ordered numerically, not lexicographically, so "99-"
#     does not sort after "126-"
#   * a step counts as finished only when it has state_out.json; OpenLane
#     creates the directory before running the step
#   * a repeated step is written `id`, `id-1`, `id-2`, so the occurrence has to
#     be counted to resume at the right one -- OpenROAD.STAMidPNR appears three
#     times in the Classic flow
set -uo pipefail
ASIC=$(cd "$(dirname "$0")" && pwd)
DES=soc_dm_4kb; TAG=${TAG:-ch4kb}
TO=${TO:-OpenROAD.CTS}
MAX=${MAX:-40}
R=$ASIC/$DES/runs/$TAG
mapfile -t STEPS < "$ASIC/classic_steps.txt"

LOCK=$R/.ch4kb.lock
if [ -f "$LOCK" ] && kill -0 "$(cat "$LOCK" 2>/dev/null)" 2>/dev/null; then
  echo "[ABORT] another ch4kb_run.sh is live (pid $(cat "$LOCK"))"; exit 1
fi
mkdir -p "$R"; echo $$ > "$LOCK"; trap 'rm -f "$LOCK"' EXIT

slug () { printf '%s' "$1" | tr 'A-Z.' 'a-z-'; }

# Index in STEPS of the first step that has NOT completed.
next_index () {
  local i=0 s sl occ_needed occ_seen d
  declare -A used
  for s in "${STEPS[@]}"; do
    sl=$(slug "$s")
    occ_needed=${used[$sl]:-0}
    if [ "$occ_needed" = 0 ]; then d="$R/"*"-$sl"; else d="$R/"*"-$sl-$occ_needed"; fi
    # shellcheck disable=SC2086
    local hit=""
    for cand in $(ls -1d $R/*/ 2>/dev/null | sed 's|/$||;s|.*/||' | sort -t- -k1,1n); do
      local base=${cand#*-}
      if [ "$occ_needed" = 0 ]; then [ "$base" = "$sl" ] || continue
      else [ "$base" = "$sl-$occ_needed" ] || continue; fi
      [ -f "$R/$cand/state_out.json" ] && hit=$cand && break
    done
    [ -n "$hit" ] || { echo "$i"; return; }
    used[$sl]=$((occ_needed+1))
    i=$((i+1))
  done
  echo "$i"
}

for attempt in $(seq 1 "$MAX"); do
  idx=$(next_index)
  if [ "$idx" -ge "${#STEPS[@]}" ]; then echo "[DONE] all steps complete"; exit 0; fi
  FROM=${STEPS[$idx]}
  # Stop once the requested end step has completed.
  target_idx=-1
  for j in "${!STEPS[@]}"; do [ "${STEPS[$j]}" = "$TO" ] && target_idx=$j && break; done
  if [ "$target_idx" -ge 0 ] && [ "$idx" -gt "$target_idx" ]; then
    echo "[DONE] reached $TO after $((attempt-1)) attempt(s)"; exit 0
  fi
  echo "[$attempt/$MAX] $(date -Is) resume from $FROM (step index $idx)"
  if [ "$idx" = 0 ]; then
    bash "$ASIC/run_pd.sh" "$DES" "$TAG" --to "$TO" >/tmp/ch4kb.log 2>&1
  else
    RESUME=1 bash "$ASIC/run_pd.sh" "$DES" "$TAG" --from "$FROM" --to "$TO" >/tmp/ch4kb.log 2>&1
  fi
  rc=$?
  newidx=$(next_index)
  echo "     rc=$rc  progress: $idx -> $newidx"
  if [ "$rc" = 0 ] && [ "$newidx" -gt "$target_idx" ]; then
    echo "[DONE] reached $TO"; exit 0
  fi
  if [ "$newidx" = "$idx" ] && [ "$rc" != 0 ]; then
    echo "     no progress; last 6 lines:"; tail -6 /tmp/ch4kb.log | sed 's/^/       /'
  fi
done
echo "[GIVEUP] $MAX attempts without reaching $TO"; exit 1
