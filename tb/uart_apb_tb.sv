`timescale 1ns/1ps
// Register-level test of uart_apb: the status register, the FIFO state bits
// 5 (tx_fifo_full) and 6 (rx_fifo_empty), and a TX->RX loopback frame.
//
// No earlier testbench reached uart_apb at register level: tb_axi_mmio uses a
// behavioural APB slave and tb_mmio_bypass only checks routing. The loopback
// also drives the RX FIFO write path in rx_block.sv, whose unreachable-state
// branch was completed to remove two inferred latches.
module tb_uart_apb;

reg         clk;
reg         reset_n;
reg         psel;
reg         penable;
reg         pwrite;
reg  [3:0]  pstrb;
reg  [11:0] paddr;
reg  [31:0] pwdata;
wire        pready;
wire        pslverr;
wire [31:0] prdata;
wire        tx;
wire        rts_n;
reg  [31:0] rd;
integer     i;
integer     errors;

// Loopback: the receiver listens to the transmitter.
uart_apb dut (
    .clk      (clk),
    .reset_n  (reset_n),
    .pclk     (clk),
    .preset_n (reset_n),
    .psel     (psel),
    .penable  (penable),
    .pwrite   (pwrite),
    .pstrb    (pstrb),
    .paddr    (paddr),
    .pwdata   (pwdata),
    .rx       (tx),
    .cts_n    (1'b0),
    .pready   (pready),
    .pslverr  (pslverr),
    .prdata   (prdata),
    .tx       (tx),
    .rts_n    (rts_n)
);

always #10 clk = ~clk;   // 50 MHz

task automatic apb_write(input [7:0] addr, input [31:0] data);
begin
    @(negedge clk);
    psel = 1; penable = 0; pwrite = 1; pstrb = 4'hF;
    paddr = {4'h0, addr}; pwdata = data;
    @(negedge clk);
    penable = 1;
    @(posedge clk); #1;
    if(!pready || pslverr) begin
        $display("[FAIL] APB write 0x%02x: pready=%b pslverr=%b", addr, pready, pslverr);
        errors = errors + 1;
    end
    @(negedge clk);
    psel = 0; penable = 0; pwrite = 0; pstrb = 0; paddr = 0; pwdata = 0;
end
endtask

task automatic apb_write_strb(input [7:0] addr, input [31:0] data, input [3:0] strb);
begin
    @(negedge clk);
    psel = 1; penable = 0; pwrite = 1; pstrb = strb;
    paddr = {4'h0, addr}; pwdata = data;
    @(negedge clk);
    penable = 1;
    @(posedge clk); #1;
    if(!pready || pslverr) begin
        $display("[FAIL] APB write 0x%02x strb %b: pready=%b pslverr=%b", addr, strb, pready, pslverr);
        errors = errors + 1;
    end
    @(negedge clk);
    psel = 0; penable = 0; pwrite = 0; pstrb = 0; paddr = 0; pwdata = 0;
end
endtask

task automatic apb_read(input [7:0] addr, output [31:0] data);
begin
    @(negedge clk);
    psel = 1; penable = 0; pwrite = 0; pstrb = 0;
    paddr = {4'h0, addr}; pwdata = 0;
    @(negedge clk);
    penable = 1;
    @(posedge clk); #1;
    if(!pready || pslverr) begin
        $display("[FAIL] APB read 0x%02x: pready=%b pslverr=%b", addr, pready, pslverr);
        errors = errors + 1;
    end
    data = prdata;
    @(negedge clk);
    psel = 0; penable = 0; paddr = 0;
end
endtask

task automatic expect_bits(input [31:0] got, input [31:0] mask,
                           input [31:0] want, input [255:0] label_text);
begin
    if((got & mask) !== want) begin
        $display("[FAIL] %0s: status 0x%08x, masked 0x%08x, expected 0x%08x",
                 label_text, got, got & mask, want);
        errors = errors + 1;
    end
end
endtask

task automatic expect_byte(input [7:0] got, input [7:0] want, input [255:0] label_text);
begin
    if(got !== want) begin
        $display("[FAIL] %0s: 0x%02x, expected 0x%02x", label_text, got, want);
        errors = errors + 1;
    end
end
endtask

// Poll STATUS until RXDATA holds a byte (frame time is ~4,500 clocks).
task automatic wait_rx_valid;
begin
    rd = 0;
    for(i = 0; (i < 20000) && !(rd & 32'h10); i = i + 1) begin
        repeat(10) @(posedge clk);
        apb_read(8'h10, rd);
    end
    if(!(rd & 32'h10)) begin
        $display("[FAIL] timed out waiting for RXDATA valid");
        errors = errors + 1;
    end
end
endtask

// Wait long enough for n frames to cross the loopback.
task automatic wait_frames(input integer n);
begin
    repeat(n * 6000) @(posedge clk);
end
endtask

localparam [31:0] TX_FULL  = 32'h20;   // status bit 5
localparam [31:0] RX_EMPTY = 32'h40;   // status bit 6
localparam [31:0] RX_DONE  = 32'h02;   // status bit 1
localparam [31:0] RX_VALID = 32'h10;   // status bit 4

initial begin
    clk = 0; reset_n = 0; errors = 0;
    psel = 0; penable = 0; pwrite = 0; pstrb = 0; paddr = 0; pwdata = 0;
    repeat(5) @(posedge clk);
    reset_n = 1;
    repeat(2) @(posedge clk);

    // 115200 baud, 8 data bits on both TX [7:6] and RX [15:14], no parity,
    // one stop bit.
    apb_write(8'h08, 32'h0000_C0C3);

    // Byte strobes (APB4). A write to byte 1 of CFG changes byte 1 only.
    apb_write_strb(8'h08, 32'hFFFF_FFFF, 4'b0010);
    apb_read(8'h08, rd);
    if(rd !== 32'h0000_FFC3) begin
        $display("[FAIL] byte-1 write to CFG gave 0x%08x, expected 0x0000ffc3", rd);
        errors = errors + 1;
    end
    apb_write(8'h08, 32'h0000_C0C3);
    // TXDATA writes whose byte 0 is not strobed push nothing: sixteen of them
    // leave the TX FIFO not full, and the loopback below still sees 0xA0 first.
    for(i = 0; i < 16; i = i + 1)
        apb_write_strb(8'h00, 32'h0000_00EE, 4'b1110);
    apb_read(8'h10, rd);
    expect_bits(rd, TX_FULL, 32'h0, "unstrobed TXDATA writes push nothing");

    // Out of reset: RX FIFO empty, TX FIFO not full.
    apb_read(8'h10, rd);
    expect_bits(rd, TX_FULL | RX_EMPTY, RX_EMPTY, "reset FIFO state");

    // Fill the 16-deep TX FIFO without starting transmission.
    for(i = 0; i < 16; i = i + 1)
        apb_write(8'h00, 32'hA0 + i);
    apb_read(8'h10, rd);
    expect_bits(rd, TX_FULL | RX_EMPTY, TX_FULL | RX_EMPTY, "TX FIFO full after 16 writes");

    // Send one frame. It leaves the TX FIFO at once and returns through the
    // loopback into the RX FIFO.
    apb_write(8'h0C, 32'h1);
    wait_rx_valid();
    expect_bits(rd, RX_DONE | RX_VALID, RX_DONE | RX_VALID, "first frame received");
    // The byte has moved to RXDATA and nothing is queued behind it.
    expect_bits(rd, TX_FULL | RX_EMPTY, RX_EMPTY, "TX no longer full, RX queue empty");
    apb_read(8'h04, rd);
    expect_byte(rd[7:0], 8'hA0, "RXDATA is the byte just received");

    // Two more frames arrive before software reads anything. RXDATA must keep
    // the oldest unread byte and the other one must wait in the FIFO.
    apb_write(8'h0C, 32'h1);
    wait_frames(1);
    apb_write(8'h0C, 32'h1);
    wait_frames(1);
    apb_read(8'h10, rd);
    expect_bits(rd, RX_VALID | RX_EMPTY, RX_VALID, "bytes queued behind RXDATA");
    apb_read(8'h04, rd);
    expect_byte(rd[7:0], 8'hA0, "RXDATA still the oldest unread byte");

    // Consume in order: A0, then A1 (CTRL[1]), then A2 (STATUS[4] write-1).
    apb_write(8'h0C, 32'h2);
    wait_rx_valid();
    apb_read(8'h04, rd);
    expect_byte(rd[7:0], 8'hA1, "second byte after one CTRL[1] consume");
    apb_write(8'h10, 32'h10);
    wait_rx_valid();
    apb_read(8'h04, rd);
    expect_byte(rd[7:0], 8'hA2, "third byte after a STATUS[4] consume");
    apb_read(8'h10, rd);
    expect_bits(rd, RX_EMPTY, RX_EMPTY, "RX queue drained");

    // Consume the last byte: nothing left.
    apb_write(8'h0C, 32'h2);
    repeat(6) @(posedge clk);
    apb_read(8'h10, rd);
    expect_bits(rd, RX_VALID | RX_EMPTY, RX_EMPTY, "RX empty after the last byte");

    // A consume with no byte held must not disturb anything.
    apb_write(8'h0C, 32'h2);
    repeat(6) @(posedge clk);
    apb_read(8'h10, rd);
    expect_bits(rd, RX_VALID | RX_EMPTY, RX_EMPTY, "consume with nothing held is a no-op");

    if(errors != 0)
        $fatal(1, "uart_apb tests failed with %0d error(s)", errors);
    $display("[PASS] UART byte strobes, status FIFO bits, TX FIFO full, loopback frames, RX order");
    $finish;
end

endmodule
