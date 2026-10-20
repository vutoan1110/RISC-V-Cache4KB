# DRV of a signed layout against the Liberty (PDK) limits alone, next to the SDC design limits of the flow.
# The flow's SDC sets one design-wide max transition / capacitance / fanout (MAX_TRANSITION_CONSTRAINT 0.75 ns,
# MAX_CAPACITANCE_CONSTRAINT 0.2 pF, MAX_FANOUT_CONSTRAINT 8 or 16) on top of the per-pin limits of the cell and
# macro Liberty files. This script reports both views for one corner of the final netlist with its RCX SPEF:
#   1. the sign-off view: the step's SDC as written (the flow's STA reports the same counts);
#   2. the PDK view: the SDC's design-wide limits are lifted (set to very large values), so only the Liberty
#      max_transition / max_capacitance attributes of each pin remain; fanout has no Liberty limit.
# Environment (drv_liberty_limits.sh): SQ_NETLIST, SQ_SPEF, SQ_SDC, SQ_LIBS (space separated), SQ_OUT, SQ_CORNER,
# MAX_FANOUT_CONSTRAINT / MAX_TRANSITION_CONSTRAINT / MAX_CAPACITANCE_CONSTRAINT as in the run.
foreach lib $::env(SQ_LIBS) { read_liberty $lib }
read_verilog $::env(SQ_NETLIST)
link_design soc_asic_top
read_spef $::env(SQ_SPEF)
read_sdc $::env(SQ_SDC)
set_propagated_clock [all_clocks]
set out $::env(SQ_OUT)
report_check_types -max_slew -max_capacitance -max_fanout -violators > $out.sdc.rpt
puts "DRV $::env(SQ_CORNER) sdc: slew [sta::max_slew_violation_count] cap [sta::max_capacitance_violation_count] fanout [sta::max_fanout_violation_count]"
set_max_transition 1000 [current_design]
set_max_capacitance 1000 [current_design]
set_max_fanout 100000 [current_design]
report_check_types -max_slew -max_capacitance -violators > $out.lib.rpt
puts "DRV $::env(SQ_CORNER) liberty: slew [sta::max_slew_violation_count] cap [sta::max_capacitance_violation_count]"
exit
