#!/usr/bin/env bash
# FLOW_JOURNAL Incident 95/96: r14F_A and r14F_B were killed on 2026-09-30 ~23:38 when the Claude Code session
# that had launched them ended (their wsl.exe clients were terminated and WSL shut its VM down; neither run
# had an error). Resume each from the step it was in -- r14F_A from Magic.StreamOut (STAPostPNR complete),
# r14F_B from OpenROAD.DetailedRouting -- through run_resume_retry.sh, which retries only this host's
# random-fault signature. The "end" lines go to r14_final_pd.log, which run_dse_pd.sh and the watcher read.
# Cooperative stop: touch asic/.abort_x_exps (run_resume_retry.sh checks it before every try).
set -u
A=/mnt/e/Projects/RISCV-research/asic
LOG=$A/r14_final_pd.log
cd $A
res () {   # <tag> <from step>
    echo "$(date -Is) resume $1 --from $2 (killed with the launching session 2026-09-30 23:38)" >> $LOG
    bash $A/run_resume_retry.sh "$1" config_R14_FINAL.json "$2"
    echo "$(date -Is) end $1 rc=$? last step $(ls $A/soc_dm_4kb/runs/$1 | grep -E '^[0-9]+-' | tail -1)" >> $LOG
}
res r14F_A Magic.StreamOut &
sleep 30
res r14F_B OpenROAD.DetailedRouting &
wait
