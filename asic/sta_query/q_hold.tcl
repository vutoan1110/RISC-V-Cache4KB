# FLOW_JOURNAL Incident 91: worst hold paths at one corner (for the X2 hold violation)
report_checks -path_delay min -group_count 5 -endpoint_count 1 -format full -fields {input_pin net} -digits 4
report_worst_slack -min -digits 4
