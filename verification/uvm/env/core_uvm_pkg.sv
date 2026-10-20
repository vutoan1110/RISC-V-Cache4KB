`timescale 1ns/1ps

// All UVM classes of the core environment. The two interfaces in
// verification/uvm/intf must be compiled before this package.
package core_uvm_pkg;

    import uvm_pkg::*;
`include "uvm_macros.svh"

    import mem_model_pkg::*;

    // One scoreboard subscribes to three different analysis sources.
    `uvm_analysis_imp_decl(_imem)
    `uvm_analysis_imp_decl(_dmem)
    `uvm_analysis_imp_decl(_rvfi)

    // Configuration and shared state.
`include "core_stats.sv"
`include "rv32_iss.sv"
`include "core_cfg.sv"

    // Native port agent.
`include "native_mem_item.sv"
`include "native_mem_sequencer.sv"
`include "native_mem_driver.sv"
`include "native_mem_monitor.sv"
`include "native_mem_agent.sv"

    // Retirement agent.
`include "rvfi_item.sv"
`include "rvfi_monitor.sv"
`include "rvfi_agent.sv"

    // Checking and assembly.
`include "core_func_coverage.sv"
`include "core_scoreboard.sv"
`include "core_env.sv"

    // Stimulus and tests.
`include "mem_backdoor.sv"
`include "rv32_instr_item.sv"
`include "rv32_program_gen.sv"
`include "program_seq.sv"
`include "core_base_test.sv"
`include "core_smoke_test.sv"
`include "core_random_test.sv"

endpackage
