#!/usr/bin/env bash
# Does keeping the hierarchy remove the naming sensitivity?
#
# The divergence was traced to opt_merge, not ABC: the same logic under two port
# names removed 18,832 and 15,901 identical cells there, and that difference of
# 2,931 carried straight into the mapped netlist. opt_merge walks the cells of a
# module in an order that follows their names, and merging one pair can expose
# another, so a single sweep over a very large module reaches a different fixed
# point depending on the order it started in.
#
# The design is flattened before that pass, so opt_merge sweeps one module of
# ~138,000 cells. With deferred_flatten it runs per module instead, on scopes
# small enough to be swept thoroughly, which should shrink the dependence on
# names. That is a configuration change, not a patched tool.
#
#   bash synth_hierarchy_probe.sh <path/to/set_branch_port.py>
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$HERE/..
DES=soc_dm_control
FLIP=$1
OUT=$ROOT/results/synth_hierarchy_probe.csv

echo "setting,port_name,cells,area_um2,merge_removed" > "$OUT"

point() {
    local tag=$1 label=$2 name=$3; shift 3
    (cd "$ROOT" && python3 "$FLIP" "$name" > /dev/null) || return 1
    bash "$HERE/run_pd.sh" "$DES" "$tag" --to Yosys.Synthesis "$@" > /dev/null 2>&1
    local dir="$HERE/$DES/runs/$tag/06-yosys-synthesis"
    local cells area merged
    cells=$(grep -m1 'Number of cells:' "$dir/reports/stat.rpt" 2>/dev/null | awk '{print $NF}')
    area=$(grep -m1 'Chip area for module' "$dir/reports/stat.rpt" 2>/dev/null | sed 's/.*: //')
    # Total cells removed by every opt_merge in the run: the quantity that
    # actually differs between the two namings.
    merged=$(grep -oE 'Removed a total of [0-9]+ cells' "$dir/yosys-synthesis.log" 2>/dev/null \
             | awk '{s+=$5} END{print s+0}')
    printf '%s,%s,%s,%s,%s\n' "$label" "$name" "${cells:-FAIL}" "${area:-FAIL}" "${merged:-0}" >> "$OUT"
    printf '  %-18s %-10s cells=%-8s area=%-16s opt_merge_removed=%s\n' \
           "$label" "$name" "${cells:-FAIL}" "${area:-FAIL}" "${merged:-0}"
}

echo "=== hierarchy mode, paired on both names ==="
point hier_def_en "deferred_flatten" branch_en -c "SYNTH_HIERARCHY_MODE=deferred_flatten"
point hier_def_br "deferred_flatten" branch    -c "SYNTH_HIERARCHY_MODE=deferred_flatten"

echo "=== resource sharing off, paired ==="
point share_off_en "SHARE_RESOURCES=0" branch_en -c "SYNTH_SHARE_RESOURCES=false"
point share_off_br "SHARE_RESOURCES=0" branch    -c "SYNTH_SHARE_RESOURCES=false"

# Always leave the tree on the linted name.
(cd "$ROOT" && python3 "$FLIP" branch_en)

echo ""
echo "results in $OUT"
