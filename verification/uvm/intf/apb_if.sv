`timescale 1ns/1ps

// Passive view of the internal APB bus of soc_top. The CPU is the only master
// through the AXI-Lite bridge, so the environment observes this bus rather
// than driving it; the register model is updated by explicit prediction from
// what the CPU actually does.
interface apb_if (input logic clk, input logic reset_n);

    logic        psel;
    logic        penable;
    logic        pwrite;
    logic [3:0]  pstrb;
    logic [31:0] paddr;
    logic [31:0] pwdata;
    logic [31:0] prdata;
    logic        pready;
    logic        pslverr;

    clocking mon_cb @(posedge clk);
        default input #1step;
        input psel, penable, pwrite, pstrb, paddr, pwdata, prdata, pready, pslverr;
    endclocking

    modport passive (clocking mon_cb, input clk, input reset_n);

endinterface
