// N-way set-associative blocking D-cache core, for the associativity axis of the cache design-space
// exploration (review item M2, 2026-09-30).
//   CACHE_CONFIG 4 (SA4): WAYS = 4.
//   CACHE_CONFIG 5      : WAYS = 2, used only to check this core against the SA2 point of
//                         dcache_dse_core.v. With two ways, tree pseudo-LRU is exactly the SA2 policy (one bit
//                         per set pointing away from the most recently used way), so both must give the same
//                         result on every counter, cycle for cycle.
// The controller is dcache_dse_core.v's: the same ten-state FSM encoding, synchronous tag read issued in
// ST_IDLE and consumed in ST_LOOKUP, the two-entry L0 hot buffer kept coherent with per-way epochs,
// write-through and no-write-allocate. Only the way count is generalised; there is no victim buffer.
module dcache_nway_core #(
    parameter LINE_COUNT = 64,
    parameter WAYS = 4,
    parameter LINE_WORDS = 4
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
    output wire [31:0] victim_hit_count,
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
    output wire [3:0] hit_way_vec_dbg,
    output wire [1:0] replacement_way_dbg
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

// Two or four ways. The way number is carried in two bits everywhere (the upper bit stays 0 at two ways);
// WAY_BITS is how many of them index the per-way state vectors.
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

// Same encoding as dcache_dse_core.v; the swap/evict states of the victim buffer are unused here.
localparam [3:0] ST_IDLE=0, ST_LOOKUP=1, ST_CPU_RESP=2,
                 ST_REFILL_REQ=7, ST_REFILL_DATA=8,
                 ST_WRITE_REQ=9, ST_WRITE_RESP=10;

reg [3:0] state;
reg request_write;
reg [31:0] request_addr, request_wdata;
reg [3:0] request_wstrb;
reg [WORD_BITS-1:0] refill_beat_count;
reg refill_error_seen;
reg [1:0] refill_way;
reg [31:0] refill_requested_word;
reg [31:0] rsp_data_reg;
reg rsp_error_reg;
reg main_read_response;
reg [LINE_WIDTH-1:0] refill_line_accum;
reg store_hit_latched;
reg [1:0] store_way_latched;
reg [31:0] store_merged_word;

reg [1:0] hot_valid;
reg [BLOCK_WIDTH-1:0] hot_block0;
reg [BLOCK_WIDTH-1:0] hot_block1;
reg [LINE_WIDTH-1:0] hot_line0;
reg [LINE_WIDTH-1:0] hot_line1;
reg hot_replace;
reg [1:0] hot_way0, hot_way1;
reg hot_epoch0, hot_epoch1;

// Per-way valid and epoch bits, bit {way, set}. The epoch flips on every refill of a way, so an L0 entry
// that recorded it can tell that its way was refilled underneath it.
reg [EFF_WAYS*SET_COUNT-1:0] valid_v;
reg [EFF_WAYS*SET_COUNT-1:0] epoch_v;
// Tree pseudo-LRU, three bits per set (two ways use bit 0 only):
//   bit 0: 0 -> the victim is in ways 0/1, 1 -> in ways 2/3
//   bit 1: victim among ways 0/1 (0 -> way 0), bit 2: among ways 2/3 (0 -> way 2)
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

// Point every tree node on the path to way w away from it.
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

wire [WAY_BITS-1:0] hw0 = hot_way0[WAY_BITS-1:0];
wire [WAY_BITS-1:0] hw1 = hot_way1[WAY_BITS-1:0];
wire hot_live_valid0 = valid_v[{hw0, live_index}] &&
                       (hot_epoch0 == epoch_v[{hw0, live_index}]);
wire hot_live_valid1 = valid_v[{hw1, live_index}] &&
                       (hot_epoch1 == epoch_v[{hw1, live_index}]);
wire hot_hit0 = hot_valid[0] && hot_live_valid0 && (hot_block0 == live_block);
wire hot_hit1 = hot_valid[1] && hot_live_valid1 && (hot_block1 == live_block);
wire [LINE_WIDTH-1:0] hot_hit_line = hot_hit0 ? hot_line0 : hot_line1;

wire hot_request_valid0 = valid_v[{hw0, request_index}] &&
                          (hot_epoch0 == epoch_v[{hw0, request_index}]);
wire hot_request_valid1 = valid_v[{hw1, request_index}] &&
                          (hot_epoch1 == epoch_v[{hw1, request_index}]);
wire request_hot_hit0 = hot_valid[0] && hot_request_valid0 && (hot_block0 == request_block);
wire request_hot_hit1 = hot_valid[1] && hot_request_valid1 && (hot_block1 == request_block);

wire lookup_active = (state == ST_LOOKUP);
wire req_fire = req_valid && req_ready;

wire [3:0] main_hit_vec;
wire main_hit = |main_hit_vec;
wire [1:0] hit_way = main_hit_vec[3] ? 2'd3 : (main_hit_vec[2] ? 2'd2 :
                     (main_hit_vec[1] ? 2'd1 : 2'd0));

wire [2:0] plru_req  = plru_v[request_index*3 +: 3];
wire [2:0] plru_live = plru_v[live_index*3 +: 3];
// The first invalid way, else the pseudo-LRU victim (SA2: way 0, way 1, then replace_way).
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

wire fast_load_main_event = (state == ST_IDLE) && req_fire &&
                            !req_write && (hot_hit0 || hot_hit1);
wire lookup_true_miss = lookup_active && !main_hit;
wire lookup_read_event = lookup_active && !request_write;
assign read_access_event = fast_load_main_event || lookup_read_event;
assign write_access_event = lookup_active && request_write;
assign main_hit_event = fast_load_main_event || (lookup_active && main_hit);
assign victim_hit_event = 1'b0;
assign victim_hit_count = 32'h0;
assign true_miss_event = lookup_true_miss;
assign read_hit_event = fast_load_main_event || (lookup_read_event && main_hit);
assign read_miss_event = lookup_read_event && lookup_true_miss;
assign write_hit_event = write_access_event && main_hit;
assign write_miss_event = write_access_event && lookup_true_miss;
wire [1:0] fast_hit_way = hot_hit0 ? hot_way0 : hot_way1;
assign hit_way_vec_dbg = fast_load_main_event ? (4'b0001 << fast_hit_way) :
                         (lookup_active ? main_hit_vec : 4'b0000);
assign replacement_way_dbg = selected_refill_way;

wire [EFF_WAYS*LINE_WIDTH-1:0] bank_rd_flat;
wire [LINE_WIDTH-1:0] refill_way_line = bank_rd_flat[refill_way[WAY_BITS-1:0]*LINE_WIDTH +: LINE_WIDTH];
wire [LINE_WIDTH-1:0] hit_way_line = bank_rd_flat[hit_way[WAY_BITS-1:0]*LINE_WIDTH +: LINE_WIDTH];
wire [LINE_WIDTH-1:0] store_way_line =
    bank_rd_flat[store_way_latched[WAY_BITS-1:0]*LINE_WIDTH +: LINE_WIDTH];

assign req_ready = (state == ST_IDLE);
assign rsp_valid = fast_load_main_event || (state == ST_CPU_RESP);
assign rsp_rdata = fast_load_main_event ?
                   select_line_word(hot_hit_line, req_addr[OFFSET_BITS-1:2]) :
                   (main_read_response ? select_line_word(refill_way_line, request_word)
                                       : rsp_data_reg);
assign rsp_error = fast_load_main_event ? 1'b0 : rsp_error_reg;
assign refill_req_valid = (state == ST_REFILL_REQ);
assign refill_req_addr = {request_addr[31:OFFSET_BITS],{OFFSET_BITS{1'b0}}};
assign mem_wr_valid = (state == ST_WRITE_REQ);
assign mem_wr_addr = {request_addr[31:2],2'b0};
assign mem_wr_data = request_wdata;
assign mem_wr_strb = request_wstrb;

wire refill_expected_last = (refill_beat_count == LAST_WORD);
wire refill_protocol_error = refill_rsp_last != refill_expected_last;
wire refill_terminal = refill_rsp_valid && (refill_rsp_last || refill_expected_last);
wire refill_success = refill_terminal && refill_expected_last && refill_rsp_last &&
                      !refill_error_seen && !refill_rsp_error && !refill_protocol_error;
wire refill_commit = (state == ST_REFILL_DATA) && refill_rsp_valid && refill_terminal &&
                     refill_success;
wire write_req_fire = mem_wr_valid && mem_wr_ready;
wire write_rsp_same_cycle = (state == ST_WRITE_REQ) && write_req_fire && mem_wr_rsp_valid;
wire write_rsp_later = (state == ST_WRITE_RESP) && mem_wr_rsp_valid;
wire store_commit = store_hit_latched &&
                    ((write_rsp_same_cycle && !mem_wr_rsp_error) ||
                     (write_rsp_later && !mem_wr_rsp_error));

wire [INDEX_WIDTH-1:0] bank_rd_index =
    (state == ST_IDLE) ? live_index : request_index;
wire bank_rd_en = (state != ST_IDLE) || (req_fire && !fast_load_main_event);
wire refill_write = (state == ST_REFILL_DATA) && refill_rsp_valid && !refill_rsp_error;
wire [WORD_BITS+3:0] request_word_p      = {4'b0, request_word};
wire [WORD_BITS+3:0] refill_beat_count_p = {4'b0, refill_beat_count};
wire [3:0] bank_wr_word = store_commit ? request_word_p[3:0] : refill_beat_count_p[3:0];
wire [31:0] bank_wr_data = store_commit ? store_merged_word : refill_rsp_data;
wire [LINE_WIDTH-1:0] refill_line_next =
    replace_line_word(refill_line_accum, refill_beat_count, refill_rsp_data);
wire [LINE_WIDTH-1:0] store_line_next =
    replace_line_word(store_way_line, request_word, store_merged_word);

// One tag array, registered tag read and data bank per way.
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
            wire bank_wr_en = (refill_write && (refill_way == gw)) ||
                              (store_commit && (store_way_latched == gw));
            cache_dse_data_bank #(.SET_COUNT(SET_COUNT),.INDEX_WIDTH(INDEX_WIDTH),
                                  .LINE_WORDS(EFF_LINE_WORDS)) u_data(
                .clk(clk),.rd_en(bank_rd_en),.rd_index(bank_rd_index),
                .rd_line(bank_rd_flat[gw*LINE_WIDTH +: LINE_WIDTH]),
                .wr_en(bank_wr_en),.wr_index(request_index),.wr_word(bank_wr_word),
                .wr_data(bank_wr_data));
        end else begin : g_absent
            assign main_hit_vec[gw] = 1'b0;
        end
    end
endgenerate

always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        state<=ST_IDLE; request_write<=0; request_addr<=0; request_wdata<=0; request_wstrb<=0;
        refill_beat_count<=0; refill_error_seen<=0; refill_way<=0;
        refill_requested_word<=0; rsp_data_reg<=0; rsp_error_reg<=0;
        main_read_response<=0; refill_line_accum<=0;
        hot_valid<=0; hot_block0<=0; hot_block1<=0;
        hot_line0<=0; hot_line1<=0; hot_replace<=0;
        hot_way0<=0; hot_way1<=0; hot_epoch0<=0; hot_epoch1<=0;
        store_hit_latched<=0; store_way_latched<=0; store_merged_word<=0;
        valid_v<={(EFF_WAYS*SET_COUNT){1'b0}};
        epoch_v<={(EFF_WAYS*SET_COUNT){1'b0}};
        plru_v<={(3*SET_COUNT){1'b0}};
        access_count<=0; read_count<=0; write_count<=0; hit_count<=0; miss_count<=0;
        read_hit_count<=0; read_miss_count<=0; write_hit_count<=0; write_miss_count<=0;
        main_hit_count<=0; true_miss_count<=0;
    end else begin
        if(store_commit) begin
            if(request_hot_hit0) begin
                hot_line0 <= replace_line_word(hot_line0, request_word, store_merged_word);
                hot_replace <= 1'b1;
            end else if(request_hot_hit1) begin
                hot_line1 <= replace_line_word(hot_line1, request_word, store_merged_word);
                hot_replace <= 1'b0;
            end else if(!hot_valid[0]) begin
                hot_valid[0] <= 1'b1; hot_block0 <= request_block;
                hot_line0 <= store_line_next; hot_replace <= 1'b1;
                hot_way0 <= store_way_latched;
                hot_epoch0 <= epoch_v[{store_way_latched[WAY_BITS-1:0], request_index}];
            end else if(!hot_valid[1]) begin
                hot_valid[1] <= 1'b1; hot_block1 <= request_block;
                hot_line1 <= store_line_next; hot_replace <= 1'b0;
                hot_way1 <= store_way_latched;
                hot_epoch1 <= epoch_v[{store_way_latched[WAY_BITS-1:0], request_index}];
            end else if(!hot_replace) begin
                hot_block0 <= request_block; hot_line0 <= store_line_next;
                hot_replace <= 1'b1;
                hot_way0 <= store_way_latched;
                hot_epoch0 <= epoch_v[{store_way_latched[WAY_BITS-1:0], request_index}];
            end else begin
                hot_block1 <= request_block; hot_line1 <= store_line_next;
                hot_replace <= 1'b0;
                hot_way1 <= store_way_latched;
                hot_epoch1 <= epoch_v[{store_way_latched[WAY_BITS-1:0], request_index}];
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
                    plru_v[live_index*3 +: 3] <= plru_touch(plru_live, fast_hit_way);
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
                    plru_v[request_index*3 +: 3] <= plru_touch(plru_req, hit_way);
                    if(request_write) begin
                        store_hit_latched<=1'b1; store_way_latched<=hit_way;
                        store_merged_word<=apply_wstrb(select_line_word(hit_way_line, request_word),
                                                       request_wdata,request_wstrb);
                        state<=ST_WRITE_REQ;
                    end else begin
                        refill_way<=hit_way;
                        main_read_response<=1'b1;
                        state<=ST_CPU_RESP;
                    end
                end else begin
                    miss_count<=miss_count+1'b1; true_miss_count<=true_miss_count+1'b1;
                    if(request_write) begin
                        write_miss_count<=write_miss_count+1'b1;
                        // Critical invariant: a store true miss changes no cache state.
                        store_hit_latched<=1'b0; state<=ST_WRITE_REQ;
                    end else begin
                        read_miss_count<=read_miss_count+1'b1; refill_beat_count<=0;
                        refill_requested_word<=0; refill_line_accum<=0;
                        refill_way<=selected_refill_way;
                        valid_v[{selected_refill_way[WAY_BITS-1:0], request_index}]<=1'b0;
                        state<=ST_REFILL_REQ;
                    end
                end
            end
            ST_CPU_RESP: begin
                if(main_read_response) begin
                    if(request_hot_hit0) begin
                        hot_line0 <= refill_way_line; hot_replace <= 1'b1;
                        hot_way0 <= refill_way;
                        hot_epoch0 <= epoch_v[{refill_way[WAY_BITS-1:0], request_index}];
                    end else if(request_hot_hit1) begin
                        hot_line1 <= refill_way_line; hot_replace <= 1'b0;
                        hot_way1 <= refill_way;
                        hot_epoch1 <= epoch_v[{refill_way[WAY_BITS-1:0], request_index}];
                    end else if(!hot_valid[0]) begin
                        hot_valid[0] <= 1'b1; hot_block0 <= request_block;
                        hot_line0 <= refill_way_line; hot_replace <= 1'b1;
                        hot_way0 <= refill_way;
                        hot_epoch0 <= epoch_v[{refill_way[WAY_BITS-1:0], request_index}];
                    end else if(!hot_valid[1]) begin
                        hot_valid[1] <= 1'b1; hot_block1 <= request_block;
                        hot_line1 <= refill_way_line; hot_replace <= 1'b0;
                        hot_way1 <= refill_way;
                        hot_epoch1 <= epoch_v[{refill_way[WAY_BITS-1:0], request_index}];
                    end else if(!hot_replace) begin
                        hot_block0 <= request_block; hot_line0 <= refill_way_line;
                        hot_replace <= 1'b1;
                        hot_way0 <= refill_way;
                        hot_epoch0 <= epoch_v[{refill_way[WAY_BITS-1:0], request_index}];
                    end else begin
                        hot_block1 <= request_block; hot_line1 <= refill_way_line;
                        hot_replace <= 1'b0;
                        hot_way1 <= refill_way;
                        hot_epoch1 <= epoch_v[{refill_way[WAY_BITS-1:0], request_index}];
                    end
                end
                state<=ST_IDLE;
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
                        // The tag itself is written in g_way on refill_commit.
                        valid_v[{refill_way[WAY_BITS-1:0], request_index}] <= 1'b1;
                        epoch_v[{refill_way[WAY_BITS-1:0], request_index}] <=
                            ~epoch_v[{refill_way[WAY_BITS-1:0], request_index}];
                        plru_v[request_index*3 +: 3] <= plru_touch(plru_req, refill_way);
                        if(hot_valid[0] && (hot_block0==request_block)) begin
                            hot_line0<=refill_line_next; hot_replace<=1'b1;
                            hot_way0<=refill_way;
                            hot_epoch0<=~epoch_v[{refill_way[WAY_BITS-1:0], request_index}];
                        end else if(hot_valid[1] && (hot_block1==request_block)) begin
                            hot_line1<=refill_line_next; hot_replace<=1'b0;
                            hot_way1<=refill_way;
                            hot_epoch1<=~epoch_v[{refill_way[WAY_BITS-1:0], request_index}];
                        end else if(!hot_valid[0]) begin
                            hot_valid[0]<=1'b1; hot_block0<=request_block;
                            hot_line0<=refill_line_next; hot_replace<=1'b1;
                            hot_way0<=refill_way;
                            hot_epoch0<=~epoch_v[{refill_way[WAY_BITS-1:0], request_index}];
                        end else if(!hot_valid[1]) begin
                            hot_valid[1]<=1'b1; hot_block1<=request_block;
                            hot_line1<=refill_line_next; hot_replace<=1'b0;
                            hot_way1<=refill_way;
                            hot_epoch1<=~epoch_v[{refill_way[WAY_BITS-1:0], request_index}];
                        end else if(!hot_replace) begin
                            hot_block0<=request_block;
                            hot_line0<=refill_line_next; hot_replace<=1'b1;
                            hot_way0<=refill_way;
                            hot_epoch0<=~epoch_v[{refill_way[WAY_BITS-1:0], request_index}];
                        end else begin
                            hot_block1<=request_block;
                            hot_line1<=refill_line_next; hot_replace<=1'b0;
                            hot_way1<=refill_way;
                            hot_epoch1<=~epoch_v[{refill_way[WAY_BITS-1:0], request_index}];
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
initial begin
    if(!WAYS_OK)
        $fatal(1, "dcache_nway_core: WAYS=%0d is unsupported (2 or 4).", WAYS);
    if((LINE_COUNT % EFF_WAYS) != 0 || (SET_COUNT & (SET_COUNT - 1)) != 0)
        $fatal(1, "dcache_nway_core: LINE_COUNT=%0d must give a power-of-two set count at %0d ways.",
               LINE_COUNT, EFF_WAYS);
    if(!LINE_WORDS_OK)
        $fatal(1, "dcache_nway_core: LINE_WORDS=%0d is unsupported. It must be a power of two from 2 to 16.",
               LINE_WORDS);
end
always @(posedge clk or negedge reset_n) begin
    if(reset_n && lookup_active) begin
        if((main_hit_vec & (main_hit_vec - 1'b1)) != 4'b0000)
            $fatal(1, "D-cache duplicate hit across ways");
        if(!(main_hit_event ^ true_miss_event))
            $fatal(1, "D-cache access classification is not exclusive");
    end
end
// synthesis translate_on

endmodule
