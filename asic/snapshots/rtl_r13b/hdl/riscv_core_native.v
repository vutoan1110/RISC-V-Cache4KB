module riscv_core_native #(
    parameter integer BRANCH_PREDICT_ENABLE = 1,
    parameter integer BHT_ENTRIES = 256
)
(
    input         clk,
    input         reset_n,
    input         irq_timer,

    // Native instruction port (one request outstanding).
    output        if_req_valid,
    output [31:0] if_req_addr,
    input         if_req_ready,
    input         if_rsp_valid,
    input  [31:0] if_rsp_data,
    input         if_rsp_error,

    // Native data port (stores also get a response).
    output        d_req_valid,
    output        d_req_write,
    output [31:0] d_req_addr,
    output [31:0] d_req_wdata,
    output [3:0]  d_req_wstrb,
    input         d_req_ready,
    input         d_rsp_valid,
    input  [31:0] d_rsp_rdata,
    input         d_rsp_error,

    output        trap_taken,
    output [31:0] mcause_dbg,
    output [31:0] mepc_dbg,
    output [31:0] mtvec_dbg,
    output [31:0] mcycle_dbg,
    output [31:0] minstret_dbg,
    output [31:0] load_stall_dbg,
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
    output        retire_interrupt,
    output [31:0] pc_f_dbg,
    output        if_wait_dbg,
    output        d_wait_dbg,
    output reg    if_error_dbg,
    output reg    d_error_dbg
);

wire [31:0] pc_f;
wire [31:0] pc_f_ic;   // R13a-2: I-cache copy of pc_f (always equal)
wire [31:0] instr;
wire        mem_wr_m;
wire        mem_rd_m;
wire [31:0] alu_result_m;
wire [31:0] wr_data_m;
wire [31:0] rd_data;
wire [2:0]  mem_funct3_m;
wire        stall_pipe;
wire        mem_access;
wire        pipeline_advance;

reg         if_pending;
reg         if_buffer_valid;
reg  [31:0] if_buffer_data;
reg         d_pending;
reg         d_buffer_valid;
reg  [31:0] d_buffer_data;
reg         d_pending_posted;
reg         d_store_ack_valid;

wire if_req_fire;
wire if_rsp_accept;
wire if_available;
wire d_req_fire;
wire d_rsp_accept;
wire d_available;
wire d_store_post_accept;
wire d_rsp_is_posted_store;
wire d_rsp_completes_current;

assign if_req_valid  = reset_n && !if_pending && !if_buffer_valid;
assign if_req_addr   = pc_f_ic;
assign if_req_fire   = if_req_valid && if_req_ready;
assign if_rsp_accept = if_rsp_valid && (if_pending || if_req_fire);
assign if_available  = if_buffer_valid || if_rsp_accept;
assign instr         = if_buffer_valid ? if_buffer_data : if_rsp_data;

assign mem_access  = mem_wr_m || mem_rd_m;
assign d_req_valid = reset_n && mem_access && !d_pending &&
                     !d_buffer_valid && !d_store_ack_valid;
assign d_req_write = mem_wr_m;
assign d_req_addr  = alu_result_m;
assign d_req_fire  = d_req_valid && d_req_ready;
assign d_rsp_accept = d_rsp_valid && (d_pending || d_req_fire);
// Cacheable RAM stores are posted; MMIO stores stay non-posted.
assign d_store_post_accept = d_req_fire && d_req_write &&
                             (d_req_addr[31:16] == 16'h0000);
assign d_rsp_is_posted_store = d_pending ? d_pending_posted :
                                            d_store_post_accept;
assign d_rsp_completes_current = d_rsp_accept && !d_rsp_is_posted_store;
assign d_available  = !mem_access ||
                      (mem_wr_m && d_store_ack_valid) ||
                      d_store_post_accept || d_buffer_valid ||
                      d_rsp_completes_current;
assign rd_data      = d_buffer_valid ? d_buffer_data : d_rsp_rdata;

// Byte-lane placement for SB/SH/SW.
assign d_req_wdata = !mem_wr_m ? 32'h0000_0000 :
                     (mem_funct3_m == 3'b000) ?
                         ({24'h0, wr_data_m[7:0]} << (8 * alu_result_m[1:0])) :
                     (mem_funct3_m == 3'b001) ?
                         ({16'h0, wr_data_m[15:0]} << (8 * alu_result_m[1:0])) :
                         wr_data_m;

assign d_req_wstrb = !mem_wr_m ? 4'b0000 :
                     (mem_funct3_m == 3'b000) ? (4'b0001 << alu_result_m[1:0]) :
                     (mem_funct3_m == 3'b001) ? (4'b0011 << alu_result_m[1:0]) :
                                                4'b1111;

// Advance only when both the instruction and the data side are ready.
// The one-entry response buffers keep a pulse from being lost meanwhile.
assign pipeline_advance = if_available && d_available;
assign stall_pipe       = !pipeline_advance;
assign pc_f_dbg         = pc_f;
assign if_wait_dbg      = !if_available;
assign d_wait_dbg       = mem_access && !d_available;

always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        if_pending      <= 1'b0;
        if_buffer_valid <= 1'b0;
        if_buffer_data  <= 32'h0000_0013;
        d_pending       <= 1'b0;
        d_buffer_valid  <= 1'b0;
        d_buffer_data   <= 32'h0000_0000;
        if_error_dbg    <= 1'b0;
        d_pending_posted <= 1'b0;
        d_store_ack_valid <= 1'b0;
        d_error_dbg     <= 1'b0;
    end
    else begin
        if(if_req_fire && !if_rsp_accept)
            if_pending <= 1'b1;

        if(if_rsp_accept) begin
            if_pending   <= 1'b0;
            if_error_dbg <= if_error_dbg || if_rsp_error;
            if(pipeline_advance) begin
                if_buffer_valid <= 1'b0;
            end
            else begin
                if_buffer_valid <= 1'b1;
                if_buffer_data  <= if_rsp_data;
            end
        end
        else if(pipeline_advance && if_buffer_valid) begin
            if_buffer_valid <= 1'b0;
        end

        if(d_req_fire && !d_rsp_accept) begin
            d_pending <= 1'b1;
            d_pending_posted <= d_store_post_accept;
        end

        if(d_rsp_accept) begin
            d_pending   <= 1'b0;
            d_error_dbg <= d_error_dbg || d_rsp_error;
            // a posted-store response must not complete a younger op in M
            if(!d_rsp_is_posted_store) begin
                if(pipeline_advance && mem_access) begin
                    d_buffer_valid <= 1'b0;
                end
                else begin
                    d_buffer_valid <= 1'b1;
                    d_buffer_data  <= d_rsp_rdata;
                end
            end
        end
        else if(pipeline_advance && mem_access && d_buffer_valid) begin
            d_buffer_valid <= 1'b0;
        end

        // hold an acceptance token so a stalled posted store is not re-issued
        if(d_store_post_accept) begin
            if(pipeline_advance)
                d_store_ack_valid <= 1'b0;
            else
                d_store_ack_valid <= 1'b1;
        end
        else if(pipeline_advance && d_store_ack_valid) begin
            d_store_ack_valid <= 1'b0;
        end
    end
end

riscv_core #(
    .BRANCH_PREDICT_ENABLE(BRANCH_PREDICT_ENABLE),
    .BHT_ENTRIES(BHT_ENTRIES)
) u_pipeline (
    .clk              (clk),
    .reset_n          (reset_n),
    .irq_timer        (irq_timer),
    .pc_f             (pc_f),
    .pc_f_ic          (pc_f_ic),
    .instr            (instr),
    .mem_wr_m         (mem_wr_m),
    .mem_rd_m         (mem_rd_m),
    .alu_result_m     (alu_result_m),
    .wr_data_m        (wr_data_m),
    .rd_data          (rd_data),
    .trap_taken       (trap_taken),
    .mcause_dbg       (mcause_dbg),
    .mepc_dbg         (mepc_dbg),
    .mtvec_dbg        (mtvec_dbg),
    .stall_pipe       (stall_pipe),
    .mcycle_dbg       (mcycle_dbg),
    .minstret_dbg     (minstret_dbg),
    .mem_funct3_m     (mem_funct3_m),
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
    .retire_interrupt  (retire_interrupt)
);

endmodule
