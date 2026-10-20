# FLOW_JOURNAL Incident 93: standalone test of the post-route hold ECO on x_E1's routed database.
# `global_route -start_incremental` in a fresh process segfaults in GlobalRouter::addDirtyNet (the router
# has no nets loaded). ECO_MODE picks how the new nets get routing guides:
#   full_grt : run a complete global_route first, then the incremental bracket around the repair
#   no_grt   : no global routing at all; detailed_route has to cope with the new, guide-less nets
# Writes only into this directory.
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
source $::env(SCRIPTS_DIR)/openroad/common/resizer.tcl
set mode $::env(ECO_MODE)
puts "ECO2 mode $mode"

load_rsz_corners
read_current_odb
set_propagated_clock [all_clocks]
set_dont_touch_objects
foreach corner [sta::corners] {
    read_spef -corner [$corner name] $::env(_ECO_SPEF)
}
puts "ECO2 before"
report_worst_slack -min -digits 4
report_worst_slack -max -digits 4

source $::env(SCRIPTS_DIR)/openroad/common/set_routing_layers.tcl
source $::env(SCRIPTS_DIR)/openroad/common/set_layer_adjustments.tcl
set_macro_extension $::env(GRT_MACRO_EXTENSION)
if { $mode == "full_grt" } {
    set_routing_alpha 0
    global_route -congestion_iterations $::env(GRT_OVERFLOW_ITERS) -verbose -critical_nets_percentage 0
    global_route -start_incremental
}

# Detailed placement on an already placed design resets every cell to its row's orientation, undoing
# optimize_mirroring (the standalone test: legalized HPWL +2 %, about 50,000 routed cells flipped). So
# every cell that existed before the repair is held FIRM while the new buffers are legalised.
foreach inst [$::block getInsts] {
    set eco_old([$inst getName]) 1
}
repair_timing -hold -verbose -hold_margin 0.05 -max_buffer_percent 5
puts "ECO2 after repair"
report_worst_slack -min -digits 4
report_worst_slack -max -digits 4

set eco_locked {}
set eco_new 0
foreach inst [$::block getInsts] {
    if { [info exists eco_old([$inst getName])] } {
        if { [$inst getPlacementStatus] == "PLACED" } {
            $inst setPlacementStatus FIRM
            lappend eco_locked $inst
        }
    } else {
        incr eco_new
    }
}
puts "\[INFO\] post-route ECO: legalising $eco_new new cells, [llength $eco_locked] cells held FIRM"
source $::env(SCRIPTS_DIR)/openroad/common/dpl_cell_pad.tcl
detailed_placement -max_displacement [subst { $::env(PL_MAX_DISPLACEMENT_X) $::env(PL_MAX_DISPLACEMENT_Y) }]
foreach inst $eco_locked {
    $inst setPlacementStatus PLACED
}
check_placement -verbose
unset_dont_touch_objects
if { $mode == "full_grt" } {
    global_route -end_incremental
}

set_thread_count $::env(DRT_THREADS)
detailed_route\
    -bottom_routing_layer $::env(RT_MIN_LAYER)\
    -top_routing_layer $::env(RT_MAX_LAYER)\
    -output_drc $::env(STEP_DIR)/eco2_$mode.drc\
    -droute_end_iter $::env(DRT_OPT_ITERS)\
    -or_seed 42\
    -verbose 1
set_thread_count 1
puts "ECO2 antennas: [check_antennas]"
write_db $::env(STEP_DIR)/eco2_$mode.odb
puts "ECO2 done"
