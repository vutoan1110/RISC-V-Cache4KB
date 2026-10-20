`timescale 1ns/1ps

// Passive observation of soc_top: the retirement record plus the whole
// performance counter bank. Nothing here is driven by the environment; the
// testbench connects every signal with continuous assignments from the DUT
// hierarchy, the same way tb/directed_isa_tb.sv reaches into it.
interface soc_obs_if (input logic clk, input logic reset_n);

    // Retirement record.
    logic        retire_valid;
    logic [63:0] retire_order;
    logic [31:0] retire_pc;
    logic [31:0] retire_pc_next;
    logic [31:0] retire_instr;
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

    // Cycle classifier, one-hot by contract.
    logic [8:0]  cycle_reason_onehot;
    logic [31:0] mcycle_count;
    logic [31:0] minstret_count;
    logic [31:0] retire_cycle_count;
    logic [31:0] load_use_cycle_count;
    logic [31:0] icache_wait_cycle_count;
    logic [31:0] dcache_wait_cycle_count;
    logic [31:0] control_redirect_cycle_count;
    logic [31:0] trap_redirect_cycle_count;
    logic [31:0] mmio_wait_cycle_count;
    logic [31:0] pipe_fill_drain_cycle_count;
    logic [31:0] other_cycle_count;

    // Cache accounting.
    logic [31:0] icache_access_count;
    logic [31:0] icache_hit_count;
    logic [31:0] icache_miss_count;
    logic [31:0] icache_main_hit_count;
    logic [31:0] icache_victim_hit_count;
    logic [31:0] icache_true_miss_count;
    logic [31:0] dcache_access_count;
    logic [31:0] dcache_read_count;
    logic [31:0] dcache_write_count;
    logic [31:0] dcache_read_hit_count;
    logic [31:0] dcache_read_miss_count;
    logic [31:0] dcache_write_hit_count;
    logic [31:0] dcache_write_miss_count;
    logic [31:0] dcache_main_hit_count;
    logic [31:0] dcache_victim_hit_count;
    logic [31:0] dcache_true_miss_count;

    // Branch and prediction events.
    logic [31:0] conditional_branch_count;
    logic [31:0] branch_taken_count;
    logic [31:0] branch_not_taken_count;
    logic [31:0] branch_prediction_count;
    logic [31:0] branch_correct_prediction_count;
    logic [31:0] mispredict_event_count;

    // Bus activity.
    logic [31:0] apb_transfer_count;
    logic        irq_timer;
    logic        trap_taken;      // irq_accept, may fire on a cycle with no retirement

    clocking mon_cb @(posedge clk);
        default input #1step;
        input retire_valid, retire_order, retire_pc, retire_pc_next, retire_instr,
              retire_rd_addr, retire_rd_wdata, retire_rd_we, retire_mem_valid,
              retire_mem_write, retire_mem_addr, retire_mem_wdata,
              retire_mem_wstrb, retire_trap, retire_interrupt;
        input cycle_reason_onehot, mcycle_count, minstret_count,
              retire_cycle_count, load_use_cycle_count, icache_wait_cycle_count,
              dcache_wait_cycle_count, control_redirect_cycle_count,
              trap_redirect_cycle_count, mmio_wait_cycle_count,
              pipe_fill_drain_cycle_count, other_cycle_count;
        input icache_access_count, icache_hit_count, icache_miss_count,
              icache_main_hit_count, icache_victim_hit_count, icache_true_miss_count,
              dcache_access_count, dcache_read_count, dcache_write_count,
              dcache_read_hit_count, dcache_read_miss_count,
              dcache_write_hit_count, dcache_write_miss_count,
              dcache_main_hit_count, dcache_victim_hit_count, dcache_true_miss_count;
        input conditional_branch_count, branch_taken_count, branch_not_taken_count,
              branch_prediction_count, branch_correct_prediction_count,
              mispredict_event_count;
        input apb_transfer_count, irq_timer, trap_taken;
    endclocking

    modport passive (clocking mon_cb, input clk, input reset_n);

endinterface
