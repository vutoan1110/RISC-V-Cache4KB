module riscv_core #(
    parameter integer BRANCH_PREDICT_ENABLE = 1,
    parameter integer BHT_ENTRIES = 256
)
(
    input         clk             ,
    input         reset_n         ,
    input         irq_timer       ,
    output [31:0] pc_f            ,
    output [31:0] pc_f_ic         ,  // R13a-2
    input  [31:0] instr           ,
    output        mem_wr_m        ,
    output        mem_rd_m        ,
    output [31:0] alu_result_m    ,
    output [31:0] wr_data_m       ,
    input  [31:0] rd_data         ,
    output        trap_taken      ,
    output [31:0] mcause_dbg      ,
    output [31:0] mepc_dbg        ,
    output [31:0] mtvec_dbg       ,
    input         stall_pipe      ,
    output [31:0] mcycle_dbg      ,
    output [31:0] minstret_dbg    ,
    output [2:0] mem_funct3_m,
    output [31:0] load_stall_dbg  ,
    output [31:0] branch_flush_dbg,
    output [31:0] control_redirect_dbg,
    output        retire_event_dbg,
    output        load_use_stall_event_dbg,
    output        control_redirect_event_dbg,
    output        mispredict_event_dbg,
    output        conditional_branch_event_dbg,
    output        branch_taken_event_dbg,
    output        branch_not_taken_event_dbg,
    output        branch_prediction_event_dbg,
    output        branch_correct_prediction_event_dbg,
    output        pipeline_nonempty_dbg,
    output        retire_valid,
    output [63:0] retire_order,
    output [31:0] retire_pc,
    output [31:0] retire_pc_next,
    output [31:0] retire_instr,
    output [4:0]  retire_rs1_addr,
    output [31:0] retire_rs1_rdata,
    output [4:0]  retire_rs2_addr,
    output [31:0] retire_rs2_rdata,
    output [4:0]  retire_rd_addr,
    output [31:0] retire_rd_wdata,
    output        retire_rd_we,
    output        retire_mem_valid,
    output        retire_mem_write,
    output [31:0] retire_mem_addr,
    output [31:0] retire_mem_wdata,
    output [3:0]  retire_mem_wstrb,
    output        retire_trap,
    output        retire_interrupt
);

wire [31:0] instr_d;
wire        alu_src_e;
wire        reg_wr_w;
wire        reg_wr_m;
wire        reg_wr_e;       // R9
wire [1:0]  result_src_m;   // R9
wire        jump_e;
wire [1:0]  result_src_e;
wire [1:0]  result_src_w;
wire [2:0]  imm_src_d;
wire [3:0]  alu_ctrl_e;
wire        flush_e;
wire        use_rs1_d;
wire        use_rs2_d;
wire        valid_d;

controller controller (
    .clk          (clk),
    .reset_n      (reset_n),
    .op           (instr_d[6:0]),
    .funct3       (instr_d[14:12]),
    .funct7       (instr_d[31:25]),
    .flush_e      (flush_e),
    .stall_pipe   (stall_pipe),
    .valid_d      (valid_d),
    .result_src_e (result_src_e),
    .result_src_m (result_src_m),
    .result_src_w (result_src_w),
    .mem_wr_m     (mem_wr_m),
    .mem_rd_m     (mem_rd_m),
    .alu_src_e    (alu_src_e),
    .reg_wr_e     (reg_wr_e),
    .reg_wr_m     (reg_wr_m),
    .reg_wr_w     (reg_wr_w),
    .jump_e       (jump_e),
    .imm_src_d    (imm_src_d),
    .alu_ctrl_e   (alu_ctrl_e),
    .use_rs1_d    (use_rs1_d),
    .use_rs2_d    (use_rs2_d)
);

datapath #(
    .BRANCH_PREDICT_ENABLE(BRANCH_PREDICT_ENABLE),
    .BHT_ENTRIES(BHT_ENTRIES)
) datapath (
    .clk              (clk),
    .reset_n          (reset_n),
    .irq_timer        (irq_timer),
    .result_src_m     (result_src_m),
    .result_src_w     (result_src_w),
    .alu_src_e        (alu_src_e),
    .reg_wr_e         (reg_wr_e),
    .reg_wr_m         (reg_wr_m),
    .reg_wr_w         (reg_wr_w),
    .imm_src_d        (imm_src_d),
    .alu_ctrl_e       (alu_ctrl_e),
    .jump_e           (jump_e),
    .pc_f             (pc_f),
    .pc_f_ic          (pc_f_ic),
    .instr            (instr),
    .alu_result_m     (alu_result_m),
    .wr_data_m        (wr_data_m),
    .mem_funct3_m     (mem_funct3_m),
    .instr_d          (instr_d),
    .valid_d          (valid_d),
    .flush_e          (flush_e),
    .rd_data          (rd_data),
    .result_src_e     (result_src_e),
    .trap_taken       (trap_taken),
    .mcause_dbg       (mcause_dbg),
    .mepc_dbg         (mepc_dbg),
    .mtvec_dbg        (mtvec_dbg),
    .stall_pipe       (stall_pipe),
    .mcycle_dbg       (mcycle_dbg),
    .minstret_dbg     (minstret_dbg),
    .load_stall_dbg   (load_stall_dbg),
    .branch_flush_dbg (branch_flush_dbg),
    .control_redirect_dbg (control_redirect_dbg),
    .retire_event_dbg (retire_event_dbg),
    .load_use_stall_event_dbg (load_use_stall_event_dbg),
    .control_redirect_event_dbg (control_redirect_event_dbg),
    .mispredict_event_dbg (mispredict_event_dbg),
    .conditional_branch_event_dbg (conditional_branch_event_dbg),
    .branch_taken_event_dbg (branch_taken_event_dbg),
    .branch_not_taken_event_dbg (branch_not_taken_event_dbg),
    .branch_prediction_event_dbg (branch_prediction_event_dbg),
    .branch_correct_prediction_event_dbg (branch_correct_prediction_event_dbg),
    .pipeline_nonempty_dbg (pipeline_nonempty_dbg),
    .retire_valid      (retire_valid),
    .retire_order      (retire_order),
    .retire_pc         (retire_pc),
    .retire_pc_next    (retire_pc_next),
    .retire_instr      (retire_instr),
    .retire_rs1_addr   (retire_rs1_addr),
    .retire_rs1_rdata  (retire_rs1_rdata),
    .retire_rs2_addr   (retire_rs2_addr),
    .retire_rs2_rdata  (retire_rs2_rdata),
    .retire_rd_addr    (retire_rd_addr),
    .retire_rd_wdata   (retire_rd_wdata),
    .retire_rd_we      (retire_rd_we),
    .retire_mem_valid  (retire_mem_valid),
    .retire_mem_write  (retire_mem_write),
    .retire_mem_addr   (retire_mem_addr),
    .retire_mem_wdata  (retire_mem_wdata),
    .retire_mem_wstrb  (retire_mem_wstrb),
    .retire_trap       (retire_trap),
    .retire_interrupt  (retire_interrupt),
    .use_rs1_d        (use_rs1_d),
    .use_rs2_d        (use_rs2_d)
);

endmodule
