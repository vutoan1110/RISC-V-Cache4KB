module cache_axi_master #(
    parameter LINE_WORDS = 4
)(
    input  wire        clk,
    input  wire        reset_n,

    // I-cache native refill channel.
    input  wire        i_refill_req_valid,
    input  wire [31:0] i_refill_req_addr,
    output wire        i_refill_req_ready,
    output wire        i_refill_rsp_valid,
    output wire [31:0] i_refill_rsp_data,
    output wire        i_refill_rsp_last,
    output wire        i_refill_rsp_error,

    // D-cache native refill channel.
    input  wire        d_refill_req_valid,
    input  wire [31:0] d_refill_req_addr,
    output wire        d_refill_req_ready,
    output wire        d_refill_rsp_valid,
    output wire [31:0] d_refill_rsp_data,
    output wire        d_refill_rsp_last,
    output wire        d_refill_rsp_error,

    // D-cache write-through, backed by the posted-write buffer.
    input  wire        d_write_req_valid,
    input  wire [31:0] d_write_req_addr,
    input  wire [31:0] d_write_req_data,
    input  wire [3:0]  d_write_req_strb,
    output wire        d_write_req_ready,
    output wire        d_write_rsp_valid,
    output wire        d_write_rsp_error,

    // AXI4 read (one LINE_WORDS-beat 32-bit INCR burst, ID 0).
    output wire [31:0] m_axi_araddr,
    output wire [7:0]  m_axi_arlen,
    output wire [2:0]  m_axi_arsize,
    output wire [1:0]  m_axi_arburst,
    output wire        m_axi_arvalid,
    input  wire        m_axi_arready,

    input  wire [31:0] m_axi_rdata,
    input  wire [1:0]  m_axi_rresp,
    input  wire        m_axi_rlast,
    input  wire        m_axi_rvalid,
    output wire        m_axi_rready,

    // AXI4 write (single beat).
    output wire [31:0] m_axi_awaddr,
    output wire [7:0]  m_axi_awlen,
    output wire [2:0]  m_axi_awsize,
    output wire [1:0]  m_axi_awburst,
    output wire        m_axi_awvalid,
    input  wire        m_axi_awready,

    output wire [31:0] m_axi_wdata,
    output wire [3:0]  m_axi_wstrb,
    output wire        m_axi_wlast,
    output wire        m_axi_wvalid,
    input  wire        m_axi_wready,

    input  wire [1:0]  m_axi_bresp,
    input  wire        m_axi_bvalid,
    output wire        m_axi_bready,

    // Debug observability.
    output wire        busy,
    output wire [1:0]  active_source,
    output reg  [31:0] axi_read_txn_count,
    output reg  [31:0] axi_write_txn_count,
    output wire        axi_read_txn_event,
    output wire        axi_write_txn_event,

    // Posted-write error capture: the first write whose BRESP was not OKAY.
    // Sticky until wr_err_clear. See the note at wb_pop.
    output reg         wr_err,
    output reg  [31:0] wr_err_addr,
    input  wire        wr_err_clear
);

localparam [1:0] SRC_ICACHE = 2'd0;
localparam [1:0] SRC_DREAD  = 2'd1;
localparam [1:0] SRC_DWRITE = 2'd2;

function integer clog2;
    input integer value;
    integer tmp;
    begin
        tmp = value - 1;
        clog2 = 0;
        while(tmp > 0) begin clog2 = clog2 + 1; tmp = tmp >> 1; end
    end
endfunction

localparam LINE_BYTES  = LINE_WORDS * 4;
localparam OFFSET_BITS = clog2(LINE_BYTES);
// Keep the beat counter exactly as wide as the frozen design at the default
// four-word line. Widening it unconditionally cost 10 LEs and 0.66 ns of
// setup slack on the direct-mapped build, enough to miss 50 MHz.
localparam BEAT_BITS   = (LINE_WORDS > 8) ? 4 : 3;

localparam [2:0] ST_IDLE       = 3'd0;
localparam [2:0] ST_READ_ADDR  = 3'd1;
localparam [2:0] ST_READ_DATA  = 3'd2;
localparam [2:0] ST_WRITE_SEND = 3'd3;
localparam [2:0] ST_WRITE_RESP = 3'd4;

localparam integer WB_DEPTH = 2;
// Write-through only targets addr[31:16]==0, so 16 address bits suffice.
localparam integer WB_AW = 16;

reg [2:0]  state;
reg [1:0]  source_q;
reg [1:0]  last_grant_q;
reg [31:0] addr_q;
reg [31:0] wdata_q;
reg [3:0]  wstrb_q;
reg        aw_done_q;
reg        w_done_q;
reg [BEAT_BITS-1:0] read_beat_count_q;

reg [WB_AW-1:0] wb_addr_q [0:WB_DEPTH-1];
reg [31:0]      wb_data_q [0:WB_DEPTH-1];
reg [3:0]       wb_strb_q [0:WB_DEPTH-1];
reg        wb_head_q;                 // pop pointer
reg        wb_tail_q;                 // push pointer
reg [1:0]  wb_count_q;
reg        d_write_rsp_valid_q;

reg        grant_valid;
reg [1:0]  grant_source;

wire ar_fire = m_axi_arvalid && m_axi_arready;
wire r_fire  = m_axi_rvalid && m_axi_rready;
wire aw_fire = m_axi_awvalid && m_axi_awready;
wire w_fire  = m_axi_wvalid && m_axi_wready;
wire b_fire  = m_axi_bvalid && m_axi_bready;

wire read_expected_last = (read_beat_count_q == (LINE_WORDS-1));
wire read_protocol_error = m_axi_rlast != read_expected_last;
wire read_error = (m_axi_rresp != 2'b00) || read_protocol_error;
wire read_terminal = r_fire && (m_axi_rlast || read_expected_last);
wire write_channels_done = (aw_done_q || aw_fire) &&
                           (w_done_q  || w_fire);
assign axi_read_txn_event  = ar_fire;
assign axi_write_txn_event = (state == ST_WRITE_SEND) && write_channels_done;

// Posted-write buffer.
wire wb_full  = (wb_count_q == 2'd2);
wire wb_empty = (wb_count_q == 2'd0);
wire wb_push  = d_write_req_valid && !wb_full;
wire wb_pop   = (state == ST_WRITE_RESP) && b_fire;

assign d_write_req_ready     = !wb_full;
assign d_write_rsp_valid     = d_write_rsp_valid_q;
// A store is acknowledged when it enters the buffer, before its BRESP exists,
// so the response to the D-cache can never carry that error. A failing BRESP
// is recorded in wr_err / wr_err_addr instead.
assign d_write_rsp_error     = 1'b0;

// Drain a buffered store before starting any read (RAM sees stores first).
wire   wb_drain_pending = !wb_empty;

// Round-robin over the two read classes; writes go through the buffer.
always @(*) begin
    grant_valid  = 1'b0;
    grant_source = SRC_ICACHE;

    if(!wb_drain_pending) begin
        case(last_grant_q)
            SRC_ICACHE: begin
                if(d_refill_req_valid) begin
                    grant_valid  = 1'b1;
                    grant_source = SRC_DREAD;
                end
                else if(i_refill_req_valid) begin
                    grant_valid  = 1'b1;
                    grant_source = SRC_ICACHE;
                end
            end

            default: begin // SRC_DREAD / reset
                if(i_refill_req_valid) begin
                    grant_valid  = 1'b1;
                    grant_source = SRC_ICACHE;
                end
                else if(d_refill_req_valid) begin
                    grant_valid  = 1'b1;
                    grant_source = SRC_DREAD;
                end
            end
        endcase
    end
end

assign i_refill_req_ready = (state == ST_IDLE) && grant_valid && wb_empty &&
                            (grant_source == SRC_ICACHE);
assign d_refill_req_ready = (state == ST_IDLE) && grant_valid && wb_empty &&
                            (grant_source == SRC_DREAD);

assign m_axi_araddr  = addr_q;
assign m_axi_arlen   = LINE_WORDS - 1;
assign m_axi_arsize  = 3'd2;
assign m_axi_arburst = 2'b01;
assign m_axi_arvalid = (state == ST_READ_ADDR);
assign m_axi_rready  = (state == ST_READ_DATA);

assign m_axi_awaddr  = addr_q;
assign m_axi_awlen   = 8'd0;
assign m_axi_awsize  = 3'd2;
assign m_axi_awburst = 2'b01;
assign m_axi_awvalid = (state == ST_WRITE_SEND) && !aw_done_q;

assign m_axi_wdata   = wdata_q;
assign m_axi_wstrb   = wstrb_q;
assign m_axi_wlast   = 1'b1;
assign m_axi_wvalid  = (state == ST_WRITE_SEND) && !w_done_q;
assign m_axi_bready  = (state == ST_WRITE_RESP);

// Refill response beats are pulses; RREADY is held for the whole burst.
assign i_refill_rsp_valid = r_fire && (source_q == SRC_ICACHE);
assign i_refill_rsp_data  = m_axi_rdata;
assign i_refill_rsp_last  = m_axi_rlast || read_expected_last;
assign i_refill_rsp_error = read_error;

assign d_refill_rsp_valid = r_fire && (source_q == SRC_DREAD);
assign d_refill_rsp_data  = m_axi_rdata;
assign d_refill_rsp_last  = m_axi_rlast || read_expected_last;
assign d_refill_rsp_error = read_error;

assign busy          = (state != ST_IDLE) || !wb_empty;
assign active_source = source_q;

integer wb_i;
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        state               <= ST_IDLE;
        source_q            <= SRC_ICACHE;
        last_grant_q        <= SRC_DWRITE;
        addr_q              <= 32'h0000_0000;
        wdata_q             <= 32'h0000_0000;
        wstrb_q             <= 4'b0000;
        aw_done_q           <= 1'b0;
        w_done_q            <= 1'b0;
        read_beat_count_q   <= 0;
        axi_read_txn_count  <= 32'h0000_0000;
        axi_write_txn_count <= 32'h0000_0000;
        wr_err              <= 1'b0;
        wr_err_addr         <= 32'h0000_0000;
        wb_head_q           <= 1'b0;
        wb_tail_q           <= 1'b0;
        wb_count_q          <= 2'd0;
        d_write_rsp_valid_q <= 1'b0;
        for(wb_i = 0; wb_i < WB_DEPTH; wb_i = wb_i + 1) begin
            wb_addr_q[wb_i] <= {WB_AW{1'b0}};
            wb_data_q[wb_i] <= 32'h0000_0000;
            wb_strb_q[wb_i] <= 4'b0000;
        end
    end
    else begin
        // buffer push + one-cycle ack, independent of the drain FSM below
        d_write_rsp_valid_q <= wb_push;
        if(wb_push) begin
            wb_addr_q[wb_tail_q] <= d_write_req_addr[WB_AW-1:0];
            wb_data_q[wb_tail_q] <= d_write_req_data;
            wb_strb_q[wb_tail_q] <= d_write_req_strb;
            wb_tail_q            <= ~wb_tail_q;
        end
        case({wb_push, wb_pop})
            2'b10:   wb_count_q <= wb_count_q + 2'd1;
            2'b01:   wb_count_q <= wb_count_q - 2'd1;
            default: wb_count_q <= wb_count_q;
        endcase

        // The store behind this BRESP retired long ago, so the error cannot be
        // returned to it. Keep the first failure for software; addr_q still
        // holds the address of the write being answered, since it only changes
        // when ST_IDLE starts the next transaction. A failure in the same
        // cycle as a clear wins, so no failure is lost to a racing clear.
        if(wb_pop && (m_axi_bresp != 2'b00) && (!wr_err || wr_err_clear)) begin
            wr_err      <= 1'b1;
            wr_err_addr <= addr_q;
        end else if(wr_err_clear) begin
            wr_err      <= 1'b0;
        end

        case(state)
            ST_IDLE: begin
                aw_done_q         <= 1'b0;
                w_done_q          <= 1'b0;
                read_beat_count_q <= 3'd0;

                if(wb_drain_pending) begin
                    source_q     <= SRC_DWRITE;
                    last_grant_q <= SRC_DWRITE;
                    addr_q       <= {16'h0000, wb_addr_q[wb_head_q][WB_AW-1:2], 2'b00};
                    wdata_q      <= wb_data_q[wb_head_q];
                    wstrb_q      <= wb_strb_q[wb_head_q];
                    state        <= ST_WRITE_SEND;
                end
                else if(grant_valid) begin
                    source_q     <= grant_source;
                    last_grant_q <= grant_source;

                    case(grant_source)
                        SRC_ICACHE: begin
                            addr_q <= {i_refill_req_addr[31:OFFSET_BITS],
                                       {OFFSET_BITS{1'b0}}};
                            state  <= ST_READ_ADDR;
                        end

                        default: begin // SRC_DREAD
                            addr_q <= {d_refill_req_addr[31:OFFSET_BITS],
                                       {OFFSET_BITS{1'b0}}};
                            state  <= ST_READ_ADDR;
                        end
                    endcase
                end
            end

            ST_READ_ADDR: begin
                if(ar_fire) begin
                    read_beat_count_q  <= 0;
                    axi_read_txn_count <= axi_read_txn_count + 1'b1;
                    state              <= ST_READ_DATA;
                end
            end

            ST_READ_DATA: begin
                if(r_fire) begin
                    if(read_terminal) begin
                        read_beat_count_q <= 0;
                        state             <= ST_IDLE;
                    end
                    else begin
                        read_beat_count_q <= read_beat_count_q + 1'b1;
                    end
                end
            end

            ST_WRITE_SEND: begin
                if(aw_fire)
                    aw_done_q <= 1'b1;
                if(w_fire)
                    w_done_q <= 1'b1;

                if(write_channels_done) begin
                    axi_write_txn_count <= axi_write_txn_count + 1'b1;
                    state               <= ST_WRITE_RESP;
                end
            end

            ST_WRITE_RESP: begin
                if(b_fire) begin
                    aw_done_q <= 1'b0;
                    w_done_q  <= 1'b0;
                    wb_head_q <= ~wb_head_q;
                    state     <= ST_IDLE;
                end
            end

            default: state <= ST_IDLE;
        endcase
    end
end


// synthesis translate_off
initial begin
    if((LINE_WORDS < 2) || (LINE_WORDS > 16) ||
       ((LINE_WORDS & (LINE_WORDS - 1)) != 0))
        $fatal(1, "cache_axi_master: LINE_WORDS=%0d is unsupported. It must be a power of two from 2 to 16; the bank word selector is four bits, so wider lines would alias their upper words onto the lower ones without any other symptom.", LINE_WORDS);
end
// synthesis translate_on

endmodule
