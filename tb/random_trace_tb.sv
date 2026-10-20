`timescale 1ns/1ps
`include "tb/rf_bht_backdoor.svh"

module tb_random_trace;

localparam [31:0] NOP  = 32'h0000_0013;
localparam [31:0] HALT = 32'h0000_006f;

reg clk;
reg reset_n;
reg [31:0] imem [0:1023];
reg [31:0] dmem_off [0:255];
reg [31:0] dmem_on [0:255];
reg [31:0] arch_off [0:31];
reg [31:0] arch_on [0:31];
integer i;
integer cycle_count;
integer max_cycles;
integer seed;
integer fd_off;
integer fd_on;
integer expected_order_off;
integer expected_order_on;
reg done_off;
reg done_on;
string hex_path;
string trace_off_path;
string trace_on_path;

wire [31:0] pc_off, pc_on;
wire [31:0] instr_off = (pc_off[31:12] == 0) ? imem[pc_off[11:2]] : NOP;
wire [31:0] instr_on  = (pc_on[31:12] == 0) ? imem[pc_on[11:2]] : NOP;
wire mem_wr_off, mem_rd_off, mem_wr_on, mem_rd_on;
wire [31:0] addr_off, addr_on, raw_wdata_off, raw_wdata_on;
wire [2:0] funct3_off, funct3_on;

wire retire_valid_off, retire_valid_on;
wire [63:0] retire_order_off, retire_order_on;
wire [31:0] retire_pc_off, retire_pc_on;
wire [31:0] retire_pc_next_off, retire_pc_next_on;
wire [31:0] retire_instr_off, retire_instr_on;
wire [4:0] retire_rs1_addr_off, retire_rs1_addr_on;
wire [31:0] retire_rs1_rdata_off, retire_rs1_rdata_on;
wire [4:0] retire_rs2_addr_off, retire_rs2_addr_on;
wire [31:0] retire_rs2_rdata_off, retire_rs2_rdata_on;
wire [4:0] retire_rd_addr_off, retire_rd_addr_on;
wire [31:0] retire_rd_wdata_off, retire_rd_wdata_on;
wire retire_rd_we_off, retire_rd_we_on;
wire retire_mem_valid_off, retire_mem_valid_on;
wire retire_mem_write_off, retire_mem_write_on;
wire [31:0] retire_mem_addr_off, retire_mem_addr_on;
wire [31:0] retire_mem_wdata_off, retire_mem_wdata_on;
wire [3:0] retire_mem_wstrb_off, retire_mem_wstrb_on;

wire [31:0] store_lane_data_off =
    (funct3_off == 3'b000) ? ({24'h0, raw_wdata_off[7:0]} << (8 * addr_off[1:0])) :
    (funct3_off == 3'b001) ? ({16'h0, raw_wdata_off[15:0]} << (8 * addr_off[1:0])) :
                             raw_wdata_off;
wire [31:0] store_lane_data_on =
    (funct3_on == 3'b000) ? ({24'h0, raw_wdata_on[7:0]} << (8 * addr_on[1:0])) :
    (funct3_on == 3'b001) ? ({16'h0, raw_wdata_on[15:0]} << (8 * addr_on[1:0])) :
                            raw_wdata_on;
wire [3:0] store_strb_off =
    (funct3_off == 3'b000) ? (4'b0001 << addr_off[1:0]) :
    (funct3_off == 3'b001) ? (4'b0011 << addr_off[1:0]) : 4'b1111;
wire [3:0] store_strb_on =
    (funct3_on == 3'b000) ? (4'b0001 << addr_on[1:0]) :
    (funct3_on == 3'b001) ? (4'b0011 << addr_on[1:0]) : 4'b1111;

riscv_core #(.BRANCH_PREDICT_ENABLE(0), .BHT_ENTRIES(256)) dut_off (
    .clk(clk), .reset_n(reset_n), .irq_timer(1'b0),
    .pc_f(pc_off), .instr(instr_off),
    .mem_wr_m(mem_wr_off), .mem_rd_m(mem_rd_off),
    .alu_result_m(addr_off), .wr_data_m(raw_wdata_off),
    .rd_data(dmem_off[addr_off[9:2]]), .mem_funct3_m(funct3_off),
    .stall_pipe(1'b0), .trap_taken(), .mcause_dbg(), .mepc_dbg(),
    .mtvec_dbg(), .mcycle_dbg(), .minstret_dbg(), .load_stall_dbg(),
    .branch_flush_dbg(), .control_redirect_dbg(), .retire_event_dbg(),
    .load_use_stall_event_dbg(), .control_redirect_event_dbg(),
    .mispredict_event_dbg(), .conditional_branch_event_dbg(),
    .branch_taken_event_dbg(), .branch_not_taken_event_dbg(),
    .branch_prediction_event_dbg(), .branch_correct_prediction_event_dbg(),
    .pipeline_nonempty_dbg(),
    .retire_valid(retire_valid_off), .retire_order(retire_order_off),
    .retire_pc(retire_pc_off), .retire_pc_next(retire_pc_next_off),
    .retire_instr(retire_instr_off),
    .retire_rs1_addr(retire_rs1_addr_off), .retire_rs1_rdata(retire_rs1_rdata_off),
    .retire_rs2_addr(retire_rs2_addr_off), .retire_rs2_rdata(retire_rs2_rdata_off),
    .retire_rd_addr(retire_rd_addr_off), .retire_rd_wdata(retire_rd_wdata_off),
    .retire_rd_we(retire_rd_we_off), .retire_mem_valid(retire_mem_valid_off),
    .retire_mem_write(retire_mem_write_off), .retire_mem_addr(retire_mem_addr_off),
    .retire_mem_wdata(retire_mem_wdata_off), .retire_mem_wstrb(retire_mem_wstrb_off),
    .retire_trap(), .retire_interrupt()
);

riscv_core #(.BRANCH_PREDICT_ENABLE(1), .BHT_ENTRIES(256)) dut_on (
    .clk(clk), .reset_n(reset_n), .irq_timer(1'b0),
    .pc_f(pc_on), .instr(instr_on),
    .mem_wr_m(mem_wr_on), .mem_rd_m(mem_rd_on),
    .alu_result_m(addr_on), .wr_data_m(raw_wdata_on),
    .rd_data(dmem_on[addr_on[9:2]]), .mem_funct3_m(funct3_on),
    .stall_pipe(1'b0), .trap_taken(), .mcause_dbg(), .mepc_dbg(),
    .mtvec_dbg(), .mcycle_dbg(), .minstret_dbg(), .load_stall_dbg(),
    .branch_flush_dbg(), .control_redirect_dbg(), .retire_event_dbg(),
    .load_use_stall_event_dbg(), .control_redirect_event_dbg(),
    .mispredict_event_dbg(), .conditional_branch_event_dbg(),
    .branch_taken_event_dbg(), .branch_not_taken_event_dbg(),
    .branch_prediction_event_dbg(), .branch_correct_prediction_event_dbg(),
    .pipeline_nonempty_dbg(),
    .retire_valid(retire_valid_on), .retire_order(retire_order_on),
    .retire_pc(retire_pc_on), .retire_pc_next(retire_pc_next_on),
    .retire_instr(retire_instr_on),
    .retire_rs1_addr(retire_rs1_addr_on), .retire_rs1_rdata(retire_rs1_rdata_on),
    .retire_rs2_addr(retire_rs2_addr_on), .retire_rs2_rdata(retire_rs2_rdata_on),
    .retire_rd_addr(retire_rd_addr_on), .retire_rd_wdata(retire_rd_wdata_on),
    .retire_rd_we(retire_rd_we_on), .retire_mem_valid(retire_mem_valid_on),
    .retire_mem_write(retire_mem_write_on), .retire_mem_addr(retire_mem_addr_on),
    .retire_mem_wdata(retire_mem_wdata_on), .retire_mem_wstrb(retire_mem_wstrb_on),
    .retire_trap(), .retire_interrupt()
);

always #5 clk = ~clk;

task automatic apply_store_off;
    integer index;
begin
    index = addr_off[9:2];
    if(store_strb_off[0]) dmem_off[index][7:0]   <= store_lane_data_off[7:0];
    if(store_strb_off[1]) dmem_off[index][15:8]  <= store_lane_data_off[15:8];
    if(store_strb_off[2]) dmem_off[index][23:16] <= store_lane_data_off[23:16];
    if(store_strb_off[3]) dmem_off[index][31:24] <= store_lane_data_off[31:24];
end
endtask

task automatic apply_store_on;
    integer index;
begin
    index = addr_on[9:2];
    if(store_strb_on[0]) dmem_on[index][7:0]   <= store_lane_data_on[7:0];
    if(store_strb_on[1]) dmem_on[index][15:8]  <= store_lane_data_on[15:8];
    if(store_strb_on[2]) dmem_on[index][23:16] <= store_lane_data_on[23:16];
    if(store_strb_on[3]) dmem_on[index][31:24] <= store_lane_data_on[31:24];
end
endtask

task automatic log_off;
begin
    if(retire_order_off !== expected_order_off)
        $fatal(1, "seed %0d BP_OFF retire order expected %0d got %0d",
               seed, expected_order_off, retire_order_off);
    expected_order_off = expected_order_off + 1;
    if(retire_instr_off == HALT) begin
        done_off <= 1'b1;
    end
    else begin
        if(retire_rs1_rdata_off !== arch_off[retire_rs1_addr_off] ||
           retire_rs2_rdata_off !== arch_off[retire_rs2_addr_off])
            $fatal(1, "seed %0d BP_OFF retirement operand mismatch order=%0d pc=%08x instr=%08x rs1=x%0d trace=%08x shadow=%08x rs2=x%0d trace=%08x shadow=%08x",
                   seed, retire_order_off, retire_pc_off, retire_instr_off,
                   retire_rs1_addr_off, retire_rs1_rdata_off, arch_off[retire_rs1_addr_off],
                   retire_rs2_addr_off, retire_rs2_rdata_off, arch_off[retire_rs2_addr_off]);
        $fdisplay(fd_off, "%0d,%08x,%08x,%0d,%0d,%08x,%0d,%08x,%08x,%x",
                  retire_order_off, retire_pc_off, retire_instr_off,
                  retire_rd_addr_off, retire_rd_we_off, retire_rd_wdata_off,
                  retire_mem_write_off, retire_mem_addr_off,
                  retire_mem_wdata_off, retire_mem_wstrb_off);
        if(retire_rd_we_off) arch_off[retire_rd_addr_off] <= retire_rd_wdata_off;
    end
end
endtask

task automatic log_on;
begin
    if(retire_order_on !== expected_order_on)
        $fatal(1, "seed %0d BP_ON retire order expected %0d got %0d",
               seed, expected_order_on, retire_order_on);
    expected_order_on = expected_order_on + 1;
    if(retire_instr_on == HALT) begin
        done_on <= 1'b1;
    end
    else begin
        if(retire_rs1_rdata_on !== arch_on[retire_rs1_addr_on] ||
           retire_rs2_rdata_on !== arch_on[retire_rs2_addr_on])
            $fatal(1, "seed %0d BP_ON retirement operand mismatch order=%0d pc=%08x instr=%08x rs1=x%0d trace=%08x shadow=%08x rs2=x%0d trace=%08x shadow=%08x",
                   seed, retire_order_on, retire_pc_on, retire_instr_on,
                   retire_rs1_addr_on, retire_rs1_rdata_on, arch_on[retire_rs1_addr_on],
                   retire_rs2_addr_on, retire_rs2_rdata_on, arch_on[retire_rs2_addr_on]);
        $fdisplay(fd_on, "%0d,%08x,%08x,%0d,%0d,%08x,%0d,%08x,%08x,%x",
                  retire_order_on, retire_pc_on, retire_instr_on,
                  retire_rd_addr_on, retire_rd_we_on, retire_rd_wdata_on,
                  retire_mem_write_on, retire_mem_addr_on,
                  retire_mem_wdata_on, retire_mem_wstrb_on);
        if(retire_rd_we_on) arch_on[retire_rd_addr_on] <= retire_rd_wdata_on;
    end
end
endtask

always @(posedge clk) begin
    if(reset_n) begin
        cycle_count <= cycle_count + 1;
        if(mem_wr_off) apply_store_off();
        if(mem_wr_on)  apply_store_on();
        if(retire_valid_off) log_off();
        if(retire_valid_on)  log_on();
        if(cycle_count > max_cycles)
            $fatal(1, "seed %0d random DUT watchdog timeout", seed);
    end
end

initial begin
    clk = 0;
    reset_n = 0;
    done_off = 0;
    done_on = 0;
    cycle_count = 0;
    expected_order_off = 0;
    expected_order_on = 0;
    max_cycles = 20000;
    seed = 0;
    if(!$value$plusargs("HEX=%s", hex_path)) $fatal(1, "missing +HEX");
    if(!$value$plusargs("TRACE_OFF=%s", trace_off_path)) $fatal(1, "missing +TRACE_OFF");
    if(!$value$plusargs("TRACE_ON=%s", trace_on_path)) $fatal(1, "missing +TRACE_ON");
    void'($value$plusargs("MAX_CYCLES=%d", max_cycles));
    void'($value$plusargs("SEED=%d", seed));
    for(i = 0; i < 1024; i = i + 1) imem[i] = NOP;
    for(i = 0; i < 256; i = i + 1) begin
        dmem_off[i] = 0;
        dmem_on[i] = 0;
    end
    for(i = 0; i < 32; i = i + 1) begin
        arch_off[i] = 0;
        arch_on[i] = 0;
        `RF_SET(dut_off.datapath.regfile, i, 0);
        `RF_SET(dut_on.datapath.regfile, i, 0);
    end
    $readmemh(hex_path, imem);
    fd_off = $fopen(trace_off_path, "w");
    fd_on = $fopen(trace_on_path, "w");
    if(fd_off == 0 || fd_on == 0) $fatal(1, "cannot open random trace files");
    $fdisplay(fd_off, "order,pc,instr,rd,we,rd_data,mem_we,mem_addr,mem_wdata,mem_wstrb");
    $fdisplay(fd_on,  "order,pc,instr,rd,we,rd_data,mem_we,mem_addr,mem_wdata,mem_wstrb");
    repeat(4) @(posedge clk);
    @(negedge clk);
    reset_n = 1;
    wait(done_off && done_on);
    #2;
    for(i = 0; i < 32; i = i + 1)
        if(arch_off[i] !== arch_on[i])
            $fatal(1, "seed %0d BP_OFF/BP_ON GPR x%0d mismatch", seed, i);
    for(i = 0; i < 256; i = i + 1)
        if(dmem_off[i] !== dmem_on[i])
            $fatal(1, "seed %0d BP_OFF/BP_ON memory word %0d mismatch", seed, i);
    $fclose(fd_off);
    $fclose(fd_on);
    $display("[PASS] Random retirement traces generated seed=%0d OFF=%0d ON=%0d",
             seed, expected_order_off - 1, expected_order_on - 1);
    $display("[PASS] BP OFF/ON architectural state equivalent seed=%0d", seed);
    $finish;
end

endmodule
