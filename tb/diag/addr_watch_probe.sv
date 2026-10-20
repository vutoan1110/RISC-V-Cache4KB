`timescale 1ns/1ps
// Watches every CPU data access to one word (+watch_addr) and reports the
// request, the cache response, and the D-cache state, in either view.
// Diagnostic only.
module addr_watch_probe;
`define WSOC tb_benchmark_snapshot.dut
`define WDC  tb_benchmark_snapshot.dut.u_dcache.g_dm_baseline
reg [31:0] watch;
integer cyc = 0, hits = 0;
reg pending = 1'b0;
initial if (!$value$plusargs("watch_addr=%h", watch)) watch = 32'h0000_0c74;
always @(posedge `WSOC.clk) begin
    cyc <= cyc + 1;
    // The D-cache is blocking: a request accepted in ST_IDLE is answered in the
    // same cycle on an L0 hit, otherwise by the next rsp_valid.
    if (`WSOC.dcache_cpu_req_valid && `WDC.u_controller.req_ready &&
        (`WSOC.d_req_addr[31:2] == watch[31:2])) begin
        hits = hits + 1;
        if (`WSOC.dcache_rsp_valid) begin
            if (hits <= 16)
                $display("[WATCH] c%0d %s addr=%h wdata=%h -> FAST(L0) rdata=%h  hot0=%h hot1=%h",
                         cyc, `WSOC.d_req_write ? "ST" : "LD", `WSOC.d_req_addr, `WSOC.d_req_wdata,
                         `WSOC.dcache_rsp_rdata, `WDC.u_controller.hot_line0, `WDC.u_controller.hot_line1);
        end else begin
            pending <= 1'b1;
            if (hits <= 16)
                $display("[WATCH] c%0d %s addr=%h wdata=%h -> slow path", cyc,
                         `WSOC.d_req_write ? "ST" : "LD", `WSOC.d_req_addr, `WSOC.d_req_wdata);
        end
    end else if (pending && `WSOC.dcache_rsp_valid) begin
        if (hits <= 16)
            $display("[WATCH] c%0d   slow rsp rdata=%h (state %0d)", cyc, `WSOC.dcache_rsp_rdata,
                     `WDC.u_controller.state);
        pending <= 1'b0;
    end
end
endmodule
