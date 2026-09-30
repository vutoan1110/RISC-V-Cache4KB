# FLOW_JOURNAL Incident 93: where the macro pin buffers end up after legalisation, relative to their pin.
source $::env(SCRIPTS_DIR)/openroad/macro_pin_buffers.tcl
source $::env(SCRIPTS_DIR)/openroad/common/dpl_cell_pad.tcl
detailed_placement -max_displacement [subst { $::env(PL_MAX_DISPLACEMENT_X) $::env(PL_MAX_DISPLACEMENT_Y) }]
set f [open $::env(STEP_DIR)/dist.tsv w]
puts $f "buf\tpin\tdx_um\tdy_um\tdist_um"
foreach inst [$::block getInsts] {
    set name [$inst getName]
    if { ![string match macro_pin_buf_* $name] } { continue }
    set b [$inst getBBox]
    set bx [expr {([$b xMin] + [$b xMax]) / 2}]; set by [expr {([$b yMin] + [$b yMax]) / 2}]
    set nn [string map {macro_pin_buf_ macro_pin_net_} $name]
    set net [$::block findNet $nn]
    foreach it [$net getITerms] {
        if { [[$it getInst] getName] == $name } { continue }
        set p [$it getAvgXY]
        set dx [expr {abs([lindex $p 1] - $bx) / 1000.0}]; set dy [expr {abs([lindex $p 2] - $by) / 1000.0}]
        puts $f "$name\t[[$it getInst] getName]/[[$it getMTerm] getName]\t$dx\t$dy\t[expr {$dx + $dy}]"
    }
}
close $f
puts "MPB2 done"
