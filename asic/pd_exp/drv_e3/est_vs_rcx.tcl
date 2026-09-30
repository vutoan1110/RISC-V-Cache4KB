# FLOW_JOURNAL Incident 93: post-GRT estimated capacitance (calibrated LAYERS_RC, GRT parasitics) of sampled
# signoff max-cap violators, at the state RepairDesignPostGRT left (x_E3 step 11), vs their signoff RCX value.
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
set ::LAYERS_RC_HERE 1
source $::env(SCRIPTS_DIR)/openroad/common/set_rc.tcl
source $::env(SCRIPTS_DIR)/openroad/common/set_routing_layers.tcl
source $::env(SCRIPTS_DIR)/openroad/common/set_layer_adjustments.tcl
set_macro_extension $::env(GRT_MACRO_EXTENSION)
set_routing_alpha 0
global_route -congestion_iterations $::env(GRT_OVERFLOW_ITERS) -critical_nets_percentage 0
estimate_parasitics -global_routing
set f [open $::env(STEP_DIR)/cap_sample.txt r]
set o [open $::env(STEP_DIR)/est_vs_rcx.tsv w]
puts $o "pin\tnet\tsignoff_cap\test_cap\tfanout_now"
foreach line [split [read $f] "\n"] {
    if {$line eq ""} continue
    lassign $line pin net rcx
    set n [get_nets -quiet $net]
    if {[llength $n] == 0} { puts $o "$pin\t$net\t$rcx\tMISSING\t"; continue }
    set c [sta::format_capacitance [$n capacitance [sta::cmd_corner] max] 5]
    set fo [llength [get_pins -of_objects $n -filter "direction == input"]]
    puts $o "$pin\t$net\t$rcx\t$c\t$fo"
}
close $o
puts "EST done"
