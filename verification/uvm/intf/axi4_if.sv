`timescale 1ns/1ps

// AXI4 subset driven by cache_axi_master: reads are one 4-beat 32-bit INCR
// burst with ID 0, writes are a single beat. The agent is the slave.
interface axi4_if (input logic clk, input logic reset_n);

    logic [31:0] araddr;
    logic [7:0]  arlen;
    logic [2:0]  arsize;
    logic [1:0]  arburst;
    logic        arvalid;
    logic        arready;

    logic [31:0] rdata;
    logic [1:0]  rresp;
    logic        rlast;
    logic        rvalid;
    logic        rready;

    logic [31:0] awaddr;
    logic [7:0]  awlen;
    logic [2:0]  awsize;
    logic [1:0]  awburst;
    logic        awvalid;
    logic        awready;

    logic [31:0] wdata;
    logic [3:0]  wstrb;
    logic        wlast;
    logic        wvalid;
    logic        wready;

    logic [1:0]  bresp;
    logic        bvalid;
    logic        bready;

    clocking slv_cb @(posedge clk);
        default input #1step output #1ns;
        input  araddr, arlen, arsize, arburst, arvalid, rready;
        input  awaddr, awlen, awsize, awburst, awvalid;
        input  wdata, wstrb, wlast, wvalid, bready;
        output arready, rdata, rresp, rlast, rvalid;
        output awready, wready, bresp, bvalid;
    endclocking

    clocking mon_cb @(posedge clk);
        default input #1step;
        input araddr, arlen, arsize, arburst, arvalid, arready;
        input rdata, rresp, rlast, rvalid, rready;
        input awaddr, awlen, awsize, awburst, awvalid, awready;
        input wdata, wstrb, wlast, wvalid, wready;
        input bresp, bvalid, bready;
    endclocking

    modport slave   (clocking slv_cb, input clk, input reset_n);
    modport passive (clocking mon_cb, input clk, input reset_n);

endinterface
