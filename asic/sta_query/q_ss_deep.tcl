# NHAT_KY.md 2026-09-27: the worst setup path into each of the N worst violating endpoints at
# one corner, full format with input pins (cell arcs vs net arcs separable), for ss_decompose.py.
# Output: $::env(SQ_OUT)/ss_paths_<corner>.rpt
set out $::env(SQ_OUT)
set c $::env(_CURRENT_CORNER_NAME)
set N [expr {[info exists ::env(SQ_N)] ? $::env(SQ_N) : 3000}]
report_checks -path_delay max -group_count $N -endpoint_count 1 -slack_max 0.0 -sort_by_slack \
    -format full -fields {input_pin net} -digits 4 > $out/ss_paths_$c.rpt
puts "SQ_SS done: $out/ss_paths_$c.rpt"
