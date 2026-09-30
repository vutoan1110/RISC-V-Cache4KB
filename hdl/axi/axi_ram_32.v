module axi_ram_32 #(
    parameter DEPTH_WORDS = 4096,   // R14: default follows soc_top (IMEM_DEPTH + DMEM_DEPTH)
    parameter MEMFILE     = "riscv_full.hex"
)(
    input  wire        clk,
    input  wire        reset_n,

    input  wire [31:0] s_axi_araddr,
    input  wire [7:0]  s_axi_arlen,
    input  wire [2:0]  s_axi_arsize,
    input  wire [1:0]  s_axi_arburst,
    input  wire        s_axi_arvalid,
    output wire        s_axi_arready,

    output wire [31:0] s_axi_rdata,
    output wire [1:0]  s_axi_rresp,
    output wire        s_axi_rlast,
    output wire        s_axi_rvalid,
    input  wire        s_axi_rready,

    input  wire [31:0] s_axi_awaddr,
    input  wire [7:0]  s_axi_awlen,
    input  wire [2:0]  s_axi_awsize,
    input  wire [1:0]  s_axi_awburst,
    input  wire        s_axi_awvalid,
    output wire        s_axi_awready,

    input  wire [31:0] s_axi_wdata,
    input  wire [3:0]  s_axi_wstrb,
    input  wire        s_axi_wlast,
    input  wire        s_axi_wvalid,
    output wire        s_axi_wready,

    output wire [1:0]  s_axi_bresp,
    output wire        s_axi_bvalid,
    input  wire        s_axi_bready,

    // Test hooks; tie low in synthesis.
    input  wire [7:0]  test_ar_stall_cycles,
    input  wire [7:0]  test_r_first_delay_cycles,
    input  wire [7:0]  test_r_gap_cycles,
    input  wire [7:0]  test_aw_stall_cycles,
    input  wire [7:0]  test_w_stall_cycles,
    input  wire [7:0]  test_b_delay_cycles,
    input  wire        test_rresp_error,
    input  wire        test_bresp_error,

    output reg  [31:0] read_burst_count,
    output reg  [31:0] write_txn_count
);

localparam [1:0] RESP_OKAY   = 2'b00;
localparam [1:0] RESP_SLVERR = 2'b10;
localparam integer RAM_ADDR_WIDTH = $clog2(DEPTH_WORDS);

localparam [1:0] RD_IDLE  = 2'd0;
localparam [1:0] RD_DELAY = 2'd1;
localparam [1:0] RD_FETCH = 2'd2;
localparam [1:0] RD_SEND  = 2'd3;

reg [1:0]  rd_state;
reg [31:0] rd_addr_q;
reg [7:0]  rd_len_q;
reg [7:0]  rd_beat_q;
reg [7:0]  rd_delay_q;
reg        rd_protocol_error_q;
reg [31:0] rdata_q;
reg [1:0]  rresp_q;
reg        rvalid_q;

reg        ar_delay_started_q;
reg [7:0]  ar_wait_q;

reg        aw_hold_q;
reg [31:0] awaddr_q;
reg [7:0]  awlen_q;
reg [2:0]  awsize_q;
reg [1:0]  awburst_q;
reg        aw_delay_started_q;
reg [7:0]  aw_wait_q;

reg        w_hold_q;
reg [31:0] wdata_q;
reg [3:0]  wstrb_q;
reg        wlast_q;
reg        w_delay_started_q;
reg [7:0]  w_wait_q;

reg        b_pending_q;
reg [7:0]  b_wait_q;
reg [1:0]  bresp_q;
reg        bvalid_q;

// Four byte-lane arrays: one per WSTRB bit, M9K-inferred, init from MIF at
// configuration and never reset.
(* ramstyle = "M9K, no_rw_check", ram_init_file = "hdl/riscv_full_byte0.mif" *)
reg [7:0] RAM0 [0:DEPTH_WORDS-1];
(* ramstyle = "M9K, no_rw_check", ram_init_file = "hdl/riscv_full_byte1.mif" *)
reg [7:0] RAM1 [0:DEPTH_WORDS-1];
(* ramstyle = "M9K, no_rw_check", ram_init_file = "hdl/riscv_full_byte2.mif" *)
reg [7:0] RAM2 [0:DEPTH_WORDS-1];
(* ramstyle = "M9K, no_rw_check", ram_init_file = "hdl/riscv_full_byte3.mif" *)
reg [7:0] RAM3 [0:DEPTH_WORDS-1];
reg [31:0] ram_read_data_q;

// synthesis translate_off
reg [31:0] init_words [0:DEPTH_WORDS-1];
integer init_index;
// synthesis translate_on

wire ar_available = (rd_state == RD_IDLE);
wire ar_delay_done = (test_ar_stall_cycles == 0) ||
                     (ar_delay_started_q && (ar_wait_q == 0));
assign s_axi_arready = ar_available && ar_delay_done;

wire aw_available = !aw_hold_q && !b_pending_q && !bvalid_q;
wire aw_delay_done = (test_aw_stall_cycles == 0) ||
                     (aw_delay_started_q && (aw_wait_q == 0));
assign s_axi_awready = aw_available && aw_delay_done;

wire w_available = !w_hold_q && !b_pending_q && !bvalid_q;
wire w_delay_done = (test_w_stall_cycles == 0) ||
                    (w_delay_started_q && (w_wait_q == 0));
assign s_axi_wready = w_available && w_delay_done;

wire ar_fire = s_axi_arvalid && s_axi_arready;
wire r_fire  = s_axi_rvalid && s_axi_rready;
wire aw_fire = s_axi_awvalid && s_axi_awready;
wire w_fire  = s_axi_wvalid && s_axi_wready;
wire b_fire  = s_axi_bvalid && s_axi_bready;

wire [31:0] selected_awaddr  = aw_hold_q ? awaddr_q  : s_axi_awaddr;
wire [7:0]  selected_awlen   = aw_hold_q ? awlen_q   : s_axi_awlen;
wire [2:0]  selected_awsize  = aw_hold_q ? awsize_q  : s_axi_awsize;
wire [1:0]  selected_awburst = aw_hold_q ? awburst_q : s_axi_awburst;
wire [31:0] selected_wdata   = w_hold_q  ? wdata_q   : s_axi_wdata;
wire [3:0]  selected_wstrb   = w_hold_q  ? wstrb_q   : s_axi_wstrb;
wire        selected_wlast   = w_hold_q  ? wlast_q   : s_axi_wlast;

wire write_pair_complete = !b_pending_q && !bvalid_q &&
                           (aw_hold_q || aw_fire) &&
                           (w_hold_q  || w_fire);
wire write_addr_in_range = (selected_awaddr[31:2] < DEPTH_WORDS) &&
                           (selected_awaddr[1:0] == 2'b00);
wire write_protocol_error = (selected_awlen != 0) ||
                            (selected_awsize != 3'd2) ||
                            (selected_awburst != 2'b01) ||
                            !selected_wlast;
wire write_error = !write_addr_in_range || write_protocol_error ||
                   test_bresp_error;

wire read_addr_in_range = (rd_addr_q[31:2] < DEPTH_WORDS) &&
                          (rd_addr_q[1:0] == 2'b00);
wire ram_read_enable = (rd_state == RD_DELAY) && (rd_delay_q == 0) &&
                       read_addr_in_range;
wire [RAM_ADDR_WIDTH-1:0] ram_read_index =
                            rd_addr_q[RAM_ADDR_WIDTH+1:2];
wire [RAM_ADDR_WIDTH-1:0] ram_write_index =
                            selected_awaddr[RAM_ADDR_WIDTH+1:2];

assign s_axi_rdata  = rdata_q;
assign s_axi_rresp  = rresp_q;
assign s_axi_rlast  = rvalid_q && (rd_beat_q == rd_len_q);
assign s_axi_rvalid = rvalid_q;
assign s_axi_bresp  = bresp_q;
assign s_axi_bvalid = bvalid_q;

// Sim init from the word-oriented HEX; hardware uses the byte-lane MIFs above.
// synthesis translate_off
initial begin
    for(init_index = 0; init_index < DEPTH_WORDS; init_index = init_index + 1)
        init_words[init_index] = 32'h0000_0000;
    if(MEMFILE != "") $readmemh(MEMFILE, init_words);
    for(init_index = 0; init_index < DEPTH_WORDS; init_index = init_index + 1) begin
        RAM0[init_index] = init_words[init_index][7:0];
        RAM1[init_index] = init_words[init_index][15:8];
        RAM2[init_index] = init_words[init_index][23:16];
        RAM3[init_index] = init_words[init_index][31:24];
    end
end
// synthesis translate_on

// Synchronous read + byte-enabled write. Read-during-write is don't-care
// (one global transaction at a time).
always @(posedge clk) begin
    if(ram_read_enable) begin
        ram_read_data_q[7:0]   <= RAM0[ram_read_index];
        ram_read_data_q[15:8]  <= RAM1[ram_read_index];
        ram_read_data_q[23:16] <= RAM2[ram_read_index];
        ram_read_data_q[31:24] <= RAM3[ram_read_index];
    end

    if(write_pair_complete && !write_error) begin
        if(selected_wstrb[0]) RAM0[ram_write_index] <= selected_wdata[7:0];
        if(selected_wstrb[1]) RAM1[ram_write_index] <= selected_wdata[15:8];
        if(selected_wstrb[2]) RAM2[ram_write_index] <= selected_wdata[23:16];
        if(selected_wstrb[3]) RAM3[ram_write_index] <= selected_wdata[31:24];
    end
end

always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        rd_state              <= RD_IDLE;
        rd_addr_q             <= 32'h0000_0000;
        rd_len_q              <= 8'd0;
        rd_beat_q             <= 8'd0;
        rd_delay_q            <= 8'd0;
        rd_protocol_error_q   <= 1'b0;
        rdata_q               <= 32'h0000_0000;
        rresp_q               <= RESP_OKAY;
        rvalid_q              <= 1'b0;
        ar_delay_started_q    <= 1'b0;
        ar_wait_q             <= 8'd0;

        aw_hold_q             <= 1'b0;
        awaddr_q              <= 32'h0000_0000;
        awlen_q               <= 8'd0;
        awsize_q              <= 3'd0;
        awburst_q             <= 2'd0;
        aw_delay_started_q    <= 1'b0;
        aw_wait_q             <= 8'd0;

        w_hold_q              <= 1'b0;
        wdata_q               <= 32'h0000_0000;
        wstrb_q               <= 4'b0000;
        wlast_q               <= 1'b0;
        w_delay_started_q     <= 1'b0;
        w_wait_q              <= 8'd0;

        b_pending_q           <= 1'b0;
        b_wait_q              <= 8'd0;
        bresp_q               <= RESP_OKAY;
        bvalid_q              <= 1'b0;
        read_burst_count      <= 32'h0000_0000;
        write_txn_count       <= 32'h0000_0000;
    end
    else begin
        // programmable per-transaction backpressure on AR/AW/W
        if(ar_fire) begin
            ar_delay_started_q <= 1'b0;
            ar_wait_q          <= 8'd0;
        end
        else if(ar_available && s_axi_arvalid && !ar_delay_started_q &&
                (test_ar_stall_cycles != 0)) begin
            ar_delay_started_q <= 1'b1;
            ar_wait_q          <= test_ar_stall_cycles;
        end
        else if(ar_delay_started_q && (ar_wait_q != 0)) begin
            ar_wait_q <= ar_wait_q - 1'b1;
        end

        if(aw_fire) begin
            aw_delay_started_q <= 1'b0;
            aw_wait_q          <= 8'd0;
        end
        else if(aw_available && s_axi_awvalid && !aw_delay_started_q &&
                (test_aw_stall_cycles != 0)) begin
            aw_delay_started_q <= 1'b1;
            aw_wait_q          <= test_aw_stall_cycles;
        end
        else if(aw_delay_started_q && (aw_wait_q != 0)) begin
            aw_wait_q <= aw_wait_q - 1'b1;
        end

        if(w_fire) begin
            w_delay_started_q <= 1'b0;
            w_wait_q          <= 8'd0;
        end
        else if(w_available && s_axi_wvalid && !w_delay_started_q &&
                (test_w_stall_cycles != 0)) begin
            w_delay_started_q <= 1'b1;
            w_wait_q          <= test_w_stall_cycles;
        end
        else if(w_delay_started_q && (w_wait_q != 0)) begin
            w_wait_q <= w_wait_q - 1'b1;
        end

        case(rd_state)
            RD_IDLE: begin
                rvalid_q <= 1'b0;
                if(ar_fire) begin
                    rd_addr_q           <= s_axi_araddr;
                    rd_len_q            <= s_axi_arlen;
                    rd_beat_q           <= 8'd0;
                    rd_delay_q          <= test_r_first_delay_cycles;
                    rd_protocol_error_q <= (s_axi_arsize != 3'd2) ||
                                           (s_axi_arburst != 2'b01) ||
                                           (s_axi_araddr[1:0] != 2'b00);
                    read_burst_count    <= read_burst_count + 1'b1;
                    rd_state            <= RD_DELAY;
                end
            end

            RD_DELAY: begin
                if(rd_delay_q == 0)
                    rd_state <= RD_FETCH;
                else
                    rd_delay_q <= rd_delay_q - 1'b1;
            end

            RD_FETCH: begin
                rdata_q  <= read_addr_in_range ? ram_read_data_q : 32'h0000_0000;
                rresp_q  <= (!read_addr_in_range || rd_protocol_error_q ||
                             test_rresp_error) ? RESP_SLVERR : RESP_OKAY;
                rvalid_q <= 1'b1;
                rd_state <= RD_SEND;
            end

            RD_SEND: begin
                if(r_fire) begin
                    rvalid_q <= 1'b0;
                    if(rd_beat_q == rd_len_q) begin
                        rd_state <= RD_IDLE;
                    end
                    else begin
                        rd_beat_q  <= rd_beat_q + 1'b1;
                        rd_addr_q  <= rd_addr_q + 32'd4;
                        rd_delay_q <= test_r_gap_cycles;
                        rd_state   <= RD_DELAY;
                    end
                end
            end

            default: rd_state <= RD_IDLE;
        endcase

        if(aw_fire) begin
            aw_hold_q  <= 1'b1;
            awaddr_q   <= s_axi_awaddr;
            awlen_q    <= s_axi_awlen;
            awsize_q   <= s_axi_awsize;
            awburst_q  <= s_axi_awburst;
        end

        if(w_fire) begin
            w_hold_q <= 1'b1;
            wdata_q  <= s_axi_wdata;
            wstrb_q  <= s_axi_wstrb;
            wlast_q  <= s_axi_wlast;
        end

        if(write_pair_complete) begin
            aw_hold_q       <= 1'b0;
            w_hold_q        <= 1'b0;
            b_pending_q     <= 1'b1;
            b_wait_q        <= test_b_delay_cycles;
            bresp_q         <= write_error ? RESP_SLVERR : RESP_OKAY;
            write_txn_count <= write_txn_count + 1'b1;
            if(test_b_delay_cycles == 0)
                bvalid_q <= 1'b1;
        end
        else if(b_pending_q && !bvalid_q) begin
            if(b_wait_q == 0)
                bvalid_q <= 1'b1;
            else
                b_wait_q <= b_wait_q - 1'b1;
        end

        if(b_fire) begin
            bvalid_q   <= 1'b0;
            b_pending_q <= 1'b0;
        end
    end
end

endmodule
