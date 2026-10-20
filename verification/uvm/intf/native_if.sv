`timescale 1ns/1ps

// Native request/response port of riscv_core_native, used for both the
// instruction and the data side.
//
// Protocol (docs/reference/01_RTL_ARCHITECTURE.md section 2):
//   - a request is taken on a clock edge where req_valid && req_ready;
//   - the response has no ready: rsp_valid is a one-cycle pulse that the core
//     consumes immediately;
//   - one request outstanding at a time;
//   - while req_ready is low the requester holds the whole payload stable.
//
// req_write/req_wdata/req_wstrb are tied off by the testbench on the
// instruction port.
interface native_if (input logic clk, input logic reset_n);

    logic        req_valid;
    logic [31:0] req_addr;
    logic        req_write;
    logic [31:0] req_wdata;
    logic [3:0]  req_wstrb;
    logic        req_ready;
    logic        rsp_valid;
    logic [31:0] rsp_rdata;
    logic        rsp_error;

    // The responder drives after the edge, so the core always samples a
    // registered value. This mirrors tb/native_interface_tb.sv.
    clocking rsp_cb @(posedge clk);
        default input #1step output #1ns;
        input  req_valid, req_addr, req_write, req_wdata, req_wstrb;
        output req_ready, rsp_valid, rsp_rdata, rsp_error;
    endclocking

    clocking mon_cb @(posedge clk);
        default input #1step;
        input req_valid, req_addr, req_write, req_wdata, req_wstrb;
        input req_ready, rsp_valid, rsp_rdata, rsp_error;
    endclocking

    modport responder (clocking rsp_cb, input clk, input reset_n);
    modport passive   (clocking mon_cb, input clk, input reset_n);

endinterface
