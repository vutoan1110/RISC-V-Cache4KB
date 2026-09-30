module dcache_controller #(
    parameter INDEX_WIDTH = 6,
    parameter TAG_WIDTH   = 22
)(
    input  wire                   clk,
    input  wire                   reset_n,

    // Native CPU data port (no rsp_ready; rsp is a one-cycle pulse).
    input  wire                   req_valid,
    input  wire                   req_write,
    input  wire [31:0]            req_addr,
    input  wire [31:0]            req_wdata,
    input  wire [3:0]             req_wstrb,
    output wire                   req_ready,
    output wire                   rsp_valid,
    output wire [31:0]            rsp_rdata,
    output wire                   rsp_error,

    // One aligned line request followed by exactly four 32-bit response beats.
    output wire                   refill_req_valid,
    output wire [31:0]            refill_req_addr,
    input  wire                   refill_req_ready,
    input  wire                   refill_rsp_valid,
    input  wire [31:0]            refill_rsp_data,
    input  wire                   refill_rsp_last,
    input  wire                   refill_rsp_error,

    // Write-through channel; payload stable until handshake, response required.
    output wire                   mem_wr_valid,
    output wire [31:0]            mem_wr_addr,
    output wire [31:0]            mem_wr_data,
    output wire [3:0]             mem_wr_strb,
    input  wire                   mem_wr_ready,
    input  wire                   mem_wr_rsp_valid,
    input  wire                   mem_wr_rsp_error,

    output reg  [31:0]            access_count,
    output reg  [31:0]            read_count,
    output reg  [31:0]            write_count,
    output reg  [31:0]            hit_count,
    output reg  [31:0]            miss_count,
    output reg  [31:0]            read_hit_count,
    output reg  [31:0]            read_miss_count,
    output reg  [31:0]            write_hit_count,
    output reg  [31:0]            write_miss_count,
    output wire                   read_access_event,
    output wire                   read_hit_event,
    output wire                   read_miss_event,
    output wire                   write_access_event,
    output wire                   write_hit_event,
    output wire                   write_miss_event,


    // Tag storage interface.
    output wire [INDEX_WIDTH-1:0] tag_rd_index,
    // Synchronous tag port; the valid port stays combinational for the
    // hot-buffer path. See CLAUDE_AUTONOMY_LOG.md entry 4.
    output wire                   tag_rd_en,
    input  wire [TAG_WIDTH-1:0]   tag_rd_tag,
    output wire [INDEX_WIDTH-1:0] tag_valid_rd_index,
    input  wire                   tag_valid_rd,
    output wire                   tag_wr_en,
    output wire [INDEX_WIDTH-1:0] tag_wr_index,
    output wire [TAG_WIDTH-1:0]   tag_wr_tag,
    output wire                   tag_wr_valid,

    // Data storage interface.
    output wire                   data_rd_en,
    output wire [INDEX_WIDTH-1:0] data_rd_index,
    input  wire [127:0]           data_rd_line,
    output wire                   data_wr_en,
    output wire [INDEX_WIDTH-1:0] data_wr_index,
    output wire [1:0]             data_wr_word,
    output wire [31:0]            data_wr_data
);

localparam [3:0] ST_IDLE        = 4'd0;
localparam [3:0] ST_LOOKUP      = 4'd1;
localparam [3:0] ST_REFILL_REQ  = 4'd2;
localparam [3:0] ST_REFILL_DATA = 4'd3;
localparam [3:0] ST_WRITE_REQ   = 4'd4;
localparam [3:0] ST_WRITE_RESP  = 4'd5;
localparam [3:0] ST_CPU_RESP    = 4'd6;

reg [3:0] state;

reg        request_write;
reg [31:0] request_addr;
reg [31:0] request_wdata;
reg [3:0]  request_wstrb;

reg [1:0]  refill_beat_count;
reg        refill_error_seen;
reg [31:0] refill_requested_word;

reg        store_hit_latched;
reg [31:0] store_merged_word;

reg [31:0] rsp_data_reg;
reg        rsp_error_reg;
reg [127:0] refill_line_accum;

reg [1:0]   hot_valid;
reg [27:0]  hot_block0;
reg [27:0]  hot_block1;
reg [127:0] hot_line0;
reg [127:0] hot_line1;
reg         hot_replace;

function [31:0] select_line_word;
    input [127:0] line;
    input [1:0] word;
    begin
        case(word)
            2'd0: select_line_word = line[31:0];
            2'd1: select_line_word = line[63:32];
            2'd2: select_line_word = line[95:64];
            default: select_line_word = line[127:96];
        endcase
    end
endfunction

function [127:0] replace_line_word;
    input [127:0] line;
    input [1:0] word;
    input [31:0] value;
    begin
        replace_line_word = line;
        case(word)
            2'd0: replace_line_word[31:0] = value;
            2'd1: replace_line_word[63:32] = value;
            2'd2: replace_line_word[95:64] = value;
            default: replace_line_word[127:96] = value;
        endcase
    end
endfunction

wire [INDEX_WIDTH-1:0] request_index = request_addr[INDEX_WIDTH+3:4];
wire [TAG_WIDTH-1:0]   request_tag   = request_addr[31:INDEX_WIDTH+4];
wire [1:0]             request_word  = request_addr[3:2];
// The valid bit read combinationally in ST_IDLE, held for the decision in
// ST_LOOKUP, where the live index may already have moved on.
reg                    lookup_valid_q;
// The tag returned in ST_LOOKUP belongs to the index presented in ST_IDLE,
// which is this request's index. lookup_valid_q is that cycle's valid bit.
wire                   lookup_hit   = lookup_valid_q && (tag_rd_tag == request_tag);
wire [INDEX_WIDTH-1:0] live_index = req_addr[INDEX_WIDTH+3:4];
wire [27:0]            live_block = req_addr[31:4];
wire [27:0]            request_block = request_addr[31:4];
wire                   hot_hit0 = hot_valid[0] &&
                                  (hot_block0 == live_block);
wire                   hot_hit1 = hot_valid[1] &&
                                  (hot_block1 == live_block);
wire [127:0]           hot_hit_line = hot_hit0 ? hot_line0 : hot_line1;

wire req_fire = req_valid && req_ready;
wire refill_req_fire = refill_req_valid && refill_req_ready;
wire write_req_fire = mem_wr_valid && mem_wr_ready;
// A load resolved in the request cycle is, by definition, a hot-buffer hit.
wire fast_load_hit_event = (state == ST_IDLE) && req_fire && !req_write &&
                           (hot_hit0 || hot_hit1);
wire main_load_hit_event = fast_load_hit_event;
wire lookup_read_event = (state == ST_LOOKUP) && !request_write;
assign read_access_event  = main_load_hit_event || lookup_read_event;
assign read_hit_event     = main_load_hit_event ||
                            (lookup_read_event && lookup_hit);
assign read_miss_event    = lookup_read_event && !lookup_hit;
assign write_access_event = (state == ST_LOOKUP) && request_write;
assign write_hit_event    = write_access_event && lookup_hit;
assign write_miss_event   = write_access_event && !lookup_hit;

wire refill_expected_last = (refill_beat_count == 2'd3);
wire refill_protocol_error = refill_rsp_last != refill_expected_last;
wire refill_terminal = refill_rsp_valid &&
                       (refill_rsp_last || refill_expected_last);
wire refill_success = refill_terminal && refill_expected_last &&
                      refill_rsp_last && !refill_error_seen &&
                      !refill_rsp_error && !refill_protocol_error;

wire write_rsp_same_cycle = (state == ST_WRITE_REQ) && write_req_fire &&
                            mem_wr_rsp_valid;
wire write_rsp_later = (state == ST_WRITE_RESP) && mem_wr_rsp_valid;
wire store_write_done = (write_rsp_same_cycle || write_rsp_later) &&
                        !mem_wr_rsp_error;
wire store_commit = store_hit_latched && store_write_done;
// A store that missed the main array is written through to memory but does
// not update any cache line. Before the tag array went synchronous that was
// harmless, because the hot buffer could not answer a load unless the main
// tag agreed. The hot buffer is authoritative now, so a hot copy of that
// block would be left behind memory and would answer with pre-store data.
// Caught by tb/dcache_tb.sv TEST 4b.
wire store_miss_done = !store_hit_latched && store_write_done;
wire [127:0] refill_line_next =
    replace_line_word(refill_line_accum, refill_beat_count, refill_rsp_data);
wire [127:0] store_line_next =
    replace_line_word(data_rd_line, request_word, store_merged_word);

function [31:0] apply_wstrb;
    input [31:0] old_word;
    input [31:0] new_word;
    input [3:0]  byte_strobe;
    begin
        apply_wstrb = old_word;
        if(byte_strobe[0]) apply_wstrb[7:0]   = new_word[7:0];
        if(byte_strobe[1]) apply_wstrb[15:8]  = new_word[15:8];
        if(byte_strobe[2]) apply_wstrb[23:16] = new_word[23:16];
        if(byte_strobe[3]) apply_wstrb[31:24] = new_word[31:24];
    end
endfunction

assign req_ready = (state == ST_IDLE);
// A read hit resolves in ST_LOOKUP: the tag and the line are both there, so
// spending a further cycle in ST_CPU_RESP only to forward a registered copy
// costs an entire cycle on the most common main-array path.
wire lookup_read_hit = (state == ST_LOOKUP) && !request_write && lookup_hit;
assign rsp_valid = fast_load_hit_event || lookup_read_hit ||
                   (state == ST_CPU_RESP);
assign rsp_rdata = fast_load_hit_event ?
                       select_line_word(hot_hit_line, req_addr[3:2]) :
                   lookup_read_hit ?
                       select_line_word(data_rd_line, request_word) :
                       rsp_data_reg;
assign rsp_error = fast_load_hit_event ? 1'b0 : rsp_error_reg;

assign refill_req_valid = (state == ST_REFILL_REQ);
assign refill_req_addr  = {request_addr[31:4], 4'b0000};

assign mem_wr_valid = (state == ST_WRITE_REQ);
assign mem_wr_addr  = {request_addr[31:2], 2'b00};
assign mem_wr_data  = request_wdata;
assign mem_wr_strb  = request_wstrb;

// The tag read is issued from ST_IDLE on the live index and consumed in
// ST_LOOKUP. No other state consumes it, so no other state enables it.
assign tag_rd_index       = live_index;
assign tag_valid_rd_index = live_index;
assign tag_rd_en          = req_fire;
assign tag_wr_en    = (state == ST_REFILL_DATA) && refill_terminal;
assign tag_wr_index = request_index;
assign tag_wr_tag   = request_tag;
assign tag_wr_valid = refill_success;

// Drive the live address in IDLE so the sync RAM reads on the req_fire edge;
// later states use the latched request.
assign data_rd_index = (state == ST_IDLE) ? req_addr[INDEX_WIDTH+3:4] : request_index;
// Conservative gating. ST_LOOKUP and ST_CPU_RESP consume the line, and
// ST_CPU_RESP is reachable from ST_LOOKUP, ST_REFILL_DATA and ST_WRITE_RESP,
// so all of those keep reading. ST_REFILL_REQ and ST_WRITE_REQ can only lead
// to a state that does not consume it, and an idle cycle with no request
// leads nowhere, so those three are the ones that hold.
assign data_rd_en = ((state == ST_IDLE) && req_valid) ||
                    (state == ST_LOOKUP) || (state == ST_REFILL_DATA) ||
                    (state == ST_WRITE_RESP) || (state == ST_CPU_RESP);

assign data_wr_en = ((state == ST_REFILL_DATA) && refill_rsp_valid &&
                     !refill_rsp_error) || store_commit;
assign data_wr_index = request_index;
assign data_wr_word = store_commit ? request_word : refill_beat_count;
assign data_wr_data = store_commit ? store_merged_word : refill_rsp_data;

always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        state                   <= ST_IDLE;
        request_write           <= 1'b0;
        lookup_valid_q          <= 1'b0;
        request_addr            <= 32'h0000_0000;
        request_wdata           <= 32'h0000_0000;
        request_wstrb           <= 4'b0000;
        refill_beat_count       <= 2'd0;
        refill_error_seen       <= 1'b0;
        refill_requested_word   <= 32'h0000_0000;
        store_hit_latched       <= 1'b0;
        store_merged_word       <= 32'h0000_0000;
        rsp_data_reg            <= 32'h0000_0000;
        rsp_error_reg           <= 1'b0;
        refill_line_accum       <= 128'b0;
        hot_valid               <= 2'b00;
        hot_block0              <= 28'b0;
        hot_block1              <= 28'b0;
        hot_line0               <= 128'b0;
        hot_line1               <= 128'b0;
        hot_replace             <= 1'b0;
        access_count            <= 32'h0000_0000;
        read_count              <= 32'h0000_0000;
        write_count             <= 32'h0000_0000;
        hit_count               <= 32'h0000_0000;
        miss_count              <= 32'h0000_0000;
        read_hit_count          <= 32'h0000_0000;
        read_miss_count         <= 32'h0000_0000;
        write_hit_count         <= 32'h0000_0000;
        write_miss_count        <= 32'h0000_0000;
    end
    else begin
        // update the hot copy only after a successful write-through response
        // The L0 is filled from the line ST_LOOKUP just read. This used to
        // happen in ST_CPU_RESP under a main_read_response flag that no longer
        // fires; without moving it the hot buffer would only ever be filled
        // by stores, and every loop would run off the main array.
        if(lookup_read_hit) begin
            if(!hot_valid[0]) begin
                hot_valid[0] <= 1'b1; hot_block0 <= request_block;
                hot_line0    <= data_rd_line; hot_replace <= 1'b1;
            end
            else if(!hot_valid[1]) begin
                hot_valid[1] <= 1'b1; hot_block1 <= request_block;
                hot_line1    <= data_rd_line; hot_replace <= 1'b0;
            end
            else if(!hot_replace) begin
                hot_block0 <= request_block;
                hot_line0  <= data_rd_line; hot_replace <= 1'b1;
            end
            else begin
                hot_block1 <= request_block;
                hot_line1  <= data_rd_line; hot_replace <= 1'b0;
            end
        end
        if(store_miss_done) begin
            if(hot_valid[0] && (hot_block0 == request_block))
                hot_valid[0] <= 1'b0;
            if(hot_valid[1] && (hot_block1 == request_block))
                hot_valid[1] <= 1'b0;
        end
        if(store_commit) begin
            if(hot_valid[0] && (hot_block0 == request_block)) begin
                hot_line0    <= replace_line_word(hot_line0, request_word,
                                                   store_merged_word);
                hot_replace  <= 1'b1;
            end
            else if(hot_valid[1] && (hot_block1 == request_block)) begin
                hot_line1    <= replace_line_word(hot_line1, request_word,
                                                   store_merged_word);
                hot_replace  <= 1'b0;
            end
            else if(!hot_valid[0]) begin
                hot_valid[0] <= 1'b1;
                hot_block0   <= request_block;
                hot_line0    <= store_line_next;
                hot_replace  <= 1'b1;
            end
            else if(!hot_valid[1]) begin
                hot_valid[1] <= 1'b1;
                hot_block1   <= request_block;
                hot_line1    <= store_line_next;
                hot_replace  <= 1'b0;
            end
            else if(!hot_replace) begin
                hot_block0   <= request_block;
                hot_line0    <= store_line_next;
                hot_replace  <= 1'b1;
            end
            else begin
                hot_block1   <= request_block;
                hot_line1    <= store_line_next;
                hot_replace  <= 1'b0;
            end
        end

        case(state)
            ST_IDLE: begin
                if(req_fire) begin
                    request_write         <= req_write;
                    request_addr          <= req_addr;
                    lookup_valid_q        <= tag_valid_rd;
                    request_wdata         <= req_wdata;
                    request_wstrb         <= req_wstrb;
                    rsp_data_reg          <= 32'h0000_0000;
                    rsp_error_reg         <= 1'b0;
                    refill_error_seen     <= 1'b0;
                    refill_requested_word <= 32'h0000_0000;
                    store_hit_latched     <= 1'b0;
                    // Only the hot buffer can resolve a load in this cycle
                    // now: it compares the whole block address against two
                    // registers, and it is updated on every store commit, so
                    // it does not need the main tag to qualify it. A main
                    // hit that misses the hot buffer used to answer from
                    // data_rd_line one cycle later, but that path needed the
                    // tag in this cycle; it is folded into ST_LOOKUP.
                    if(!req_write && (hot_hit0 || hot_hit1)) begin
                        access_count   <= access_count + 1'b1;
                        read_count     <= read_count + 1'b1;
                        hit_count      <= hit_count + 1'b1;
                        read_hit_count <= read_hit_count + 1'b1;
                        hot_replace    <= hot_hit0 ? 1'b1 : 1'b0;
                        state          <= ST_IDLE;
                    end else begin
                        state <= ST_LOOKUP;
                    end
                end
            end

            ST_LOOKUP: begin
                access_count <= access_count + 1'b1;
                if(request_write) begin
                    write_count       <= write_count + 1'b1;
                    store_hit_latched <= lookup_hit;
                    store_merged_word <= apply_wstrb(
                                                     select_line_word(data_rd_line,
                                                                      request_word),
                                                     request_wdata,
                                                     request_wstrb);
                    if(lookup_hit) begin
                        hit_count       <= hit_count + 1'b1;
                        write_hit_count <= write_hit_count + 1'b1;
                    end
                    else begin
                        miss_count       <= miss_count + 1'b1;
                        write_miss_count <= write_miss_count + 1'b1;
                    end
                    state <= ST_WRITE_REQ;
                end
                else begin
                    read_count <= read_count + 1'b1;
                    if(lookup_hit) begin
                        hit_count      <= hit_count + 1'b1;
                        read_hit_count <= read_hit_count + 1'b1;
                        rsp_error_reg  <= 1'b0;
                        state          <= ST_IDLE;
                    end
                    else begin
                        miss_count       <= miss_count + 1'b1;
                        read_miss_count  <= read_miss_count + 1'b1;
                        refill_beat_count <= 2'd0;
                        state            <= ST_REFILL_REQ;
                    end
                end
            end

            ST_REFILL_REQ: begin
                if(refill_req_fire) begin
                    refill_beat_count     <= 2'd0;
                    refill_error_seen     <= 1'b0;
                    refill_requested_word <= 32'h0000_0000;
                    refill_line_accum     <= 128'b0;
                    state                 <= ST_REFILL_DATA;
                end
            end

            ST_REFILL_DATA: begin
                if(refill_rsp_valid) begin
                    refill_line_accum <= refill_line_next;
                    if(refill_beat_count == request_word)
                        refill_requested_word <= refill_rsp_data;

                    if(refill_rsp_error || refill_protocol_error)
                        refill_error_seen <= 1'b1;

                    if(refill_terminal) begin
                        if(refill_beat_count == request_word)
                            rsp_data_reg <= refill_rsp_data;
                        else
                            rsp_data_reg <= refill_requested_word;
                        rsp_error_reg <= !refill_success;
                        if(refill_success) begin
                            if(hot_valid[0] &&
                               (hot_block0 == request_block)) begin
                                hot_line0   <= refill_line_next;
                                hot_replace <= 1'b1;
                            end
                            else if(hot_valid[1] &&
                                    (hot_block1 == request_block)) begin
                                hot_line1   <= refill_line_next;
                                hot_replace <= 1'b0;
                            end
                            else if(!hot_valid[0]) begin
                                hot_valid[0] <= 1'b1;
                                hot_block0   <= request_block;
                                hot_line0    <= refill_line_next;
                                hot_replace  <= 1'b1;
                            end
                            else if(!hot_valid[1]) begin
                                hot_valid[1] <= 1'b1;
                                hot_block1   <= request_block;
                                hot_line1    <= refill_line_next;
                                hot_replace  <= 1'b0;
                            end
                            else if(!hot_replace) begin
                                hot_block0   <= request_block;
                                hot_line0    <= refill_line_next;
                                hot_replace  <= 1'b1;
                            end
                            else begin
                                hot_block1   <= request_block;
                                hot_line1    <= refill_line_next;
                                hot_replace  <= 1'b0;
                            end
                        end
                        state         <= ST_CPU_RESP;
                    end
                    else begin
                        refill_beat_count <= refill_beat_count + 1'b1;
                    end
                end
            end

            ST_WRITE_REQ: begin
                if(write_req_fire) begin
                    if(mem_wr_rsp_valid) begin
                        rsp_data_reg  <= 32'h0000_0000;
                        rsp_error_reg <= mem_wr_rsp_error;
                        state         <= ST_CPU_RESP;
                    end
                    else begin
                        state <= ST_WRITE_RESP;
                    end
                end
            end

            ST_WRITE_RESP: begin
                if(mem_wr_rsp_valid) begin
                    rsp_data_reg  <= 32'h0000_0000;
                    rsp_error_reg <= mem_wr_rsp_error;
                    state         <= ST_CPU_RESP;
                end
            end

            ST_CPU_RESP: begin
                // Only the refill and write-response paths reach here now.
                // The L0 fill moved to the single site above, driven by
                // lookup_read_hit.
                state <= ST_IDLE;
            end

            default: state <= ST_IDLE;
        endcase
    end
end

endmodule
