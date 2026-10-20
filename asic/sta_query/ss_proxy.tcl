# 2026-10-15 ss study: early ss estimate of a run after P2 (before detailed routing), so a PD knob can be judged on
# ss in ~1 h instead of a full flow. Loads the post-GRT database with tt / ss / ff corners (RSZ_CORNER_0..2, set
# by ss_proxy.sh), estimates parasitics (SQ_EST = placement | grt) with the per-layer RC of LAYERS_RC applied
# everywhere (ss_proxy.sh sets LAYERS_RC_SCOPE all: the calibrated k = 2 values, close to RCX), and prints the
# setup WNS / TNS per corner plus the worst endpoints at ss. Read only: nothing is written back.
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
source $::env(SCRIPTS_DIR)/openroad/common/resizer.tcl
load_rsz_corners
read_current_odb
set_propagated_clock [all_clocks]
source $::env(SCRIPTS_DIR)/openroad/common/set_rc.tcl
if { $::env(SQ_EST) eq "grt" } {
    source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl
    estimate_parasitics -global_routing
} else {
    estimate_parasitics -placement
}
foreach corner [sta::corners] {
    set n [$corner name]
    puts [format "SS_PROXY %s setup_ws %.3f setup_tns %.1f hold_ws %.3f" $n \
        [worst_slack -corner $n -max] [total_negative_slack -corner $n -max] [worst_slack -corner $n -min]]
}
foreach n {nom_ss_100C_1v60 nom_tt_025C_1v80} {
    puts "SS_PROXY_PATHS $n"
    report_checks -path_delay max -corner $n -group_count 12 -endpoint_count 1 -format end -digits 3
}
# Optional (SQ_FULLPATH_OUT = file): the worst nom_ss paths in full (cells, slews, delays), one per endpoint.
if { [info exists ::env(SQ_FULLPATH_OUT)] } {
    set n [expr {[info exists ::env(SQ_FULLPATH_COUNT)] ? $::env(SQ_FULLPATH_COUNT) : 50}]
    report_checks -path_delay max -corner nom_ss_100C_1v60 -group_count $n -endpoint_count 1 -format full \
        -fields {fanout cap slew} -digits 3 > $::env(SQ_FULLPATH_OUT)
    puts "SS_PROXY full paths written: $::env(SQ_FULLPATH_OUT)"
}
# Optional (SQ_ENDGROUPS_OUT = TSV path): every violating nom_ss setup endpoint with the RTL name of the capturing
# register, the format of q_endgroups.tcl, for endpoint_groups_compare.py.
if { [info exists ::env(SQ_ENDGROUPS_OUT)] } {
    set f [open $::env(SQ_ENDGROUPS_OUT) w]
    puts $f "endpoint\tqnet\tslack\tstartpoint\tstartnet"
    foreach pe [find_timing_paths -path_delay max -corner nom_ss_100C_1v60 -group_count 20000 -endpoint_count 1 -slack_max 0.0] {
        set pin [get_property $pe endpoint]
        set q ""
        if {![catch {set inst [get_cells -of_objects $pin]}]} {
            foreach qp {Q Q_N} {
                set p [get_pins -quiet "[get_full_name $inst]/$qp"]
                if {[llength $p]} {
                    set n [get_nets -quiet -of_objects $p]
                    if {[llength $n]} { set q [get_full_name $n]; break }
                }
            }
        }
        set spin [get_property $pe startpoint]
        set sn ""
        catch { set sn [get_full_name [get_nets -of_objects $spin]] }
        puts $f "[get_full_name $pin]\t$q\t[get_property $pe slack]\t[get_full_name $spin]\t$sn"
    }
    close $f
    puts "SS_PROXY endgroups written: $::env(SQ_ENDGROUPS_OUT)"
}
puts "SS_PROXY done"
