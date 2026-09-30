#!/usr/bin/env bash
# Sweep Yosys/ABC area knobs against the same RTL and report the cell count.
#
# Background: renaming one port moved the cell count by 2,728 (2.8 %) with no
# logic change, because Yosys names cells after their driving signals and that
# order feeds ABC's technology mapping. The question here is whether a deeper
# area script collapses that heuristic spread -- and, separately, whether any of
# these settings simply gives a smaller design than either naming produced.
#
# Each point runs only as far as tech mapping, which is where the instance count
# is decided.
#
#   bash synth_strategy_probe.sh [DESIGN_DIR]
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
DES=${1:-soc_dm_control}
OUT=$HERE/../results/synth_strategy_probe.csv

echo "tag,setting,cells,area_um2" > "$OUT"

run_point() {
    local tag=$1; shift
    local label=$1; shift
    bash "$HERE/run_pd.sh" "$DES" "$tag" --to Yosys.Synthesis "$@" > /dev/null 2>&1
    local rpt="$HERE/$DES/runs/$tag/06-yosys-synthesis/reports/stat.rpt"
    local cells area
    cells=$(grep -m1 'Number of cells:' "$rpt" 2>/dev/null | awk '{print $NF}')
    area=$(grep -m1 'Chip area for module' "$rpt" 2>/dev/null | sed "s/.*: //")
    printf '%s,%s,%s,%s\n' "$tag" "$label" "${cells:-FAIL}" "${area:-FAIL}" >> "$OUT"
    printf '  %-22s %-34s cells=%-8s area=%s\n' "$tag" "$label" "${cells:-FAIL}" "${area:-FAIL}"
}

echo "=== area-strategy sweep on $DES ==="
run_point strat_area1 "SYNTH_STRATEGY=AREA 1"  -c "SYNTH_STRATEGY=AREA 1"
run_point strat_area2 "SYNTH_STRATEGY=AREA 2"  -c "SYNTH_STRATEGY=AREA 2"
run_point strat_area3 "SYNTH_STRATEGY=AREA 3"  -c "SYNTH_STRATEGY=AREA 3"
run_point strat_mfs3  "AREA 0 + ABC_USE_MFS3"  -c "SYNTH_ABC_USE_MFS3=true"
run_point strat_nf    "AREA 0 + ABC_AREA_USE_NF" -c "SYNTH_ABC_AREA_USE_NF=true"

echo ""
echo "results in $OUT"
