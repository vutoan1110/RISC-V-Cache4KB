#!/usr/bin/env bash
# FLOW_JOURNAL Incident 93: x_E6 (config_E6) from final3_A's post-GPL state to STAPostPNR; random crashes after
# the ECO step are resumed with run_resume_retry.sh. Cooperative stop: touch asic/.abort_x_exps
A=/mnt/e/Projects/RISCV-research/asic
bash $A/run_x_exps2.sh x_E6 config_E6.json final3_A/30-openroad-stamidpnr/state_out.json OpenROAD.RepairDesignPostGPL
R=$A/soc_dm_4kb/runs/x_E6
if ! ls $R | grep -q stapostpnr; then
    if [ -f "$(ls -d $R/*-openroad-postrouteholdeco 2>/dev/null | tail -1)/state_out.json" ]; then
        bash $A/run_resume_retry.sh x_E6 config_E6.json Odb.RemoveRoutingObstructions OpenROAD.STAPostPNR
    else
        echo "$(date -Is) x_E6: stopped before the ECO step completed; not resumed automatically" >> $A/x_exps.log
    fi
fi
