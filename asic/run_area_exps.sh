#!/usr/bin/env bash
# FLOW_JOURNAL Incident 95: area-recovery experiments, queued behind r14_E12 / r14_E13 so that no more than two
# PD runs overlap.
#   r14_E14  hold margins 0.03 / 0.03, RCX hold ECO 0.02   from r14_E10's post-CTS state   after r14_E12 ends
#   r14_E15  PL_TARGET_DENSITY_PCT 55                     from r14_A's pre-GPL state      after r14_E13 ends
#   f3_H1    final3 + hold margins 0.02 + RCX hold ECO    from final3_A's post-CTS state  after r14_E14 ends
# Random crashes after the ECO step are resumed with retry (run_resume_retry.sh).
# Cooperative stop: touch asic/.abort_x_exps
A=/mnt/e/Projects/RISCV-research/asic
RUNS=$A/soc_dm_4kb/runs
done_run () {   # finished: STAPostPNR wrote its state, or no process of the tag has existed for 3 minutes
    local t=$1 idle=0
    while true; do
        [ -e $A/.abort_x_exps ] && return 1
        ls $RUNS/$t/*-openroad-stapostpnr/state_out.json > /dev/null 2>&1 && return 0
        if pgrep -f "[ /]$t( |$)" > /dev/null; then idle=0; else idle=$((idle + 1)); fi
        [ $idle -ge 3 ] && return 0
        sleep 60
    done
}
one () {   # <tag> <config> <state under runs/> <from step>
    bash $A/run_x_exps2.sh $1 $2 $3 $4
    R=$RUNS/$1
    if ! ls $R | grep -q stapostpnr && [ -f "$(ls -d $R/*-openroad-postrouteholdeco 2>/dev/null | tail -1)/state_out.json" ]; then
        bash $A/run_resume_retry.sh $1 $2 Odb.RemoveRoutingObstructions OpenROAD.STAPostPNR
    fi
}
(
    done_run r14_E12 || exit 0
    one r14_E14 config_R14_E14.json r14_E10/06-openroad-stamidpnr-1/state_out.json OpenROAD.ResizerTimingPostCTS
    done_run r14_E14 || exit 0
    one f3_H1 config_F3_H1.json final3_A/35-openroad-stamidpnr-1/state_out.json OpenROAD.ResizerTimingPostCTS
) &
(
    done_run r14_E13 || exit 0
    one r14_E15 config_R14_E15.json r14_A/22-odb-addroutingobstructions/state_out.json OpenROAD.GlobalPlacementSkipIO
) &
wait
