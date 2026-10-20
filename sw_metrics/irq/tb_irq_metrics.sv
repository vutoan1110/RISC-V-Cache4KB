`timescale 1ns/1ps
// sw_metrics/irq/tb_irq_metrics.sv -- interrupt latency and context-switch monitor (metric
// expansion, 2026-09-30). Runs sw_metrics/irq/irq_bench_rv32.hex on soc_top (FPGA view, same
// parameters as tb_benchmark_snapshot) and timestamps, for every machine-timer interrupt:
//   t0  the timer's irq line rises                         (dut.irq_timer)
//   t1  the core accepts it and redirects fetch to mtvec   (datapath.irq_accept)
//   t2  the first handler instruction retires              (retire_pc == mtvec)
//   t3  the handler's mret retires                         (retire_instr == 0x30200073)
//   t4  the first instruction after mret retires           (the interrupted code resumes)
// and prints one IRQ_SAMPLE line per interrupt with
//   accept = t1-t0, entry = t2-t0, handler = t3-t2, resume = t4-t3, total = t4-t0 (cycles).
// The phase (1..4, see irq_bench.c) is read from DISP_VALUE (0x1A00000p). The run passes only if the
// firmware reports DONE (its transparency and count checks) and every phase has >= 16 samples.
// Simulation only; nothing here is in the RTL manifest.
module tb_irq_metrics #(
    parameter integer CACHE_CONFIG = 0,
    parameter integer ICACHE_LINE_COUNT = 256,
    parameter integer DCACHE_LINE_COUNT = 256,
    parameter integer BRANCH_PREDICT_ENABLE = 1,
    parameter integer L0_ENTRIES = 8,
    parameter MEMFILE = "sw_metrics/irq/irq_bench_rv32.hex"
);
reg clk = 0, reset_n = 0, uart_rx = 1, key1_n = 1;
always #10 clk = ~clk;
wire uart_tx; wire [6:0] HEX0, HEX1, HEX2, HEX3, HEX4, HEX5, HEX6, HEX7;
wire [7:0] LEDR, LCD_DATA; wire LCD_EN, LCD_RS, LCD_RW, LCD_ON, LCD_BLON;
localparam [31:0] DONE_MAGIC = 32'hB16B00B5, FAIL_MAGIC = 32'hDEADFA11;
localparam [31:0] MRET = 32'h30200073;

soc_top #(.CACHE_CONFIG(CACHE_CONFIG), .ICACHE_LINE_COUNT(ICACHE_LINE_COUNT),
          .DCACHE_LINE_COUNT(DCACHE_LINE_COUNT), .VICTIM_ENTRIES(4), .CACHE_LINE_WORDS(4),
          .BRANCH_PREDICT_ENABLE(BRANCH_PREDICT_ENABLE), .L0_ENTRIES(L0_ENTRIES),
          .IMEM_DEPTH(2048), .DMEM_DEPTH(2048), .BHT_ENTRIES(256), .MEMFILE(MEMFILE)) dut (
    .clk(clk), .reset_n(reset_n), .key1_n(key1_n), .uart_rx(uart_rx), .uart_tx(uart_tx),
    .HEX0(HEX0), .HEX1(HEX1), .HEX2(HEX2), .HEX3(HEX3), .HEX4(HEX4), .HEX5(HEX5), .HEX6(HEX6), .HEX7(HEX7),
    .LEDR(LEDR), .LCD_DATA(LCD_DATA), .LCD_EN(LCD_EN), .LCD_RS(LCD_RS), .LCD_RW(LCD_RW),
    .LCD_ON(LCD_ON), .LCD_BLON(LCD_BLON));

wire        irq    = dut.irq_timer;
wire        acc    = dut.u_core.u_pipeline.datapath.irq_accept;
wire [31:0] mtvec  = dut.u_core.u_pipeline.datapath.csr_mtvec;
wire        rv     = dut.retire_valid;
wire [31:0] rpc    = dut.retire_pc;
wire [31:0] rinstr = dut.retire_instr;
wire [31:0] disp   = dut.disp_value;

integer cyc = 0, st = 0, t0 = 0, t1 = 0, t2 = 0, t3 = 0, ph = 0, n = 0;
integer samples [0:4];
reg     irq_q = 1'b0;
initial for (int i = 0; i <= 4; i++) samples[i] = 0;

always @(posedge clk) begin
    cyc   <= cyc + 1;
    irq_q <= irq;
    case (st)
        0: if (irq && !irq_q) begin
               t0 = cyc;
               ph = (disp[31:8] == 24'h1A0000) ? disp[3:0] : 0;
               if (acc) begin t1 = cyc; st = 2; end else st = 1;
           end
        1: if (acc) begin t1 = cyc; st = 2; end
        2: if (rv && rpc == mtvec) begin t2 = cyc; st = 3; end
        3: if (rv && rinstr == MRET) begin t3 = cyc; st = 4; end
        4: if (rv) begin
               n = n + 1;
               if (ph >= 1 && ph <= 4) samples[ph] = samples[ph] + 1;
               $display("IRQ_SAMPLE cfg=%0d phase=%0d n=%0d accept=%0d entry=%0d handler=%0d resume=%0d total=%0d",
                        CACHE_CONFIG, ph, n, t1 - t0, t2 - t0, t3 - t2, cyc - t3, cyc - t0);
               st = 0;
           end
        default: st = 0;
    endcase
end

integer cycles, max_cycles;
initial begin
    cycles = 0;
    if (!$value$plusargs("max_cycles=%d", max_cycles)) max_cycles = 3000000;
    repeat (5) @(posedge clk);
    reset_n = 1;
    while (cycles < max_cycles && dut.disp_ctrl != DONE_MAGIC && dut.disp_ctrl != FAIL_MAGIC) begin
        @(posedge clk);
        cycles = cycles + 1;
    end
    if (cycles >= max_cycles) $fatal(1, "IRQ_METRICS timeout cfg=%0d", CACHE_CONFIG);
    if (dut.disp_ctrl != DONE_MAGIC) $fatal(1, "IRQ_METRICS firmware check failed cfg=%0d (LEDR=%h)", CACHE_CONFIG, LEDR);
    for (int p = 1; p <= 4; p++)
        if (samples[p] < 16) $fatal(1, "IRQ_METRICS phase %0d has only %0d samples", p, samples[p]);
    $display("[PASS] IRQ_METRICS cfg=%0d samples %0d/%0d/%0d/%0d cycles=%0d",
             CACHE_CONFIG, samples[1], samples[2], samples[3], samples[4], cycles);
    $finish;
end
endmodule
