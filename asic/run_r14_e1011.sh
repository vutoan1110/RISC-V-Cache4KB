#!/usr/bin/env bash
# FLOW_JOURNAL Incident 94: R14 PD knob experiments E10 and E11 from r14_A's post-GPL state, E11 started 30 min after E10 so
# their detailed-routing and ECO steps do not overlap. Random crashes after the ECO step are resumed with retry.
# Cooperative stop: touch asic/.abort_x_exps
A=/mnt/e/Projects/RISCV-research/asic
one () {
    bash $A/run_x_exps2.sh $1 $2 r14_A/30-openroad-stamidpnr/state_out.json OpenROAD.RepairDesignPostGPL
    R=$A/soc_dm_4kb/runs/$1
    if ! ls $R | grep -q stapostpnr && [ -f "$(ls -d $R/*-openroad-postrouteholdeco 2>/dev/null | tail -1)/state_out.json" ]; then
        bash $A/run_resume_retry.sh $1 $2 Odb.RemoveRoutingObstructions OpenROAD.STAPostPNR
    fi
}
one r14_E10 config_R14_E10.json &
sleep 1800
one r14_E11 config_R14_E11.json &
wait
