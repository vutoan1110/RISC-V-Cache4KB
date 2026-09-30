# FLOW_JOURNAL Incident 93: for every SRAM addr/wmask pin, the driver, the net capacitance (pin + wire, from
# the SPEF) and the transition at the pin, to see why some still exceed 0.04 ns after MacroPinBuffers.
set out $::env(SQ_OUT)
set f [open $out/sram_pin_load.tsv w]
puts $f "pin\tdriver\tdriver_ref\tnet\tcap_pf\tslew_ns"
foreach pin [get_pins -hierarchical *u_bank/addr* ] {
    lappend pins $pin
}
foreach pin [get_pins -hierarchical *u_bank/wmask* ] {
    lappend pins $pin
}
foreach pin $pins {
    set net [get_nets -of_objects $pin]
    set drv [get_pins -of_objects $net -filter "direction == output"]
    set dref ""
    catch { set dref [get_property [get_cells -of_objects $drv] ref_name] }
    set cap [sta::format_capacitance [$net capacitance [sta::cmd_corner] max] 5]
    set slew [get_property $pin slew_max]
    puts $f "[get_full_name $pin]\t[get_full_name $drv]\t$dref\t[get_full_name $net]\t$cap\t$slew"
}
close $f
puts "SQ_SRAMPIN done"
