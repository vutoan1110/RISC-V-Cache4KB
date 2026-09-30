# Hold-slack distribution seen by OpenROAD.ResizerTimingPostCTS, before it repairs anything.
# Loads the step's input exactly as rsz_timing_postcts.tcl does (resizer corners, propagated clocks,
# set_rc, placement parasitics), then bins the worst-corner hold slack of every timing endpoint:
# register data pins and macro input pins. A hold margin M makes the resizer buffer every endpoint
# with slack < M, so the cumulative counts predict the hold-buffer load of a smaller margin.
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
source $::env(SCRIPTS_DIR)/openroad/common/resizer.tcl

load_rsz_corners
read_current_odb
set_propagated_clock [all_clocks]
set_dont_touch_objects
source $::env(SCRIPTS_DIR)/openroad/common/set_rc.tcl
estimate_parasitics -placement

set pins [all_registers -data_pins]
set npins [llength $pins]
foreach inst [get_cells -filter "is_macro == 1"] {
    foreach p [get_pins -of_objects $inst -filter "direction == input"] {
        if { [get_property $p is_clock] } { continue }
        lappend pins $p
    }
}
puts "HH endpoints: [llength $pins] (register data pins $npins)"

set edges {-0.05 0 0.01 0.02 0.03 0.04 0.05 0.075 0.1 0.15 0.2}
foreach e $edges { set below($e) 0 }
set unconstrained 0
set worst 1e9
foreach p $pins {
    set s [get_property $p slack_min]
    if { $s == "INF" || $s == "" || $s > 1e20 } { incr unconstrained; continue }
    if { $s < $worst } { set worst $s }
    foreach e $edges {
        if { $s < $e } { incr below($e) }
    }
}
puts "HH worst hold slack (all resizer corners): $worst ns; unconstrained endpoints: $unconstrained"
foreach e $edges {
    puts [format "HH slack < %6.3f ns : %6d endpoints" $e $below($e)]
}
