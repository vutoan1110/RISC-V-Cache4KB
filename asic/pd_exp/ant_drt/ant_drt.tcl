# FLOW_JOURNAL Incident 91 (exploration, final_A untouched): post-detailed-route antenna repair,
# the step OpenLane 2.3.10 lacks (ORFS does it): check -> repair_antennas on the detailed routes ->
# incremental detailed_route -> check again.  Reads final_A step 46's ODB, writes only here.
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
set_thread_count 1
puts "ANT_EXP: check before repair"
check_antennas -report_file $::env(STEP_DIR)/ant_before.rpt
set diode_split [split $::env(DIODE_CELL) "/"]
puts "ANT_EXP: repair_antennas on detailed routes"
set t0 [clock seconds]
set rc [repair_antennas "[lindex $diode_split 0]" -iterations 1 -ratio_margin 10]
puts "ANT_EXP: repair_antennas returned '$rc' after [expr [clock seconds]-$t0] s"
check_placement -verbose
set_thread_count $::env(DRT_THREADS)
set t0 [clock seconds]
detailed_route -bottom_routing_layer $::env(RT_MIN_LAYER) -top_routing_layer $::env(RT_MAX_LAYER) \
    -output_drc $::env(STEP_DIR)/soc_asic_top.drc -droute_end_iter $::env(DRT_OPT_ITERS) -or_seed 42 -verbose 1
puts "ANT_EXP: detailed_route (post-repair) took [expr [clock seconds]-$t0] s"
set_thread_count 1
puts "ANT_EXP: check after repair + reroute"
check_antennas -report_file $::env(STEP_DIR)/ant_after.rpt
write_views
