`timescale 1ns/1ps

// UVM classes for the hdl/soc_top.v environment. It needs soc_obs_if, apb_if
// and uart_if, and nothing from the other two environments, so a SoC testbench
// does not have to elaborate their interfaces.
package soc_uvm_pkg;

    import uvm_pkg::*;
`include "uvm_macros.svh"

    `uvm_analysis_imp_decl(_retire)
    `uvm_analysis_imp_decl(_apb)

`include "soc_reg_model.sv"
`include "soc_common.sv"
`include "soc_obs_agent.sv"
`include "apb_agent.sv"
`include "uart_agent.sv"
`include "soc_func_coverage.sv"
`include "soc_scoreboard.sv"
`include "soc_env.sv"

`include "soc_base_test.sv"
`include "soc_directed_test.sv"
`include "soc_periph_test.sv"

endpackage
