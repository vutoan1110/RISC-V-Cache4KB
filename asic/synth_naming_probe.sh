#!/usr/bin/env bash
# Does an area strategy actually remove the naming sensitivity, or only move it?
#
# Renaming one port moved the cell count by 2,728 under AREA 0 with no logic
# change. AREA 1 and AREA 2 did not bring the count back down, but that is the
# wrong question on its own: what matters for reproducibility is whether a given
# strategy gives the SAME answer under both names. This runs each strategy twice,
# once per name, and prints the gap.
#
# A strategy whose gap collapses has defeated the noise even if its absolute
# count is higher, because the result no longer depends on an identifier.
#
#   bash synth_naming_probe.sh
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$HERE/..
DES=soc_dm_control
FLIP=$1                       # path to set_branch_port.py
OUT=$ROOT/results/synth_naming_probe.csv

echo "strategy,port_name,cells,area_um2" > "$OUT"

point() {
    local tag=$1 label=$2 name=$3; shift 3
    (cd "$ROOT" && python3 "$FLIP" "$name" > /dev/null) || return 1
    bash "$HERE/run_pd.sh" "$DES" "$tag" --to Yosys.Synthesis "$@" > /dev/null 2>&1
    local rpt="$HERE/$DES/runs/$tag/06-yosys-synthesis/reports/stat.rpt"
    local cells area
    cells=$(grep -m1 'Number of cells:' "$rpt" 2>/dev/null | awk '{print $NF}')
    area=$(grep -m1 'Chip area for module' "$rpt" 2>/dev/null | sed 's/.*: //')
    printf '%s,%s,%s,%s\n' "$label" "$name" "${cells:-FAIL}" "${area:-FAIL}" >> "$OUT"
    printf '  %-12s %-10s cells=%-8s area=%s\n' "$label" "$name" "${cells:-FAIL}" "${area:-FAIL}"
}

echo "=== finishing step 1: the &nf area mapper ==="
point nf_en "AREA0+nf" branch_en -c "SYNTH_ABC_AREA_USE_NF=true"

echo "=== paired naming test ==="
point a2_en   "AREA 2" branch_en -c "SYNTH_STRATEGY=AREA 2"
point a2_br   "AREA 2" branch    -c "SYNTH_STRATEGY=AREA 2"
point a1_en   "AREA 1" branch_en -c "SYNTH_STRATEGY=AREA 1"
point a1_br   "AREA 1" branch    -c "SYNTH_STRATEGY=AREA 1"

# Always leave the tree on the linted name.
(cd "$ROOT" && python3 "$FLIP" branch_en)

echo ""
echo "results in $OUT"
