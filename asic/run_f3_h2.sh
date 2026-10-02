#!/usr/bin/env bash
# FLOW_JOURNAL Incident 95: F3_H2 = final3 + density 55 + hold margins 0.03/0.02 + CTS clustering 8, from
# final3_A's pre-GPL state. Random crashes after the ECO step are resumed with retry. Stop: touch asic/.abort_x_exps
A=/mnt/e/Projects/RISCV-research/asic
bash $A/run_x_exps2.sh f3_H2 config_F3_H2.json final3_A/22-odb-addroutingobstructions/state_out.json OpenROAD.GlobalPlacementSkipIO
R=$A/soc_dm_4kb/runs/f3_H2
if ! ls $R | grep -q stapostpnr && [ -f "$(ls -d $R/*-openroad-postrouteholdeco 2>/dev/null | tail -1)/state_out.json" ]; then
    bash $A/run_resume_retry.sh f3_H2 config_F3_H2.json Odb.RemoveRoutingObstructions OpenROAD.STAPostPNR
fi
