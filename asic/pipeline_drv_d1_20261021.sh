#!/usr/bin/env bash
# 2026-10-21 DRV-fix screen D1 (owner: fix every violation the sign-off STA still reports, improve ss where possible).
# Waits for the SA2 acceptance pipeline to end (one heavy phase at a time), branches the accepted DM run after detailed
# routing (step 46) and runs the post-route ECO with repair_design on the extracted parasitics
# (POST_ROUTE_ECO_REPAIR_DESIGN) followed by the sign-off part and the final gate (run_gated_resume.sh ... hold).
set -u
A=/mnt/e/Projects/RISCV-research/asic
cd $A
SRC=dm_grid3665x2900_rtl6c4c_rsztf_tdp_rszctsall_noor34_rcrep_r1
NEW=dm_grid3665x2900_rtl6c4c_rsztf_tdp_rszctsall_noor34_rcrep_drveco_scr_r1
CFG=config_R14_FINAL_rtl6c4c_rsztf_tdp_rszctsall_noor34_rcrep_drveco.json
while pgrep -f pipeline_sa2_acc_20261020.sh > /dev/null; do sleep 60; done
echo "$(date -Is) NOTE pipeline_drv_d1_20261021: branching $SRC after step 46 into $NEW" >> gated_pd.log
bash branch_run.sh soc_dm_4kb $SRC $NEW 46 || { echo "$(date -Is) STOP $NEW: branch failed" >> gated_pd.log; exit 1; }
bash run_gated_resume.sh soc_dm_4kb $NEW $CFG "DRV screen D1: post-route repair_design on extracted parasitics, branch of the accepted DM run after detailed routing" hold
echo "$(date -Is) NOTE pipeline_drv_d1_20261021 done" >> gated_pd.log
