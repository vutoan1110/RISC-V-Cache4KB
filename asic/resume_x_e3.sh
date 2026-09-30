#!/usr/bin/env bash
# FLOW_JOURNAL Incident 93: x_E3 died with SIGSEGV in Odb.ReportDisconnectedPins (odbpy, the known random crash
# of this host); resume the same tag from that step to STAPostPNR.
A=/mnt/e/Projects/RISCV-research/asic
echo "$(date -Is) start x_E3 resume (from Odb.ReportDisconnectedPins, SIGSEGV retry)" >> $A/x_exps.log
cd $A && RESUME=1 CONFIG=config_E3.json bash run_pd_mk.sh soc_dm_4kb x_E3 --from Odb.ReportDisconnectedPins --to OpenROAD.STAPostPNR > x_E3_resume.log 2>&1
echo "$(date -Is) end x_E3 resume rc=$?" >> $A/x_exps.log
