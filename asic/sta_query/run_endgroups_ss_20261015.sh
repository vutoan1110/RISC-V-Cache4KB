#!/usr/bin/env bash
# 2026-10-15 ss study (owner: sign-off not accepted, ss far worse than R14). Every violating max_ss setup endpoint
# of the R14 layouts and of the 6c4ccffd layouts, with the RTL name of the capturing register (q_endgroups.tcl), so
# the ss loss can be located per register group (endpoint_groups_compare.py). Read only: writes under
# results/ss_study_20261015/. Two queries at a time (each loads the netlist + max SPEF, ~3-4 GB).
set -u
A=/mnt/e/Projects/RISCV-research/asic
O=/mnt/e/Projects/RISCV-research/results/ss_study_20261015
mkdir -p $O
one () {   # <label> <STAPostPNR step dir relative to asic/>
    mkdir -p $O/$1
    SQ_OUT=$O/$1 bash $A/sta_query/sta_query.sh $A/$2 max_ss_100C_1v60 $A/sta_query/q_endgroups.tcl > $O/$1/q_endgroups_max_ss.log 2>&1
    echo "$(date -u +%FT%TZ) $1 exit $? $(tail -1 $O/$1/q_endgroups_max_ss.log)"
}
one dm_r14F_A soc_dm_4kb/runs/r14F_A/58-openroad-stapostpnr &
one dm_6c4c_rsztf_tdp_r2 soc_dm_4kb/runs/dm_grid3665x2900_rtl6c4c_rsztf_tdp_r2/58-openroad-stapostpnr &
wait
one sa2_r14_ecomaxmin_r1 soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1/59-openroad-stapostpnr &
one sa2_6c4c_eco2_r2 soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_eco2_rtl6c4c_r2/58-openroad-stapostpnr &
wait
echo "$(date -u +%FT%TZ) endgroups done"
