# FLOW_JOURNAL Incident 91: RC correlation of the post-GRT estimate (estimate_parasitics -global_routing,
# what steps 40/44 use) vs RCX, same nets as rc_corr.tcl. Reads final_A step 44 (read only).
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
source $::env(SCRIPTS_DIR)/openroad/common/set_rc.tcl
catch { puts "RC_CORR wire_signal R/C: [rsz::wire_signal_resistance [sta::cmd_corner]] [rsz::wire_signal_capacitance [sta::cmd_corner]]" }
foreach layer [$::tech getLayers] {
    if { [$layer getRoutingLevel] >= 1 } {
        puts "RC_CORR layer [$layer getName] lef_R [$layer getResistance] lef_C [$layer getCapacitance] edgeC [$layer getEdgeCapacitance] width [$layer getWidth]"
    }
}
source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl
estimate_parasitics -global_routing
set d $::env(STEP_DIR)
set fh [open $d/nets.txt r]; set nets [split [string trim [read $fh]] "\n"]; close $fh
file delete -force $d/est_grt_k2.txt $d/spef_grt_k2.txt
foreach nm $nets { catch { report_net -digits 6 $nm >> $d/est_grt_k2.txt } }
read_spef $::env(RC_SPEF)
foreach nm $nets { catch { report_net -digits 6 $nm >> $d/spef_grt_k2.txt } }
puts "RC_CORR_GRT done: [llength $nets] nets"
