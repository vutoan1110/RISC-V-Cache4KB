`timescale 1ns/1ps

// UVM classes for the hdl/axi/cache_axi_master.v environment. It reuses
// native_mem_model from mem_model_pkg as the memory behind the AXI slave, so
// that package must be compiled first, together with refill_if, wthru_if and
// axi4_if.
package axi_uvm_pkg;

    import uvm_pkg::*;
`include "uvm_macros.svh"

    import mem_model_pkg::*;

    `uvm_analysis_imp_decl(_refill)
    `uvm_analysis_imp_decl(_wthru)
    `uvm_analysis_imp_decl(_axi)

`include "axi_common.sv"
`include "refill_agent.sv"
`include "wthru_agent.sv"
`include "axi_slave_agent.sv"
`include "axi_func_coverage.sv"
`include "axi_scoreboard.sv"
`include "axi_env.sv"

`include "axi_traffic_seq.sv"
`include "axi_base_test.sv"
`include "axi_smoke_test.sv"

endpackage
