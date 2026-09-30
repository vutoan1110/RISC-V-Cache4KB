# Clock latency (arrival of clk) at every register clock pin, min_ff corner,
# written as "pin latency_rise" for a histogram (FLOW_JOURNAL Incident 76).
puts "SQ_PROPS"
catch {report_clock_latency -digits 3} e1
puts "report_clock_latency: $e1"
set out [open $::env(SQ_OUT) w]
set n 0
foreach pin [all_registers -clock_pins] {
    set v ""
    if {[catch {set v [get_property $pin arrival_max_rise]} err]} { set v "ERR:$err" }
    puts $out "[get_full_name $pin] $v"
    incr n
    if {$n == 1} { puts "first: [get_full_name $pin] $v" }
}
close $out
puts "SQ_DONE $n pins"
