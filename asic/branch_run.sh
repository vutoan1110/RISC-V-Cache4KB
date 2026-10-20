#!/usr/bin/env bash
# Start a new run from the finished steps of an existing run, for a knob that only acts after those steps (for example
# a post-GRT repair margin screened on a run whose P1 already passed). The source run is only read.
#   bash branch_run.sh <design dir> <source tag> <new tag> <last step number to copy>
# Copies the step directories 1 .. N of runs/<source tag> to runs/<new tag> (timestamps kept), rewrites the run path in
# the copied state files, and makes step N's state_out.json the newest one: OpenLane resumes from the newest
# state_out.json of a run directory (Flow.start). Continue with RESUME=1 run_pd_mk.sh ... --from <step N+1>, or with
# run_gated_resume.sh <design dir> <new tag> <config> <reason> p2 when N is the OpenROAD.GlobalRouting step.
# A BRANCHED_FROM file in the new run records the source.
set -eu
A=$(cd "$(dirname "$0")" && pwd)
des=$1; src=$2; new=$3; last=$4
S=$A/$des/runs/$src
D=$A/$des/runs/$new
[ -d "$S" ] || { echo "no source run $S"; exit 2; }
[ -e "$D" ] && { echo "run $D exists already"; exit 2; }
steps=$(ls "$S" | grep -E '^[0-9]+-' | awk -F- -v n="$last" '$1 + 0 <= n + 0' | sort -n)
lastdir=$(echo "$steps" | awk -F- -v n="$last" '$1 + 0 == n + 0')
[ -n "$lastdir" ] && [ -f "$S/$lastdir/state_out.json" ] || { echo "step $last of $src has no state_out.json"; exit 2; }
mkdir -p "$D"
for s in $steps; do cp -a "$S/$s" "$D/"; done
# state files name the source run by absolute path (/mnt/e/... in WSL); rewrite every json that mentions it
grep -rlF --include='*.json' "/runs/$src/" "$D" | while read -r f; do
    sed -i "s#/runs/$src/#/runs/$new/#g" "$f"
done
sleep 1
touch "$D/$lastdir/state_out.json"
left=$(grep -rlF --include='*.json' "/runs/$src/" "$D" | wc -l)
{
    echo "branched from runs/$src after step $lastdir on $(date -Is)"
    echo "steps copied: $(echo $steps | wc -w); state files still naming the source: $left"
} > "$D/BRANCHED_FROM"
cat "$D/BRANCHED_FROM"
