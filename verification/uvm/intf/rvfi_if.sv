`timescale 1ns/1ps

// Passive retirement (RVFI-style) and observability port of
// riscv_core_native. Nothing in the environment drives these signals.
interface rvfi_if (input logic clk, input logic reset_n);

    // Retirement record.
    logic        retire_valid;
    logic [63:0] retire_order;
    logic [31:0] retire_pc;
    logic [31:0] retire_pc_next;
    logic [31:0] retire_instr;
    logic [4:0]  retire_rs1_addr;
    logic [31:0] retire_rs1_rdata;
    logic [4:0]  retire_rs2_addr;
    logic [31:0] retire_rs2_rdata;
    logic [4:0]  retire_rd_addr;
    logic [31:0] retire_rd_wdata;
    logic        retire_rd_we;
    logic        retire_mem_valid;
    logic        retire_mem_write;
    logic [31:0] retire_mem_addr;
    logic [31:0] retire_mem_wdata;
    logic [3:0]  retire_mem_wstrb;
    logic        retire_trap;
    logic        retire_interrupt;

    // Architectural counters and one-cycle event pulses.
    logic [31:0] mcycle_dbg;
    logic [31:0] minstret_dbg;
    logic        retire_event_dbg;
    logic        load_use_stall_event_dbg;
    logic        control_redirect_event_dbg;
    logic        mispredict_event_dbg;
    logic        conditional_branch_event_dbg;
    logic        branch_taken_event_dbg;
    logic        branch_not_taken_event_dbg;
    logic        branch_prediction_event_dbg;
    logic        branch_correct_prediction_event_dbg;
    logic        pipeline_nonempty_dbg;

    // Sticky native-interface error flags and stall visibility.
    logic        if_wait_dbg;
    logic        d_wait_dbg;
    logic        if_error_dbg;
    logic        d_error_dbg;
    logic        trap_taken;

    clocking mon_cb @(posedge clk);
        default input #1step;
        input retire_valid, retire_order, retire_pc, retire_pc_next,
              retire_instr, retire_rs1_addr, retire_rs1_rdata,
              retire_rs2_addr, retire_rs2_rdata, retire_rd_addr,
              retire_rd_wdata, retire_rd_we, retire_mem_valid,
              retire_mem_write, retire_mem_addr, retire_mem_wdata,
              retire_mem_wstrb, retire_trap, retire_interrupt;
        input mcycle_dbg, minstret_dbg, retire_event_dbg,
              load_use_stall_event_dbg, control_redirect_event_dbg,
              mispredict_event_dbg, conditional_branch_event_dbg,
              branch_taken_event_dbg, branch_not_taken_event_dbg,
              branch_prediction_event_dbg,
              branch_correct_prediction_event_dbg, pipeline_nonempty_dbg;
        input if_wait_dbg, d_wait_dbg, if_error_dbg, d_error_dbg, trap_taken;
    endclocking

    modport passive (clocking mon_cb, input clk, input reset_n);

endinterface
