`timescale 1ns/1ps
// Board-level input synchronisers in the two chip wrappers (NHAT_KY_RTL.md, R8).
//
// uart_rx, key1_n and reset_n come from outside the clock domain. rx_block
// uses rx directly in its FSM next-state logic, so each wrapper has to hand
// soc_top a copy that has been through two flip-flops; reset must be asserted
// asynchronously and released on a clock edge. These wrappers had never been
// simulated before this test: de2_115_top synchronised reset and key1_n but not
// uart_rx, and soc_asic_top synchronised nothing.
//
// Checked for each wrapper, on the signals soc_top actually receives:
//   * while reset_n is low, soc_top's reset is low
//   * after reset_n rises between edges, soc_top's reset rises exactly on the
//     second rising clk edge, never before
//   * uart_rx and key1_n reach soc_top exactly two rising edges after they
//     change, and read 1 (idle / not pressed) straight out of reset
//
// tb_de2_115_top_sync is compiled by tb/compile_active_design.do,
// tb_soc_asic_top_sync by tb/compile_asic_view.do (it needs the SRAM models).

module top_sync_checker #(parameter string NAME = "wrapper") (
    input  logic clk,
    output logic reset_n,
    output logic key1_n,
    output logic uart_rx,
    input  logic soc_reset_n,
    input  logic soc_key1_n,
    input  logic soc_uart_rx
);
    integer errors = 0;

    task automatic check(input logic got, input logic want, input string what);
        if (got !== want) begin
            errors++;
            $display("[FAIL] %s: %s = %b, expected %b (t=%0t)", NAME, what, got, want, $time);
        end
    endtask

    // Drive an input just after a rising edge, then look at soc_top's copy
    // just after each of the next three edges. which: 0 = uart_rx, 1 = key1_n.
    function automatic logic seen(input int which);
        return which == 0 ? soc_uart_rx : soc_key1_n;
    endfunction

    task automatic latency(input string what, input logic value, input int which);
        @(posedge clk); #1;
        if (which == 0) uart_rx = value; else key1_n = value;
        #1 check(seen(which), !value, {what, " before any edge"});
        @(posedge clk); #1 check(seen(which), !value, {what, " one edge after the change"});
        @(posedge clk); #1 check(seen(which), value, {what, " two edges after the change"});
        @(posedge clk); #1 check(seen(which), value, {what, " three edges after the change"});
    endtask

    initial begin
        reset_n = 1'b0; key1_n = 1'b1; uart_rx = 1'b1;
        repeat (3) @(posedge clk);
        #1 check(soc_reset_n, 1'b0, "soc reset while reset_n is low");
        check(soc_uart_rx, 1'b1, "uart_rx in reset (idle high)");
        check(soc_key1_n, 1'b1, "key1_n in reset (not pressed)");

        // Release between edges.
        @(negedge clk) reset_n = 1'b1;
        #1 check(soc_reset_n, 1'b0, "soc reset right after release (no edge yet)");
        @(posedge clk); #1 check(soc_reset_n, 1'b0, "soc reset after the first edge");
        @(posedge clk); #1 check(soc_reset_n, 1'b1, "soc reset after the second edge");

        latency("uart_rx falling", 1'b0, 0);
        latency("uart_rx rising",  1'b1, 0);
        latency("key1_n falling",  1'b0, 1);
        latency("key1_n rising",   1'b1, 1);

        // Asynchronous assertion: no clock edge needed.
        @(negedge clk) reset_n = 1'b0;
        #1 check(soc_reset_n, 1'b0, "soc reset asserts without a clock edge");

        if (errors == 0)
            $display("[PASS] %s: reset synchroniser and uart_rx/key1_n two-flop synchronisers", NAME);
        else
            $display("[FAIL] %s: %0d check(s) failed", NAME, errors);
        $finish;
    end
endmodule

`ifndef ASIC_VIEW_SIM
module tb_de2_115_top_sync;
    logic clk = 0;
    always #10 clk = ~clk;
    logic reset_n, key1_n, uart_rx;
    wire  uart_tx;
    wire [6:0] HEX0, HEX1, HEX2, HEX3, HEX4, HEX5, HEX6, HEX7;
    wire [7:0] LEDR, LCD_DATA;
    wire LCD_EN, LCD_RS, LCD_RW, LCD_ON;

    de2_115_top dut (
        .clk(clk), .reset_n(reset_n), .key1_n(key1_n), .uart_rx(uart_rx),
        .uart_tx(uart_tx), .HEX0(HEX0), .HEX1(HEX1), .HEX2(HEX2), .HEX3(HEX3),
        .HEX4(HEX4), .HEX5(HEX5), .HEX6(HEX6), .HEX7(HEX7), .LEDR(LEDR),
        .LCD_DATA(LCD_DATA), .LCD_EN(LCD_EN), .LCD_RS(LCD_RS), .LCD_RW(LCD_RW),
        .LCD_ON(LCD_ON));

    top_sync_checker #(.NAME("de2_115_top")) chk (
        .clk(clk), .reset_n(reset_n), .key1_n(key1_n), .uart_rx(uart_rx),
        .soc_reset_n(dut.u_soc.reset_n), .soc_key1_n(dut.u_soc.key1_n),
        .soc_uart_rx(dut.u_soc.uart_rx));
endmodule
`else
module tb_soc_asic_top_sync;
    logic clk = 0;
    always #10 clk = ~clk;
    logic reset_n, key1_n, uart_rx;
    wire  uart_tx;
    wire [6:0] HEX0, HEX1, HEX2, HEX3, HEX4, HEX5, HEX6, HEX7;
    wire [7:0] LEDR, LCD_DATA;
    wire LCD_EN, LCD_RS, LCD_RW, LCD_ON, LCD_BLON;

    soc_asic_top dut (
        .clk(clk), .reset_n(reset_n), .key1_n(key1_n), .uart_rx(uart_rx),
        .uart_tx(uart_tx), .HEX0(HEX0), .HEX1(HEX1), .HEX2(HEX2), .HEX3(HEX3),
        .HEX4(HEX4), .HEX5(HEX5), .HEX6(HEX6), .HEX7(HEX7), .LEDR(LEDR),
        .LCD_DATA(LCD_DATA), .LCD_EN(LCD_EN), .LCD_RS(LCD_RS), .LCD_RW(LCD_RW),
        .LCD_ON(LCD_ON), .LCD_BLON(LCD_BLON));

    top_sync_checker #(.NAME("soc_asic_top")) chk (
        .clk(clk), .reset_n(reset_n), .key1_n(key1_n), .uart_rx(uart_rx),
        .soc_reset_n(dut.u_soc.reset_n), .soc_key1_n(dut.u_soc.key1_n),
        .soc_uart_rx(dut.u_soc.uart_rx));
endmodule
`endif
