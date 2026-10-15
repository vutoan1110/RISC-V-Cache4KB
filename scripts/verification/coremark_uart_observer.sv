`timescale 1ns/1ps
// Passive observation of accepted APB UART TXDATA writes. This captures the
// firmware's printed bytes; it does not test the physical UART serial output.
module tb_coremark_crc_audit #(
    parameter integer CACHE_CONFIG = 0,
    parameter integer CACHE_FAST_HIT = 0,
    parameter integer ICACHE_LINE_COUNT = 256,
    parameter integer DCACHE_LINE_COUNT = 256,
    parameter integer L0_ENTRIES = 8,
    parameter integer IMEM_DEPTH = 4096,
    parameter integer DMEM_DEPTH = 4096
);
    tb_benchmark_snapshot #(
        .CACHE_CONFIG(CACHE_CONFIG), .CACHE_FAST_HIT(CACHE_FAST_HIT),
        .ICACHE_LINE_COUNT(ICACHE_LINE_COUNT), .DCACHE_LINE_COUNT(DCACHE_LINE_COUNT),
        .L0_ENTRIES(L0_ENTRIES), .IMEM_DEPTH(IMEM_DEPTH), .DMEM_DEPTH(DMEM_DEPTH),
        .MEMFILE("fw/coremark.hex")
    ) bench();

    integer uart_fd = 0;
    integer uart_bytes = 0;
    string uart_path;
    initial begin
        if (!$value$plusargs("coremark_uart=%s", uart_path))
            $fatal(1, "Missing +coremark_uart=<path>");
        uart_fd = $fopen(uart_path, "wb");
        if (uart_fd == 0) $fatal(1, "Cannot open CoreMark UART transcript");
    end

    always @(posedge bench.clk) begin
        if (bench.reset_n && bench.dut.u_uart.psel &&
            bench.dut.u_uart.penable && bench.dut.u_uart.pready &&
            bench.dut.u_uart.pwrite && bench.dut.u_uart.pstrb[0] &&
            bench.dut.u_uart.paddr[7:0] == 8'h00) begin
            if ($isunknown(bench.dut.u_uart.pwdata[7:0]))
                $fatal(1, "Unknown byte on accepted UART TXDATA write");
            $fwrite(uart_fd, "%c", bench.dut.u_uart.pwdata[7:0]);
            $fflush(uart_fd);
            uart_bytes = uart_bytes + 1;
        end
    end

    final begin
        if (uart_fd != 0) $fclose(uart_fd);
        $display("COREMARK_UART_CAPTURE bytes=%0d method=accepted_apb_txdata_writes", uart_bytes);
    end
endmodule
