#!/usr/bin/env bash
# FLOW_JOURNAL Incident 93: wait for x_E5's detailed routing, then run the tail of the flow from that state
# with config_E5b (post-route repair_design OFF), tag x_E5b; random crashes retried by run_resume_retry.sh.
# Cooperative stop: touch asic/.abort_x_exps
A=/mnt/e/Projects/RISCV-research/asic
S=$A/soc_dm_4kb/runs/x_E5/16-openroad-detailedrouting/state_out.json
until [ -f $S ]; do [ -e $A/.abort_x_exps ] && exit 0; [ -s $A/soc_dm_4kb/runs/x_E5/error.log ] && exit 1; sleep 60; done
bash $A/run_x_exps2.sh x_E5b config_E5b.json x_E5/16-openroad-detailedrouting/state_out.json OpenROAD.PostRouteHoldECO
R=$A/soc_dm_4kb/runs/x_E5b
if ! ls $R | grep -q stapostpnr; then
    if ls $R | grep -q postrouteholdeco && [ -f "$(ls -d $R/*-openroad-postrouteholdeco | tail -1)/state_out.json" ]; then
        bash $A/run_resume_retry.sh x_E5b config_E5b.json Odb.RemoveRoutingObstructions OpenROAD.STAPostPNR
    else
        bash $A/run_resume_retry.sh x_E5b config_E5b.json OpenROAD.PostRouteHoldECO OpenROAD.STAPostPNR
    fi
fi
