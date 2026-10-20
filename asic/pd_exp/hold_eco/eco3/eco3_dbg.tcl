# FLOW_JOURNAL Incident 93 (local addition, off unless RUN_POST_ROUTE_HOLD_ECO): hold repair after
# detailed routing, on EXTRACTED parasitics.
#
# The flow's own hold repair (post-CTS / post-GRT) runs on estimated parasitics at the three nominal
# resizer corners. On this design that estimate misses the skew to a few late clock branches by up to
# ~0.2 ns, so PD variants kept ending with one to three max_ff hold violations of 10-30 ps. The Python
# side of this step extracts the routed DEF with one OpenRCX ruleset and its matching tech LEF (the
# same way the RCX step does, default max_*), and this script annotates that SPEF on every resizer
# corner, so the ff corner is max_ff for hold and the ss/tt corners are max_ss/max_tt for the setup
# guard. repair_timing -hold then inserts the few buffers needed, detailed placement legalises them,
# global routing gives the touched nets guides incrementally and detailed routing reroutes them.
# Measured by hand on x_E1: the extraction reproduces the signoff max_ff hold WNS (-0.0101 ns) and
# 3 buffers bring it to +0.061 ns with setup unchanged.
# POST_ROUTE_ECO_REPAIR_DESIGN adds a repair_design pass on the same parasitics before the hold repair:
# on x_E3, 366 of the 391 nom_tt max-cap violators were buffers that the post-GPL repair_design had
# sized on its placement estimate, and no later step looked at them with real wires.
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
source $::env(SCRIPTS_DIR)/openroad/common/resizer.tcl

load_rsz_corners
read_current_odb

set_propagated_clock [all_clocks]

set_dont_touch_objects

foreach corner [sta::corners] {
    read_spef -corner [$corner name] $::env(_ECO_SPEF)
}
puts "\[INFO\] post-route hold ECO: '$::env(_ECO_SPEF)' annotated on every resizer corner"
puts "\[INFO\] post-route hold ECO: before"
report_worst_slack -min -digits 4
report_worst_slack -max -digits 4

# Detailed placement on an already placed design resets every cell to its row's orientation, undoing
# optimize_mirroring (the standalone test: legalized HPWL +2 %, about 50,000 routed cells flipped). So
# every cell that existed before the repair, with the same master, is held FIRM while the new (and any
# resized) cells are legalised.
foreach inst [$::block getInsts] {
    set eco_old([$inst getName]) [[$inst getMaster] getName]
}

# Optional DRV repair on the extracted parasitics (POST_ROUTE_ECO_REPAIR_DESIGN). The violations are
# found by STA on the SPEF; the new wire segments are planned with the flow's wire RC, the calibrated
# LAYERS_RC when it is set.
if { [info exists ::env(POST_ROUTE_ECO_REPAIR_DESIGN)] && $::env(POST_ROUTE_ECO_REPAIR_DESIGN) } {
    set ::LAYERS_RC_HERE 1
    source $::env(SCRIPTS_DIR)/openroad/common/set_rc.tcl
    puts "\[INFO\] post-route ECO: repair_design on the extracted parasitics"
    repair_design -verbose \
        -slew_margin $::env(POST_ROUTE_ECO_SLEW_PCT) \
        -cap_margin $::env(POST_ROUTE_ECO_CAP_PCT)
}

set hold_args [list]
lappend hold_args -verbose
lappend hold_args -hold
lappend hold_args -hold_margin $::env(POST_ROUTE_HOLD_ECO_MARGIN)
lappend hold_args -max_buffer_percent $::env(POST_ROUTE_HOLD_ECO_MAX_BUFFER_PCT)
if { $::env(POST_ROUTE_HOLD_ECO_ALLOW_SETUP_VIOS) == 1 } {
    lappend hold_args -allow_setup_violations
}
repair_timing {*}$hold_args

# The new buffers' nets are not in the SPEF, so these numbers use wire-load estimates for them.
puts "\[INFO\] post-route hold ECO: after"
report_worst_slack -min -digits 4
report_worst_slack -max -digits 4

set eco_locked {}
set eco_new 0
set eco_resized 0
foreach inst [$::block getInsts] {
    set name [$inst getName]
    if { ![info exists eco_old($name)] } {
        incr eco_new
    } elseif { $eco_old($name) != [[$inst getMaster] getName] } {
        incr eco_resized
    } elseif { [$inst getPlacementStatus] == "PLACED" } {
        $inst setPlacementStatus FIRM
        lappend eco_locked $inst
    }
}
puts "\[INFO\] post-route ECO: legalising $eco_new new and $eco_resized resized cells, [llength $eco_locked] cells held FIRM"
source $::env(SCRIPTS_DIR)/openroad/common/dpl_cell_pad.tcl
detailed_placement -max_displacement [subst { $::env(PL_MAX_DISPLACEMENT_X) $::env(PL_MAX_DISPLACEMENT_Y) }]
foreach inst $eco_locked {
    $inst setPlacementStatus PLACED
}
check_placement -verbose
unset_dont_touch_objects

# Guides for the ECO nets. Global routing skips every net that already has wires: on this routed design
# a full global_route reports "Routed nets: 0", and the -start/-end_incremental bracket (which also
# segfaults in GlobalRouter::addDirtyNet unless a full route ran first) produced no new guides, so the
# 3-buffer hold ECO only worked because detailed routing patched pins a few microns away, while the
# 1,325-buffer DRV ECO of x_E3R (cells moved up to 98.6 um) died with DRT-0218. So the nets of every new
# or resized cell lose their wires here, a full global_route routes exactly those nets, and detailed
# routing routes them (everything else keeps its wires). Only guides are needed, so the timing-driven
# parts of GRT (where this host's GRT crashes cluster, see grt.tcl) are off.
set eco_nets [dict create]
foreach inst [$::block getInsts] {
    set name [$inst getName]
    if { [info exists eco_old($name)] && $eco_old($name) == [[$inst getMaster] getName] } { continue }
    foreach it [$inst getITerms] {
        set net [$it getNet]
        if { $net == "NULL" } { continue }
        if { [$net getSigType] == "POWER" || [$net getSigType] == "GROUND" } { continue }
        dict set eco_nets [$net getName] $net
    }
}
set eco_ripped 0
dict for {name net} $eco_nets {
    set wire [$net getWire]
    if { $wire != "NULL" } {
        odb::dbWire_destroy $wire
        incr eco_ripped
    }
    catch { $net clearGuides }
}
puts "\[INFO\] post-route ECO: [dict size $eco_nets] nets touched, $eco_ripped wires removed for rerouting"
source $::env(SCRIPTS_DIR)/openroad/common/set_routing_layers.tcl
source $::env(SCRIPTS_DIR)/openroad/common/set_layer_adjustments.tcl
set_macro_extension $::env(GRT_MACRO_EXTENSION)
set_routing_alpha 0
global_route -congestion_iterations $::env(GRT_OVERFLOW_ITERS) -critical_nets_percentage 0 -verbose

write_db $::env(STEP_DIR)/after_grt.odb
set net [[[$::block findInst wire11106] findITerm A] getNet]
puts "DBG net [$net getName] guides [llength [$net getGuides]] wire [$net getWire]"
foreach g [$net getGuides] { set b [$g getBox]; puts "DBG guide [[$g getLayer] getName] [$b xMin] [$b yMin] [$b xMax] [$b yMax]" }
foreach it [$net getITerms] { set b [$it getBBox]; set i [$it getInst]; puts "DBG iterm [$i getName]/[[$it getMTerm] getName] [$i getPlacementStatus] [$b xMin] [$b yMin] [$b xMax] [$b yMax]" }
