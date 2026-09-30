#!/bin/bash
# Evidence archive for the superseded PD runs of the experimental phase (cleanup approved by the user on
# 2026-09-30). Copies the small evidence files of each run into results/pd_run_archive/<run>/ and writes a
# manifest; it deletes nothing. The run numbers are already in asic/FLOW_JOURNAL.md (Incident 93: x_E*,
# r13a_A; Incident 94: r14_E7..E11).
set -u
R=/e/Projects/RISCV-research
RUNS=$R/asic/soc_dm_4kb/runs
A=$R/results/pd_run_archive
M=$A/ARCHIVE_2026-09-30.tsv
LIST="x_E1 x_E1H x_E2 x_E3 x_E3R x_E3R2 x_E4_A x_E5 x_E5b x_E6 r13a_A r14_E7 r14_E8 r14_E9 r14_E11"
mkdir -p "$A"
printf 'run\tbytes\tfiles\tarchived\n' > "$M"
for r in $LIST; do
    d=$RUNS/$r
    [ -d "$d" ] || { echo "skip $r (absent)"; continue; }
    o=$A/$r; mkdir -p "$o"
    for f in resolved.json flow.log error.log warning.log; do
        [ -f "$d/$f" ] && cp "$d/$f" "$o/"
    done
    [ -f "$d/final/metrics.json" ] && cp "$d/final/metrics.json" "$o/"
    [ -f "$d/final/metrics.csv" ] && cp "$d/final/metrics.csv" "$o/"
    for s in "$d"/*-openroad-stapostpnr; do
        [ -d "$s" ] || continue
        [ -f "$s/summary.rpt" ] && cp "$s/summary.rpt" "$o/$(basename "$s")_summary.rpt"
        [ -f "$s/state_out.json" ] && cp "$s/state_out.json" "$o/$(basename "$s")_state_out.json"
    done
    b=$(du -sb "$d" | cut -f1); n=$(find "$d" -type f | wc -l)
    printf '%s\t%s\t%s\t%s\n' "$r" "$b" "$n" "$(ls "$o" | tr '\n' ' ')" >> "$M"
    echo "archived $r ($((b / 1000000)) MB, $n files)"
done
du -sh "$A"
