# 2026-10-20 DM_VC4 congestion study: where does global routing overflow before FastRoute's "Extra Run for hard
# benchmark" (GRT-0103, iteration 20 with total overflow > 200) re-routes with long detours? Loads a step's output
# database (placement after that step), re-runs global routing with the run's own layer settings but only
# SQ_GRT_ITERS congestion iterations (default 15, so the hard-benchmark run never starts) and writes the remaining
# overflow as a congestion report (SQ_CONG_OUT). Read only: nothing is written back to the run.
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
source $::env(SCRIPTS_DIR)/openroad/common/set_routing_layers.tcl
source $::env(SCRIPTS_DIR)/openroad/common/set_layer_adjustments.tcl
set_macro_extension $::env(GRT_MACRO_EXTENSION)
if { [info exists ::env(GRT_ROUTING_ALPHA)] } { set_routing_alpha $::env(GRT_ROUTING_ALPHA) }
set iters [expr {[info exists ::env(SQ_GRT_ITERS)] ? $::env(SQ_GRT_ITERS) : 15}]
global_route -congestion_iterations $iters -verbose -allow_congestion \
    -congestion_report_file $::env(SQ_CONG_OUT)
puts "GRT_HOTSPOT done iterations $iters report $::env(SQ_CONG_OUT)"
