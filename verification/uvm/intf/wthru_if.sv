`timescale 1ns/1ps

// D-cache write-through channel into cache_axi_master. It is backed by a
// two-entry posted-write buffer: the response comes one cycle
// after the request is accepted and rsp_error is always 0, while the AXI B
// response drains in the background.
interface wthru_if (input logic clk, input logic reset_n);

    logic        req_valid;
    logic [31:0] req_addr;
    logic [31:0] req_data;
    logic [3:0]  req_strb;
    logic        req_ready;
    logic        rsp_valid;
    logic        rsp_error;

    clocking drv_cb @(posedge clk);
        default input #1step output #1ns;
        output req_valid, req_addr, req_data, req_strb;
        input  req_ready, rsp_valid, rsp_error;
    endclocking

    clocking mon_cb @(posedge clk);
        default input #1step;
        input req_valid, req_addr, req_data, req_strb, req_ready;
        input rsp_valid, rsp_error;
    endclocking

    modport initiator (clocking drv_cb, input clk, input reset_n);
    modport passive   (clocking mon_cb, input clk, input reset_n);

endinterface
