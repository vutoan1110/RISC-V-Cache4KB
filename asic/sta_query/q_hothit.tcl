# Worst max path through every input of the cells that combine the icache
# hot-hit terms (r9_ecf4 names); the caller greps the arrival at each pin.
foreach c {_050499_ _050703_ _050704_ _050735_ _050779_ _050780_ _050781_ _052567_} {
    foreach p [get_pins -of_objects [get_cells $c] -filter "direction == input"] {
        puts "SQ_THROUGH [get_full_name $p]"
        report_checks -through $p -path_delay max -format full -digits 3
    }
}
