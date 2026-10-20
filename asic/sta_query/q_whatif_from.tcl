# NHAT_KY.md 2026-09-28 (Task B bound): remove every setup path that STARTS at the registers whose Q nets
# match the patterns in $::env(SQ_FROM) (one glob per line), then report the worst slack and how many
# endpoints stay below -1..-8 ns. Removing ALL paths from a register over-cuts (its legitimate data paths go
# too), so the result is an OPTIMISTIC bound for re-architecting what those registers feed.
set f [open $::env(SQ_FROM) r]
foreach line [split [read $f] "\n"] {
    set line [string trim $line]
    if {$line eq "" || [string index $line 0] eq "#"} { continue }
    set pins [get_pins -quiet -of_objects [get_nets -quiet $line] -filter "direction == output"]
    puts "WHATIF_FROM $line: [llength $pins] driver pin(s)"
    if {[llength $pins]} { set_false_path -from [get_cells -of_objects $pins] }
}
close $f
puts "WHATIF_FROM worst setup slack: [format %.3f [sta::worst_slack_cmd max]]"
set ends [find_timing_paths -path_delay max -group_count 20000 -endpoint_count 1 -slack_max 0.0]
set hist ""
foreach t {-1 -2 -3 -4 -5 -6 -7 -8} {
    set n 0
    foreach pe $ends { if {[get_property $pe slack] < $t} { incr n } }
    append hist " <$t:$n"
}
puts "WHATIF_FROM violating endpoints [llength $ends]$hist"
report_checks -path_delay max -group_count 1 -format full -fields {net} -digits 3
