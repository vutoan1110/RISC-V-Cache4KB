#!/usr/bin/env bash
# FLOW_JOURNAL Incident 95: E16 = E15 (density 55) + E14 hold margins + E13 CTS clustering, from r14_A's
# pre-GPL state. Random crashes after the ECO step are resumed with retry. Stop: touch asic/.abort_x_exps
A=/mnt/e/Projects/RISCV-research/asic
bash $A/run_x_exps2.sh r14_E16 config_R14_E16.json r14_A/22-odb-addroutingobstructions/state_out.json OpenROAD.GlobalPlacementSkipIO
R=$A/soc_dm_4kb/runs/r14_E16
if ! ls $R | grep -q stapostpnr && [ -f "$(ls -d $R/*-openroad-postrouteholdeco 2>/dev/null | tail -1)/state_out.json" ]; then
    bash $A/run_resume_retry.sh r14_E16 config_R14_E16.json Odb.RemoveRoutingObstructions OpenROAD.STAPostPNR
fi
