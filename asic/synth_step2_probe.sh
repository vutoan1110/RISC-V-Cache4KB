#!/usr/bin/env bash
# Three remaining mitigations, all with the linted port name kept.
#
#   1. deferred_flatten, branch_en -- a retry. The first attempt crashed inside
#      Yosys after ABC re-integration, but it had already logged that opt_merge
#      removed 21,502 cells, the same figure the branch run produced, which is
#      the first setting where the two namings agree at that pass.
#   2. the duplicate expression -- datapath.v computes
#      valid_e && (instr_e[6:0] == 7'b1100011) twice, once as is_branch_e and
#      once inline at the branch instance. opt_merge is the sensitive pass, so
#      removing a real duplicate is worth measuring on its own merits.
#   3. (* keep *) on the branch enable, as specified in step 2 of the directive.
#
#   bash synth_step2_probe.sh <set_branch_port.py> <set_branch_keep.py> <dedup.py>
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$HERE/..
DES=soc_dm_control
FLIP=$1; KEEP=$2; DEDUP=$3
OUT=$ROOT/results/synth_step2_probe.csv

echo "variant,cells,area_um2,merge_removed" > "$OUT"

measure() {
    local tag=$1 label=$2
    local dir="$HERE/$DES/runs/$tag/06-yosys-synthesis"
    local cells area merged
    cells=$(grep -m1 'Number of cells:' "$dir/reports/stat.rpt" 2>/dev/null | awk '{print $NF}')
    area=$(grep -m1 'Chip area for module' "$dir/reports/stat.rpt" 2>/dev/null | sed 's/.*: //')
    merged=$(grep -oE 'Removed a total of [0-9]+ cells' "$dir/yosys-synthesis.log" 2>/dev/null \
             | awk '{s+=$5} END{print s+0}')
    printf '%s,%s,%s,%s\n' "$label" "${cells:-FAIL}" "${area:-FAIL}" "${merged:-0}" >> "$OUT"
    printf '  %-26s cells=%-8s area=%-16s opt_merge_removed=%s\n' \
           "$label" "${cells:-FAIL}" "${area:-FAIL}" "${merged:-0}"
}

cd "$ROOT" && python3 "$FLIP" branch_en > /dev/null

echo "=== 1. deferred_flatten, branch_en (retry after a native crash) ==="
bash "$HERE/run_pd.sh" "$DES" hier_def_en2 --to Yosys.Synthesis \
     -c "SYNTH_HIERARCHY_MODE=deferred_flatten" > /dev/null 2>&1
measure hier_def_en2 "deferred_flatten"

echo "=== 2. duplicate expression removed ==="
(cd "$ROOT" && python3 "$DEDUP" on > /dev/null)
bash "$HERE/run_pd.sh" "$DES" dedup_en --to Yosys.Synthesis > /dev/null 2>&1
measure dedup_en "dedup .branch_en(is_branch_e)"
(cd "$ROOT" && python3 "$DEDUP" off > /dev/null)

echo "=== 3. (* keep *) on the branch enable ==="
(cd "$ROOT" && python3 "$KEEP" on > /dev/null)
bash "$HERE/run_pd.sh" "$DES" keep_en --to Yosys.Synthesis > /dev/null 2>&1
measure keep_en "(* keep *) branch_en"
(cd "$ROOT" && python3 "$KEEP" off > /dev/null)

echo ""
echo "results in $OUT"
