// DE2-115 board wrapper: 50 MHz clock, KEY0/KEY1, RS-232 UART, LEDR[7:0],
// HEX0..7, and the character LCD are pins. LCD_BLON stays internal (the
// fitted module has no controllable backlight).
module de2_115_top #(
    parameter integer ICACHE_LINE_COUNT       = 64,
    parameter integer DCACHE_LINE_COUNT       = 64,
    parameter integer ICACHE_MISS_PENALTY     = 2,
    parameter integer DCACHE_MISS_PENALTY     = 2,
    parameter integer IMEM_DEPTH              = 2048,  // R14 2026-09-29: 16 KiB unified RAM, was 1024+1024 words (RAM16K_CHANGES.md)
    parameter integer DMEM_DEPTH              = 2048,
    parameter         MEMFILE                 = "riscv_full.hex",
    parameter integer BRANCH_PREDICT_ENABLE   = 1,
    parameter integer BHT_ENTRIES             = 256,
    parameter integer CACHE_CONFIG            = 1,
    parameter integer VICTIM_ENTRIES          = 4,
    parameter integer CACHE_LINE_WORDS        = 4,
    // R16 (review M1): see soc_top.v
    parameter integer CACHE_FAST_HIT          = 0,
    // 1 builds the performance counter bank; 0 removes it so the core's own
    // area can be quoted apart from the instrumentation's.
    parameter integer PERF_COUNTERS_ENABLE    = 1,
    parameter integer L0_ENTRIES              = 8
) (
    input  wire       clk,
    input  wire       reset_n,
    input  wire       key1_n,
    input  wire       uart_rx,
    output wire       uart_tx,
    output wire [7:0] LEDR,
    output wire [6:0] HEX0,
    output wire [6:0] HEX1,
    output wire [6:0] HEX2,
    output wire [6:0] HEX3,
    output wire [6:0] HEX4,
    output wire [6:0] HEX5,
    output wire [6:0] HEX6,
    output wire [6:0] HEX7,
    output wire [7:0] LCD_DATA,
    output wire       LCD_EN,
    output wire       LCD_RS,
    output wire       LCD_RW,
    output wire       LCD_ON
);

// KEY0 = async reset; release is synchronized (2 flops) before the SoC sees it.
(* altera_attribute = "-name SYNCHRONIZER_IDENTIFICATION FORCED" *)
reg [1:0] reset_sync_q;

always @(posedge clk or negedge reset_n) begin
    if (!reset_n)
        reset_sync_q <= 2'b00;
    else
        reset_sync_q <= {reset_sync_q[0], 1'b1};
end

wire soc_reset_n = reset_sync_q[1];

// KEY1 -> 2-flop synchronizer; firmware reads it as a level (no debounce).
(* altera_attribute = "-name SYNCHRONIZER_IDENTIFICATION FORCED" *)
reg [1:0] key1_sync_q;

always @(posedge clk or negedge soc_reset_n) begin
    if (!soc_reset_n)
        key1_sync_q <= 2'b11;
    else
        key1_sync_q <= {key1_sync_q[0], key1_n};
end

wire soc_key1_n = key1_sync_q[1];

// UART RX -> 2-flop synchronizer. rx_block uses rx directly in its FSM
// next-state logic, so an unsynchronised edge could be seen differently by
// different state bits. Resets to 1, the idle level of the line.
(* altera_attribute = "-name SYNCHRONIZER_IDENTIFICATION FORCED" *)
reg [1:0] uart_rx_sync_q;

always @(posedge clk or negedge soc_reset_n) begin
    if (!soc_reset_n)
        uart_rx_sync_q <= 2'b11;
    else
        uart_rx_sync_q <= {uart_rx_sync_q[0], uart_rx};
end

wire soc_uart_rx = uart_rx_sync_q[1];

wire       unused_lcd_blon;

soc_top #(
    .ICACHE_LINE_COUNT      (ICACHE_LINE_COUNT),
    .DCACHE_LINE_COUNT      (DCACHE_LINE_COUNT),
    .ICACHE_MISS_PENALTY    (ICACHE_MISS_PENALTY),
    .DCACHE_MISS_PENALTY    (DCACHE_MISS_PENALTY),
    .IMEM_DEPTH             (IMEM_DEPTH),
    .DMEM_DEPTH             (DMEM_DEPTH),
    .MEMFILE                (MEMFILE),
    .BRANCH_PREDICT_ENABLE  (BRANCH_PREDICT_ENABLE),
    .BHT_ENTRIES            (BHT_ENTRIES),
    .CACHE_CONFIG           (CACHE_CONFIG),
    .VICTIM_ENTRIES         (VICTIM_ENTRIES),
    .CACHE_LINE_WORDS       (CACHE_LINE_WORDS),
    .CACHE_FAST_HIT         (CACHE_FAST_HIT),
    .PERF_COUNTERS_ENABLE   (PERF_COUNTERS_ENABLE),
    .L0_ENTRIES             (L0_ENTRIES)
) u_soc (
    .clk       (clk),
    .reset_n   (soc_reset_n),
    .key1_n    (soc_key1_n),
    .uart_rx   (soc_uart_rx),
    .uart_tx   (uart_tx),
    .HEX0      (HEX0),
    .HEX1      (HEX1),
    .HEX2      (HEX2),
    .HEX3      (HEX3),
    .HEX4      (HEX4),
    .HEX5      (HEX5),
    .HEX6      (HEX6),
    .HEX7      (HEX7),
    .LEDR      (LEDR),
    .LCD_DATA  (LCD_DATA),
    .LCD_EN    (LCD_EN),
    .LCD_RS    (LCD_RS),
    .LCD_RW    (LCD_RW),
    .LCD_ON    (LCD_ON),
    .LCD_BLON  (unused_lcd_blon)
);

endmodule
