# Activity-based power of one signed-off run (FLOW_JOURNAL Incident 69).
#
# Loads the design exactly as OpenLane's STAPostPNR did for one corner: the
# step's own environment file, then io.tcl's read_timing_info / read_spefs,
# with the libraries and SPEF that the step's sta.log says it read (the
# wrapper sta_power.sh passes those in). Without PW_SAIF this is the
# vectorless report and must reproduce the step's power.rpt; with PW_SAIF the
# switching activity of every annotated net comes from gate-level simulation.
#
#   env: _TCL_ENV_IN  _env_*.tcl of the corner directory of STAPostPNR (io.tcl
#                     sources it, as in the flow); SCRIPTS_DIR
#        _CURRENT_CORNER_NAME _CURRENT_CORNER_LIBS _CURRENT_CORNER_NETLISTS
#        _CURRENT_SPEF_BY_CORNER   (set by sta_power.sh)
#        PW_SAIF (optional), PW_SCOPE (default tb_gls_soc/dut)
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl

set_cmd_units -time ns -capacitance pF -current mA -voltage V -resistance kOhm -distance um
set sta_report_default_digits 6

read_timing_info
read_spefs

if { [info exists ::env(PW_SAIF)] && $::env(PW_SAIF) ne "" } {
    set scope tb_gls_soc/dut
    if { [info exists ::env(PW_SCOPE)] } { set scope $::env(PW_SCOPE) }
    puts "PW_INFO reading activity from $::env(PW_SAIF) scope $scope"
    read_saif -scope $scope $::env(PW_SAIF)
    if { [llength [info commands report_activity_annotation]] } {
        report_activity_annotation
    }
} else {
    puts "PW_INFO vectorless (no SAIF)"
}
report_power

# Where every driver pin's activity came from. OpenSTA 2.6 only propagates
# activity from its BFS roots; a feedback loop that no root reaches keeps
# "unknown" (zero) activity even where the SAIF annotates it (measured on a
# small netlist, FLOW_JOURNAL Incident 69). A power number is only as good as
# the share of driver pins whose origin is the SAIF itself.
set tally [dict create]
set n 0
set unk {}
foreach pin [get_pins -hierarchical *] {
    if { [get_property $pin direction] ne "output" } { continue }
    set origin [lindex [get_property $pin activity] 2]
    dict incr tally $origin
    incr n
    if { $origin eq "unknown" } {
        lappend unk "[get_full_name $pin] [get_property [get_cells -of_objects $pin] ref_name]"
    }
}
# The unknown pins are listed so their share can be estimated from the SAIF
# (asic/gls/unknown_power.py), not silently counted as zero.
if { [info exists ::env(PW_UNKNOWN_OUT)] } {
    set fh [open $::env(PW_UNKNOWN_OUT) w]
    foreach line $unk { puts $fh $line }
    close $fh
}
foreach origin [lsort [dict keys $tally]] {
    puts [format "PW_ORIGIN %-12s %8d  %6.2f %%" $origin [dict get $tally $origin] \
        [expr {100.0 * [dict get $tally $origin] / $n}]]
}
puts "PW_ORIGIN total_output_pins $n"
