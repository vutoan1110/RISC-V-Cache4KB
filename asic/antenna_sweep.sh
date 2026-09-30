#!/usr/bin/env bash
# Single-variable sweep of the two antenna-repair mechanisms.
#
# The baseline (heuristic off, GRT_ANTENNA_ITERS 3) left 498 net and 643 pin
# violations after repair, so it does not meet the sign-off requirement. The
# question is which mechanism closes the gap, and what each costs in area.
#
#   A  heuristic diode insertion on, iterations at the default 3
#   B  heuristic off, iterations raised to 15   <- preferred if it reaches zero,
#                                                 because it adds no diodes
#   C  both
#
# Run in two phases on purpose. Phase 1 stops at RepairAntennas, which is where
# the violation count is decided, around step 40 of 55. That is the right place
# to measure: there is no antenna repair after detailed routing, so both knobs
# act here and nothing downstream can improve the count. Measured on the
# baseline, the two stages agree closely -- 498 net violations after repair at
# global routing, 501 after detailed routing -- so step 40 is a proxy for the
# sign-off number, and an empirically checked one rather than an assumed one. A configuration that
# does not reach zero is disqualified by the primary goal and its area is
# irrelevant, so there is no reason to spend another hour routing it. Phase 2
# takes whichever configurations survive all the way to post-route area.
#
#   bash antenna_sweep.sh phase1            # violation counts for A, B, C
#   bash antenna_sweep.sh phase2 <tag>...   # full flow for the survivors
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
DES=soc_dm_control
OUT=$HERE/../results/antenna_sweep.csv

# tag | label | extra openlane args
points() {
    cat <<'EOF'
ant_A|heuristic=on  iters=3|-c RUN_HEURISTIC_DIODE_INSERTION=true
ant_B|heuristic=off iters=15|-c GRT_ANTENNA_ITERS=15
ant_C|heuristic=on  iters=10|-c RUN_HEURISTIC_DIODE_INSERTION=true -c GRT_ANTENNA_ITERS=10
EOF
}

# Violations reported by the check that runs *after* repair, plus diode count.
measure() {
    local tag=$1 label=$2
    local run="$HERE/$DES/runs/$tag"
    local post="$run/40-openroad-repairantennas/2-openroad-checkantennas"
    local pre="$run/38-openroad-checkantennas"
    local nets pins nets0 pins0 diodes area
    nets0=$(grep -ohE 'ANT-0002\] Found [0-9]+' "$pre"/*.log 2>/dev/null | grep -oE '[0-9]+$' | tail -1)
    pins0=$(grep -ohE 'ANT-0001\] Found [0-9]+' "$pre"/*.log 2>/dev/null | grep -oE '[0-9]+$' | tail -1)
    nets=$(grep -ohE 'ANT-0002\] Found [0-9]+' "$post"/*.log 2>/dev/null | grep -oE '[0-9]+$' | tail -1)
    pins=$(grep -ohE 'ANT-0001\] Found [0-9]+' "$post"/*.log 2>/dev/null | grep -oE '[0-9]+$' | tail -1)
    diodes=$(grep -ohE 'Inserted [0-9]+ diodes' "$run"/40-openroad-repairantennas/1-diodeinsertion/*.log 2>/dev/null \
             | grep -oE '[0-9]+' | awk '{s+=$1} END{print s+0}')
    area=$(grep -ohE '"design__instance__area": *[0-9.]+' "$run"/*/or_metrics_out.json 2>/dev/null \
           | grep -oE '[0-9.]+$' | tail -1)
    printf '%s,%s,%s,%s,%s,%s,%s,%s\n' \
           "$tag" "$label" "${nets0:-NA}" "${pins0:-NA}" \
           "${nets:-NA}" "${pins:-NA}" "${diodes:-0}" "${area:-NA}" >> "$OUT"
    printf '  %-8s %-24s truoc: %5s net /%5s pin   sau: %5s net /%5s pin   diode=%-5s area=%s\n' \
           "$tag" "$label" "${nets0:-NA}" "${pins0:-NA}" "${nets:-NA}" "${pins:-NA}" \
           "${diodes:-0}" "${area:-NA}"
}

case "${1:-}" in
phase1)
    echo "tag,setting,nets_before,pins_before,nets_after,pins_after,diodes,area_um2" > "$OUT"
    echo "=== Phase 1: dem vi pham, dung o RepairAntennas ==="
    points | while IFS='|' read -r tag label args; do
        # shellcheck disable=SC2086
        bash "$HERE/run_pd.sh" "$DES" "$tag" --to OpenROAD.RepairAntennas $args > /dev/null 2>&1
        measure "$tag" "$label"
    done
    echo ""
    echo "ket qua trong $OUT"
    ;;
phase2)
    shift
    [ $# -gt 0 ] || { echo "phase2 can it nhat mot tag" >&2; exit 2; }
    for tag in "$@"; do
        label=$(points | grep "^$tag|" | cut -d'|' -f2)
        args=$(points | grep "^$tag|" | cut -d'|' -f3)
        echo "=== Phase 2: full flow cho $tag ($label) ==="
        # shellcheck disable=SC2086
        bash "$HERE/run_pd.sh" "$DES" "${tag}_full" $args 2>&1 | tail -6
    done
    ;;
*)
    echo "usage: antenna_sweep.sh phase1 | phase2 <tag>..." >&2
    exit 2
    ;;
esac
