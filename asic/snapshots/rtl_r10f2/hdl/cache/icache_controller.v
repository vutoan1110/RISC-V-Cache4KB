module icache_controller #(
    parameter INDEX_WIDTH = 6,
    parameter TAG_WIDTH   = 22,
    // Entries in the L0 hot buffer. Each one holds a whole 128-bit line in
    // flip-flops, because the fast path reads it combinationally in the request
    // cycle and so it cannot be a block RAM. Eight entries is 1,024 flops for
    // 128 bytes; the data cache uses two. Power of two, 1 to 8.
    parameter L0_ENTRIES  = 8
)(
    input  wire                   clk,
    input  wire                   reset_n,

    // Native instruction request/response interface.
    input  wire                   req_valid,
    input  wire [31:0]            req_addr,
    output wire                   req_ready,
    output wire                   rsp_valid,
    output wire [31:0]            rsp_data,
    output wire                   rsp_error,

    // One line request followed by exactly four 32-bit response beats.
    output wire                   refill_req_valid,
    output wire [31:0]            refill_req_addr,
    input  wire                   refill_req_ready,
    input  wire                   refill_rsp_valid,
    input  wire [31:0]            refill_rsp_data,
    input  wire                   refill_rsp_last,
    input  wire                   refill_rsp_error,

    output reg  [31:0]            access_count,
    output reg  [31:0]            hit_count,
    output reg  [31:0]            miss_count,
    output wire                   access_event,
    output wire                   hit_event,
    output wire                   miss_event,


    // Tag storage interface. The tag port is synchronous: tag_rd_tag is the
    // tag of the index presented one cycle earlier. The valid port is
    // combinational, because the hot-buffer path has to consult it in the same
    // cycle it accepts a request.
    output wire                   tag_rd_en,
    output wire [INDEX_WIDTH-1:0] tag_rd_index,
    input  wire [TAG_WIDTH-1:0]   tag_rd_tag,
    output wire [INDEX_WIDTH-1:0] tag_valid_rd_index,
    input  wire                   tag_valid_rd,
    output wire                   tag_wr_en,
    output wire [INDEX_WIDTH-1:0] tag_wr_index,
    output wire [TAG_WIDTH-1:0]   tag_wr_tag,
    output wire                   tag_wr_valid,

    // Data storage interface, also synchronous.
    output wire                   data_rd_en,
    output wire [INDEX_WIDTH-1:0] data_rd_index,
    input  wire [127:0]           data_rd_line,
    output wire                   data_wr_en,
    output wire [INDEX_WIDTH-1:0] data_wr_index,
    output wire [1:0]             data_wr_word,
    output wire [31:0]            data_wr_data
);

localparam [2:0] ST_IDLE        = 3'd0;
// Was ST_HIT_RESP. With a synchronous tag this state is reached before the
// hit is known, so it is the lookup state now, matching icache_dse_core.
localparam [2:0] ST_LOOKUP      = 3'd1;
localparam [2:0] ST_REFILL_REQ  = 3'd2;
localparam [2:0] ST_REFILL_DATA = 3'd3;
localparam [2:0] ST_MISS_RESP   = 3'd4;

reg [2:0] state;
reg [31:0] miss_line_base;
reg [INDEX_WIDTH-1:0] miss_index;
reg [TAG_WIDTH-1:0]   miss_tag;
reg [1:0]             miss_word;
reg [2:0]             refill_beat_count;
reg                   refill_error_seen;
reg [31:0]            miss_rsp_data;
reg                   miss_rsp_error;
reg [127:0]           refill_line_accum;

// 8-entry direct-mapped L0 for same-cycle response; the main tag is authoritative.
localparam L0_IDX_BITS = (L0_ENTRIES > 1) ? $clog2(L0_ENTRIES) : 1;
reg [L0_ENTRIES-1:0]  hot_valid;
// Tag is everything above the index. Both must move together: pinning this
// at bit 3 while the index narrows leaves bits in neither field.
reg [27-L0_IDX_BITS:0] hot_tag [0:L0_ENTRIES-1];
reg [127:0]           hot_line [0:L0_ENTRIES-1];
// R10a -- main-array valid bit of the line each hot entry holds. The hot hit
// used to read the tag RAM's valid bit at the live index: a LINE_COUNT:1 mux
// on the fetch critical path. That bit only matters when the hot tag matches,
// i.e. when the live line IS the hot entry's line, so it is kept per hot
// entry instead: set on a fill (the line is valid then) and following every
// tag-RAM valid write to that line. Checked every cycle by icache.v.
reg [L0_ENTRIES-1:0]  hot_mvalid;

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

wire [INDEX_WIDTH-1:0] request_index;
wire [TAG_WIDTH-1:0]   request_tag;
wire [1:0]             request_word;
wire                   request_hit;
wire                   request_fire;
wire                   miss_accept;
wire                   refill_write_beat;
wire                   refill_success;
wire [27:0]            request_block;
wire [27:0]            miss_block;
wire [L0_IDX_BITS-1:0] hot_index;
wire [L0_IDX_BITS-1:0] miss_hot_index;
wire                   hot_hit;
wire [127:0]           hot_hit_line;
wire [127:0]           refill_line_next;

wire lookup_active = (state == ST_LOOKUP);
// The valid bit is read combinationally at the live index in ST_IDLE. By
// ST_LOOKUP the live index may have moved, so the bit that belongs to this
// request is latched alongside the tag and the index.
reg  lookup_valid_q;

assign request_word  = req_addr[3:2];
assign request_index = req_addr[(4 + INDEX_WIDTH) - 1:4];
assign request_tag   = req_addr[31:(4 + INDEX_WIDTH)];
// The main-array decision is made in ST_LOOKUP, against the tag that the
// synchronous array returned for the index presented in ST_IDLE, and the tag
// latched from that same request.
assign request_hit   = lookup_valid_q && (tag_rd_tag == miss_tag);
assign request_block = req_addr[31:4];
assign miss_block    = {miss_tag, miss_index};
assign hot_index      = request_block[L0_IDX_BITS-1:0];
assign miss_hot_index = miss_block[L0_IDX_BITS-1:0];
assign hot_hit        = hot_valid[hot_index] && hot_mvalid[hot_index] &&
                        (hot_tag[hot_index] == request_block[27:L0_IDX_BITS]);
assign hot_hit_line   = hot_line[hot_index];

assign req_ready    = (state == ST_IDLE);
assign request_fire = req_valid && req_ready;
// The miss is accepted in ST_LOOKUP now, on the latched request.
assign miss_accept  = lookup_active && !request_hit;
// The hot buffer answers in the request cycle. It is qualified by the main
// array's valid bit (its per-entry copy, hot_mvalid), not by its tag: the
// tag is no longer readable in this cycle, and icache_dse_core has never
// used it here either.
wire fast_hit_response = (state == ST_IDLE) && request_fire && hot_hit;

// An access is counted when the hot buffer answers it, or when ST_LOOKUP
// resolves it. Exactly one of those happens per accepted request.
assign access_event = fast_hit_response || lookup_active;
assign hit_event    = fast_hit_response || (lookup_active && request_hit);
assign miss_event   = lookup_active && !request_hit;

// Main data is synchronous M9K. An L0 hit completes same-cycle; other main
// hits take one registered read cycle, then fill L0.
// Reads are issued from ST_IDLE on the live index and consumed in ST_LOOKUP.
// Nothing else in the machine consumes them, so nothing else enables them.
assign tag_rd_index       = request_index;
assign data_rd_index      = request_index;
assign tag_valid_rd_index = request_index;
assign tag_rd_en          = request_fire && !hot_hit;
assign data_rd_en         = request_fire && !hot_hit;

assign rsp_valid = fast_hit_response || (lookup_active && request_hit) ||
                   (state == ST_MISS_RESP);
assign rsp_data  = fast_hit_response ? select_line_word(hot_hit_line, request_word) :
                   lookup_active ?
                       select_line_word(data_rd_line, miss_word) :
                       miss_rsp_data;
assign rsp_error = (state == ST_MISS_RESP) && miss_rsp_error;

assign refill_req_valid = (state == ST_REFILL_REQ);
assign refill_req_addr  = miss_line_base;

assign refill_write_beat = (state == ST_REFILL_DATA) && refill_rsp_valid &&
                           (refill_beat_count < 3'd4);
assign refill_success = refill_write_beat && refill_rsp_last &&
                        (refill_beat_count == 3'd3) &&
                        !refill_error_seen && !refill_rsp_error;
assign refill_line_next = replace_line_word(refill_line_accum,
                                             refill_beat_count[1:0],
                                             refill_rsp_data);

// invalidate on miss; re-validate only after a clean beat 4 (refill_rsp_last)
assign tag_wr_en    = miss_accept || refill_success;
assign tag_wr_index = miss_index;
assign tag_wr_tag   = miss_tag;
assign tag_wr_valid = refill_success;

assign data_wr_en    = refill_write_beat;
assign data_wr_index = miss_index;
assign data_wr_word  = refill_beat_count[1:0];
assign data_wr_data  = refill_rsp_data;

integer hi;
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        state               <= ST_IDLE;
        miss_line_base      <= 32'h0000_0000;
        miss_index          <= {INDEX_WIDTH{1'b0}};
        miss_tag            <= {TAG_WIDTH{1'b0}};
        miss_word           <= 2'b00;
        lookup_valid_q      <= 1'b0;
        refill_beat_count   <= 3'd0;
        refill_error_seen   <= 1'b0;
        miss_rsp_data       <= 32'h0000_0013;
        miss_rsp_error      <= 1'b0;
        refill_line_accum   <= 128'b0;
        hot_valid           <= {L0_ENTRIES{1'b0}};
        for(hi = 0; hi < L0_ENTRIES; hi = hi + 1) begin
            hot_tag[hi]  <= {(28-L0_IDX_BITS){1'b0}};
            hot_line[hi] <= 128'b0;
        end
        access_count        <= 32'h0000_0000;
        hit_count           <= 32'h0000_0000;
        miss_count          <= 32'h0000_0000;
    end
    else begin
        case(state)
            ST_IDLE: begin
                if(request_fire) begin
                    if(hot_hit) begin
                        // Answered from the hot buffer in this cycle; the main
                        // array was never consulted beyond its valid bit.
                        access_count <= access_count + 1'b1;
                        hit_count    <= hit_count + 1'b1;
                        state        <= ST_IDLE;
                    end
                    else begin
                        // Tag and data reads were issued this cycle. Latch
                        // everything the decision in ST_LOOKUP will need.
                        miss_line_base    <= {req_addr[31:4], 4'b0000};
                        miss_index        <= request_index;
                        miss_tag          <= request_tag;
                        miss_word         <= request_word;
                        lookup_valid_q    <= tag_valid_rd;
                        refill_beat_count <= 3'd0;
                        refill_error_seen <= 1'b0;
                        refill_line_accum <= 128'b0;
                        miss_rsp_data     <= 32'h0000_0013;
                        miss_rsp_error    <= 1'b0;
                        state             <= ST_LOOKUP;
                    end
                end
            end

            ST_LOOKUP: begin
                // one edge: access == hit + miss
                access_count <= access_count + 1'b1;
                if(request_hit) begin
                    hit_count                 <= hit_count + 1'b1;
                    hot_valid[miss_hot_index] <= 1'b1;
                    hot_tag[miss_hot_index]   <= miss_block[27:L0_IDX_BITS];
                    hot_line[miss_hot_index]  <= data_rd_line;
                    state <= ST_IDLE;
                end
                else begin
                    miss_count <= miss_count + 1'b1;
                    state      <= ST_REFILL_REQ;
                end
            end

            ST_REFILL_REQ: begin
                if(refill_req_valid && refill_req_ready)
                    state <= ST_REFILL_DATA;
            end

            ST_REFILL_DATA: begin
                if(refill_rsp_valid) begin
                    if(refill_rsp_error)
                        refill_error_seen <= 1'b1;

                    if(refill_beat_count < 3'd4) begin
                        refill_line_accum <= refill_line_next;
                        if(refill_beat_count[1:0] == miss_word)
                            miss_rsp_data <= refill_rsp_data;
                    end

                    if(refill_success) begin
                        hot_valid[miss_hot_index] <= 1'b1;
                        hot_tag[miss_hot_index] <= miss_block[27:L0_IDX_BITS];
                        hot_line[miss_hot_index] <= refill_line_next;
                    end

                    if(refill_rsp_last) begin
                        // early/late LAST or backend error -> invalidate, error the request
                        miss_rsp_error <= refill_error_seen || refill_rsp_error ||
                                          (refill_beat_count != 3'd3);
                        state <= ST_MISS_RESP;
                    end
                    else if(refill_beat_count < 3'd4) begin
                        refill_beat_count <= refill_beat_count + 1'b1;
                    end
                end
            end

            ST_MISS_RESP: begin
                // refill completion IS the response; not replayed as a hit
                state <= ST_IDLE;
            end

            default: state <= ST_IDLE;
        endcase
    end
end

// R10a -- hot_mvalid upkeep. Line miss_index can only sit in hot entry
// miss_hot_index (its low index bits are the hot index); it is there when the
// line-index bits kept in that entry's tag match.
localparam HOT_LI_BITS = INDEX_WIDTH - L0_IDX_BITS;
wire hot_holds_miss_line;
generate
if(HOT_LI_BITS > 0) begin : g_hot_li
    assign hot_holds_miss_line =
        (hot_tag[miss_hot_index][HOT_LI_BITS-1:0] == miss_index[INDEX_WIDTH-1:L0_IDX_BITS]);
end
else begin : g_hot_li_none
    assign hot_holds_miss_line = 1'b1;
end
endgenerate
// A hot fill: exactly the two places the main always block writes hot_line.
wire hot_fill = (lookup_active && request_hit) || refill_success;

// synthesis translate_off
initial if(INDEX_WIDTH < L0_IDX_BITS)
    $fatal(1, "%m: R10a needs INDEX_WIDTH >= log2(L0_ENTRIES), got %0d < %0d",
           INDEX_WIDTH, L0_IDX_BITS);
// synthesis translate_on

always @(posedge clk or negedge reset_n) begin
    if(!reset_n)
        hot_mvalid <= {L0_ENTRIES{1'b0}};
    else if(hot_fill)
        hot_mvalid[miss_hot_index] <= 1'b1;
    else if(tag_wr_en && hot_holds_miss_line)
        hot_mvalid[miss_hot_index] <= tag_wr_valid;
end

endmodule
