#!/usr/bin/env bash
# FLOW_JOURNAL Incident 93 (Task A): EDA-lever experiments E1, E2 after the stock-EQY run, one at a time,
# each from final3_A's post-GPL state (same placement as final3). Cooperative stop: touch asic/.abort_x_exps
A=/mnt/e/Projects/RISCV-research/asic
until grep -q "end final3_eqy" $A/x_exps.log 2>/dev/null; do [ -e $A/.abort_x_exps ] && exit 0; sleep 60; done
for e in E1 E2; do
  [ -e $A/.abort_x_exps ] && exit 0
  bash $A/run_x_exps2.sh x_$e config_$e.json final3_A/30-openroad-stamidpnr/state_out.json OpenROAD.RepairDesignPostGPL
done
