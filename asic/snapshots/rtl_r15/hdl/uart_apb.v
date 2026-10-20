module uart_apb (
    input  wire        clk,
    input  wire        reset_n,
    input  wire        pclk,
    input  wire        preset_n,
    input  wire        psel,
    input  wire        penable,
    input  wire        pwrite,
    input  wire [3:0]  pstrb,
    input  wire [11:0] paddr,
    input  wire [31:0] pwdata,
    input  wire        rx,
    input  wire        cts_n,
    output wire        pready,
    output wire        pslverr,
    output reg  [31:0] prdata,
    output wire        tx,
    output wire        rts_n
);

    wire apb_wr = psel && penable && pwrite;
    wire apb_rd = psel && penable && !pwrite;

    reg  [31:0] cfg_reg;
    reg  [31:0] ctrl_reg;
    reg  [7:0]  tx_data_reg;
    // rx_data_valid: RXDATA holds the oldest unread byte. See the note at
    // the RX prefetch below.
    reg         rx_data_valid;
    reg         tx_done_latched;
    reg         rx_done_latched;
    reg         tx_active_seen;

    reg         write_tx_fifo_pulse;
    reg         start_tx_pulse;
    reg         read_rx_fifo_pulse;

    wire [7:0]  rx_data_o;
    wire        tx_done;
    wire        rx_done;
    wire        parity_bit_error;
    wire        tx_fifo_full;
    wire        rx_fifo_empty;

    assign pready  = 1'b1;
    assign pslverr = 1'b0;

    always @(posedge pclk or negedge preset_n) begin
        if (!preset_n) begin
            cfg_reg             <= 32'h0000_00C3; // 8N1, baud sel=3
            ctrl_reg            <= 32'h0000_0000;
            tx_data_reg         <= 8'h00;
            rx_data_valid       <= 1'b0;
            tx_done_latched     <= 1'b0;
            rx_done_latched     <= 1'b0;
            tx_active_seen      <= 1'b0;
            write_tx_fifo_pulse <= 1'b0;
            start_tx_pulse      <= 1'b0;
            read_rx_fifo_pulse  <= 1'b0;
        end else begin
            write_tx_fifo_pulse <= 1'b0;
            start_tx_pulse      <= 1'b0;
            read_rx_fifo_pulse  <= 1'b0;
            ctrl_reg            <= 32'h0000_0000;

            if (tx_done)
                tx_done_latched <= 1'b1;
            if (rx_done)
                rx_done_latched <= 1'b1;

            // RX prefetch. The RX FIFO registers its output on a read, so the
            // byte at its head is not visible until it has been read once.
            // RXDATA used to be captured from that output on rx_done, before
            // any read, so it always returned the previous read -- 0x00 after
            // reset -- never the byte just received. Keep the head loaded
            // instead: when no byte is held and the FIFO has one, read it. The
            // pulse is registered, so while it is high the read is in flight
            // and no second read is issued. RXDATA then shows the oldest unread
            // byte, and CTRL[1] or STATUS[4] (write 1) consumes it.
            read_rx_fifo_pulse <= !rx_data_valid && !read_rx_fifo_pulse &&
                                  !rx_fifo_empty;
            if (read_rx_fifo_pulse)
                rx_data_valid <= 1'b1;
            if (tx == 1'b0)
                tx_active_seen <= 1'b1;

            // Byte strobes are honoured (APB4). The data byte of TXDATA and every
            // command or write-1-to-clear bit of CTRL and STATUS sit in byte 0, so
            // those act only when pstrb[0] is set; CFG is updated byte by byte.
            // pstrb used to be ignored, and a byte write to CFG overwrote the
            // other three bytes with whatever the bus carried in those lanes.
            if (apb_wr) begin
                case (paddr[7:0])
                    8'h00: if (pstrb[0]) begin
                        tx_data_reg <= pwdata[7:0];
                        write_tx_fifo_pulse <= 1'b1;
                    end
                    8'h08: begin
                        if (pstrb[0]) cfg_reg[7:0]   <= pwdata[7:0];
                        if (pstrb[1]) cfg_reg[15:8]  <= pwdata[15:8];
                        if (pstrb[2]) cfg_reg[23:16] <= pwdata[23:16];
                        if (pstrb[3]) cfg_reg[31:24] <= pwdata[31:24];
                    end
                    8'h0C: if (pstrb[0]) begin
                        ctrl_reg <= pwdata;
                        if (pwdata[0])
                            start_tx_pulse <= 1'b1;
                        // Consume only a byte that is actually held. While a
                        // prefetch is in flight rx_data_valid is still 0, and
                        // clearing it here would drop the byte being loaded.
                        if (pwdata[1] && rx_data_valid) begin
                            // consume the byte in RXDATA
                            rx_data_valid      <= 1'b0;
                            rx_done_latched    <= 1'b0;
                        end
                        if (pwdata[2])
                            tx_done_latched <= 1'b0;
                        if (pwdata[3])
                            tx_active_seen <= 1'b0;
                    end
                    8'h10: if (pstrb[0]) begin
                        // write-1-to-clear status bits for convenience
                        if (pwdata[0]) tx_done_latched <= 1'b0;
                        if (pwdata[1]) rx_done_latched <= 1'b0;
                        if (pwdata[4] && rx_data_valid) rx_data_valid <= 1'b0; // consume, as CTRL[1]
                        if (pwdata[3]) tx_active_seen  <= 1'b0;
                    end
                    default: begin
                    end
                endcase
            end
        end
    end

    always @(*) begin
        prdata = 32'h0000_0000;
        if (apb_rd) begin
            case (paddr[7:0])
                8'h00: prdata = {24'h0, tx_data_reg};
                8'h04: prdata = {24'h0, rx_data_o};   // head of the RX FIFO
                8'h08: prdata = cfg_reg;
                8'h0C: prdata = ctrl_reg;
                // bit 5 tx_fifo_full, bit 6 rx_fifo_empty: live FIFO state, read-only.
                8'h10: prdata = {25'h0, rx_fifo_empty, tx_fifo_full, rx_data_valid, tx_active_seen, parity_bit_error, rx_done_latched, tx_done_latched};
                default: prdata = 32'h0000_0000;
            endcase
        end
    end

    uart_core u_uart_core (
        .clk                (clk),
        .reset_n            (reset_n),
        .set_baud           (cfg_reg[1:0]),
        .write_tx_fifo      (write_tx_fifo_pulse),
        .read_rx_fifo       (read_rx_fifo_pulse),
        .start_tx           (start_tx_pulse),
        .parity_bit_tx_en   (cfg_reg[4]),
        .parity_bit_tx_type (cfg_reg[5]),
        .data_bit_tx_config (cfg_reg[7:6]),
        .stop_bit_tx_config (cfg_reg[8]),
        .tx_data_i          (tx_data_reg),
        .cts_n              (cts_n),
        .tx                 (tx),
        .tx_done            (tx_done),
        .parity_bit_rx_en   (cfg_reg[12]),
        .parity_bit_rx_type (cfg_reg[13]),
        .data_bit_rx_config (cfg_reg[15:14]),
        .stop_bit_rx_config (cfg_reg[16]),
        .rx                 (rx),
        .rx_data_o          (rx_data_o),
        .parity_bit_error   (parity_bit_error),
        .rx_done            (rx_done),
        .tx_fifo_full_o     (tx_fifo_full),
        .rx_fifo_empty_o    (rx_fifo_empty),
        .rts_n              (rts_n)
    );

endmodule
