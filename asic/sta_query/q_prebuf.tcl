# NHAT_KY.md 2026-09-28: transitions along pre-buffer -> pin buffer -> SRAM pin for the worst E5b pins.
set out $::env(SQ_OUT)
set f [open $out/prebuf.txt w]
foreach n {208 34 33 35 251 0 1} {
    foreach p [list macro_pin_pre_$n/A macro_pin_pre_$n/X macro_pin_buf_$n/A macro_pin_buf_$n/X] {
        set pin [get_pins -quiet $p]
        if {[llength $pin] == 0} { puts $f "$p missing"; continue }
        set net [get_nets -of_objects $pin]
        puts $f "$p slew_max=[get_property $pin slew_max] net=[get_full_name $net] cap=[sta::format_capacitance [$net capacitance [sta::cmd_corner] max] 5]"
    }
}
close $f
puts "SQ_PREBUF done"
