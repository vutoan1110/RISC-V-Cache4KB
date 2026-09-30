# FLOW_JOURNAL Incident 93 (local addition, off unless RUN_MACRO_PIN_BUFFERS): a dedicated buffer
# right outside the macro edge at every selected macro pin.
#
# The OpenRAM liberty limits the transition at the SRAM inputs to 0.04 ns and the load on dout to
# 0.0276 pF. A shared address net that runs from one driver to four banks cannot meet 0.04 ns (signoff
# median 0.125 ns at nom_tt), and the resizer, working on estimated parasitics, did not see it. From the
# sky130_fd_sc_hd tt liberty: buf_8 driving 0.0108 pF has a 0.0325 ns output transition, and an SRAM
# address pin is 0.0069 pF, so a buf_8 a few microns from the pin meets the limit by construction.
#
# Inputs matching MACRO_PIN_BUFFER_IN_PINS always get a buffer (a short net with a weak driver violates
# too). Outputs matching MACRO_PIN_BUFFER_OUT_PINS get one when the net's half-perimeter exceeds
# MACRO_PIN_BUFFER_OUT_MIN_HPWL. The new macro-side nets are named macro_pin_net_<n>, so that
# RSZ_DONT_TOUCH_RX can keep the resizer from buffering them or removing the buffers again. Detailed
# placement (the next placement step) legalises the buffers.
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb

set dbu [$::tech getDbUnitsPerMicron]
set in_master [$::db findMaster $::env(MACRO_PIN_BUFFER_IN_CELL)]
set out_master [$::db findMaster $::env(MACRO_PIN_BUFFER_OUT_CELL)]
if { $in_master == "NULL" || $out_master == "NULL" } {
    puts stderr "\[ERROR\] macro pin buffer cell not found"
    exit 1
}
# Optional second stage in front of each input buffer. x_E3: the buf_8 loads were only 0.0084-0.012 pF,
# yet 70 of 248 pins were 0.040-0.050 ns, because the buf_8 INPUT came from the long shared address net
# (0.2-0.6 ns); buf_8 driving 0.0108 pF gives 0.0325 ns only for input transitions up to ~0.08 ns
# (0.0357 at 0.224, 0.0448 at 0.630). A small buffer right behind it restores a sharp input edge.
set pre_master "NULL"
if { [info exists ::env(MACRO_PIN_BUFFER_IN_PRE_CELL)] } {
    set pre_master [$::db findMaster $::env(MACRO_PIN_BUFFER_IN_PRE_CELL)]
    if { $pre_master == "NULL" } {
        puts stderr "\[ERROR\] macro pin pre-buffer cell not found"
        exit 1
    }
}
set n_pre 0
set in_rx $::env(MACRO_PIN_BUFFER_IN_PINS)
set out_rx $::env(MACRO_PIN_BUFFER_OUT_PINS)
set out_min_hpwl [expr {$::env(MACRO_PIN_BUFFER_OUT_MIN_HPWL) * $dbu}]
set gap [expr {int($::env(MACRO_PIN_BUFFER_GAP) * $dbu)}]

proc net_hpwl {net} {
    set xs {}
    set ys {}
    foreach it [$net getITerms] {
        set p [$it getAvgXY]
        if { [lindex $p 0] } {
            lappend xs [lindex $p 1]
            lappend ys [lindex $p 2]
        }
    }
    foreach bt [$net getBTerms] {
        set b [$bt getBBox]
        lappend xs [expr {([$b xMin] + [$b xMax]) / 2}]
        lappend ys [expr {([$b yMin] + [$b yMax]) / 2}]
    }
    if { [llength $xs] < 2 } { return 0 }
    set xs [lsort -integer $xs]
    set ys [lsort -integer $ys]
    return [expr {[lindex $xs end] - [lindex $xs 0] + [lindex $ys end] - [lindex $ys 0]}]
}

set n 0
set n_in 0
set n_out 0
foreach inst [$::block getInsts] {
    if { ![[$inst getMaster] isBlock] } { continue }
    set box [$inst getBBox]
    set mx0 [$box xMin]; set my0 [$box yMin]; set mx1 [$box xMax]; set my1 [$box yMax]
    foreach it [$inst getITerms] {
        set pin [[$it getMTerm] getName]
        set net [$it getNet]
        if { $net == "NULL" } { continue }
        if { [$net getSigType] != "SIGNAL" } { continue }
        set io [$it getIoType]
        if { $io == "INPUT" && [regexp -- $in_rx $pin] } {
            set master $in_master
        } elseif { $io == "OUTPUT" && [regexp -- $out_rx $pin] && [net_hpwl $net] > $out_min_hpwl } {
            set master $out_master
        } else {
            continue
        }
        set p [$it getAvgXY]
        if { ![lindex $p 0] } { continue }
        set px [lindex $p 1]; set py [lindex $p 2]
        set w [$master getWidth]; set h [$master getHeight]
        # Nearest macro edge to the pin; the buffer goes just outside it, facing the pin.
        set dl [expr {$px - $mx0}]; set dr [expr {$mx1 - $px}]
        set db [expr {$py - $my0}]; set dt [expr {$my1 - $py}]
        set dmin [lindex [lsort -integer [list $dl $dr $db $dt]] 0]
        if { $dmin == $db } {
            set x [expr {$px - $w / 2}]; set y [expr {$my0 - $gap - $h}]
        } elseif { $dmin == $dt } {
            set x [expr {$px - $w / 2}]; set y [expr {$my1 + $gap}]
        } elseif { $dmin == $dl } {
            set x [expr {$mx0 - $gap - $w}]; set y [expr {$py - $h / 2}]
        } else {
            set x [expr {$mx1 + $gap}]; set y [expr {$py - $h / 2}]
        }
        set buf [odb::dbInst_create $::block $master "macro_pin_buf_$n"]
        set new_net [odb::dbNet_create $::block "macro_pin_net_$n"]
        $it disconnect
        $it connect $new_net
        if { $io == "INPUT" && $pre_master != "NULL" } {
            set pre [odb::dbInst_create $::block $pre_master "macro_pin_pre_$n"]
            set pre_net [odb::dbNet_create $::block "macro_pin_pre_net_$n"]
            [$pre findITerm A] connect $net
            [$pre findITerm X] connect $pre_net
            [$buf findITerm A] connect $pre_net
            [$buf findITerm X] connect $new_net
            # one cell further from the macro than the pin buffer
            set pw [$pre_master getWidth]; set ph [$pre_master getHeight]
            if { $dmin == $db } {
                $pre setLocation $x [expr {$y - $ph}]
            } elseif { $dmin == $dt } {
                $pre setLocation $x [expr {$y + $h}]
            } elseif { $dmin == $dl } {
                $pre setLocation [expr {$x - $pw}] $y
            } else {
                $pre setLocation [expr {$x + $w}] $y
            }
            $pre setPlacementStatus PLACED
            incr n_pre
            incr n_in
        } elseif { $io == "INPUT" } {
            [$buf findITerm A] connect $net
            [$buf findITerm X] connect $new_net
            incr n_in
        } else {
            [$buf findITerm A] connect $new_net
            [$buf findITerm X] connect $net
            incr n_out
        }
        $buf setLocation $x $y
        $buf setPlacementStatus PLACED
        incr n
    }
}
puts "\[INFO\] macro pin buffers: $n inserted ($n_in on inputs, $n_out on outputs), plus $n_pre pre-buffers"
puts "%OL_METRIC_I design__macro_pin_buffer__count [expr {$n + $n_pre}]"

write_views
