# Worst register->register path of each counter variant at the ss corner.
read_liberty $::env(LIB_SS)
foreach m {cnt_a cnt_b} {
    read_verilog $m.nl.v
    link_design $m
    create_clock -name clk -period 20 [get_ports clk]
    puts "== $m"
    report_checks -path_delay max -digits 3 -fields {} > /tmp/r10k_$m.txt
    report_checks -path_delay max -digits 3 -format summary
}
