# NHAT_KY.md 2026-09-28 (Task B feasibility): "what if a pipeline register were inserted here?"
# Each line of $::env(SQ_CUTS) names a net; every timing path THROUGH it is removed (set_false_path
# -through), which is what a register on that net would do to the current single-cycle path. The script
# reports, after all cuts, the worst setup slack and the worst path (named nets only), so the cuts needed
# for ss closure can be counted before any RTL is written. Output goes to stdout.
set cuts {}
if {[info exists ::env(SQ_CUTS)] && [file exists $::env(SQ_CUTS)]} {
    set f [open $::env(SQ_CUTS) r]
    foreach line [split [read $f] "\n"] {
        set line [string trim $line]
        if {$line eq "" || [string index $line 0] eq "#"} { continue }
        lappend cuts $line
    }
    close $f
}
foreach c $cuts {
    set n [get_nets -quiet $c]
    if {[llength $n] == 0} { puts "WHATIF missing net: $c"; continue }
    set_false_path -through $n
    puts "WHATIF cut through $c ([llength $n] net(s))"
}
puts "WHATIF worst setup slack after [llength $cuts] cut(s): [format %.3f [sta::worst_slack_cmd max]]"
report_checks -path_delay max -group_count 1 -format full -fields {net} -digits 3
report_checks -path_delay max -group_count 12 -endpoint_count 1 -format end -digits 3
