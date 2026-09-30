# FLOW_JOURNAL Incident 93: can the resizer repair hold AFTER detailed routing, on EXTRACTED parasitics?
# x_E1's routed database (read only), RCX SPEFs of the same run: nom RC into the tt corner, MAX RC into the
# ff and ss corners (= max_ff for hold, max_ss for setup). No views are written.
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
source $::env(SCRIPTS_DIR)/openroad/common/resizer.tcl
load_rsz_corners
read_current_odb
set_propagated_clock [all_clocks]
set X /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/x_E1/25-openroad-rcx
read_spef -corner nom_tt_025C_1v80 $X/nom/soc_asic_top.nom.spef
read_spef -corner nom_ff_n40C_1v95 $X/max/soc_asic_top.max.spef
read_spef -corner nom_ss_100C_1v60 $X/max/soc_asic_top.max.spef
puts "HOLDECO before:"
report_worst_slack -min -digits 4
report_worst_slack -max -digits 4
puts "HOLDECO repair_timing -hold"
if {[catch {repair_timing -hold -hold_margin 0.05 -verbose -max_buffer_percent 5} err]} { puts "HOLDECO repair_timing error: $err" }
puts "HOLDECO after:"
report_worst_slack -min -digits 4
report_worst_slack -max -digits 4
