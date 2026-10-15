`timescale 1ns/1ps
// sw_metrics/conflict/tb_conflict_probe.sv -- runs the extended conflict probe (conflict_probe.c) on soc_top (FPGA
// view, same parameters as tb_benchmark_snapshot) and prints one CPROBE_WINDOW line per frozen sysmon snapshot,
// labelled with the experiment id the firmware wrote to DISP_VALUE (0xC90000id). +trace=<file> also writes the
// D-cache access trace of tb_benchmark_snapshot (one cycle late, with the counting gate the counters saw, MARK CLEAR
// at every window), which sw_metrics/conflict/model_windows.py replays through the independent cache model.
// Simulation only; nothing here is in the RTL manifest.
module tb_conflict_probe #(
    parameter integer CACHE_CONFIG = 0,
    parameter integer ICACHE_LINE_COUNT = 256,
    parameter integer DCACHE_LINE_COUNT = 256,
    parameter integer BRANCH_PREDICT_ENABLE = 1,
    parameter integer L0_ENTRIES = 8,
    parameter MEMFILE = "sw_metrics/conflict/conflict_probe_4k_rv32.hex"
);
reg clk = 0, reset_n = 0, uart_rx = 1, key1_n = 1;
always #10 clk = ~clk;
wire uart_tx; wire [6:0] HEX0, HEX1, HEX2, HEX3, HEX4, HEX5, HEX6, HEX7;
wire [7:0] LEDR, LCD_DATA; wire LCD_EN, LCD_RS, LCD_RW, LCD_ON, LCD_BLON;
localparam [31:0] DONE_MAGIC = 32'hB16B00B5, FAIL_MAGIC = 32'hDEADFA11;

soc_top #(.CACHE_CONFIG(CACHE_CONFIG), .ICACHE_LINE_COUNT(ICACHE_LINE_COUNT),
          .DCACHE_LINE_COUNT(DCACHE_LINE_COUNT), .VICTIM_ENTRIES(4), .CACHE_LINE_WORDS(4),
          .BRANCH_PREDICT_ENABLE(BRANCH_PREDICT_ENABLE), .L0_ENTRIES(L0_ENTRIES),
          .IMEM_DEPTH(2048), .DMEM_DEPTH(2048), .BHT_ENTRIES(256), .MEMFILE(MEMFILE)) dut (
    .clk(clk), .reset_n(reset_n), .key1_n(key1_n), .uart_rx(uart_rx), .uart_tx(uart_tx),
    .HEX0(HEX0), .HEX1(HEX1), .HEX2(HEX2), .HEX3(HEX3), .HEX4(HEX4), .HEX5(HEX5), .HEX6(HEX6), .HEX7(HEX7),
    .LEDR(LEDR), .LCD_DATA(LCD_DATA), .LCD_EN(LCD_EN), .LCD_RS(LCD_RS), .LCD_RW(LCD_RW),
    .LCD_ON(LCD_ON), .LCD_BLON(LCD_BLON));

// D-cache access trace, exactly as tb_benchmark_snapshot writes it
integer trace_fd = 0;
reg [8*256-1:0] trace_path;
initial if ($value$plusargs("trace=%s", trace_path)) trace_fd = $fopen(trace_path, "w");
reg        d_fire_q = 1'b0, d_wr_q = 1'b0;
reg [31:0] d_addr_q = 32'h0;
wire trace_gate = !dut.u_observability.counter_freeze && !dut.u_observability.counter_clear;
always @(posedge clk) if (trace_fd != 0) begin
    if (d_fire_q) $fdisplay(trace_fd, "D %08x %0d %0d", d_addr_q, d_wr_q, trace_gate ? 1 : 0);
    if (dut.u_observability.counter_clear) $fdisplay(trace_fd, "MARK CLEAR");
    d_fire_q <= dut.u_dcache.req_valid && dut.u_dcache.req_ready;
    d_addr_q <= dut.u_dcache.req_addr;
    d_wr_q   <= dut.u_dcache.req_write;
end

`define SM dut.u_observability.u_sysmon
integer cycles = 0, max_cycles, windows = 0;
reg [31:0] seq_q = 32'h0;
always @(posedge clk) begin
    if (reset_n && `SM.snapshot_sequence_q !== seq_q) begin
        seq_q <= `SM.snapshot_sequence_q;
        windows = windows + 1;
        if (`SM.snap_dcache_read_access + `SM.snap_dcache_write_access !==
            `SM.snap_dcache_main_hit + `SM.snap_dcache_victim_hit + `SM.snap_dcache_true_miss)
            $fatal(1, "D-cache invariant failed in window %0d", windows);
        $display("CPROBE_WINDOW config=%0d lines=%0d id=%0d d_read=%0d d_write=%0d d_main=%0d d_victim=%0d d_miss=%0d d_rd_hit=%0d d_rd_miss=%0d d_wr_hit=%0d d_wr_miss=%0d axi_read=%0d axi_write=%0d mcycle=%0d minstret=%0d",
                 CACHE_CONFIG, DCACHE_LINE_COUNT, dut.disp_value[7:0],
                 `SM.snap_dcache_read_access, `SM.snap_dcache_write_access, `SM.snap_dcache_main_hit,
                 `SM.snap_dcache_victim_hit, `SM.snap_dcache_true_miss, `SM.snap_dcache_read_hit,
                 `SM.snap_dcache_read_miss, `SM.snap_dcache_write_hit, `SM.snap_dcache_write_miss,
                 `SM.snap_axi_read_txn, `SM.snap_axi_write_txn, `SM.snap_mcycle, `SM.snap_minstret);
    end
end

initial begin
    if (!$value$plusargs("max_cycles=%d", max_cycles)) max_cycles = 20000000;
    repeat (5) @(posedge clk);
    reset_n = 1;
    while (cycles < max_cycles && dut.disp_ctrl != DONE_MAGIC && dut.disp_ctrl != FAIL_MAGIC) begin
        @(posedge clk);
        cycles = cycles + 1;
    end
    repeat (2) @(posedge clk);
    if (trace_fd != 0) $fclose(trace_fd);
    if (cycles >= max_cycles) $fatal(1, "FAIL_TIMEOUT conflict probe cfg=%0d", CACHE_CONFIG);
    if (dut.disp_ctrl != DONE_MAGIC) $fatal(1, "conflict probe firmware reported FAIL cfg=%0d", CACHE_CONFIG);
    $display("[PASS] CPROBE config=%0d lines=%0d windows=%0d cycles=%0d", CACHE_CONFIG, DCACHE_LINE_COUNT, windows,
             cycles);
    $finish;
end
endmodule
