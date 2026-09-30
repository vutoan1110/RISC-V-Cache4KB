`timescale 1ns/1ps

module tb_mmio_bypass;

reg clk;
reg reset_n;
reg key1_n;
reg uart_rx;

wire uart_tx;
wire [6:0] HEX0, HEX1, HEX2, HEX3, HEX4, HEX5, HEX6, HEX7;
wire [7:0] LEDR;
wire [7:0] LCD_DATA;
wire LCD_EN, LCD_RS, LCD_RW, LCD_ON, LCD_BLON;

integer watchdog;
integer errors;
reg test_pass;
reg saw_uart_apb;
reg saw_cache_request;

soc_top #(
    .ICACHE_LINE_COUNT   (8),
    .DCACHE_LINE_COUNT   (64),
    .ICACHE_MISS_PENALTY (1),
    .DCACHE_MISS_PENALTY (1),
    .IMEM_DEPTH          (1024),
    .DMEM_DEPTH          (64),
    .MEMFILE             ("hdl/riscv_full.hex")
) dut (
    .clk      (clk),
    .reset_n  (reset_n),
    .key1_n   (key1_n),
    .uart_rx  (uart_rx),
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

always #5 clk = ~clk;

always @(posedge clk) begin
    if(reset_n) begin
        if(dut.PSEL_bus && dut.apb_sel_uart)
            saw_uart_apb <= 1'b1;
        if(dut.u_dcache.req_valid)
            saw_cache_request <= 1'b1;
    end
end

initial begin
    clk = 1'b0;
    reset_n = 1'b0;
    key1_n = 1'b1;
    uart_rx = 1'b1;
    watchdog = 0;
    errors = 0;
    test_pass = 1'b0;
    saw_uart_apb = 1'b0;
    saw_cache_request = 1'b0;

    repeat(4) @(posedge clk);
    @(negedge clk);
    reset_n = 1'b1;

    // Override only the native data request emitted by the core. This keeps the
    // actual SoC decoder, native-to-APB adapter and UART path in the test while
    // avoiding dependence on a particular software image.
    force dut.d_req_valid = 1'b1;
    force dut.d_req_write = 1'b0;
    force dut.d_req_addr  = 32'h4000_0000;
    force dut.d_req_wdata = 32'h0000_0000;
    force dut.d_req_wstrb = 4'b0000;

    while(!dut.d_req_ready) begin
        @(posedge clk);
        #1;
        watchdog = watchdog + 1;
        if(watchdog > 100)
            $fatal(1, "MMIO request was never accepted");
    end

    @(posedge clk);
    #1;
    watchdog = 0;
    while(!dut.d_rsp_valid) begin
        @(posedge clk);
        #1;
        watchdog = watchdog + 1;
        if(watchdog > 100)
            $fatal(1, "MMIO response timeout");
    end

    if(dut.d_rsp_error) begin
        $error("unexpected MMIO response error");
        errors = errors + 1;
    end

    @(negedge clk);
    release dut.d_req_valid;
    release dut.d_req_write;
    release dut.d_req_addr;
    release dut.d_req_wdata;
    release dut.d_req_wstrb;

    repeat(2) @(posedge clk);
    #1;

    if(!saw_uart_apb) begin
        $error("0x40000000 transaction did not reach UART APB path");
        errors = errors + 1;
    end
    if(saw_cache_request) begin
        $error("MMIO request was incorrectly presented to D-cache");
        errors = errors + 1;
    end
    if((dut.dcache_access_count != 0) ||
       (dut.dcache_hit_count != 0) ||
       (dut.dcache_miss_count != 0)) begin
        $error("MMIO changed D-cache counters access/hit/miss=%0d/%0d/%0d",
               dut.dcache_access_count, dut.dcache_hit_count,
               dut.dcache_miss_count);
        errors = errors + 1;
    end
    if(dut.dcache_refill_req_valid || dut.dcache_mem_wr_valid) begin
        $error("MMIO generated D-cache backend traffic");
        errors = errors + 1;
    end
    if(dut.u_dcache.g_dm_baseline.u_tag_ram.valid_bits !== 64'h0000_0000_0000_0000) begin
        $error("MMIO modified D-cache valid metadata");
        errors = errors + 1;
    end

    if(errors != 0)
        $fatal(1, "MMIO bypass failed with %0d error(s)", errors);

    test_pass = 1'b1;
    $display("[PASS] MMIO bypass test");
    $display("[PASS] MMIO generated no D-cache access, refill or write traffic");
    $finish;
end

endmodule
