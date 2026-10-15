# Cleanup proposal: approval required, no deletion performed

The handover size file is an inventory containing protected runs as well as possible candidates. The list below separates them. Sizes are the original inventory MB, not a freshly measured or guaranteed reclaimed amount. Synthesis evidence and VC4 controls needed by T5 are deferred.

Text evidence archives include resolved config, merged metrics, step list, flow/step logs, warning/error logs and timing reports; copied files are hash-checked. No source is removed. A deletion would require explicit approval and a separate log entry for each removed run.

| inventory path under asic/ | MB | decision | reason | archive |
|---|---:|---|---|---|
| soc_sa2_4kb/runs/sa2_corr3400x3100_f220_capm20_fo16_pad1_tdp_clkm3_r1 | 9157 | PROPOSE_ONLY | failed or superseded run; explicit owner approval still required | EVIDENCE_ARCHIVED_NO_DELETION |
| soc_sa2_4kb/runs/sa2_corr3400x3100_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1 | 3634 | PROPOSE_ONLY | failed or superseded run; explicit owner approval still required | EVIDENCE_ARCHIVED_NO_DELETION |
| soc_sa2_4kb/runs/sa2_corr3400x3100_f220_capm20_fo16_pad1_tdp_clkm3_seco_r1 | 7176 | PROPOSE_ONLY | failed or superseded run; explicit owner approval still required | EVIDENCE_ARCHIVED_NO_DELETION |
| soc_sa2_4kb/runs/sa2_corr3400x3100_f220_capm20_fo16_pad1_tdp_clkm3_secott_r1 | 3810 | PROPOSE_ONLY | failed or superseded run; explicit owner approval still required | EVIDENCE_ARCHIVED_NO_DELETION |
| soc_sa2_4kb/runs/sa2_corr3400x3100_f220_capm20_fo16_r1 | 3645 | PROPOSE_ONLY | failed or superseded run; explicit owner approval still required | EVIDENCE_ARCHIVED_NO_DELETION |
| soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1 | 7938 | KEEP | locked/sign-off/source run or reported corridor control | not archived for deletion |
| soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomin_r1 | 12207 | PROPOSE_ONLY | failed or superseded run; explicit owner approval still required | EVIDENCE_ARCHIVED_NO_DELETION |
| soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1 | 12227 | KEEP | locked/sign-off/source run or reported corridor control | not archived for deletion |
| soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r2 | 33 | KEEP | locked/sign-off/source run or reported corridor control | not archived for deletion |
| soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_r1 | 3742 | PROPOSE_ONLY | failed or superseded run; explicit owner approval still required | EVIDENCE_ARCHIVED_NO_DELETION |
| soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_r1 | 2621 | DEFER | required archive evidence incomplete; not eligible for deletion approval | MISSING_RESOLVED_CONFIG_NOT_ELIGIBLE |
| soc_sa2_4kb/runs/sa2_synth2 | 191 | DEFER | synthesis provenance; do not delete before the relevant proof inputs are reviewed | not archived for deletion |
| soc_sa2_4kb/runs/sa2_synth_rfbhtm9k_r1 | 191 | DEFER | synthesis provenance; do not delete before the relevant proof inputs are reviewed | not archived for deletion |
| soc_sa2_4kb/runs/sa2uA | 3798 | PROPOSE_ONLY | failed or superseded run; explicit owner approval still required | EVIDENCE_ARCHIVED_NO_DELETION |
| soc_sa2_4kb/runs/sa2uB | 3835 | KEEP | reported 54-iteration routing trajectory and sign-off baseline | not archived for deletion |
| soc_vc4_4kb/runs/vc4_corr3400x3400_f220_capm20_antm10_r1 | 3937 | PROPOSE_ONLY | failed or superseded run; explicit owner approval still required | EVIDENCE_ARCHIVED_NO_DELETION |
| soc_vc4_4kb/runs/vc4_corr3400x3400_f220_capm20_antoff_r1 | 3673 | PROPOSE_ONLY | failed or superseded run; explicit owner approval still required | EVIDENCE_ARCHIVED_NO_DELETION |
| soc_vc4_4kb/runs/vc4_corr3400x3400_f220_capm20_antoff_rsztf_nogrtt_clkm3_pad1_r1 | 1432 | PROPOSE_ONLY | failed or superseded run; explicit owner approval still required | EVIDENCE_ARCHIVED_NO_DELETION |
| soc_vc4_4kb/runs/vc4_corr3400x3400_f220_capm20_antoff_rsztf_nogrtt_clkm3_r1 | 3401 | PROPOSE_ONLY | failed or superseded run; explicit owner approval still required | EVIDENCE_ARCHIVED_NO_DELETION |
| soc_vc4_4kb/runs/vc4_corr3400x3400_f220_capm20_antoff_rsztf_nogrtt_r1 | 3396 | PROPOSE_ONLY | failed or superseded run; explicit owner approval still required | EVIDENCE_ARCHIVED_NO_DELETION |
| soc_vc4_4kb/runs/vc4_corr3400x3400_f220_capm20_antoff_rsztf_r1 | 3694 | PROPOSE_ONLY | failed or superseded run; explicit owner approval still required | EVIDENCE_ARCHIVED_NO_DELETION |
| soc_vc4_4kb/runs/vc4_corr3400x3400_f220_capm20_fo16_r1 | 3001 | PROPOSE_ONLY | failed or superseded run; explicit owner approval still required | EVIDENCE_ARCHIVED_NO_DELETION |
| soc_vc4_4kb/runs/vc4_corr3400x3400_f220_capm20_r1 | 3942 | PROPOSE_ONLY | failed or superseded run; explicit owner approval still required | EVIDENCE_ARCHIVED_NO_DELETION |
| soc_vc4_4kb/runs/vc4_corr3600x3400_f220_capm20_r1 | 2711 | DEFER | required archive evidence incomplete; not eligible for deletion approval | MISSING_RESOLVED_CONFIG_NOT_ELIGIBLE |
| soc_vc4_4kb/runs/vc4_corr3600x3400_f220_r1 | 3700 | DEFER | old VC4 die/clock-routing control still needed until T5 | not archived for deletion |
| soc_vc4_4kb/runs/vc4_corr3800x3400_f220_r1 | 3789 | DEFER | old VC4 die/clock-routing control still needed until T5 | not archived for deletion |
| soc_vc4_4kb/runs/vc4_synth2 | 200 | DEFER | synthesis provenance; do not delete before the relevant proof inputs are reviewed | not archived for deletion |
| soc_vc4_4kb/runs/vc4_synth_rfbhtm9k_r1 | 200 | DEFER | synthesis provenance; do not delete before the relevant proof inputs are reviewed | not archived for deletion |
| soc_vc4_4kb/runs/vc4uA | 3389 | PROPOSE_ONLY | failed or superseded run; explicit owner approval still required | EVIDENCE_ARCHIVED_NO_DELETION |
| soc_vc4_4kb/runs/vc4uB | 3409 | PROPOSE_ONLY | failed or superseded run; explicit owner approval still required | EVIDENCE_ARCHIVED_NO_DELETION |
| soc_dm_4kb/runs/dm_synth_r16_r1 | 153 | DEFER | synthesis provenance; do not delete before the relevant proof inputs are reviewed | not archived for deletion |
| soc_dm_4kb/runs/dm_synth_rfbht_r1 | 153 | DEFER | synthesis provenance; do not delete before the relevant proof inputs are reviewed | not archived for deletion |
| soc_dm_4kb/runs/dmuA | 10749 | KEEP | locked/sign-off/source run or reported corridor control | not archived for deletion |
| soc_dm_4kb/runs/dmuB | 12232 | KEEP | locked/sign-off/source run or reported corridor control | not archived for deletion |
| soc_dm_4kb/runs/final3_A | 7150 | KEEP | locked/sign-off/source run or reported corridor control | not archived for deletion |
| soc_dm_4kb/runs/final3_B | 7150 | KEEP | locked/sign-off/source run or reported corridor control | not archived for deletion |
| soc_dm_4kb/runs/final_B | 9414 | PROPOSE_ONLY | failed or superseded run; explicit owner approval still required | EVIDENCE_ARCHIVED_NO_DELETION |
| soc_dm_4kb/runs/r14F_A | 10804 | KEEP | locked/sign-off/source run or reported corridor control | not archived for deletion |
| soc_dm_4kb/runs/r14F_B | 10803 | KEEP | locked/sign-off/source run or reported corridor control | not archived for deletion |
| soc_dm_4kb/runs/r14sat_synth | 153 | DEFER | synthesis provenance; do not delete before the relevant proof inputs are reviewed | not archived for deletion |
