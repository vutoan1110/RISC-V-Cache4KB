`timescale 1ns/1ps
// ASIC view only: R-channel statistics of the macro-backed main memory.
// Counts beats accepted with X data, and whether each one had been held under
// backpressure (rvalid high, rready low) before being accepted.
module ram_r_probe;
`define RR tb_benchmark_snapshot.dut.u_axi_ram
integer beats = 0, xbeats = 0, xafter_wait = 0, waited_beats = 0;
reg waited = 1'b0;
always @(posedge `RR.clk) begin
    if (`RR.s_axi_rvalid && !`RR.s_axi_rready) waited <= 1'b1;
    if (`RR.s_axi_rvalid && `RR.s_axi_rready) begin
        beats = beats + 1;
        if (waited) waited_beats = waited_beats + 1;
        if ((^`RR.s_axi_rdata) === 1'bx) begin
            xbeats = xbeats + 1;
            if (waited) xafter_wait = xafter_wait + 1;
        end
        waited <= 1'b0;
    end
end
final $display("[RPROBE] beats=%0d held_under_backpressure=%0d X_beats=%0d X_beats_that_were_held=%0d",
               beats, waited_beats, xbeats, xafter_wait);
endmodule
