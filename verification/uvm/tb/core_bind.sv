`timescale 1ns/1ps

// Reuse the existing pipeline assertions instead of rewriting them. Binding
// into riscv_core gives the checker plain access to the pipeline internals and
// to stall_pipe, which riscv_core_native drives as an input port.
//
// verification/assertions/axi_assertions.sv and cache_assertions.sv are not
// bound here: the AXI and cache signals they check do not exist at the
// riscv_core_native boundary. They belong to the cache_axi_master DUT of
// phase 4 and the SoC DUT of phase 5.
//
// The bind lives inside a module rather than in compilation-unit scope so it
// elaborates without needing vlog -mfcu -cuname. tb_core_top instantiates this
// module; the bind itself still reaches every riscv_core instance.
module core_assertion_bind;

bind riscv_core core_assertions #(
    .BRANCH_PREDICT_ENABLE (BRANCH_PREDICT_ENABLE)
) u_core_assertions (
    .clk        (clk),
    .reset_n    (reset_n),
    .stall_pipe (stall_pipe),

    .valid_d (datapath.valid_d),
    .valid_e (datapath.valid_e),
    .valid_m (datapath.valid_m),
    .valid_w (datapath.valid_w),
    .instr_d (datapath.instr_d),
    .instr_e (datapath.instr_e),
    .instr_m (datapath.instr_m),

    .use_rs1_d    (use_rs1_d),
    .use_rs2_d    (use_rs2_d),
    .result_src_e (result_src_e),

    .load_use_hazard (datapath.load_use_hazard),
    .stall_f         (datapath.stall_f),
    .stall_d         (datapath.stall_d),
    .flush_e         (datapath.flush_e),

    .pc_f     (datapath.pc_f),
    .pc_d     (datapath.pc_d),
    .pc_e     (datapath.pc_e),
    .pc_src_e (datapath.pc_src_e),

    .is_branch_e         (datapath.is_branch_e),
    .branch_taken_e      (datapath.branch_taken_e),
    .mispredict_e        (datapath.mispredict_e),
    .pc_target_e         (datapath.pc_target_e),
    .pc_plus4_e          (datapath.pc_plus4_e),
    .branch_resolve_fire (datapath.branch_resolve_fire),
    .bht_update_en       (datapath.branch_resolve_fire),

    .mem_wr_m (mem_wr_m),
    .architectural_reg_write (reg_wr_w && datapath.valid_w && !stall_pipe &&
                              (datapath.instr_w[11:7] != 5'd0)),

    .retire_valid     (retire_valid),
    .retire_order     (retire_order),
    .retire_pc        (retire_pc),
    .retire_instr     (retire_instr),
    .retire_rs1_addr  (retire_rs1_addr),
    .retire_rs1_rdata (retire_rs1_rdata),
    .retire_rs2_addr  (retire_rs2_addr),
    .retire_rs2_rdata (retire_rs2_rdata),
    .retire_rd_we     (retire_rd_we),
    .retire_rd_addr   (retire_rd_addr),
    .retire_mem_write (retire_mem_write),
    .retire_mem_addr  (retire_mem_addr),
    .retire_mem_wstrb (retire_mem_wstrb),

    .assertion_checks ()
);

endmodule
