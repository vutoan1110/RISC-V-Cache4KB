// N-way set-associative blocking I-cache core, for the associativity axis of the cache design-space
// exploration (review item M2, 2026-09-30).
//   CACHE_CONFIG 4 (SA4): WAYS = 4.
//   CACHE_CONFIG 5      : WAYS = 2, used only to check this core against the SA2 point of
//                         icache_dse_core.v: with two ways, tree pseudo-LRU is exactly the SA2 policy, so both
//                         must give the same result on every counter, cycle for cycle.
// The controller is icache_dse_core.v's (same FSM encoding, synchronous tag read issued in ST_IDLE and consumed
// in ST_LOOKUP, the L0 hot buffer of L0_ENTRIES full lines); only the way count is generalised, and there is
// no victim buffer. L0 stays a coherent subset of the main array because every block of a set shares one L0
// slot: the L0 index is the low block bits, which are also the low set-index bits (L0_IDX_BITS <= INDEX_WIDTH),
// so refilling any way of a set overwrites the L0 slot an evicted block of that set could occupy.
module icache_nway_core #(
    parameter LINE_COUNT      = 64,
    parameter WAYS            = 4,
    parameter LINE_WORDS      = 4,
    parameter L0_ENTRIES      = 8
)(
    input  wire        clk,
    input  wire        reset_n,
    input  wire        req_valid,
    input  wire [31:0] req_addr,
    output wire        req_ready,
    output wire        rsp_valid,
    output wire [31:0] rsp_data,
    output wire        rsp_error,
    output wire        refill_req_valid,
    output wire [31:0] refill_req_addr,
    input  wire        refill_req_ready,
    input  wire        refill_rsp_valid,
    input  wire [31:0] refill_rsp_data,
    input  wire        refill_rsp_last,
    input  wire        refill_rsp_error,
    output reg  [31:0] access_count,
    output reg  [31:0] hit_count,
    output reg  [31:0] miss_count,
    output reg  [31:0] main_hit_count,
    output wire [31:0] victim_hit_count,
    output reg  [31:0] true_miss_count,
    output wire        access_event,
    output wire        hit_event,
    output wire        miss_event,
    output wire        main_hit_event,
    output wire        victim_hit_event,
    output wire        true_miss_event,
    output wire [3:0]  hit_way_vec_dbg,
    output wire [1:0]  replacement_way_dbg
);

function integer clog2;
    input integer value;
    integer tmp;
    begin
        tmp = value - 1;
        clog2 = 0;
        while(tmp > 0) begin
            clog2 = clog2 + 1;
            tmp = tmp >> 1;
        end
    end
endfunction

localparam WAYS_OK = (WAYS == 2) || (WAYS == 4);
localparam EFF_WAYS = WAYS_OK ? WAYS : 4;
localparam WAY_BITS = (EFF_WAYS == 4) ? 2 : 1;
localparam SET_COUNT = LINE_COUNT / EFF_WAYS;
localparam INDEX_WIDTH = (SET_COUNT > 1) ? clog2(SET_COUNT) : 1;
localparam LINE_WORDS_OK = (LINE_WORDS >= 2) && (LINE_WORDS <= 16) &&
                           ((LINE_WORDS & (LINE_WORDS - 1)) == 0);
localparam EFF_LINE_WORDS = LINE_WORDS_OK ? LINE_WORDS : 4;
localparam LINE_BYTES  = EFF_LINE_WORDS * 4;
localparam OFFSET_BITS = clog2(LINE_BYTES);
localparam WORD_BITS   = clog2(EFF_LINE_WORDS);
localparam LINE_WIDTH  = 32 * EFF_LINE_WORDS;
localparam BLOCK_WIDTH = 32 - OFFSET_BITS;
localparam TAG_WIDTH = 32 - OFFSET_BITS - INDEX_WIDTH;
localparam [31:0] LAST_WORD_32 = EFF_LINE_WORDS - 1;
localparam [WORD_BITS-1:0] LAST_WORD = LAST_WORD_32[WORD_BITS-1:0];

// Same encoding as icache_dse_core.v; the swap/evict states of the victim buffer are unused here.
localparam [3:0] ST_IDLE         = 4'd0;
localparam [3:0] ST_LOOKUP       = 4'd1;
localparam [3:0] ST_HIT_RESP     = 4'd2;
localparam [3:0] ST_REFILL_REQ   = 4'd7;
localparam [3:0] ST_REFILL_DATA  = 4'd8;
localparam [3:0] ST_MISS_RESP    = 4'd9;

reg [3:0] state;
reg [31:0] request_addr;
reg [WORD_BITS-1:0] refill_beat_count;
reg refill_error_seen;
reg [1:0] refill_way;
reg [31:0] refill_requested_word;
reg [31:0] rsp_data_reg;
reg rsp_error_reg;
reg main_read_response;
reg [LINE_WIDTH-1:0] refill_line_accum;

localparam L0_IDX_BITS = (L0_ENTRIES > 1) ? clog2(L0_ENTRIES) : 1;
reg [L0_ENTRIES-1:0] hot_valid;
reg [BLOCK_WIDTH-1-L0_IDX_BITS:0] hot_tag [0:L0_ENTRIES-1];
reg [LINE_WIDTH-1:0] hot_line [0:L0_ENTRIES-1];
reg [1:0] hot_way [0:L0_ENTRIES-1];

reg [EFF_WAYS*SET_COUNT-1:0] valid_v;
// Tree pseudo-LRU, three bits per set (two ways use bit 0 only); see dcache_nway_core.v.
reg [3*SET_COUNT-1:0] plru_v;

function [31:0] select_line_word;
    input [LINE_WIDTH-1:0] line;
    input [WORD_BITS-1:0] word;
    begin
        select_line_word = line[(word*32) +: 32];
    end
endfunction

function [LINE_WIDTH-1:0] replace_line_word;
    input [LINE_WIDTH-1:0] line;
    input [WORD_BITS-1:0] word;
    input [31:0] value;
    begin
        replace_line_word = line;
        replace_line_word[(word*32) +: 32] = value;
    end
endfunction

function [2:0] plru_touch;
    input [2:0] bits;
    input [1:0] w;
    begin
        plru_touch = bits;
        if(EFF_WAYS == 2) begin
            plru_touch[0] = (w[0] == 1'b0);
        end else begin
            plru_touch[0] = (w[1] == 1'b0);
            if(w[1] == 1'b0) plru_touch[1] = (w[0] == 1'b0);
            else             plru_touch[2] = (w[0] == 1'b0);
        end
    end
endfunction

function [1:0] plru_victim;
    input [2:0] bits;
    begin
        if(EFF_WAYS == 2) plru_victim = {1'b0, bits[0]};
        else plru_victim = bits[0] ? {1'b1, bits[2]} : {1'b0, bits[1]};
    end
endfunction

wire [INDEX_WIDTH-1:0] request_index =
    request_addr[INDEX_WIDTH+OFFSET_BITS-1:OFFSET_BITS];
wire [TAG_WIDTH-1:0] request_tag = request_addr[31:INDEX_WIDTH+OFFSET_BITS];
wire [WORD_BITS-1:0] request_word = request_addr[OFFSET_BITS-1:2];
wire [BLOCK_WIDTH-1:0] request_block = request_addr[31:OFFSET_BITS];

wire [INDEX_WIDTH-1:0] live_index =
    req_addr[INDEX_WIDTH+OFFSET_BITS-1:OFFSET_BITS];
wire [BLOCK_WIDTH-1:0] live_block = req_addr[31:OFFSET_BITS];
wire [L0_IDX_BITS-1:0] live_hot_index = live_block[L0_IDX_BITS-1:0];
wire [L0_IDX_BITS-1:0] request_hot_index = request_block[L0_IDX_BITS-1:0];
wire [1:0] live_hot_way = hot_way[live_hot_index];
wire hot_selected_valid = valid_v[{live_hot_way[WAY_BITS-1:0], live_index}];
wire hot_hit = hot_valid[live_hot_index] && hot_selected_valid &&
               (hot_tag[live_hot_index] == live_block[BLOCK_WIDTH-1:L0_IDX_BITS]);
wire [LINE_WIDTH-1:0] hot_hit_line = hot_line[live_hot_index];

wire [3:0] main_hit_vec;
wire main_hit = |main_hit_vec;
wire [1:0] hit_way = main_hit_vec[3] ? 2'd3 : (main_hit_vec[2] ? 2'd2 :
                     (main_hit_vec[1] ? 2'd1 : 2'd0));

wire [2:0] plru_req  = plru_v[request_index*3 +: 3];
wire [2:0] plru_live = plru_v[live_index*3 +: 3];
reg [1:0] selected_refill_way;
reg invalid_found;
integer si;
always @(*) begin
    selected_refill_way = plru_victim(plru_req);
    invalid_found = 1'b0;
    for(si = 0; si < EFF_WAYS; si = si + 1) begin
        if(!invalid_found && !valid_v[{si[WAY_BITS-1:0], request_index}]) begin
            selected_refill_way = si[1:0];
            invalid_found = 1'b1;
        end
    end
end

wire lookup_active = (state == ST_LOOKUP);
wire req_fire = req_valid && req_ready;

wire main_hit_accept_event = (state == ST_IDLE) && req_fire && hot_hit;
wire fast_main_hit_event = main_hit_accept_event;
wire lookup_true_miss = lookup_active && !main_hit;
assign access_event = main_hit_accept_event || lookup_active;
assign main_hit_event = main_hit_accept_event || (lookup_active && main_hit);
assign victim_hit_event = 1'b0;
assign victim_hit_count = 32'h0;
assign true_miss_event = lookup_true_miss;
assign hit_event = main_hit_event;
assign miss_event = true_miss_event;
assign hit_way_vec_dbg = main_hit_accept_event ? (4'b0001 << live_hot_way) :
                         (lookup_active ? main_hit_vec : 4'b0000);
assign replacement_way_dbg = selected_refill_way;

wire [EFF_WAYS*LINE_WIDTH-1:0] bank_rd_flat;
wire [LINE_WIDTH-1:0] refill_way_line = bank_rd_flat[refill_way[WAY_BITS-1:0]*LINE_WIDTH +: LINE_WIDTH];

assign req_ready = (state == ST_IDLE);
assign rsp_valid = fast_main_hit_event || (state == ST_HIT_RESP) ||
                   (state == ST_MISS_RESP);
assign rsp_data = fast_main_hit_event ?
                  select_line_word(hot_hit_line, req_addr[OFFSET_BITS-1:2]) :
                  (main_read_response ? select_line_word(refill_way_line, request_word)
                                      : rsp_data_reg);
assign rsp_error = fast_main_hit_event ? 1'b0 : rsp_error_reg;
assign refill_req_valid = (state == ST_REFILL_REQ);
assign refill_req_addr =
    {request_addr[31:OFFSET_BITS], {OFFSET_BITS{1'b0}}};

wire refill_expected_last = (refill_beat_count == LAST_WORD);
wire refill_protocol_error = refill_rsp_last != refill_expected_last;
wire refill_terminal = refill_rsp_valid &&
                       (refill_rsp_last || refill_expected_last);
wire refill_success = refill_terminal && refill_expected_last &&
                      refill_rsp_last && !refill_error_seen &&
                      !refill_rsp_error && !refill_protocol_error;
wire refill_commit = (state == ST_REFILL_DATA) && refill_rsp_valid && refill_terminal &&
                     refill_success;

wire [INDEX_WIDTH-1:0] bank_rd_index =
    (state == ST_IDLE) ? live_index : request_index;
wire bank_rd_en = (state != ST_IDLE) || (req_fire && !hot_hit);
wire refill_write = (state == ST_REFILL_DATA) && refill_rsp_valid &&
                    !refill_rsp_error;
wire [WORD_BITS+3:0] refill_beat_count_p = {4'b0, refill_beat_count};
wire [3:0] bank_wr_word = refill_beat_count_p[3:0];
wire [LINE_WIDTH-1:0] refill_line_next =
    replace_line_word(refill_line_accum, refill_beat_count, refill_rsp_data);

genvar gw;
generate
    for(gw = 0; gw < 4; gw = gw + 1) begin : g_way
        if(gw < EFF_WAYS) begin : g_live
            localparam [31:0] WAY_ID_32 = gw;
            reg [TAG_WIDTH-1:0] tag_mem [0:SET_COUNT-1];
            reg [TAG_WIDTH-1:0] tag_rd_q;
            always @(posedge clk) begin
                if(refill_commit && (refill_way == gw)) tag_mem[request_index] <= request_tag;
                if(req_fire) tag_rd_q <= tag_mem[live_index];
            end
            assign main_hit_vec[gw] = valid_v[{WAY_ID_32[WAY_BITS-1:0], request_index}] &&
                                      (tag_rd_q == request_tag);
            wire bank_wr_en = refill_write && (refill_way == gw);
            cache_dse_data_bank #(.SET_COUNT(SET_COUNT), .INDEX_WIDTH(INDEX_WIDTH),
                                  .LINE_WORDS(EFF_LINE_WORDS)) u_data (
                .clk(clk), .rd_en(bank_rd_en), .rd_index(bank_rd_index),
                .rd_line(bank_rd_flat[gw*LINE_WIDTH +: LINE_WIDTH]),
                .wr_en(bank_wr_en), .wr_index(request_index), .wr_word(bank_wr_word),
                .wr_data(refill_rsp_data));
        end else begin : g_absent
            assign main_hit_vec[gw] = 1'b0;
        end
    end
endgenerate

integer i;
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        state <= ST_IDLE;
        request_addr <= 32'h0;
        refill_beat_count <= {WORD_BITS{1'b0}};
        refill_error_seen <= 1'b0;
        refill_way <= 2'b00;
        refill_requested_word <= 32'h0;
        rsp_data_reg <= 32'h0000_0013;
        rsp_error_reg <= 1'b0;
        main_read_response <= 1'b0;
        refill_line_accum <= {LINE_WIDTH{1'b0}};
        hot_valid <= {L0_ENTRIES{1'b0}};
        for(i = 0; i < L0_ENTRIES; i = i + 1) begin
            hot_tag[i] <= {(BLOCK_WIDTH-L0_IDX_BITS){1'b0}};
            hot_line[i] <= {LINE_WIDTH{1'b0}};
            hot_way[i] <= 2'b00;
        end
        valid_v <= {(EFF_WAYS*SET_COUNT){1'b0}};
        plru_v <= {(3*SET_COUNT){1'b0}};
        access_count <= 32'h0;
        hit_count <= 32'h0;
        miss_count <= 32'h0;
        main_hit_count <= 32'h0;
        true_miss_count <= 32'h0;
    end else begin
        case(state)
            ST_IDLE: begin
                if(req_fire) begin
                    rsp_error_reg <= 1'b0;
                    refill_error_seen <= 1'b0;
                    main_read_response <= 1'b0;
                    if(hot_hit) begin
                        access_count <= access_count + 1'b1;
                        hit_count <= hit_count + 1'b1;
                        main_hit_count <= main_hit_count + 1'b1;
                        plru_v[live_index*3 +: 3] <= plru_touch(plru_live, live_hot_way);
                        state <= ST_IDLE;
                    end else begin
                        request_addr <= req_addr;
                        refill_line_accum <= {LINE_WIDTH{1'b0}};
                        state <= ST_LOOKUP;
                    end
                end
            end
            ST_LOOKUP: begin
                access_count <= access_count + 1'b1;
                if(main_hit) begin
                    hit_count <= hit_count + 1'b1;
                    main_hit_count <= main_hit_count + 1'b1;
                    refill_way <= hit_way;
                    main_read_response <= 1'b1;
                    plru_v[request_index*3 +: 3] <= plru_touch(plru_req, hit_way);
                    state <= ST_HIT_RESP;
                end else begin
                    miss_count <= miss_count + 1'b1;
                    true_miss_count <= true_miss_count + 1'b1;
                    refill_beat_count <= {WORD_BITS{1'b0}};
                    refill_requested_word <= 32'h0;
                    refill_way <= selected_refill_way;
                    valid_v[{selected_refill_way[WAY_BITS-1:0], request_index}] <= 1'b0;
                    state <= ST_REFILL_REQ;
                end
            end
            ST_HIT_RESP: begin
                if(main_read_response) begin
                    hot_valid[request_hot_index] <= 1'b1;
                    hot_tag[request_hot_index] <= request_block[BLOCK_WIDTH-1:L0_IDX_BITS];
                    hot_line[request_hot_index] <= refill_way_line;
                    hot_way[request_hot_index] <= refill_way;
                end
                state <= ST_IDLE;
            end
            ST_REFILL_REQ: begin
                if(refill_req_valid && refill_req_ready) begin
                    refill_beat_count <= {WORD_BITS{1'b0}};
                    refill_error_seen <= 1'b0;
                    refill_line_accum <= {LINE_WIDTH{1'b0}};
                    state <= ST_REFILL_DATA;
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
                        rsp_data_reg <= (refill_beat_count == request_word) ?
                                        refill_rsp_data : refill_requested_word;
                        rsp_error_reg <= !refill_success;
                        if(refill_success) begin
                            // The tag itself is written in g_way on refill_commit.
                            valid_v[{refill_way[WAY_BITS-1:0], request_index}] <= 1'b1;
                            plru_v[request_index*3 +: 3] <= plru_touch(plru_req, refill_way);
                            hot_valid[request_hot_index] <= 1'b1;
                            hot_tag[request_hot_index] <=
                                request_block[BLOCK_WIDTH-1:L0_IDX_BITS];
                            hot_line[request_hot_index] <= refill_line_next;
                            hot_way[request_hot_index] <= refill_way;
                        end
                        state <= ST_MISS_RESP;
                    end else begin
                        refill_beat_count <= refill_beat_count + 1'b1;
                    end
                end
            end
            ST_MISS_RESP: state <= ST_IDLE;
            default: state <= ST_IDLE;
        endcase
    end
end

// synthesis translate_off
initial begin
    if(!WAYS_OK)
        $fatal(1, "icache_nway_core: WAYS=%0d is unsupported (2 or 4).", WAYS);
    if((LINE_COUNT % EFF_WAYS) != 0 || (SET_COUNT & (SET_COUNT - 1)) != 0)
        $fatal(1, "icache_nway_core: LINE_COUNT=%0d must give a power-of-two set count at %0d ways.",
               LINE_COUNT, EFF_WAYS);
    if(L0_IDX_BITS > INDEX_WIDTH)
        $fatal(1, "icache_nway_core: L0 coherence needs L0_IDX_BITS (%0d) <= INDEX_WIDTH (%0d).",
               L0_IDX_BITS, INDEX_WIDTH);
    if(!LINE_WORDS_OK)
        $fatal(1, "icache_nway_core: LINE_WORDS=%0d is unsupported. It must be a power of two from 2 to 16.",
               LINE_WORDS);
end
always @(posedge clk or negedge reset_n) begin
    if(reset_n && lookup_active) begin
        if((main_hit_vec & (main_hit_vec - 1'b1)) != 4'b0000)
            $fatal(1, "I-cache duplicate hit across ways");
        if(!(main_hit_event ^ true_miss_event))
            $fatal(1, "I-cache access classification is not exclusive");
    end
end
// synthesis translate_on

endmodule
