`timescale 1ns/1ps

// Native refill channel into cache_axi_master: one address request, four
// response beats with rsp_last on the fourth. Used for both the I-cache and
// the D-cache refill port. The agent is the initiator, so it drives the
// request side and observes the response.
interface refill_if (input logic clk, input logic reset_n);

    logic        req_valid;
    logic [31:0] req_addr;
    logic        req_ready;
    logic        rsp_valid;
    logic [31:0] rsp_data;
    logic        rsp_last;
    logic        rsp_error;

    clocking drv_cb @(posedge clk);
        default input #1step output #1ns;
        output req_valid, req_addr;
        input  req_ready, rsp_valid, rsp_data, rsp_last, rsp_error;
    endclocking

    clocking mon_cb @(posedge clk);
        default input #1step;
        input req_valid, req_addr, req_ready;
        input rsp_valid, rsp_data, rsp_last, rsp_error;
    endclocking

    modport initiator (clocking drv_cb, input clk, input reset_n);
    modport passive   (clocking mon_cb, input clk, input reset_n);

endinterface
