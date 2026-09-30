# Worst max path into the worst endpoint of each violating group (r9_ecf4)
puts "SQ_GROUP u_soc.if_req_addr"
report_checks -to _117013_/D -path_delay max -format full -digits 3 -fields {net}
puts "SQ_GROUP u_soc.u_core.u_pipeline.datapath.g_bp_on.u_bht.bht_mem"
report_checks -to _118919_/D -path_delay max -format full -digits 3 -fields {net}
puts "SQ_GROUP u_soc.mepc_dbg"
report_checks -to _117965_/D -path_delay max -format full -digits 3 -fields {net}
puts "SQ_GROUP u_soc.u_core.u_pipeline.datapath.csr_mstatus"
report_checks -to _117845_/D -path_delay max -format full -digits 3 -fields {net}
puts "SQ_GROUP u_soc.mcycle_dbg"
report_checks -to _118003_/D -path_delay max -format full -digits 3 -fields {net}
puts "SQ_GROUP u_soc.u_core.u_pipeline.datapath.immext_e"
report_checks -to _118612_/D -path_delay max -format full -digits 3 -fields {net}
puts "SQ_GROUP u_soc.u_core.u_pipeline.controller.alu_ctrl_e"
report_checks -to _112724_/D -path_delay max -format full -digits 3 -fields {net}
puts "SQ_GROUP u_soc.d_req_addr"
report_checks -to _118234_/D -path_delay max -format full -digits 3 -fields {net}
puts "SQ_GROUP u_soc.u_observability.pipe_fill_drain_cycle_count"
report_checks -to _110226_/D -path_delay max -format full -digits 3 -fields {net}
puts "SQ_GROUP u_soc.u_core.u_pipeline.datapath.predicted_target_d"
report_checks -to _118593_/D -path_delay max -format full -digits 3 -fields {net}
puts "SQ_GROUP u_soc.u_core.u_pipeline.datapath.pc_d"
report_checks -to _118653_/D -path_delay max -format full -digits 3 -fields {net}
puts "SQ_GROUP u_soc.u_core.u_pipeline.datapath.regfile.regs"
report_checks -to _106629_/D -path_delay max -format full -digits 3 -fields {net}
