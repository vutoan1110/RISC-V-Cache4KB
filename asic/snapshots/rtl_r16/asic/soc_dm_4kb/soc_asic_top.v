// ASIC top-level wrapper for the full SoC (core + DM/SA2/DM_VC4 caches +
// AXI4 + AXI4-Lite/APB + UART/timer/display + performance counters),
// backed by real Sky130 SRAM hard macros instead of the FPGA-side
// behavioral RAM array.
//
// Follows the exact same pattern as the already-proven
// asic/openlane2/core/riscv_core_asic_top.v: a thin pass-through wrapper
// around one already-verified module (there: riscv_core_native; here:
// hdl/soc_top.v itself. The macro-backed memories are supplied by module
// name: axi_ram_32_asic_macro.v defines axi_ram_32, cache_data_ram_sram4.v
// defines icache_data_ram and dcache_data_ram).
//
// STATUS: structurally complete, NOT YET RUN through Yosys/OpenLane in
// this session (see chat response for what has and has not been
// attempted). CACHE_CONFIG is fixed at elaboration time to DM (0); a
// separate hardened build is required per cache config, exactly like the
// three separate FPGA .qpf/.qsf projects (soc_top_de2_115_dm/sa2/dm_vc4).
module soc_asic_top (
    input  wire        clk,
    input  wire        reset_n,
    input  wire        key1_n,
    input  wire        uart_rx,
    output wire        uart_tx,

    output wire [6:0]  HEX0,
    output wire [6:0]  HEX1,
    output wire [6:0]  HEX2,
    output wire [6:0]  HEX3,
    output wire [6:0]  HEX4,
    output wire [6:0]  HEX5,
    output wire [6:0]  HEX6,
    output wire [6:0]  HEX7,
    output wire [7:0]  LEDR,

    output wire [7:0]  LCD_DATA,
    output wire        LCD_EN,
    output wire        LCD_RS,
    output wire        LCD_RW,
    output wire        LCD_ON,
    output wire        LCD_BLON
);

// Board-level inputs are asynchronous to clk (NHAT_KY_RTL.md, R8). This used to
// pass all three straight to soc_top: reset was released asynchronously, and
// rx_block used an unsynchronised uart_rx in its FSM next-state logic. The
// same synchronisers as hdl/board/de2_115_top.v, so both builds see identical
// inputs.

// reset_n: asserted asynchronously, released on the second rising edge.
// The two stages are separate registers, not one 2-bit vector: the second
// stage drives every other flop's asynchronous reset, and a vector whose bit 0
// is synchronous data for bit 1 is one signal used both ways (Verilator
// SYNCASYNCNET). Same two flops, same behaviour.
reg reset_meta_q;
reg reset_sync_q;

always @(posedge clk or negedge reset_n) begin
    if (!reset_n) begin
        reset_meta_q <= 1'b0;
        reset_sync_q <= 1'b0;
    end else begin
        reset_meta_q <= 1'b1;
        reset_sync_q <= reset_meta_q;
    end
end

wire soc_reset_n = reset_sync_q;

// key1_n: 2-flop synchroniser; reads 1 (not pressed) out of reset.
reg [1:0] key1_sync_q;

always @(posedge clk or negedge soc_reset_n) begin
    if (!soc_reset_n)
        key1_sync_q <= 2'b11;
    else
        key1_sync_q <= {key1_sync_q[0], key1_n};
end

wire soc_key1_n = key1_sync_q[1];

// uart_rx: 2-flop synchroniser; reads 1 (line idle) out of reset.
reg [1:0] uart_rx_sync_q;

always @(posedge clk or negedge soc_reset_n) begin
    if (!soc_reset_n)
        uart_rx_sync_q <= 2'b11;
    else
        uart_rx_sync_q <= {uart_rx_sync_q[0], uart_rx};
end

wire soc_uart_rx = uart_rx_sync_q[1];

soc_top #(
    // 4 KiB caches: 256 lines x 16 bytes. INDEX_WIDTH and TAG_WIDTH are
    // derived inside icache.v/dcache.v, so this is the only knob.
    .ICACHE_LINE_COUNT     (256),
    .DCACHE_LINE_COUNT     (256),
    .ICACHE_MISS_PENALTY   (2),
    .DCACHE_MISS_PENALTY   (2),
    .IMEM_DEPTH            (2048),   // R14 2026-09-29: 16 KiB unified RAM, was 1024+1024 words (RAM16K_CHANGES.md)
    .DMEM_DEPTH            (2048),
    .MEMFILE               ("riscv_full.hex"),
    .BRANCH_PREDICT_ENABLE (1),
    .BHT_ENTRIES           (256),
    .CACHE_CONFIG          (0),   // 0 = frozen baseline; ASIC control point
                                  // for the other two configs -- see note
                                  // above.
    .VICTIM_ENTRIES        (4),
    // Stated rather than inherited from defaults, so the ASIC build cannot
    // silently differ from the FPGA configuration it is compared against.
    .CACHE_LINE_WORDS      (4),
    .PERF_COUNTERS_ENABLE  (1),
    .L0_ENTRIES            (8)
) u_soc (
    .clk      (clk),
    .reset_n  (soc_reset_n),
    .key1_n   (soc_key1_n),
    .uart_rx  (soc_uart_rx),
    .uart_tx  (uart_tx),
    .HEX0     (HEX0),
    .HEX1     (HEX1),
    .HEX2     (HEX2),
    .HEX3     (HEX3),
    .HEX4     (HEX4),
    .HEX5     (HEX5),
    .HEX6     (HEX6),
    .HEX7     (HEX7),
    .LEDR     (LEDR),
    .LCD_DATA (LCD_DATA),
    .LCD_EN   (LCD_EN),
    .LCD_RS   (LCD_RS),
    .LCD_RW   (LCD_RW),
    .LCD_ON   (LCD_ON),
    .LCD_BLON (LCD_BLON)
);

endmodule
