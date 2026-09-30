# FLOW_JOURNAL Incident 91: RC correlation of the resizer's parasitic estimate vs RCX (final_A, read only).
# For every 40th signal net: wire capacitance from (a) estimate_parasitics -placement with the flow's
# set_rc.tcl, (b) the signed-off RCX SPEF (nom corner). Output est.txt / spef.txt (report_net), compared by rc_corr.py.
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
source $::env(SCRIPTS_DIR)/openroad/common/set_rc.tcl
estimate_parasitics -placement
set nets {}
set i 0
foreach n [get_nets *] {
    incr i
    if {$i % 40 != 0} { continue }
    set nm [get_full_name $n]
    if {[string match "clknet*" $nm] || $nm eq "clk" || [string first "\[" $nm] >= 0} { continue }
    lappend nets $nm
}
set d $::env(STEP_DIR)
file delete -force $d/est.txt $d/spef.txt
foreach nm $nets { report_net -digits 6 $nm >> $d/est.txt }
read_spef $::env(RC_SPEF)
foreach nm $nets { report_net -digits 6 $nm >> $d/spef.txt }
puts "RC_CORR done: [llength $nets] nets"
