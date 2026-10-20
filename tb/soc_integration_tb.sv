`timescale 1ns/1ps
`include "tb/rf_bht_backdoor.svh"

module tb_soc_integration;

reg clk;
reg reset_n;
reg key1_n;
reg uart_rx;

wire uart_tx;
wire [6:0] HEX0, HEX1, HEX2, HEX3, HEX4, HEX5, HEX6, HEX7;
wire [7:0] LEDR;
wire [7:0] LCD_DATA;
wire LCD_EN, LCD_RS, LCD_RW, LCD_ON, LCD_BLON;

integer errors;
integer timeout_count;
integer if_request_count;
integer if_refill_request_count;
integer if_refill_beat_count;
integer d_request_count;
integer store_request_count;
integer load_request_count;
integer i;

soc_top #(
    .ICACHE_LINE_COUNT   (8),
    .DCACHE_LINE_COUNT   (8),
    .ICACHE_MISS_PENALTY (2),
    .DCACHE_MISS_PENALTY (2),
    .IMEM_DEPTH          (1024),
    .DMEM_DEPTH          (64),
    .MEMFILE             ("hdl/riscv_full.hex")
) dut (
    .clk(clk), .reset_n(reset_n), .key1_n(key1_n),
    .uart_rx(uart_rx), .uart_tx(uart_tx),
    .HEX0(HEX0), .HEX1(HEX1), .HEX2(HEX2), .HEX3(HEX3),
    .HEX4(HEX4), .HEX5(HEX5), .HEX6(HEX6), .HEX7(HEX7),
    .LEDR(LEDR), .LCD_DATA(LCD_DATA), .LCD_EN(LCD_EN),
    .LCD_RS(LCD_RS), .LCD_RW(LCD_RW), .LCD_ON(LCD_ON),
    .LCD_BLON(LCD_BLON)
);

always #5 clk = ~clk;

always @(posedge clk) begin
    if(reset_n) begin
        if(dut.if_req_valid && dut.if_req_ready)
            if_request_count = if_request_count + 1;
        if(dut.icache_refill_req_valid && dut.icache_refill_req_ready)
            if_refill_request_count = if_refill_request_count + 1;
        if(dut.icache_refill_rsp_valid)
            if_refill_beat_count = if_refill_beat_count + 1;

        if(dut.d_req_valid && dut.d_req_ready) begin
            d_request_count = d_request_count + 1;
            if(dut.d_req_write)
                store_request_count = store_request_count + 1;
            else
                load_request_count = load_request_count + 1;
        end

        assert(dut.icache_access_count <= if_request_count)
            else $fatal(1, "I-cache counted an unaccepted native request");
        assert(dut.dcache_access_count <= d_request_count)
            else $fatal(1, "D-cache counted an unaccepted native request");
        assert(dut.icache_access_count ==
               (dut.icache_hit_count + dut.icache_miss_count))
            else $fatal(1, "I-cache counter invariant failed");
        assert(dut.dcache_access_count ==
               (dut.dcache_hit_count + dut.dcache_miss_count))
            else $fatal(1, "D-cache hit/miss invariant failed");
        assert(dut.dcache_access_count ==
               (dut.dcache_read_count + dut.dcache_write_count))
            else $fatal(1, "D-cache read/write invariant failed");
    end
end

task automatic check(input condition, input string message);
    begin
        if(!condition) begin
            $error("%s", message);
            errors = errors + 1;
        end
    end
endtask
task automatic soc_ram_set_word(input integer word_index, input [31:0] value);
    begin
        dut.u_axi_ram.RAM0[word_index] = value[7:0];
        dut.u_axi_ram.RAM1[word_index] = value[15:8];
        dut.u_axi_ram.RAM2[word_index] = value[23:16];
        dut.u_axi_ram.RAM3[word_index] = value[31:24];
    end
endtask

function automatic [31:0] soc_ram_get_word(input integer word_index);
    begin
        soc_ram_get_word = {dut.u_axi_ram.RAM3[word_index],
                            dut.u_axi_ram.RAM2[word_index],
                            dut.u_axi_ram.RAM1[word_index],
                            dut.u_axi_ram.RAM0[word_index]};
    end
endfunction
initial begin
    clk = 0;
    reset_n = 0;
    key1_n = 1;
    uart_rx = 1;
    errors = 0;
    timeout_count = 0;
    if_request_count = 0;
    if_refill_request_count = 0;
    if_refill_beat_count = 0;
    d_request_count = 0;
    store_request_count = 0;
    load_request_count = 0;

    // The active memory system is unified on the AXI slave side. Address
    // 0x1000 is word index 1024; instruction words remain at indices 0..5.
    #1;
    for(i = 0; i < 1088; i = i + 1)
        soc_ram_set_word(i, 32'h0000_0000);
    for(i = 0; i < 64; i = i + 1)
        soc_ram_set_word(i, 32'h0000_0013);

    soc_ram_set_word(0, 32'h0050_0093); // addi x1, x0, 5
    soc_ram_set_word(1, 32'h0000_1137); // lui  x2, 0x1
    soc_ram_set_word(2, 32'h0011_2023); // sw   x1, 0(x2)
    soc_ram_set_word(3, 32'h0001_2183); // lw   x3, 0(x2)
    soc_ram_set_word(4, 32'h0011_8213); // addi x4, x3, 1
    soc_ram_set_word(5, 32'h0000_006f); // jal  x0, 0

    repeat(4) @(posedge clk);
    @(negedge clk); reset_n = 1;

    while(`RF_GET(dut.u_core.u_pipeline.datapath.regfile, 4) !== 32'h0000_0006) begin
        @(posedge clk); #1;
        timeout_count = timeout_count + 1;
        if(timeout_count > 2000)
            $fatal(1, "Timeout waiting for SoC program completion");
    end

    repeat(5) @(posedge clk); #1;

    check(soc_ram_get_word(32'h1000 >> 2) === 32'h0000_0005,
          "Shared AXI RAM did not receive the write-through store");
    check(`RF_GET(dut.u_core.u_pipeline.datapath.regfile, 3) === 32'h0000_0005,
          "Core load result x3 is incorrect");
    check(`RF_GET(dut.u_core.u_pipeline.datapath.regfile, 4) === 32'h0000_0006,
          "Core dependent ALU result x4 is incorrect");
    check((d_request_count == 2) && (store_request_count == 1) &&
          (load_request_count == 1),
          "Native data request count/order is incorrect");
    check(dut.dcache_access_count == 2,
          "Both cacheable CPU data requests must be counted exactly once");
    check(dut.axi_write_txn_count == 1,
          "The program must issue exactly one AXI write transaction");
    check(dut.axi_ram_write_txn_count == 1,
          "AXI RAM must complete exactly one write transaction");
    check(dut.axi_read_txn_count >= 2,
          "I-cache and D-cache refills must both traverse AXI");
    check(dut.axi_read_txn_count == dut.axi_ram_read_burst_count,
          "AXI master/slave read transaction counters differ");
    check(if_refill_beat_count == (4 * if_refill_request_count),
          "Every I-cache refill must contain exactly four accepted beats");
    check(!dut.if_error_dbg && !dut.d_error_dbg,
          "Native interface reported an unexpected error");

    $display("----- SOC INTEGRATION SUMMARY -----");
    $display("Native IF accepted / I-cache accesses = %0d / %0d",
             if_request_count, dut.icache_access_count);
    $display("Native D accepted / D-cache accesses  = %0d / %0d",
             d_request_count, dut.dcache_access_count);
    $display("AXI reads/writes                     = %0d / %0d",
             dut.axi_read_txn_count, dut.axi_write_txn_count);
    $display("RAM[0x1000], x3, x4                  = %08h/%08h/%08h",
             soc_ram_get_word(32'h1000 >> 2),
             `RF_GET(dut.u_core.u_pipeline.datapath.regfile, 3),
             `RF_GET(dut.u_core.u_pipeline.datapath.regfile, 4));

    if(errors != 0)
        $fatal(1, "[FAIL] SoC integration: %0d error(s)", errors);

    $display("[PASS] SoC native/cache/AXI integration test");
    $finish;
end

endmodule
