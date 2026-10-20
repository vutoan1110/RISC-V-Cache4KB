`timescale 1ns/1ps
// Diagnostic probe for both the FPGA view and the ASIC view: reports stores
// whose data is X and the first cycle X enters a valid D-cache L0 line. It
// never stops the run; it only reports, so the two views can be compared.
module x_origin_probe;
`define PSOC tb_benchmark_snapshot.dut
`define PDC  tb_benchmark_snapshot.dut.u_dcache.g_dm_baseline
integer cyc = 0, xstores = 0;
reg hot_x = 1'b0;
always @(posedge `PSOC.clk) begin
    cyc <= cyc + 1;
    if (`PSOC.d_req_valid && `PSOC.d_req_write && ((^`PSOC.d_req_wdata) === 1'bx)) begin
        xstores = xstores + 1;
        if (xstores <= 6)
            $display("[XPROBE] cycle %0d: store of X data to %h (wdata=%h strb=%b)",
                     cyc, `PSOC.d_req_addr, `PSOC.d_req_wdata, `PSOC.d_req_wstrb);
    end
    if (!hot_x && ((`PDC.u_controller.hot_valid[0] && ((^`PDC.u_controller.hot_line0) === 1'bx)) ||
                   (`PDC.u_controller.hot_valid[1] && ((^`PDC.u_controller.hot_line1) === 1'bx)))) begin
        hot_x <= 1'b1;
        $display("[XPROBE] cycle %0d: X first enters a valid D-cache L0 line", cyc);
    end
end
final $display("[XPROBE] stores carrying X data: %0d", xstores);
endmodule
