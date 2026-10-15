#!/usr/bin/env bash
# 2026-10-14 (owner: "cac ban PD loi thoi xoa di, rac may"). For every failed / stopped / screening PD directory below:
# keep its text evidence (state_out.json metrics, logs, reports, configs; no ODB / DEF / GDS / MAG / SPEF / netlists)
# as results/pd_run_archive/20261014/<design>__<dir>.tar.gz, check the archive lists, then delete the directory.
# Kept on purpose: signed runs (r14F_A/B, final3_A/B, ecomaxmin_r1/_r2), running runs (dm_grid3665x2900_rtl6c4c_r1,
# sa2_..._cts25_r5 until it ends), synthesis-only evidence runs (*synth*), eco2pass_check_20261013 (E0 evidence), the DM
# corridor references dmuA / dmuB (not failed; owner decides). Branch runs copy their steps (branch_run.sh: cp -a), so
# deleting a source run (rsztf_r1/_r2) does not touch the signed ecomaxmin runs.
#   bash scripts/maintenance/archive_and_delete_failed_pd_20261014.sh            (Git Bash, repo root)
set -u
R=$(cd "$(dirname "$0")/../.." && pwd)
OUT=$R/results/pd_run_archive/20261014
mkdir -p "$OUT"
LIST="
soc_dm_4kb/runs/dm_grid3665x2900_r3
soc_dm_4kb/runs/dm_grid3665x2900_r4
soc_dm_4kb/runs/final_B
soc_sa2_4kb/runs/sa2_corr3400x3250_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1
soc_sa2_4kb/runs/sa2_corr3400x3250_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r2
soc_sa2_4kb/runs/sa2_corr3400x3325_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1
soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25_r1
soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25_r2
soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25_r3
soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_cts25_r4
soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_grtskew_scr_r1
soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1
soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r2
soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_r1
soc_sa2_4kb/runs/sa2uB
soc_sa2_4kb/diag_cts25_r3_antcheck_20261014
soc_sa2_4kb/diag_cts25_step41_20261013
soc_vc4_4kb/runs/vc4_corr3400x3400_f220_capm20_antoff_rsztf_nogrtt_clkm3_pad1_grtit150_grtscr_r1
soc_vc4_4kb/runs/vc4_corr3400x3400_f220_capm20_antoff_rsztf_nogrtt_clkm3_pad1_r1
soc_vc4_4kb/runs/vc4_corr3400x3400_f220_capm20_antoff_rsztf_nogrtt_clkm4_pad1_grtscr_r1
soc_vc4_4kb/runs/vc4_corr3400x3400_f220_capm20_antoff_rsztf_nogrtt_clkm4_pad1_grtscr_r1_sta
soc_vc4_4kb/runs/vc4_corr3500x3400_f220_capm20_antoff_rsztf_nogrtt_clkm3_pad1_grtskew_scr_r1
soc_vc4_4kb/runs/vc4_corr3500x3400_f220_capm20_antoff_rsztf_nogrtt_clkm3_pad1_r1
soc_vc4_4kb/runs/vc4_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd_r1
soc_vc4_4kb/runs/vc4_corr3600x3400_f220_capm20_antoff_nogrtt_r1
soc_vc4_4kb/runs/vc4_corr3600x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong_mwl500_r1
soc_vc4_4kb/runs/vc4_corr3600x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong_r1
soc_vc4_4kb/runs/vc4_corr3600x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong_r2
soc_vc4_4kb/runs/vc4_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_antcong_r1
soc_vc4_4kb/runs/vc4_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_initialgrtskew_r1
soc_vc4_4kb/runs/vc4_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_r1
soc_vc4_4kb/runs/vc4_corr3600x3400_f220_capm20_r1
soc_vc4_4kb/runs/vc4_corr3600x3400_f220_grtskew_scr_r1
soc_vc4_4kb/runs/vc4_corr3600x3400_f220_r1
soc_vc4_4kb/runs/vc4_corr3800x3400_f220_capm20_pad1_antgrt10_nogrtt_nogrtd_antcong_r1
soc_vc4_4kb/runs/vc4_corr3800x3400_f220_grtskew_scr_r1
soc_vc4_4kb/runs/vc4_corr3800x3400_f220_r1
soc_vc4_4kb/screen_ant_postdrt_v2_20261014
soc_vc4_4kb/screen_antgrt10_20261014
soc_vc4_4kb/screen_antgrt20_20261014
soc_vc4_4kb/screen_antgrt30_20261014
soc_vc4_4kb/screen_drt_replay_v2_20261014
"
[ $# -gt 0 ] && LIST="$*"   # explicit directories (relative to asic/), e.g. the owner-approved dmuA / dmuB on 2026-10-15
ok=0; fail=0
for rel in $LIST; do
    d=$R/asic/$rel
    [ -d "$d" ] || { echo "SKIP (not found) $rel"; continue; }
    name=$(echo "$rel" | sed 's#/runs/#__#; s#/#__#g')
    arc=$OUT/$name.tar.gz
    ( cd "$(dirname "$d")" && find "$(basename "$d")" -type f \( -name '*.json' -o -name '*.log' -o -name '*.rpt' \
        -o -name '*.txt' -o -name '*.csv' -o -name '*.tcl' -o -name 'COMMANDS' -o -name '*.drc' -o -name '*.md' \
        -o -name '*.out' -o -name '*.tsv' \) -size -200M ! -path '*/tmp/*' -print0 \
      | tar --null -czf "$arc" -T - ) 2>/dev/null
    n=$(tar -tzf "$arc" 2>/dev/null | wc -l)
    if [ "$n" -gt 0 ]; then
        rm -rf "$d" && { echo "DELETED $rel (archive $n files, $(du -h "$arc" | cut -f1))"; ok=$((ok+1)); } || { echo "DELETE FAILED $rel"; fail=$((fail+1)); }
    else
        echo "ARCHIVE EMPTY, NOT DELETED $rel"; fail=$((fail+1))
    fi
done
echo "done: deleted $ok, failed $fail"
