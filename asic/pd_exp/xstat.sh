#!/usr/bin/env bash
# FLOW_JOURNAL Incident 91: status of an exploration run (current step, resizer iterations, openroad alive)
R=/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/${1:-x1_nohd}
date -Is
tail -2 /mnt/e/Projects/RISCV-research/asic/x_exps.log
S=$(ls -1d $R/[0-9]*/ 2>/dev/null | tail -1); echo "last step: $S"
L=$(ls -t $S/*.log 2>/dev/null | head -1); [ -n "$L" ] && { ls -la $L; grep -a -E '^ *([0-9]+|final) \|' $L | tail -2; grep -a -E 'RSZ-00(94|62|46)|post-DRT antenna|ANT-000|DRT-0199' $L | tail -4; }
echo "openroad procs: $(pgrep -c openroad)"; free -g | sed -n 2p
[ -s $R/error.log ] && head -c 400 $R/error.log
