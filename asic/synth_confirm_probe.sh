#!/usr/bin/env bash
# Confirm that the step-2 fixes are robust rather than lucky.
#
# Both (* keep *) on the branch enable and removing the duplicate expression
# brought the cell count back to ~99.1k under the linted name branch_en. That is
# the target, but landing on it once is exactly the evidence that misled this
# investigation the first time. The question now is whether each fix gives the
# same answer under BOTH namings -- if it does, the result no longer depends on
# an identifier and the noise really is gone.
#
# Also tries the two together, since they act on the same net by different means.
#
#   bash synth_confirm_probe.sh <set_branch_port.py> <set_branch_keep.py> <set_branch_dedup.py>
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$HERE/..
DES=soc_dm_control
FLIP=$1; KEEP=$2; DEDUP=$3
OUT=$ROOT/results/synth_confirm_probe.csv

echo "variant,port_name,cells,area_um2,merge_removed" > "$OUT"

measure() {
    local tag=$1 label=$2 name=$3
    local dir="$HERE/$DES/runs/$tag/06-yosys-synthesis"
    local cells area merged
    cells=$(grep -m1 'Number of cells:' "$dir/reports/stat.rpt" 2>/dev/null | awk '{print $NF}')
    area=$(grep -m1 'Chip area for module' "$dir/reports/stat.rpt" 2>/dev/null | sed 's/.*: //')
    merged=$(grep -oE 'Removed a total of [0-9]+ cells' "$dir/yosys-synthesis.log" 2>/dev/null \
             | awk '{s+=$5} END{print s+0}')
    printf '%s,%s,%s,%s,%s\n' "$label" "$name" "${cells:-FAIL}" "${area:-FAIL}" "${merged:-0}" >> "$OUT"
    printf '  %-22s %-10s cells=%-8s area=%-16s opt_merge_removed=%s\n' \
           "$label" "$name" "${cells:-FAIL}" "${area:-FAIL}" "${merged:-0}"
}

echo "=== (* keep *) under the original name ==="
(cd "$ROOT" && python3 "$FLIP" branch > /dev/null; python3 "$KEEP" on > /dev/null) || exit 1
bash "$HERE/run_pd.sh" "$DES" keep_br --to Yosys.Synthesis > /dev/null 2>&1
measure keep_br "(* keep *)" branch
(cd "$ROOT" && python3 "$KEEP" off > /dev/null)

echo "=== dedup under the original name ==="
(cd "$ROOT" && python3 "$DEDUP" on > /dev/null)
bash "$HERE/run_pd.sh" "$DES" dedup_br --to Yosys.Synthesis > /dev/null 2>&1
measure dedup_br "dedup" branch
(cd "$ROOT" && python3 "$DEDUP" off > /dev/null)

echo "=== both together, linted name ==="
(cd "$ROOT" && python3 "$FLIP" branch_en > /dev/null; python3 "$DEDUP" on > /dev/null; python3 "$KEEP" on > /dev/null)
bash "$HERE/run_pd.sh" "$DES" both_en --to Yosys.Synthesis > /dev/null 2>&1
measure both_en "dedup + keep" branch_en
(cd "$ROOT" && python3 "$KEEP" off > /dev/null; python3 "$DEDUP" off > /dev/null)

# Always leave the tree clean and on the linted name.
(cd "$ROOT" && python3 "$FLIP" branch_en)

echo ""
echo "results in $OUT"
