#!/usr/bin/env bash
# FLOW_JOURNAL Incident 91: run X2 after X1 has finished (sequential PD explorations).
# Cooperative stop: touch asic/.abort_x_exps
A=/mnt/e/Projects/RISCV-research/asic
until grep -q "end x1_nohd" $A/x_exps.log 2>/dev/null; do
  [ -e $A/.abort_x_exps ] && exit 0
  sleep 30
done
bash $A/run_x_exps.sh x2_rc2 config_X2.json 26-odb-applydeftemplate/state_out.json OpenROAD.GlobalPlacement
