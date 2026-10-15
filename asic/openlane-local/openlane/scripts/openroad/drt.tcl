# Copyright 2020-2022 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb

set_thread_count $::env(DRT_THREADS)

set min_layer $::env(RT_MIN_LAYER)
if { [info exists ::env(DRT_MIN_LAYER)] } {
    set min_layer $::env(DRT_MIN_LAYER)
}

set max_layer $::env(RT_MAX_LAYER)
if { [info exists ::env(DRT_MAX_LAYER)] } {
    set max_layer $::env(DRT_MAX_LAYER)
}

# Local addition (2026-10-07, off unless DRT_DRC_REPORT_ITER_STEP > 0): DRC report every N iterations, also in the
# antenna-repair calls (2026-10-08).
set drt_extra {}
if { [info exists ::env(DRT_DRC_REPORT_ITER_STEP)] && $::env(DRT_DRC_REPORT_ITER_STEP) > 0 } {
    lappend drt_extra -drc_report_iter_step $::env(DRT_DRC_REPORT_ITER_STEP)
}
# Every detailed_route call writes <design>.drc-<iteration>.rpt; move them to drc_iter_<call> after each call so the
# antenna-repair calls below do not overwrite the reports of the main route.
proc keep_iter_reports {call} {
    set files [glob -nocomplain -directory $::env(STEP_DIR) "$::env(DESIGN_NAME).drc-*.rpt"]
    if { [llength $files] > 0 } {
        set d [file join $::env(STEP_DIR) drc_iter_$call]
        file mkdir $d
        foreach f $files { file rename -force $f [file join $d [file tail $f]] }
    }
}

detailed_route\
    -bottom_routing_layer $min_layer\
    -top_routing_layer $max_layer\
    -output_drc $::env(STEP_DIR)/$::env(DESIGN_NAME).drc\
    -droute_end_iter $::env(DRT_OPT_ITERS)\
    -or_seed 42\
    -verbose 1\
    {*}$drt_extra
keep_iter_reports main

# Local addition (2026-10-13, off unless DRT_SAVE_MAIN_ROUTE): keep the database of the main detailed route before the
# antenna repair below, so a failure in that repair does not lose a long main route.
if { [info exists ::env(DRT_SAVE_MAIN_ROUTE)] && $::env(DRT_SAVE_MAIN_ROUTE) } {
    write_db $::env(STEP_DIR)/main_route.odb
    puts "\[INFO\] main detailed route saved to $::env(STEP_DIR)/main_route.odb"
}

# FLOW_JOURNAL Incident 91 (local addition, off unless DRT_ANTENNA_REPAIR_ITERS > 0): post-detailed-
# route antenna repair as in ORFS. repair_antennas checks the DETAILED routes and inserts diodes at
# the violating gates (placed legally), then detailed_route reroutes incrementally. The antenna code
# is pinned to one thread (see antenna_repair.tcl for the segfaults this avoids).
if { [info exists ::env(DRT_ANTENNA_REPAIR_ITERS)] && $::env(DRT_ANTENNA_REPAIR_ITERS) > 0 } {
    set diode_split [split $::env(DIODE_CELL) "/"]
    for {set i 1} {$i <= $::env(DRT_ANTENNA_REPAIR_ITERS)} {incr i} {
        set_thread_count 1
        set nv [check_antennas]
        puts "\[INFO\] post-DRT antenna round $i: check_antennas returned '$nv'"
        if { [string is integer -strict $nv] && $nv == 0 } { break }
        # Local addition (2026-10-13, off unless DRT_ANTENNA_REPAIR_ALLOW_CONGESTION): repair_antennas re-routes the
        # diode connections with the incremental global router, whose GlobalRouter::updateDirtyRoutes raises GRT-0232
        # on any remaining 2D overflow unless congestion is allowed; the incremental detailed_route below must then
        # resolve the overflow (its DRC result is still checked by the sign-off gate).
        if { [info exists ::env(DRT_ANTENNA_REPAIR_ALLOW_CONGESTION)] && $::env(DRT_ANTENNA_REPAIR_ALLOW_CONGESTION) } {
            grt::set_allow_congestion 1
            puts "\[INFO\] post-DRT antenna round $i: global-route overflow allowed in the diode re-route"
        }
        repair_antennas "[lindex $diode_split 0]" -iterations 1 -ratio_margin $::env(DRT_ANTENNA_REPAIR_MARGIN)
        check_placement -verbose
        set_thread_count $::env(DRT_THREADS)
        detailed_route\
            -bottom_routing_layer $min_layer\
            -top_routing_layer $max_layer\
            -output_drc $::env(STEP_DIR)/$::env(DESIGN_NAME).drc\
            -droute_end_iter $::env(DRT_OPT_ITERS)\
            -or_seed 42\
            -verbose 1\
            {*}$drt_extra
        keep_iter_reports ant$i
    }
    set_thread_count 1
    set nv [check_antennas]
    puts "\[INFO\] post-DRT antenna repair done: check_antennas returned '$nv'"
    set_thread_count $::env(DRT_THREADS)
}

write_views