// Configurable blocking D-cache core.
// CACHE_CONFIG: 1 = SA2, 2 = direct-mapped main cache plus VC4.
// Policy is write-through and no-write-allocate.
module dcache_dse_core #(
    parameter LINE_COUNT = 64,
    parameter CACHE_CONFIG = 1,
    parameter VICTIM_ENTRIES = 4,
    parameter LINE_WORDS = 4,
    // R16 (review M1): 1 answers a main-array hit in ST_LOOKUP (one extra cycle, as in the five-state
    // DM controller) instead of in the following response state (two). 0 = the original core.
    parameter FAST_HIT = 0
)(
    input wire clk,
    input wire reset_n,
    input wire req_valid,
    input wire req_write,
    input wire [31:0] req_addr,
    input wire [31:0] req_wdata,
    input wire [3:0] req_wstrb,
    output wire req_ready,
    output wire rsp_valid,
    output wire [31:0] rsp_rdata,
    output wire rsp_error,
    output wire refill_req_valid,
    output wire [31:0] refill_req_addr,
    input wire refill_req_ready,
    input wire refill_rsp_valid,
    input wire [31:0] refill_rsp_data,
    input wire refill_rsp_last,
    input wire refill_rsp_error,
    output wire mem_wr_valid,
    output wire [31:0] mem_wr_addr,
    output wire [31:0] mem_wr_data,
    output wire [3:0] mem_wr_strb,
    input wire mem_wr_ready,
    input wire mem_wr_rsp_valid,
    input wire mem_wr_rsp_error,
    output reg [31:0] access_count,
    output reg [31:0] read_count,
    output reg [31:0] write_count,
    output reg [31:0] hit_count,
    output reg [31:0] miss_count,
    output reg [31:0] read_hit_count,
    output reg [31:0] read_miss_count,
    output reg [31:0] write_hit_count,
    output reg [31:0] write_miss_count,
    output reg [31:0] main_hit_count,
    output reg [31:0] victim_hit_count,
    output reg [31:0] true_miss_count,
    output wire read_access_event,
    output wire read_hit_event,
    output wire read_miss_event,
    output wire write_access_event,
    output wire write_hit_event,
    output wire write_miss_event,
    output wire main_hit_event,
    output wire victim_hit_event,
    output wire true_miss_event,
    output wire hit_way0_dbg,
    output wire hit_way1_dbg,
    output wire [VICTIM_ENTRIES-1:0] victim_hit_vec_dbg,
    output wire replacement_way_dbg
);

function integer clog2;
    input integer value;
    integer tmp;
    begin
        tmp = value - 1;
        clog2 = 0;
        while(tmp > 0) begin clog2 = clog2 + 1; tmp = tmp >> 1; end
    end
endfunction

function [31:0] apply_wstrb;
    input [31:0] old_word;
    input [31:0] new_word;
    input [3:0] byte_strobe;
    begin
        apply_wstrb = old_word;
        if(byte_strobe[0]) apply_wstrb[7:0] = new_word[7:0];
        if(byte_strobe[1]) apply_wstrb[15:8] = new_word[15:8];
        if(byte_strobe[2]) apply_wstrb[23:16] = new_word[23:16];
        if(byte_strobe[3]) apply_wstrb[31:24] = new_word[31:24];
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

localparam [3:0] ST_IDLE=0, ST_LOOKUP=1, ST_CPU_RESP=2,
                 ST_SWAP_READ=3, ST_SWAP_WRITE=4,
                 ST_EVICT_READ=5, ST_EVICT_WRITE=6,
                 ST_REFILL_REQ=7, ST_REFILL_DATA=8,
                 ST_WRITE_REQ=9, ST_WRITE_RESP=10;

reg [3:0] state;
reg request_write;
reg [31:0] request_addr, request_wdata;
reg [3:0] request_wstrb;
reg [WORD_BITS-1:0] transfer_beat, refill_beat_count;
reg refill_error_seen, refill_way;
reg [31:0] refill_requested_word;
reg [31:0] rsp_data_reg;
reg rsp_error_reg;
reg main_read_response;
reg [LINE_WIDTH-1:0] refill_line_accum;
wire [LINE_WIDTH-1:0] bank0_rd_line;
wire [LINE_WIDTH-1:0] bank1_rd_line;
reg store_hit_latched, store_way_latched;
reg [31:0] store_merged_word;

reg [1:0] hot_valid;
reg [BLOCK_WIDTH-1:0] hot_block0;
reg [BLOCK_WIDTH-1:0] hot_block1;
reg [LINE_WIDTH-1:0] hot_line0;
reg [LINE_WIDTH-1:0] hot_line1;
reg hot_replace;
reg hot_way0, hot_way1;
reg hot_epoch0, hot_epoch1;

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
reg [SET_COUNT-1:0] valid_way0, valid_way1, replace_way;
reg [SET_COUNT-1:0] tag_epoch_way0, tag_epoch_way1;
reg [VC_DEPTH-1:0] vc_valid;
reg [BLOCK_WIDTH-1:0] vc_block [0:VC_DEPTH-1];
reg [31:0] vc_data [0:(VC_DEPTH*EFF_LINE_WORDS)-1];
reg [VC_INDEX_WIDTH-1:0] vc_replace_ptr, vc_selected;
reg old_main_valid;
reg [BLOCK_WIDTH-1:0] old_main_block;
reg [31:0] swap_word [0:EFF_LINE_WORDS-1];

wire [INDEX_WIDTH-1:0] request_index =
    request_addr[INDEX_WIDTH+OFFSET_BITS-1:OFFSET_BITS];
wire [TAG_WIDTH-1:0] request_tag = request_addr[31:INDEX_WIDTH+OFFSET_BITS];
wire [WORD_BITS-1:0] request_word = request_addr[OFFSET_BITS-1:2];
wire [BLOCK_WIDTH-1:0] request_block = request_addr[31:OFFSET_BITS];
wire [INDEX_WIDTH-1:0] live_index =
    req_addr[INDEX_WIDTH+OFFSET_BITS-1:OFFSET_BITS];
wire [BLOCK_WIDTH-1:0] live_block = req_addr[31:OFFSET_BITS];
wire hot_live_valid0 = hot_way0 ?
                     (IS_SA2 && valid_way1[live_index] &&
                      (hot_epoch0 == tag_epoch_way1[live_index])) :
                     (valid_way0[live_index] &&
                      (hot_epoch0 == tag_epoch_way0[live_index]));
wire hot_live_valid1 = hot_way1 ?
                     (IS_SA2 && valid_way1[live_index] &&
                      (hot_epoch1 == tag_epoch_way1[live_index])) :
                     (valid_way0[live_index] &&
                      (hot_epoch1 == tag_epoch_way0[live_index]));
wire hot_hit0 = hot_valid[0] && hot_live_valid0 &&
                (hot_block0 == live_block);
wire hot_hit1 = hot_valid[1] && hot_live_valid1 &&
                (hot_block1 == live_block);
wire [LINE_WIDTH-1:0] hot_hit_line = hot_hit0 ? hot_line0 : hot_line1;

wire hot_request_valid0 = hot_way0 ?
                     (IS_SA2 && valid_way1[request_index] &&
                      (hot_epoch0 == tag_epoch_way1[request_index])) :
                     (valid_way0[request_index] &&
                      (hot_epoch0 == tag_epoch_way0[request_index]));
wire hot_request_valid1 = hot_way1 ?
                     (IS_SA2 && valid_way1[request_index] &&
                      (hot_epoch1 == tag_epoch_way1[request_index])) :
                     (valid_way0[request_index] &&
                      (hot_epoch1 == tag_epoch_way0[request_index]));
wire request_hot_hit0 = hot_valid[0] && hot_request_valid0 &&
                        (hot_block0 == request_block);
wire request_hot_hit1 = hot_valid[1] && hot_request_valid1 &&
                        (hot_block1 == request_block);

wire main_hit0 = valid_way0[request_index] && tag_rd0_q == request_tag;
wire main_hit1 = IS_SA2 && valid_way1[request_index] && tag_rd1_q == request_tag;
wire main_hit = main_hit0 || main_hit1;
wire selected_refill_way = !valid_way0[request_index] ? 1'b0 :
                           (!valid_way1[request_index] ? 1'b1 : replace_way[request_index]);

reg [VC_DEPTH-1:0] vc_hit_vec;
reg vc_hit, vc_has_invalid;
reg [VC_INDEX_WIDTH-1:0] vc_hit_index, vc_insert_index;
integer vi;
always @(*) begin
    vc_hit_vec = {VC_DEPTH{1'b0}};
    vc_hit = 1'b0;
    vc_hit_index = {VC_INDEX_WIDTH{1'b0}};
    vc_has_invalid = 1'b0;
    vc_insert_index = vc_replace_ptr;
    for(vi=0; vi<VC_DEPTH; vi=vi+1) begin
        if(IS_VC4 && vc_valid[vi] && vc_block[vi] == request_block) begin
            vc_hit_vec[vi] = 1'b1;
            if(!vc_hit) begin vc_hit=1'b1; vc_hit_index=vi[VC_INDEX_WIDTH-1:0]; end
        end
        if(IS_VC4 && !vc_valid[vi] && !vc_has_invalid) begin
            vc_has_invalid=1'b1; vc_insert_index=vi[VC_INDEX_WIDTH-1:0];
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
wire fast_load_main_event = (state == ST_IDLE) && req_fire &&
                            !req_write && (hot_hit0 || hot_hit1);
wire lookup_victim_hit = lookup_active && !main_hit && IS_VC4 && vc_hit;
wire lookup_true_miss = lookup_active && !main_hit && !lookup_victim_hit;
wire lookup_read_event = lookup_active && !request_write;
assign read_access_event = fast_load_main_event || lookup_read_event;
assign write_access_event = lookup_active && request_write;
assign main_hit_event = fast_load_main_event || (lookup_active && main_hit);
assign victim_hit_event = lookup_victim_hit;
assign true_miss_event = lookup_true_miss;
assign read_hit_event = fast_load_main_event ||
                        (lookup_read_event && (main_hit || lookup_victim_hit));
assign read_miss_event = lookup_read_event && lookup_true_miss;
assign write_hit_event = write_access_event && (main_hit || lookup_victim_hit);
assign write_miss_event = write_access_event && lookup_true_miss;
assign hit_way0_dbg = fast_load_main_event ?
                      (hot_hit0 ? !hot_way0 : !hot_way1) :
                      (lookup_active && main_hit0);
assign hit_way1_dbg = fast_load_main_event ?
                      (hot_hit0 ? hot_way0 : hot_way1) :
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
// R16: with FAST_HIT a main-array LOAD hit is answered in ST_LOOKUP (stores keep their write path).
wire fast_lookup_load_hit = (FAST_HIT != 0) && lookup_active && main_hit && !request_write;
assign rsp_valid = fast_load_main_event || fast_lookup_load_hit || (state == ST_CPU_RESP);
assign rsp_rdata = fast_load_main_event ?
                   select_line_word(hot_hit_line, req_addr[OFFSET_BITS-1:2]) :
                   fast_lookup_load_hit ?
                   select_line_word(main_hit1 ? bank1_rd_line : bank0_rd_line, request_word) :
                   (main_read_response ?
                    select_line_word(refill_way ? bank1_rd_line : bank0_rd_line,
                                     request_word) : rsp_data_reg);
assign rsp_error = (fast_load_main_event || fast_lookup_load_hit) ? 1'b0 : rsp_error_reg;
assign refill_req_valid = (state == ST_REFILL_REQ);
assign refill_req_addr =
    {request_addr[31:OFFSET_BITS],{OFFSET_BITS{1'b0}}};
assign mem_wr_valid = (state == ST_WRITE_REQ);
assign mem_wr_addr = {request_addr[31:2],2'b0};
assign mem_wr_data = request_wdata;
assign mem_wr_strb = request_wstrb;

wire refill_expected_last = (refill_beat_count == LAST_WORD);
wire refill_protocol_error = refill_rsp_last != refill_expected_last;
wire refill_terminal = refill_rsp_valid && (refill_rsp_last || refill_expected_last);
wire refill_success = refill_terminal && refill_expected_last && refill_rsp_last &&
                      !refill_error_seen && !refill_rsp_error && !refill_protocol_error;
wire write_req_fire = mem_wr_valid && mem_wr_ready;
wire write_rsp_same_cycle = (state == ST_WRITE_REQ) && write_req_fire && mem_wr_rsp_valid;
wire write_rsp_later = (state == ST_WRITE_RESP) && mem_wr_rsp_valid;
wire store_commit = store_hit_latched &&
                    ((write_rsp_same_cycle && !mem_wr_rsp_error) ||
                     (write_rsp_later && !mem_wr_rsp_error));

wire [INDEX_WIDTH-1:0] bank_rd_index =
    (state == ST_IDLE) ?
        req_addr[INDEX_WIDTH+OFFSET_BITS-1:OFFSET_BITS] : request_index;
// ST_LOOKUP consumes the line read in ST_IDLE: a store hit merges its bytes
// into bank*_rd_line there. So the ST_IDLE read must stay enabled on every
// request that goes to ST_LOOKUP, which is every store and every load that
// misses the L0 buffer. Only idle cycles and L0 load hits skip the read.
wire bank_rd_en = (state != ST_IDLE) || (req_fire && !fast_load_main_event);
wire swap_write = (state == ST_SWAP_WRITE);
wire refill_write = (state == ST_REFILL_DATA) && refill_rsp_valid && !refill_rsp_error;
wire bank0_wr_en = (swap_write && !IS_SA2) || (refill_write && !refill_way) ||
                   (store_commit && !store_way_latched);
wire bank1_wr_en = (refill_write && refill_way) || (store_commit && store_way_latched);
// The bank word selector is a fixed four bits, so the bank port width never
// depends on LINE_WORDS. Padding through a wider vector rather than a
// replication keeps this legal at LINE_WORDS=16, where the pad is zero bits.
wire [WORD_BITS+3:0] request_word_p      = {4'b0, request_word};
wire [WORD_BITS+3:0] transfer_beat_p     = {4'b0, transfer_beat};
wire [WORD_BITS+3:0] refill_beat_count_p = {4'b0, refill_beat_count};
wire [3:0] bank_wr_word = store_commit ? request_word_p[3:0] :
                          (swap_write ? transfer_beat_p[3:0]
                                      : refill_beat_count_p[3:0]);
wire [31:0] swap_in_word = swap_word[transfer_beat];
wire [31:0] bank_wr_data = store_commit ? store_merged_word :
                            (swap_write ? swap_in_word : refill_rsp_data);
wire [LINE_WIDTH-1:0] refill_line_next =
    replace_line_word(refill_line_accum, refill_beat_count, refill_rsp_data);
wire [LINE_WIDTH-1:0] swap_in_line;
genvar sw;
generate
    for(sw = 0; sw < EFF_LINE_WORDS; sw = sw + 1) begin : g_swap_line
        assign swap_in_line[(sw*32)+31 -: 32] = swap_word[sw];
    end
endgenerate
wire [LINE_WIDTH-1:0] selected_bank_line =
    store_way_latched ? bank1_rd_line : bank0_rd_line;
wire [LINE_WIDTH-1:0] store_line_next =
    replace_line_word(selected_bank_line, request_word, store_merged_word);

cache_dse_data_bank #(.SET_COUNT(SET_COUNT),.INDEX_WIDTH(INDEX_WIDTH),
                      .LINE_WORDS(EFF_LINE_WORDS)) u_data_way0(
    .clk(clk),.rd_en(bank_rd_en),.rd_index(bank_rd_index),.rd_line(bank0_rd_line),
    .wr_en(bank0_wr_en),.wr_index(request_index),.wr_word(bank_wr_word),.wr_data(bank_wr_data));
cache_dse_data_bank #(.SET_COUNT(SET_COUNT),.INDEX_WIDTH(INDEX_WIDTH),
                      .LINE_WORDS(EFF_LINE_WORDS)) u_data_way1(
    .clk(clk),.rd_en(bank_rd_en),.rd_index(bank_rd_index),.rd_line(bank1_rd_line),
    .wr_en(bank1_wr_en),.wr_index(request_index),.wr_word(bank_wr_word),.wr_data(bank_wr_data));

integer i;
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        state<=ST_IDLE; request_write<=0; request_addr<=0; request_wdata<=0; request_wstrb<=0;
        transfer_beat<=0; refill_beat_count<=0; refill_error_seen<=0; refill_way<=0;
        refill_requested_word<=0; rsp_data_reg<=0; rsp_error_reg<=0;
        main_read_response<=0; refill_line_accum<=0;
        hot_valid<=0; hot_block0<=0; hot_block1<=0;
        hot_line0<=0; hot_line1<=0; hot_replace<=0;
        hot_way0<=0; hot_way1<=0; hot_epoch0<=0; hot_epoch1<=0;
        store_hit_latched<=0; store_way_latched<=0; store_merged_word<=0;
        valid_way0<={SET_COUNT{1'b0}}; valid_way1<={SET_COUNT{1'b0}};
        replace_way<={SET_COUNT{1'b0}}; vc_valid<={VC_DEPTH{1'b0}};
        tag_epoch_way0<={SET_COUNT{1'b0}};
        tag_epoch_way1<={SET_COUNT{1'b0}};
        vc_replace_ptr<=0; vc_selected<=0; old_main_valid<=0; old_main_block<=0;
        for(i=0;i<EFF_LINE_WORDS;i=i+1) swap_word[i]<=0;
        access_count<=0; read_count<=0; write_count<=0; hit_count<=0; miss_count<=0;
        read_hit_count<=0; read_miss_count<=0; write_hit_count<=0; write_miss_count<=0;
        main_hit_count<=0; victim_hit_count<=0; true_miss_count<=0;
    end else begin
        if(store_commit) begin
            if(request_hot_hit0) begin
                hot_line0 <= replace_line_word(hot_line0, request_word,
                                                store_merged_word);
                hot_replace <= 1'b1;
            end else if(request_hot_hit1) begin
                hot_line1 <= replace_line_word(hot_line1, request_word,
                                                store_merged_word);
                hot_replace <= 1'b0;
            end else if(!hot_valid[0]) begin
                hot_valid[0] <= 1'b1; hot_block0 <= request_block;
                hot_line0 <= store_line_next; hot_replace <= 1'b1;
                hot_way0 <= store_way_latched;
                hot_epoch0 <= store_way_latched ?
                    tag_epoch_way1[request_index] : tag_epoch_way0[request_index];
            end else if(!hot_valid[1]) begin
                hot_valid[1] <= 1'b1; hot_block1 <= request_block;
                hot_line1 <= store_line_next; hot_replace <= 1'b0;
                hot_way1 <= store_way_latched;
                hot_epoch1 <= store_way_latched ?
                    tag_epoch_way1[request_index] : tag_epoch_way0[request_index];
            end else if(!hot_replace) begin
                hot_block0 <= request_block; hot_line0 <= store_line_next;
                hot_replace <= 1'b1;
                hot_way0 <= store_way_latched;
                hot_epoch0 <= store_way_latched ?
                    tag_epoch_way1[request_index] : tag_epoch_way0[request_index];
            end else begin
                hot_block1 <= request_block; hot_line1 <= store_line_next;
                hot_replace <= 1'b0;
                hot_way1 <= store_way_latched;
                hot_epoch1 <= store_way_latched ?
                    tag_epoch_way1[request_index] : tag_epoch_way0[request_index];
            end
        end
        case(state)
            ST_IDLE: if(req_fire) begin
                rsp_error_reg<=0; refill_error_seen<=0; store_hit_latched<=0;
                main_read_response<=0;
                if(!req_write && (hot_hit0 || hot_hit1)) begin
                    access_count<=access_count+1'b1;
                    read_count<=read_count+1'b1;
                    hit_count<=hit_count+1'b1;
                    read_hit_count<=read_hit_count+1'b1;
                    main_hit_count<=main_hit_count+1'b1;
                    if(IS_SA2)
                        replace_way[live_index] <= hot_hit0 ?
                            (hot_way0 ? 1'b0 : 1'b1) :
                            (hot_way1 ? 1'b0 : 1'b1);
                    hot_replace<=hot_hit0?1'b1:1'b0;
                    state<=ST_IDLE;
                end else begin
                    request_write<=req_write; request_addr<=req_addr;
                    request_wdata<=req_wdata; request_wstrb<=req_wstrb;
                    state<=ST_LOOKUP;
                end
            end
            ST_LOOKUP: begin
                access_count<=access_count+1'b1;
                if(request_write) write_count<=write_count+1'b1; else read_count<=read_count+1'b1;
                if(main_hit) begin
                    hit_count<=hit_count+1'b1; main_hit_count<=main_hit_count+1'b1;
                    if(request_write) write_hit_count<=write_hit_count+1'b1;
                    else read_hit_count<=read_hit_count+1'b1;
                    if(IS_SA2) replace_way[request_index]<=main_hit0?1'b1:1'b0;
                    if(request_write) begin
                        store_hit_latched<=1'b1; store_way_latched<=main_hit1;
                        store_merged_word<=apply_wstrb(
                                                       select_line_word(
                                                       main_hit1?bank1_rd_line:
                                                                 bank0_rd_line,
                                                       request_word),
                                                       request_wdata,request_wstrb);
                        state<=ST_WRITE_REQ;
                    end else begin
                        refill_way<=main_hit1;
                        main_read_response<=1'b1;
                        if(FAST_HIT != 0) begin
                            // R16: the ST_CPU_RESP L0 fill, done here because the response leaves now
                            if(request_hot_hit0) begin
                                hot_line0 <= main_hit1 ? bank1_rd_line : bank0_rd_line;
                                hot_replace <= 1'b1;
                                hot_way0 <= main_hit1;
                                hot_epoch0 <= main_hit1 ?
                                    tag_epoch_way1[request_index] :
                                    tag_epoch_way0[request_index];
                            end else if(request_hot_hit1) begin
                                hot_line1 <= main_hit1 ? bank1_rd_line : bank0_rd_line;
                                hot_replace <= 1'b0;
                                hot_way1 <= main_hit1;
                                hot_epoch1 <= main_hit1 ?
                                    tag_epoch_way1[request_index] :
                                    tag_epoch_way0[request_index];
                            end else if(!hot_valid[0]) begin
                                hot_valid[0] <= 1'b1; hot_block0 <= request_block;
                                hot_line0 <= main_hit1 ? bank1_rd_line : bank0_rd_line;
                                hot_replace <= 1'b1;
                                hot_way0 <= main_hit1;
                                hot_epoch0 <= main_hit1 ?
                                    tag_epoch_way1[request_index] :
                                    tag_epoch_way0[request_index];
                            end else if(!hot_valid[1]) begin
                                hot_valid[1] <= 1'b1; hot_block1 <= request_block;
                                hot_line1 <= main_hit1 ? bank1_rd_line : bank0_rd_line;
                                hot_replace <= 1'b0;
                                hot_way1 <= main_hit1;
                                hot_epoch1 <= main_hit1 ?
                                    tag_epoch_way1[request_index] :
                                    tag_epoch_way0[request_index];
                            end else if(!hot_replace) begin
                                hot_block0 <= request_block;
                                hot_line0 <= main_hit1 ? bank1_rd_line : bank0_rd_line;
                                hot_replace <= 1'b1;
                                hot_way0 <= main_hit1;
                                hot_epoch0 <= main_hit1 ?
                                    tag_epoch_way1[request_index] :
                                    tag_epoch_way0[request_index];
                            end else begin
                                hot_block1 <= request_block;
                                hot_line1 <= main_hit1 ? bank1_rd_line : bank0_rd_line;
                                hot_replace <= 1'b0;
                                hot_way1 <= main_hit1;
                                hot_epoch1 <= main_hit1 ?
                                    tag_epoch_way1[request_index] :
                                    tag_epoch_way0[request_index];
                            end
                            state<=ST_IDLE;
                        end else
                            state<=ST_CPU_RESP;
                    end
                end else if(IS_VC4 && vc_hit) begin
                    hit_count<=hit_count+1'b1; victim_hit_count<=victim_hit_count+1'b1;
                    if(request_write) write_hit_count<=write_hit_count+1'b1;
                    else read_hit_count<=read_hit_count+1'b1;
                    vc_selected<=vc_hit_index; old_main_valid<=valid_way0[request_index];
                    old_main_block<={tag_rd0_q,request_index};
                    for(i=0;i<EFF_LINE_WORDS;i=i+1)
                        swap_word[i]<=vc_data[(vc_hit_index*EFF_LINE_WORDS)+i];
                    if(request_write) begin
                        store_hit_latched<=1'b1; store_way_latched<=1'b0;
                        store_merged_word<=apply_wstrb(
                            vc_data[(vc_hit_index*EFF_LINE_WORDS)+request_word],
                            request_wdata,request_wstrb);
                    end
                    transfer_beat<=0; state<=ST_SWAP_READ;
                end else begin
                    miss_count<=miss_count+1'b1; true_miss_count<=true_miss_count+1'b1;
                    if(request_write) begin
                        write_miss_count<=write_miss_count+1'b1;
                        // Critical invariant: a store true miss changes no cache state.
                        store_hit_latched<=1'b0; state<=ST_WRITE_REQ;
                    end else begin
                        read_miss_count<=read_miss_count+1'b1; refill_beat_count<=0;
                        refill_requested_word<=0; refill_line_accum<=0;
                        if(!IS_VC4) begin
                            // Gated on IS_VC4, not on !IS_SA2: see the note in
                            // icache_dse_core.v. A direct-mapped point with no
                            // readable victim buffer must not pay to fill one.
                            refill_way<=IS_SA2 ? selected_refill_way : 1'b0;
                            if(IS_SA2 && selected_refill_way) valid_way1[request_index]<=0;
                            else valid_way0[request_index]<=0;
                            state<=ST_REFILL_REQ;
                        end else begin
                            refill_way<=0;
                            if(valid_way0[request_index]) begin
                                vc_selected<=vc_insert_index; old_main_valid<=1'b1;
                                old_main_block<={tag_rd0_q,request_index};
                                valid_way0[request_index]<=0; transfer_beat<=0; state<=ST_EVICT_READ;
                            end else begin valid_way0[request_index]<=0; state<=ST_REFILL_REQ; end
                        end
                    end
                end
            end
            ST_CPU_RESP: begin
                if(main_read_response) begin
                    if(request_hot_hit0) begin
                        hot_line0 <= refill_way ? bank1_rd_line : bank0_rd_line;
                        hot_replace <= 1'b1;
                        hot_way0 <= refill_way;
                        hot_epoch0 <= refill_way ?
                            tag_epoch_way1[request_index] :
                            tag_epoch_way0[request_index];
                    end else if(request_hot_hit1) begin
                        hot_line1 <= refill_way ? bank1_rd_line : bank0_rd_line;
                        hot_replace <= 1'b0;
                        hot_way1 <= refill_way;
                        hot_epoch1 <= refill_way ?
                            tag_epoch_way1[request_index] :
                            tag_epoch_way0[request_index];
                    end else if(!hot_valid[0]) begin
                        hot_valid[0] <= 1'b1; hot_block0 <= request_block;
                        hot_line0 <= refill_way ? bank1_rd_line : bank0_rd_line;
                        hot_replace <= 1'b1;
                        hot_way0 <= refill_way;
                        hot_epoch0 <= refill_way ?
                            tag_epoch_way1[request_index] :
                            tag_epoch_way0[request_index];
                    end else if(!hot_valid[1]) begin
                        hot_valid[1] <= 1'b1; hot_block1 <= request_block;
                        hot_line1 <= refill_way ? bank1_rd_line : bank0_rd_line;
                        hot_replace <= 1'b0;
                        hot_way1 <= refill_way;
                        hot_epoch1 <= refill_way ?
                            tag_epoch_way1[request_index] :
                            tag_epoch_way0[request_index];
                    end else if(!hot_replace) begin
                        hot_block0 <= request_block;
                        hot_line0 <= refill_way ? bank1_rd_line : bank0_rd_line;
                        hot_replace <= 1'b1;
                        hot_way0 <= refill_way;
                        hot_epoch0 <= refill_way ?
                            tag_epoch_way1[request_index] :
                            tag_epoch_way0[request_index];
                    end else begin
                        hot_block1 <= request_block;
                        hot_line1 <= refill_way ? bank1_rd_line : bank0_rd_line;
                        hot_replace <= 1'b0;
                        hot_way1 <= refill_way;
                        hot_epoch1 <= refill_way ?
                            tag_epoch_way1[request_index] :
                            tag_epoch_way0[request_index];
                    end
                end
                state<=ST_IDLE;
            end
            ST_SWAP_READ: state<=ST_SWAP_WRITE;
            ST_SWAP_WRITE: begin
                vc_data[(vc_selected*EFF_LINE_WORDS)+transfer_beat]<=
                    select_line_word(bank0_rd_line,transfer_beat);
                if(transfer_beat==LAST_WORD) begin
                    vc_valid[vc_selected]<=old_main_valid;
                    if(old_main_valid) vc_block[vc_selected]<=old_main_block;
                    tag_way0[request_index]<=request_tag; valid_way0[request_index]<=1'b1;
                    tag_epoch_way0[request_index] <=
                        ~tag_epoch_way0[request_index];
                    if(!hot_valid[0]) begin
                        hot_valid[0]<=1'b1; hot_block0<=request_block;
                        hot_line0<=swap_in_line; hot_replace<=1'b1;
                        hot_way0<=1'b0;
                        hot_epoch0<=~tag_epoch_way0[request_index];
                    end else if(!hot_valid[1]) begin
                        hot_valid[1]<=1'b1; hot_block1<=request_block;
                        hot_line1<=swap_in_line; hot_replace<=1'b0;
                        hot_way1<=1'b0;
                        hot_epoch1<=~tag_epoch_way0[request_index];
                    end else if(!hot_replace) begin
                        hot_block0<=request_block; hot_line0<=swap_in_line;
                        hot_replace<=1'b1;
                        hot_way0<=1'b0;
                        hot_epoch0<=~tag_epoch_way0[request_index];
                    end else begin
                        hot_block1<=request_block; hot_line1<=swap_in_line;
                        hot_replace<=1'b0;
                        hot_way1<=1'b0;
                        hot_epoch1<=~tag_epoch_way0[request_index];
                    end
                    if(request_write) state<=ST_WRITE_REQ;
                    else begin
                        rsp_data_reg<=swap_word[request_word];
                        state<=ST_CPU_RESP;
                    end
                end else begin transfer_beat<=transfer_beat+1'b1; state<=ST_SWAP_READ; end
            end
            ST_EVICT_READ: state<=ST_EVICT_WRITE;
            ST_EVICT_WRITE: begin
                vc_data[(vc_selected*EFF_LINE_WORDS)+transfer_beat]<=
                    select_line_word(bank0_rd_line,transfer_beat);
                if(transfer_beat==LAST_WORD) begin
                    vc_valid[vc_selected]<=1'b1; vc_block[vc_selected]<=old_main_block;
                    vc_replace_ptr<=(vc_selected==VC_LAST)
                        ? {VC_INDEX_WIDTH{1'b0}} : vc_selected+1'b1;
                    state<=ST_REFILL_REQ;
                end else begin transfer_beat<=transfer_beat+1'b1; state<=ST_EVICT_READ; end
            end
            ST_REFILL_REQ: if(refill_req_valid&&refill_req_ready) begin
                refill_beat_count<=0; refill_error_seen<=0;
                refill_line_accum<=0; state<=ST_REFILL_DATA;
            end
            ST_REFILL_DATA: if(refill_rsp_valid) begin
                refill_line_accum<=refill_line_next;
                if(refill_beat_count==request_word) refill_requested_word<=refill_rsp_data;
                if(refill_rsp_error||refill_protocol_error) refill_error_seen<=1'b1;
                if(refill_terminal) begin
                    rsp_data_reg<=(refill_beat_count==request_word)?refill_rsp_data:refill_requested_word;
                    rsp_error_reg<=!refill_success;
                    if(refill_success) begin
                        if(refill_way) begin
                            tag_way1[request_index]<=request_tag;
                            valid_way1[request_index]<=1'b1;
                            tag_epoch_way1[request_index] <=
                                ~tag_epoch_way1[request_index];
                        end else begin
                            tag_way0[request_index]<=request_tag;
                            valid_way0[request_index]<=1'b1;
                            tag_epoch_way0[request_index] <=
                                ~tag_epoch_way0[request_index];
                        end
                        if(IS_SA2) replace_way[request_index]<=refill_way?1'b0:1'b1;
                        if(hot_valid[0] &&
                           (hot_block0==request_block)) begin
                            hot_line0<=refill_line_next; hot_replace<=1'b1;
                            hot_way0<=refill_way;
                            hot_epoch0<=refill_way ?
                                ~tag_epoch_way1[request_index] :
                                ~tag_epoch_way0[request_index];
                        end else if(hot_valid[1] &&
                                    (hot_block1==request_block)) begin
                            hot_line1<=refill_line_next; hot_replace<=1'b0;
                            hot_way1<=refill_way;
                            hot_epoch1<=refill_way ?
                                ~tag_epoch_way1[request_index] :
                                ~tag_epoch_way0[request_index];
                        end else if(!hot_valid[0]) begin
                            hot_valid[0]<=1'b1; hot_block0<=request_block;
                            hot_line0<=refill_line_next; hot_replace<=1'b1;
                            hot_way0<=refill_way;
                            hot_epoch0<=refill_way ?
                                ~tag_epoch_way1[request_index] :
                                ~tag_epoch_way0[request_index];
                        end else if(!hot_valid[1]) begin
                            hot_valid[1]<=1'b1; hot_block1<=request_block;
                            hot_line1<=refill_line_next; hot_replace<=1'b0;
                            hot_way1<=refill_way;
                            hot_epoch1<=refill_way ?
                                ~tag_epoch_way1[request_index] :
                                ~tag_epoch_way0[request_index];
                        end else if(!hot_replace) begin
                            hot_block0<=request_block;
                            hot_line0<=refill_line_next; hot_replace<=1'b1;
                            hot_way0<=refill_way;
                            hot_epoch0<=refill_way ?
                                ~tag_epoch_way1[request_index] :
                                ~tag_epoch_way0[request_index];
                        end else begin
                            hot_block1<=request_block;
                            hot_line1<=refill_line_next; hot_replace<=1'b0;
                            hot_way1<=refill_way;
                            hot_epoch1<=refill_way ?
                                ~tag_epoch_way1[request_index] :
                                ~tag_epoch_way0[request_index];
                        end
                    end
                    state<=ST_CPU_RESP;
                end else refill_beat_count<=refill_beat_count+1'b1;
            end
            ST_WRITE_REQ: if(write_req_fire) begin
                if(mem_wr_rsp_valid) begin rsp_data_reg<=0; rsp_error_reg<=mem_wr_rsp_error; state<=ST_CPU_RESP; end
                else state<=ST_WRITE_RESP;
            end
            ST_WRITE_RESP: if(mem_wr_rsp_valid) begin
                rsp_data_reg<=0; rsp_error_reg<=mem_wr_rsp_error; state<=ST_CPU_RESP;
            end
            default: state<=ST_IDLE;
        endcase
    end
end

// synthesis translate_off
integer a,b;
initial if(IS_SA2 && ((LINE_COUNT%2)!=0)) $fatal(1,"SA2 requires even LINE_COUNT");
// reset_n is the asynchronous reset of every sequential block in this module.
// Sampling it synchronously here would make this the one place where the reset
// net acts as ordinary data. The sensitivity list matches the rest of the
// module; on negedge reset_n the guard is false, so no check runs in reset.
always @(posedge clk or negedge reset_n) begin
    if(reset_n && lookup_active) begin
        if(main_hit0&&main_hit1) $fatal(1,"D-cache duplicate SA2 hit");
        if((vc_hit_vec&(vc_hit_vec-1'b1))!={VC_DEPTH{1'b0}})
            $fatal(1,"D-cache victim lookup is not onehot0");
        if(!(main_hit_event^victim_hit_event^true_miss_event))
            $fatal(1,"D-cache access classification is not exclusive");
    end
    if(reset_n&&IS_VC4) begin
        for(a=0;a<VICTIM_ENTRIES;a=a+1) for(b=a+1;b<VICTIM_ENTRIES;b=b+1)
            if(vc_valid[a]&&vc_valid[b]&&(vc_block[a]==vc_block[b]))
                $fatal(1,"D-cache duplicate victim block");
    end
end
// synthesis translate_on


// synthesis translate_off
initial begin
    if(!LINE_WORDS_OK)
        $fatal(1, "dcache_dse_core: LINE_WORDS=%0d is unsupported. It must be a power of two from 2 to 16; the bank word selector is four bits, so wider lines would alias their upper words onto the lower ones without any other symptom.", LINE_WORDS);
end
// synthesis translate_on

`ifndef __openlane__
// synthesis translate_off
// R16 sim-only per-cycle checker (rule D.3). With FAST_HIT a main hit is answered in ST_LOOKUP from the bank
// line read in ST_IDLE; the original core answered one cycle later from the line read in ST_LOOKUP at the
// same index. The next cycle the bank output holds that ST_LOOKUP read: the fast answer must equal its word,
// and with FAST_HIT no main hit may reach the old response state any more.
reg r16_pend;
reg [0:0] r16_way;
reg [WORD_BITS-1:0] r16_widx;
reg [31:0] r16_word;
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        r16_pend <= 1'b0;
    end else begin
        if(r16_pend && (select_line_word(r16_way[0] ? bank1_rd_line : bank0_rd_line, r16_widx) !== r16_word))
            $fatal(1, "R16 FAST_HIT: ST_LOOKUP answer %h is not the word the old response state reads", r16_word);
        if((FAST_HIT != 0) && (state == ST_CPU_RESP) && main_read_response)
            $fatal(1, "R16 FAST_HIT: a main hit reached ST_CPU_RESP");
        r16_pend <= fast_lookup_load_hit;
        r16_way <= main_hit1;
        r16_widx <= request_word;
        r16_word <= rsp_rdata;
    end
end
// synthesis translate_on
`endif

endmodule
