// Configurable blocking I-cache core.
// CACHE_CONFIG: 1 = 32-set x 2-way SA2, 2 = 64-line DM + VC4.
// CACHE_CONFIG 0 stays on the DM controller in icache.v.
module icache_dse_core #(
    parameter LINE_COUNT      = 64,
    parameter CACHE_CONFIG    = 1,
    parameter VICTIM_ENTRIES  = 4,
    parameter LINE_WORDS      = 4,
    // Depth of the L0 hot buffer; see icache_controller.v.
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
    output reg  [31:0] victim_hit_count,
    output reg  [31:0] true_miss_count,
    output wire        access_event,
    output wire        hit_event,
    output wire        miss_event,
    output wire        main_hit_event,
    output wire        victim_hit_event,
    output wire        true_miss_event,
    output wire        hit_way0_dbg,
    output wire        hit_way1_dbg,
    output wire [VICTIM_ENTRIES-1:0] victim_hit_vec_dbg,
    output wire        replacement_way_dbg
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

localparam IS_SA2 = (CACHE_CONFIG == 1);
localparam IS_VC4 = (CACHE_CONFIG == 2);
// Victim storage exists only where it can be read. A configuration with
// IS_VC4 low never writes and never reads these arrays, so sizing them by
// VICTIM_ENTRIES would leave dead memory for the optimiser to remove.
localparam VC_DEPTH = IS_VC4 ? VICTIM_ENTRIES : 1;
localparam SET_COUNT = IS_SA2 ? (LINE_COUNT / 2) : LINE_COUNT;
localparam INDEX_WIDTH = (SET_COUNT > 1) ? clog2(SET_COUNT) : 1;
// A line size outside the supported set makes several derived widths illegal
// -- at LINE_WORDS=1, OFFSET_BITS is 2 and request_addr[OFFSET_BITS-1:2] is a
// reversed part-select -- so elaboration fails with a message about a range
// before the check below can run. Widths are therefore derived from a clamped
// copy, which lets elaboration finish and lets the guard report the real value.
localparam LINE_WORDS_OK = (LINE_WORDS >= 2) && (LINE_WORDS <= 16) &&
                           ((LINE_WORDS & (LINE_WORDS - 1)) == 0);
localparam EFF_LINE_WORDS = LINE_WORDS_OK ? LINE_WORDS : 4;
localparam LINE_BYTES  = EFF_LINE_WORDS * 4;
localparam OFFSET_BITS = clog2(LINE_BYTES);
localparam WORD_BITS   = clog2(EFF_LINE_WORDS);
localparam LINE_WIDTH  = 32 * EFF_LINE_WORDS;
localparam BLOCK_WIDTH = 32 - OFFSET_BITS;
localparam TAG_WIDTH = 32 - OFFSET_BITS - INDEX_WIDTH;
localparam VC_INDEX_WIDTH = (VC_DEPTH > 1) ? clog2(VC_DEPTH) : 1;

// Parameter arithmetic is 32 bits wide; these counters are not. Taking the
// part-select of a 32-bit constant states which bits the hardware compares
// instead of letting every comparison widen the counter to 32 bits.
localparam [31:0] LAST_WORD_32 = EFF_LINE_WORDS - 1;
localparam [WORD_BITS-1:0] LAST_WORD = LAST_WORD_32[WORD_BITS-1:0];
localparam [31:0] VC_LAST_32 = VC_DEPTH - 1;
localparam [VC_INDEX_WIDTH-1:0] VC_LAST = VC_LAST_32[VC_INDEX_WIDTH-1:0];

localparam [3:0] ST_IDLE         = 4'd0;
localparam [3:0] ST_LOOKUP       = 4'd1;
localparam [3:0] ST_HIT_RESP     = 4'd2;
localparam [3:0] ST_SWAP_READ    = 4'd3;
localparam [3:0] ST_SWAP_WRITE   = 4'd4;
localparam [3:0] ST_EVICT_READ   = 4'd5;
localparam [3:0] ST_EVICT_WRITE  = 4'd6;
localparam [3:0] ST_REFILL_REQ   = 4'd7;
localparam [3:0] ST_REFILL_DATA  = 4'd8;
localparam [3:0] ST_MISS_RESP    = 4'd9;

reg [3:0] state;
reg [31:0] request_addr;
reg [WORD_BITS-1:0] transfer_beat;
reg [WORD_BITS-1:0] refill_beat_count;
reg refill_error_seen;
reg refill_way;
reg [31:0] refill_requested_word;
reg [31:0] rsp_data_reg;
reg rsp_error_reg;
reg main_read_response;
reg [LINE_WIDTH-1:0] refill_line_accum;
wire [LINE_WIDTH-1:0] bank0_rd_line;
wire [LINE_WIDTH-1:0] bank1_rd_line;

// See icache_controller.v: these are full lines in flip-flops because the
// fast path needs them in the request cycle.
localparam L0_IDX_BITS = (L0_ENTRIES > 1) ? clog2(L0_ENTRIES) : 1;
reg [L0_ENTRIES-1:0] hot_valid;
// See icache_controller.v: tag and index must narrow together.
reg [BLOCK_WIDTH-1-L0_IDX_BITS:0] hot_tag [0:L0_ENTRIES-1];
reg [LINE_WIDTH-1:0] hot_line [0:L0_ENTRIES-1];
reg [L0_ENTRIES-1:0] hot_way;

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

reg [TAG_WIDTH-1:0] tag_way0 [0:SET_COUNT-1];
reg [TAG_WIDTH-1:0] tag_way1 [0:SET_COUNT-1];
// Registered copies of the two tag ways; see the read below.
reg [TAG_WIDTH-1:0] tag_rd0_q;
reg [TAG_WIDTH-1:0] tag_rd1_q;
reg [SET_COUNT-1:0] valid_way0;
reg [SET_COUNT-1:0] valid_way1;
reg [SET_COUNT-1:0] replace_way;

reg [VC_DEPTH-1:0] vc_valid;
reg [BLOCK_WIDTH-1:0] vc_block [0:VC_DEPTH-1];
reg [31:0] vc_data [0:(VC_DEPTH*EFF_LINE_WORDS)-1];
reg [VC_INDEX_WIDTH-1:0] vc_replace_ptr;
reg [VC_INDEX_WIDTH-1:0] vc_selected;
reg old_main_valid;
reg [BLOCK_WIDTH-1:0] old_main_block;
reg [31:0] swap_word [0:EFF_LINE_WORDS-1];

wire [INDEX_WIDTH-1:0] request_index =
    request_addr[INDEX_WIDTH+OFFSET_BITS-1:OFFSET_BITS];
wire [TAG_WIDTH-1:0] request_tag = request_addr[31:INDEX_WIDTH+OFFSET_BITS];
wire [WORD_BITS-1:0] request_word = request_addr[OFFSET_BITS-1:2];
wire [BLOCK_WIDTH-1:0] request_block = request_addr[31:OFFSET_BITS];

// L0 is a coherent subset of main. Fast lookup reads only the small valid/way
// vectors; main tags are read (latched) in ST_LOOKUP so Quartus does not build
// an async tag mux next to the tag RAM.
wire [INDEX_WIDTH-1:0] live_index =
    req_addr[INDEX_WIDTH+OFFSET_BITS-1:OFFSET_BITS];
wire [BLOCK_WIDTH-1:0] live_block = req_addr[31:OFFSET_BITS];
wire [L0_IDX_BITS-1:0] live_hot_index = live_block[L0_IDX_BITS-1:0];
wire [L0_IDX_BITS-1:0] request_hot_index = request_block[L0_IDX_BITS-1:0];
wire hot_selected_valid = hot_way[live_hot_index] ?
                          (IS_SA2 && valid_way1[live_index]) :
                          valid_way0[live_index];
wire hot_hit = hot_valid[live_hot_index] && hot_selected_valid &&
               (hot_tag[live_hot_index] == live_block[BLOCK_WIDTH-1:L0_IDX_BITS]);
wire [LINE_WIDTH-1:0] hot_hit_line = hot_line[live_hot_index];

wire main_hit0 = valid_way0[request_index] &&
                 (tag_rd0_q == request_tag);
wire main_hit1 = IS_SA2 && valid_way1[request_index] &&
                 (tag_rd1_q == request_tag);
wire main_hit = main_hit0 || main_hit1;
wire selected_refill_way = !valid_way0[request_index] ? 1'b0 :
                           (!valid_way1[request_index] ? 1'b1 :
                            replace_way[request_index]);

reg [VC_DEPTH-1:0] vc_hit_vec;
reg vc_hit;
reg [VC_INDEX_WIDTH-1:0] vc_hit_index;
reg vc_has_invalid;
reg [VC_INDEX_WIDTH-1:0] vc_insert_index;
integer vi;
always @(*) begin
    vc_hit_vec = {VC_DEPTH{1'b0}};
    vc_hit = 1'b0;
    vc_hit_index = {VC_INDEX_WIDTH{1'b0}};
    vc_has_invalid = 1'b0;
    vc_insert_index = vc_replace_ptr;
    for(vi = 0; vi < VC_DEPTH; vi = vi + 1) begin
        if(IS_VC4 && vc_valid[vi] && (vc_block[vi] == request_block)) begin
            vc_hit_vec[vi] = 1'b1;
            if(!vc_hit) begin
                vc_hit = 1'b1;
                vc_hit_index = vi[VC_INDEX_WIDTH-1:0];
            end
        end
        if(IS_VC4 && !vc_valid[vi] && !vc_has_invalid) begin
            vc_has_invalid = 1'b1;
            vc_insert_index = vi[VC_INDEX_WIDTH-1:0];
        end
    end
end

wire lookup_active = (state == ST_LOOKUP);
wire req_fire = req_valid && req_ready;

// Synchronous tag read. Issued in ST_IDLE on the live index, consumed in
// ST_LOOKUP -- the same cycle the combinational read used to resolve in, so the
// state machine does not move. The valid bits stay combinational because the
// hot-buffer path needs them in the request cycle.
always @(posedge clk) begin
    if(req_fire) begin
        tag_rd0_q <= tag_way0[live_index];
        tag_rd1_q <= tag_way1[live_index];
    end
end
wire main_hit_accept_event = (state == ST_IDLE) && req_fire && hot_hit;
wire fast_main_hit_event = main_hit_accept_event;
wire lookup_victim_hit = lookup_active && !main_hit && IS_VC4 && vc_hit;
wire lookup_true_miss = lookup_active && !main_hit && !lookup_victim_hit;
assign access_event = main_hit_accept_event || lookup_active;
assign main_hit_event = main_hit_accept_event || (lookup_active && main_hit);
assign victim_hit_event = lookup_victim_hit;
assign true_miss_event = lookup_true_miss;
assign hit_event = main_hit_event || victim_hit_event;
assign miss_event = true_miss_event;
assign hit_way0_dbg = main_hit_accept_event ? !hot_way[live_hot_index] :
                      (lookup_active && main_hit0);
assign hit_way1_dbg = main_hit_accept_event ? hot_way[live_hot_index] :
                      (lookup_active && main_hit1);
// vc_hit_vec is VC_DEPTH wide and the debug port is VICTIM_ENTRIES wide; the
// two are equal only when the victim buffer exists. Padding through a wider
// vector and selecting states the zero-extension explicitly, and unlike a
// replication it stays legal when the two widths are the same.
wire [VICTIM_ENTRIES+VC_DEPTH-1:0] vc_hit_vec_p =
    {{VICTIM_ENTRIES{1'b0}}, vc_hit_vec};
assign victim_hit_vec_dbg = lookup_active
    ? vc_hit_vec_p[VICTIM_ENTRIES-1:0] : {VICTIM_ENTRIES{1'b0}};
assign replacement_way_dbg = selected_refill_way;

assign req_ready = (state == ST_IDLE);
assign rsp_valid = fast_main_hit_event || (state == ST_HIT_RESP) ||
                   (state == ST_MISS_RESP);
assign rsp_data = fast_main_hit_event ?
                  select_line_word(hot_hit_line, req_addr[OFFSET_BITS-1:2]) :
                  (main_read_response ?
                   select_line_word(refill_way ? bank1_rd_line : bank0_rd_line,
                                    request_word) : rsp_data_reg);
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

wire [INDEX_WIDTH-1:0] bank_rd_index =
    (state == ST_IDLE) ?
        req_addr[INDEX_WIDTH+OFFSET_BITS-1:OFFSET_BITS] : request_index;
// Every cycle that consumes bank*_rd_line (ST_HIT_RESP, ST_SWAP_WRITE,
// ST_EVICT_WRITE) follows a cycle outside ST_IDLE, so reading only there would
// already be exact. The ST_IDLE read is kept for the one case that leaves
// ST_IDLE for ST_LOOKUP, matching the D-cache, whose ST_LOOKUP does consume
// the line. Idle cycles and L0 hot hits no longer read the banks.
wire bank_rd_en = (state != ST_IDLE) || (req_fire && !hot_hit);
wire swap_write = (state == ST_SWAP_WRITE);
wire refill_write = (state == ST_REFILL_DATA) && refill_rsp_valid &&
                    !refill_rsp_error;
wire bank0_wr_en = (swap_write && !IS_SA2) ||
                   (refill_write && !refill_way);
wire bank1_wr_en = refill_write && refill_way;
// The bank word selector is a fixed four bits, so the bank port width never
// depends on LINE_WORDS. Padding through a wider vector rather than a
// replication keeps this legal at LINE_WORDS=16, where the pad is zero bits.
wire [WORD_BITS+3:0] transfer_beat_p     = {4'b0, transfer_beat};
wire [WORD_BITS+3:0] refill_beat_count_p = {4'b0, refill_beat_count};
wire [3:0] bank_wr_word = swap_write ? transfer_beat_p[3:0]
                                     : refill_beat_count_p[3:0];
wire [31:0] swap_in_word = swap_word[transfer_beat];
wire [31:0] bank_wr_data = swap_write ? swap_in_word : refill_rsp_data;
wire [LINE_WIDTH-1:0] refill_line_next =
    replace_line_word(refill_line_accum, refill_beat_count, refill_rsp_data);
wire [LINE_WIDTH-1:0] swap_in_line;
genvar sw;
generate
    for(sw = 0; sw < EFF_LINE_WORDS; sw = sw + 1) begin : g_swap_line
        assign swap_in_line[(sw*32)+31 -: 32] = swap_word[sw];
    end
endgenerate

cache_dse_data_bank #(.SET_COUNT(SET_COUNT), .INDEX_WIDTH(INDEX_WIDTH),
                      .LINE_WORDS(EFF_LINE_WORDS))
u_data_way0 (
    .clk(clk), .rd_en(bank_rd_en), .rd_index(bank_rd_index), .rd_line(bank0_rd_line),
    .wr_en(bank0_wr_en),
    .wr_index(request_index), .wr_word(bank_wr_word), .wr_data(bank_wr_data)
);

cache_dse_data_bank #(.SET_COUNT(SET_COUNT), .INDEX_WIDTH(INDEX_WIDTH),
                      .LINE_WORDS(EFF_LINE_WORDS))
u_data_way1 (
    .clk(clk), .rd_en(bank_rd_en), .rd_index(bank_rd_index), .rd_line(bank1_rd_line),
    .wr_en(bank1_wr_en),
    .wr_index(request_index), .wr_word(bank_wr_word), .wr_data(bank_wr_data)
);

integer i;
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        state <= ST_IDLE;
        request_addr <= 32'h0;
        transfer_beat <= {WORD_BITS{1'b0}};
        refill_beat_count <= {WORD_BITS{1'b0}};
        refill_error_seen <= 1'b0;
        refill_way <= 1'b0;
        refill_requested_word <= 32'h0;
        rsp_data_reg <= 32'h0000_0013;
        rsp_error_reg <= 1'b0;
        main_read_response <= 1'b0;
        refill_line_accum <= {LINE_WIDTH{1'b0}};
        hot_valid <= {L0_ENTRIES{1'b0}};
        hot_way <= {L0_ENTRIES{1'b0}};
        for(i = 0; i < 8; i = i + 1) begin
            hot_tag[i] <= {(BLOCK_WIDTH-L0_IDX_BITS){1'b0}};
            hot_line[i] <= {LINE_WIDTH{1'b0}};
        end
        valid_way0 <= {SET_COUNT{1'b0}};
        valid_way1 <= {SET_COUNT{1'b0}};
        replace_way <= {SET_COUNT{1'b0}};
        vc_valid <= {VC_DEPTH{1'b0}};
        vc_replace_ptr <= {VC_INDEX_WIDTH{1'b0}};
        vc_selected <= {VC_INDEX_WIDTH{1'b0}};
        old_main_valid <= 1'b0;
        old_main_block <= {BLOCK_WIDTH{1'b0}};
        for(i = 0; i < EFF_LINE_WORDS; i = i + 1)
            swap_word[i] <= 32'h0;
        access_count <= 32'h0;
        hit_count <= 32'h0;
        miss_count <= 32'h0;
        main_hit_count <= 32'h0;
        victim_hit_count <= 32'h0;
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
                        if(IS_SA2)
                            replace_way[live_index] <= hot_way[live_hot_index] ?
                                                       1'b0 : 1'b1;
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
                    refill_way <= main_hit1;
                    main_read_response <= 1'b1;
                    if(IS_SA2)
                        replace_way[request_index] <= main_hit0 ? 1'b1 : 1'b0;
                    state <= ST_HIT_RESP;
                end else if(IS_VC4 && vc_hit) begin
                    hit_count <= hit_count + 1'b1;
                    victim_hit_count <= victim_hit_count + 1'b1;
                    vc_selected <= vc_hit_index;
                    old_main_valid <= valid_way0[request_index];
                    old_main_block <= {tag_rd0_q, request_index};
                    for(i = 0; i < EFF_LINE_WORDS; i = i + 1)
                        swap_word[i] <=
                            vc_data[(vc_hit_index*EFF_LINE_WORDS)+i];
                    transfer_beat <= {WORD_BITS{1'b0}};
                    state <= ST_SWAP_READ;
                end else begin
                    miss_count <= miss_count + 1'b1;
                    true_miss_count <= true_miss_count + 1'b1;
                    refill_beat_count <= {WORD_BITS{1'b0}};
                    refill_requested_word <= 32'h0;
                    if(!IS_VC4) begin
                        // SA2 and the plain direct-mapped point both refill in
                        // place. Only the victim configuration copies the
                        // outgoing line into the buffer first, so this is gated
                        // on IS_VC4 rather than on !IS_SA2: otherwise the
                        // direct-mapped ablation pays an eviction cost it can
                        // never recover, since its hit path never reads the
                        // buffer back.
                        refill_way <= IS_SA2 ? selected_refill_way : 1'b0;
                        if(IS_SA2 && selected_refill_way)
                            valid_way1[request_index] <= 1'b0;
                        else
                            valid_way0[request_index] <= 1'b0;
                        state <= ST_REFILL_REQ;
                    end else begin
                        refill_way <= 1'b0;
                        if(valid_way0[request_index]) begin
                            vc_selected <= vc_insert_index;
                            old_main_valid <= 1'b1;
                            old_main_block <= {tag_rd0_q, request_index};
                            valid_way0[request_index] <= 1'b0;
                            transfer_beat <= {WORD_BITS{1'b0}};
                            state <= ST_EVICT_READ;
                        end else begin
                            valid_way0[request_index] <= 1'b0;
                            state <= ST_REFILL_REQ;
                        end
                    end
                end
            end
            ST_HIT_RESP: begin
                if(main_read_response) begin
                    hot_valid[request_hot_index] <= 1'b1;
                    hot_tag[request_hot_index] <= request_block[BLOCK_WIDTH-1:L0_IDX_BITS];
                    hot_line[request_hot_index] <=
                        refill_way ? bank1_rd_line : bank0_rd_line;
                    hot_way[request_hot_index] <= refill_way;
                end
                state <= ST_IDLE;
            end
            ST_SWAP_READ: state <= ST_SWAP_WRITE;
            ST_SWAP_WRITE: begin
                vc_data[(vc_selected*EFF_LINE_WORDS)+transfer_beat] <=
                    select_line_word(bank0_rd_line, transfer_beat);
                if(transfer_beat == LAST_WORD) begin
                    vc_valid[vc_selected] <= old_main_valid;
                    if(old_main_valid)
                        vc_block[vc_selected] <= old_main_block;
                    tag_way0[request_index] <= request_tag;
                    valid_way0[request_index] <= 1'b1;
                    rsp_data_reg <= swap_word[request_word];
                    hot_valid[request_hot_index] <= 1'b1;
                    hot_tag[request_hot_index] <= request_block[BLOCK_WIDTH-1:L0_IDX_BITS];
                    hot_line[request_hot_index] <= swap_in_line;
                    hot_way[request_hot_index] <= 1'b0;
                    state <= ST_HIT_RESP;
                end else begin
                    transfer_beat <= transfer_beat + 1'b1;
                    state <= ST_SWAP_READ;
                end
            end
            ST_EVICT_READ: state <= ST_EVICT_WRITE;
            ST_EVICT_WRITE: begin
                vc_data[(vc_selected*EFF_LINE_WORDS)+transfer_beat] <=
                    select_line_word(bank0_rd_line, transfer_beat);
                if(transfer_beat == LAST_WORD) begin
                    vc_valid[vc_selected] <= 1'b1;
                    vc_block[vc_selected] <= old_main_block;
                    vc_replace_ptr <= (vc_selected == VC_LAST)
                        ? {VC_INDEX_WIDTH{1'b0}} : vc_selected + 1'b1;
                    state <= ST_REFILL_REQ;
                end else begin
                    transfer_beat <= transfer_beat + 1'b1;
                    state <= ST_EVICT_READ;
                end
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
                            if(refill_way) begin
                                tag_way1[request_index] <= request_tag;
                                valid_way1[request_index] <= 1'b1;
                            end else begin
                                tag_way0[request_index] <= request_tag;
                                valid_way0[request_index] <= 1'b1;
                            end
                            if(IS_SA2)
                                replace_way[request_index] <= refill_way ? 1'b0 : 1'b1;
                            hot_valid[request_hot_index] <= 1'b1;
                            hot_tag[request_hot_index] <=
                                request_block[BLOCK_WIDTH-1:L0_IDX_BITS];
                            hot_line[request_hot_index] <=
                                refill_line_next;
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
integer a, b;
initial begin
    if(IS_SA2 && ((LINE_COUNT % 2) != 0))
        $fatal(1, "SA2 requires an even total LINE_COUNT");
    if(IS_VC4 && (VICTIM_ENTRIES != 4))
        $display("NOTE: the evaluated configuration uses VICTIM_ENTRIES=4");
end
// reset_n is the asynchronous reset of every sequential block in this module.
// Sampling it synchronously here would make this the one place where the reset
// net acts as ordinary data. The sensitivity list matches the rest of the
// module; on negedge reset_n the guard is false, so no check runs in reset.
always @(posedge clk or negedge reset_n) begin
    if(reset_n && lookup_active) begin
        if(main_hit0 && main_hit1)
            $fatal(1, "I-cache duplicate SA2 hit");
        if((vc_hit_vec & (vc_hit_vec - 1'b1)) != {VC_DEPTH{1'b0}})
            $fatal(1, "I-cache victim lookup is not onehot0");
        if(!(main_hit_event ^ victim_hit_event ^ true_miss_event))
            $fatal(1, "I-cache access classification is not exclusive");
    end
    if(reset_n && IS_VC4) begin
        for(a = 0; a < VICTIM_ENTRIES; a = a + 1)
            for(b = a + 1; b < VICTIM_ENTRIES; b = b + 1)
                if(vc_valid[a] && vc_valid[b] && (vc_block[a] == vc_block[b]))
                    $fatal(1, "I-cache duplicate victim block");
    end
end
// synthesis translate_on


// synthesis translate_off
initial begin
    if(!LINE_WORDS_OK)
        $fatal(1, "icache_dse_core: LINE_WORDS=%0d is unsupported. It must be a power of two from 2 to 16; the bank word selector is four bits, so wider lines would alias their upper words onto the lower ones without any other symptom.", LINE_WORDS);
end
// synthesis translate_on

endmodule
