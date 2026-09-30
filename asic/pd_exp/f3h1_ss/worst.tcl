# Worst max-delay path at the loaded corner, with the cells it goes through.
report_checks -path_delay max -group_count 1 -format full -fields {fanout cap slew} -digits 3
