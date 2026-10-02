// Instruction-cache organization selector shared by all configurations.
// CACHE_CONFIG: 0=DM, 1=SA2, 2=DM_VC4.
module icache #(
    parameter LINE_COUNT = 64,
    parameter CACHE_CONFIG = 0,
    parameter LINE_WORDS = 4,
    parameter VICTIM_ENTRIES = 4,
    // Depth of the L0 hot buffer; see icache_controller.v.
    parameter L0_ENTRIES = 8
)(
    input wire clk,
    input wire reset_n,
    input wire req_valid,
    input wire [31:0] req_addr,
    output wire req_ready,
    output wire rsp_valid,
    output wire [31:0] rsp_data,
    output wire rsp_error,
    output wire refill_req_valid,
    output wire [31:0] refill_req_addr,
    input wire refill_req_ready,
    input wire refill_rsp_valid,
    input wire [31:0] refill_rsp_data,
    input wire refill_rsp_last,
    input wire refill_rsp_error,
    output wire [31:0] access_count,
    output wire [31:0] hit_count,
    output wire [31:0] miss_count,
    output wire access_event,
    output wire hit_event,
    output wire miss_event,
    output wire [31:0] main_hit_count,
    output wire [31:0] victim_hit_count,
    output wire [31:0] true_miss_count,
    output wire main_hit_event,
    output wire victim_hit_event,
    output wire true_miss_event
);

function integer clog2;
    input integer value;
    integer tmp;
    begin
        tmp=value-1; clog2=0;
        while(tmp>0) begin clog2=clog2+1; tmp=tmp>>1; end
    end
endfunction

generate
if(CACHE_CONFIG == 0) begin : g_dm_baseline
    localparam INDEX_WIDTH=(LINE_COUNT>1)?clog2(LINE_COUNT):1;
    localparam TAG_WIDTH=32-4-INDEX_WIDTH;
    // This branch is a 16-byte-line design: TAG_WIDTH, the 128-bit line and the
    // two-bit word select below are all literals, and LINE_WORDS is not carried
    // into the controller or the RAMs. The line-size study therefore runs on the
    // DSE core, and this guard makes the combination fail loudly instead of
    // elaborating into a cache that quietly addresses the wrong words.
    // synthesis translate_off
    initial if(LINE_WORDS != 4)
        $fatal(1, "%m: CACHE_CONFIG=0 supports LINE_WORDS=4 only, got %0d",
               LINE_WORDS);
    // synthesis translate_on
    wire [INDEX_WIDTH-1:0] tag_rd_index,tag_wr_index,data_rd_index,data_wr_index;
    wire [TAG_WIDTH-1:0] tag_rd_tag,tag_wr_tag;
    wire tag_rd_en,tag_valid_rd,tag_wr_en,tag_wr_valid,data_wr_en,data_rd_en;
    wire [INDEX_WIDTH-1:0] tag_valid_rd_index;
    wire [1:0] data_wr_word;
    wire [127:0] data_rd_line;
    wire [31:0] data_wr_data;

    icache_controller #(.INDEX_WIDTH(INDEX_WIDTH),.TAG_WIDTH(TAG_WIDTH),
                       .L0_ENTRIES(L0_ENTRIES)) u_controller(
        .clk(clk),.reset_n(reset_n),.req_valid(req_valid),.req_addr(req_addr),
        .req_ready(req_ready),.rsp_valid(rsp_valid),.rsp_data(rsp_data),.rsp_error(rsp_error),
        .refill_req_valid(refill_req_valid),.refill_req_addr(refill_req_addr),
        .refill_req_ready(refill_req_ready),.refill_rsp_valid(refill_rsp_valid),
        .refill_rsp_data(refill_rsp_data),.refill_rsp_last(refill_rsp_last),
        .refill_rsp_error(refill_rsp_error),.access_count(access_count),
        .hit_count(hit_count),.miss_count(miss_count),.access_event(access_event),
        .hit_event(hit_event),.miss_event(miss_event),
        .tag_rd_en(tag_rd_en),.tag_rd_index(tag_rd_index),.tag_rd_tag(tag_rd_tag),
        .tag_valid_rd_index(tag_valid_rd_index),.tag_valid_rd(tag_valid_rd),
        .tag_wr_en(tag_wr_en),
        .tag_wr_index(tag_wr_index),.tag_wr_tag(tag_wr_tag),.tag_wr_valid(tag_wr_valid),
        .data_rd_en(data_rd_en),.data_rd_index(data_rd_index),.data_rd_line(data_rd_line),
        .data_wr_en(data_wr_en),.data_wr_index(data_wr_index),.data_wr_word(data_wr_word),
        .data_wr_data(data_wr_data));

    icache_tag_ram #(.LINE_COUNT(LINE_COUNT),.INDEX_WIDTH(INDEX_WIDTH),.TAG_WIDTH(TAG_WIDTH))
    u_tag_ram(.clk(clk),.reset_n(reset_n),
              .rd_en(tag_rd_en),.rd_index(tag_rd_index),.rd_tag(tag_rd_tag),
              .valid_rd_index(tag_valid_rd_index),.valid_rd(tag_valid_rd),
              .wr_en(tag_wr_en),.wr_index(tag_wr_index),
              .wr_tag(tag_wr_tag),.wr_valid(tag_wr_valid));
    icache_data_ram #(.LINE_COUNT(LINE_COUNT),.INDEX_WIDTH(INDEX_WIDTH))
    u_data_ram(.clk(clk),.rd_en(data_rd_en),.rd_index(data_rd_index),.rd_line(data_rd_line),
               .wr_en(data_wr_en),.wr_index(data_wr_index),.wr_word(data_wr_word),.wr_data(data_wr_data));

    // R10a equivalence checker -- simulation only (hidden from Quartus by
    // translate_off and from every OpenLane tool by __openlane__). Every cycle
    // it checks the invariant that makes hot_mvalid exact (each bit equals the
    // tag RAM's valid bit of the line its hot entry holds) and that the hot
    // hit equals its pre-R10a form, which read tag_valid_rd at the live index.
`ifndef __openlane__
    // synthesis translate_off
    // same as the controller's L0_IDX_BITS (clog2 above == $clog2)
    localparam R10_L0B = (L0_ENTRIES > 1) ? clog2(L0_ENTRIES) : 1;
    integer    r10_e;
    reg        r10_inv_ok;
    reg [27:0] r10_blk;   // block address held by hot entry r10_e
    always @(*) begin
        r10_inv_ok = 1'b1;
        r10_blk    = 28'd0;
        for(r10_e = 0; r10_e < L0_ENTRIES; r10_e = r10_e + 1) begin
            r10_blk = {u_controller.hot_tag[r10_e], r10_e[R10_L0B-1:0]};
            if(u_controller.hot_mvalid[r10_e] !== u_tag_ram.valid_bits[r10_blk[INDEX_WIDTH-1:0]])
                r10_inv_ok = 1'b0;
        end
    end
    wire r10_ref_hot_hit = u_controller.hot_valid[u_controller.hot_index] && tag_valid_rd &&
                           (u_controller.hot_tag[u_controller.hot_index] ==
                            u_controller.request_block[27:R10_L0B]);
    reg [63:0] r10_checks;
    always @(posedge clk or negedge reset_n) begin
        if(!reset_n)
            r10_checks <= 64'd0;
        else if(!r10_inv_ok || (u_controller.hot_hit !== r10_ref_hot_hit))
            $fatal(1, "R10a equivalence broken at %0t: hot_hit %b/%b invariant %b",
                   $time, u_controller.hot_hit, r10_ref_hot_hit, r10_inv_ok);
        else
            r10_checks <= r10_checks + 64'd1;
    end
    final
        $display("R10_EQUIV %m: %0d cycles matched", r10_checks);
    // synthesis translate_on
`endif

    assign main_hit_count=hit_count;
    assign victim_hit_count=32'h0;
    assign true_miss_count=miss_count;
    assign main_hit_event=hit_event;
    assign victim_hit_event=1'b0;
    assign true_miss_event=miss_event;
end else if(CACHE_CONFIG >= 4) begin : g_nway
    // 4 = SA4 (four ways, tree pseudo-LRU). 5 = the same core at two ways, only to check it against SA2.
    wire [3:0] hit_way_vec_unused; wire [1:0] replacement_way_unused;
    icache_nway_core #(.LINE_COUNT(LINE_COUNT),.WAYS((CACHE_CONFIG==5)?2:4),
                       .LINE_WORDS(LINE_WORDS),.L0_ENTRIES(L0_ENTRIES)) u_core(
        .clk(clk),.reset_n(reset_n),.req_valid(req_valid),.req_addr(req_addr),
        .req_ready(req_ready),.rsp_valid(rsp_valid),.rsp_data(rsp_data),.rsp_error(rsp_error),
        .refill_req_valid(refill_req_valid),.refill_req_addr(refill_req_addr),
        .refill_req_ready(refill_req_ready),.refill_rsp_valid(refill_rsp_valid),
        .refill_rsp_data(refill_rsp_data),.refill_rsp_last(refill_rsp_last),
        .refill_rsp_error(refill_rsp_error),.access_count(access_count),.hit_count(hit_count),
        .miss_count(miss_count),.main_hit_count(main_hit_count),
        .victim_hit_count(victim_hit_count),.true_miss_count(true_miss_count),
        .access_event(access_event),.hit_event(hit_event),.miss_event(miss_event),
        .main_hit_event(main_hit_event),.victim_hit_event(victim_hit_event),
        .true_miss_event(true_miss_event),.hit_way_vec_dbg(hit_way_vec_unused),
        .replacement_way_dbg(replacement_way_unused));
end else begin : g_dse
    wire hit_way0_unused,hit_way1_unused,replacement_way_unused;
    wire [VICTIM_ENTRIES-1:0] victim_hit_vec_unused;
    icache_dse_core #(.LINE_COUNT(LINE_COUNT),.CACHE_CONFIG(CACHE_CONFIG),
                      .LINE_WORDS(LINE_WORDS),
                      .VICTIM_ENTRIES(VICTIM_ENTRIES),
                      .L0_ENTRIES(L0_ENTRIES)) u_core(
        .clk(clk),.reset_n(reset_n),.req_valid(req_valid),.req_addr(req_addr),
        .req_ready(req_ready),.rsp_valid(rsp_valid),.rsp_data(rsp_data),.rsp_error(rsp_error),
        .refill_req_valid(refill_req_valid),.refill_req_addr(refill_req_addr),
        .refill_req_ready(refill_req_ready),.refill_rsp_valid(refill_rsp_valid),
        .refill_rsp_data(refill_rsp_data),.refill_rsp_last(refill_rsp_last),
        .refill_rsp_error(refill_rsp_error),.access_count(access_count),.hit_count(hit_count),
        .miss_count(miss_count),.main_hit_count(main_hit_count),
        .victim_hit_count(victim_hit_count),.true_miss_count(true_miss_count),
        .access_event(access_event),.hit_event(hit_event),.miss_event(miss_event),
        .main_hit_event(main_hit_event),.victim_hit_event(victim_hit_event),
        .true_miss_event(true_miss_event),.hit_way0_dbg(hit_way0_unused),
        .hit_way1_dbg(hit_way1_unused),.victim_hit_vec_dbg(victim_hit_vec_unused),
        .replacement_way_dbg(replacement_way_unused));
end
endgenerate

endmodule
