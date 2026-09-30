`timescale 1ns/1ps

// Simulation-only pipeline invariants. Retirement trace is the architectural
// reference; control signals are only observed.
module core_assertions #(
    parameter integer BRANCH_PREDICT_ENABLE = 1
) (
    input wire clk,
    input wire reset_n,
    input wire stall_pipe,
    input wire valid_d,
    input wire valid_e,
    input wire valid_m,
    input wire valid_w,
    input wire [31:0] instr_d,
    input wire [31:0] instr_e,
    input wire [31:0] instr_m,
    input wire use_rs1_d,
    input wire use_rs2_d,
    input wire [1:0] result_src_e,
    input wire load_use_hazard,
    input wire stall_f,
    input wire stall_d,
    input wire flush_e,
    input wire [31:0] pc_f,
    input wire [31:0] pc_d,
    input wire [31:0] pc_e,
    input wire pc_src_e,
    input wire is_branch_e,
    input wire branch_taken_e,
    input wire mispredict_e,
    input wire [31:0] pc_target_e,
    input wire [31:0] pc_plus4_e,
    input wire branch_resolve_fire,
    input wire bht_update_en,
    input wire mem_wr_m,
    input wire architectural_reg_write,
    input wire retire_valid,
    input wire [63:0] retire_order,
    input wire [31:0] retire_pc,
    input wire [31:0] retire_instr,
    input wire [4:0] retire_rs1_addr,
    input wire [31:0] retire_rs1_rdata,
    input wire [4:0] retire_rs2_addr,
    input wire [31:0] retire_rs2_rdata,
    input wire retire_rd_we,
    input wire [4:0] retire_rd_addr,
    input wire retire_mem_write,
    input wire [31:0] retire_mem_addr,
    input wire [3:0] retire_mem_wstrb,
    output reg [31:0] assertion_checks
);

reg [63:0] expected_order;
reg load_hold_pending;
reg recovery_pending;
reg flush_pending;
reg [31:0] held_pc_f;
reg [31:0] held_pc_d;
reg [31:0] held_instr_d;
reg [31:0] expected_recovery_pc;

wire expected_load_use = (result_src_e == 2'b01) &&
                         (instr_e[11:7] != 5'd0) &&
                         ((use_rs1_d && (instr_d[19:15] == instr_e[11:7])) ||
                          (use_rs2_d && (instr_d[24:20] == instr_e[11:7])));

always @(negedge clk or negedge reset_n) begin
    if(!reset_n) begin
        load_hold_pending  <= 1'b0;
        recovery_pending   <= 1'b0;
        flush_pending      <= 1'b0;
        held_pc_f          <= 32'h0;
        held_pc_d          <= 32'h0;
        held_instr_d       <= 32'h0;
        expected_recovery_pc <= 32'h0;
    end
    else begin
        load_hold_pending <= load_use_hazard && !stall_pipe;
        recovery_pending  <= mispredict_e && !stall_pipe;
        flush_pending     <= flush_e && !stall_pipe;
        held_pc_f         <= pc_f;
        held_pc_d         <= pc_d;
        held_instr_d      <= instr_d;
        expected_recovery_pc <= branch_taken_e ? pc_target_e : pc_plus4_e;
    end
end

always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        expected_order  = 64'd0;
        assertion_checks = 32'd0;
    end
    else begin
        assertion_checks = assertion_checks + 1'b1;

        if(retire_valid !== (valid_w && !stall_pipe))
            $fatal(1, "retire_valid differs from valid_w && pipeline advance");
        if(architectural_reg_write && !retire_valid)
            $fatal(1, "architectural register write without valid retirement");
        if(retire_rd_we && (!retire_valid || retire_rd_addr == 5'd0))
            $fatal(1, "invalid/x0 architectural register write in trace");
        if(mem_wr_m && (!valid_m || instr_m[6:0] != 7'b0100011))
            $fatal(1, "store side effect without a valid M-stage store");

        if(load_use_hazard !== expected_load_use)
            $fatal(1, "false or missing load-use hazard classification");
        if(load_use_hazard && (!stall_f || !stall_d || !flush_e))
            $fatal(1, "load-use hazard does not hold F/D and bubble E");

        if(branch_resolve_fire !== (is_branch_e && !stall_pipe))
            $fatal(1, "conditional branch resolve pulse is duplicated or missing");
        if(bht_update_en !== ((BRANCH_PREDICT_ENABLE != 0) && branch_resolve_fire))
            $fatal(1, "BHT update is not exactly one enabled branch-resolve pulse");
        if((BRANCH_PREDICT_ENABLE != 0) && is_branch_e && !stall_pipe &&
           !mispredict_e && pc_src_e)
            $fatal(1, "correct conditional prediction generated recovery flush");

        if(retire_valid) begin
            if(retire_order !== expected_order)
                $fatal(1, "retire_order expected %0d got %0d at pc=%08x",
                       expected_order, retire_order, retire_pc);
            expected_order = expected_order + 64'd1;
            if(retire_pc[1:0] != 2'b00)
                $fatal(1, "unaligned retired PC %08x", retire_pc);
            if(retire_rs1_addr == 5'd0 && retire_rs1_rdata != 32'd0)
                $fatal(1, "x0 rs1 read was nonzero");
            if(retire_rs2_addr == 5'd0 && retire_rs2_rdata != 32'd0)
                $fatal(1, "x0 rs2 read was nonzero");
            if(retire_instr == 32'h0000_0000)
                $fatal(1, "invalid/bubble instruction retired");
        end

        if(retire_mem_write) begin
            case(retire_instr[14:12])
                3'b000: if(retire_mem_wstrb !== (4'b0001 << retire_mem_addr[1:0]))
                            $fatal(1, "SB retirement strobe incorrect");
                3'b001: if(retire_mem_wstrb !== (4'b0011 << retire_mem_addr[1:0]))
                            $fatal(1, "SH retirement strobe incorrect");
                3'b010: if(retire_mem_wstrb !== 4'b1111)
                            $fatal(1, "SW retirement strobe incorrect");
                default: $fatal(1, "unsupported store funct3 retired");
            endcase
        end
    end
end

// Sampled at the following edge after pipeline registers update.
always @(posedge clk) begin
    #1;
    if(reset_n && flush_pending && valid_e)
        $fatal(1, "flushed/bubbled decode instruction remained valid in E");
    if(reset_n && load_hold_pending) begin
        if(pc_f !== held_pc_f || pc_d !== held_pc_d || instr_d !== held_instr_d)
            $fatal(1, "load-use hazard failed to hold PC and IF/ID");
        if(valid_e)
            $fatal(1, "load-use hazard failed to insert ID/EX bubble");
    end
    if(reset_n && recovery_pending && pc_f !== expected_recovery_pc)
        $fatal(1, "mispredict recovery PC expected %08x got %08x",
               expected_recovery_pc, pc_f);
end

endmodule
