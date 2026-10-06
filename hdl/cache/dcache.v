// D-cache organization selector. CACHE_CONFIG: 0=DM, 1=SA2, 2=DM_VC4.
module dcache #(
    parameter LINE_COUNT=64,
    parameter CACHE_CONFIG=0,
    parameter LINE_WORDS=4,
    parameter VICTIM_ENTRIES=4,
    // R16 (review M1): DSE / N-way cores answer a main-array load hit in ST_LOOKUP; the DM controller ignores it.
    parameter FAST_HIT=0
)(
    input wire clk,input wire reset_n,
    input wire req_valid,input wire req_write,input wire [31:0] req_addr,
    input wire [31:0] req_wdata,input wire [3:0] req_wstrb,
    output wire req_ready,output wire rsp_valid,output wire [31:0] rsp_rdata,output wire rsp_error,
    output wire refill_req_valid,output wire [31:0] refill_req_addr,input wire refill_req_ready,
    input wire refill_rsp_valid,input wire [31:0] refill_rsp_data,input wire refill_rsp_last,
    input wire refill_rsp_error,output wire mem_wr_valid,output wire [31:0] mem_wr_addr,
    output wire [31:0] mem_wr_data,output wire [3:0] mem_wr_strb,input wire mem_wr_ready,
    input wire mem_wr_rsp_valid,input wire mem_wr_rsp_error,
    output wire [31:0] access_count,output wire [31:0] read_count,output wire [31:0] write_count,
    output wire [31:0] hit_count,output wire [31:0] miss_count,
    output wire [31:0] read_hit_count,output wire [31:0] read_miss_count,
    output wire [31:0] write_hit_count,output wire [31:0] write_miss_count,
    output wire read_access_event,output wire read_hit_event,output wire read_miss_event,
    output wire write_access_event,output wire write_hit_event,output wire write_miss_event,
    output wire [31:0] main_hit_count,output wire [31:0] victim_hit_count,
    output wire [31:0] true_miss_count,output wire main_hit_event,
    output wire victim_hit_event,output wire true_miss_event
);

function integer clog2;
    input integer value; integer tmp;
    begin tmp=value-1;clog2=0;while(tmp>0)begin clog2=clog2+1;tmp=tmp>>1;end end
endfunction

generate
if(CACHE_CONFIG==0) begin:g_dm_baseline
    localparam INDEX_WIDTH=(LINE_COUNT>1)?clog2(LINE_COUNT):1;
    localparam TAG_WIDTH=32-4-INDEX_WIDTH;
    // See icache.v: this branch is a 16-byte-line design and LINE_WORDS is not
    // carried into the controller or the RAMs, so the combination must fail
    // loudly rather than elaborate into a cache that addresses the wrong words.
    // synthesis translate_off
    initial if(LINE_WORDS != 4)
        $fatal(1, "%m: CACHE_CONFIG=0 supports LINE_WORDS=4 only, got %0d",
               LINE_WORDS);
    // synthesis translate_on
    wire [INDEX_WIDTH-1:0] tag_rd_index,tag_wr_index,data_rd_index,data_wr_index;
    wire [TAG_WIDTH-1:0] tag_rd_tag,tag_wr_tag;
    wire tag_rd_en,tag_valid_rd,tag_wr_en,tag_wr_valid,data_wr_en,data_rd_en;
    wire [INDEX_WIDTH-1:0] tag_valid_rd_index;
    wire [1:0] data_wr_word; wire [127:0] data_rd_line; wire [31:0] data_wr_data;
    dcache_controller #(.INDEX_WIDTH(INDEX_WIDTH),.TAG_WIDTH(TAG_WIDTH)) u_controller(
        .clk(clk),.reset_n(reset_n),.req_valid(req_valid),.req_write(req_write),.req_addr(req_addr),
        .req_wdata(req_wdata),.req_wstrb(req_wstrb),.req_ready(req_ready),.rsp_valid(rsp_valid),
        .rsp_rdata(rsp_rdata),.rsp_error(rsp_error),.refill_req_valid(refill_req_valid),
        .refill_req_addr(refill_req_addr),.refill_req_ready(refill_req_ready),
        .refill_rsp_valid(refill_rsp_valid),.refill_rsp_data(refill_rsp_data),
        .refill_rsp_last(refill_rsp_last),.refill_rsp_error(refill_rsp_error),
        .mem_wr_valid(mem_wr_valid),.mem_wr_addr(mem_wr_addr),.mem_wr_data(mem_wr_data),
        .mem_wr_strb(mem_wr_strb),.mem_wr_ready(mem_wr_ready),.mem_wr_rsp_valid(mem_wr_rsp_valid),
        .mem_wr_rsp_error(mem_wr_rsp_error),.access_count(access_count),.read_count(read_count),
        .write_count(write_count),.hit_count(hit_count),.miss_count(miss_count),
        .read_hit_count(read_hit_count),.read_miss_count(read_miss_count),
        .write_hit_count(write_hit_count),.write_miss_count(write_miss_count),
        .read_access_event(read_access_event),.read_hit_event(read_hit_event),
        .read_miss_event(read_miss_event),.write_access_event(write_access_event),
        .write_hit_event(write_hit_event),.write_miss_event(write_miss_event),
        .tag_rd_en(tag_rd_en),.tag_rd_index(tag_rd_index),.tag_rd_tag(tag_rd_tag),
        .tag_valid_rd_index(tag_valid_rd_index),.tag_valid_rd(tag_valid_rd),
        .tag_wr_en(tag_wr_en),.tag_wr_index(tag_wr_index),.tag_wr_tag(tag_wr_tag),
        .tag_wr_valid(tag_wr_valid),
        .data_rd_en(data_rd_en),.data_rd_index(data_rd_index),.data_rd_line(data_rd_line),
        .data_wr_en(data_wr_en),.data_wr_index(data_wr_index),
        .data_wr_word(data_wr_word),.data_wr_data(data_wr_data));
    dcache_tag_ram #(.LINE_COUNT(LINE_COUNT),.INDEX_WIDTH(INDEX_WIDTH),.TAG_WIDTH(TAG_WIDTH)) u_tag_ram(
        .clk(clk),.reset_n(reset_n),
        .rd_en(tag_rd_en),.rd_index(tag_rd_index),.rd_tag(tag_rd_tag),
        .valid_rd_index(tag_valid_rd_index),.valid_rd(tag_valid_rd),
        .wr_en(tag_wr_en),.wr_index(tag_wr_index),.wr_tag(tag_wr_tag),.wr_valid(tag_wr_valid));
    dcache_data_ram #(.LINE_COUNT(LINE_COUNT),.INDEX_WIDTH(INDEX_WIDTH)) u_data_ram(
        .clk(clk),.rd_en(data_rd_en),.rd_index(data_rd_index),.rd_line(data_rd_line),
        .wr_en(data_wr_en),.wr_index(data_wr_index),.wr_word(data_wr_word),.wr_data(data_wr_data));
    assign main_hit_count=hit_count; assign victim_hit_count=0; assign true_miss_count=miss_count;
    assign main_hit_event=read_hit_event||write_hit_event;
    assign victim_hit_event=1'b0; assign true_miss_event=read_miss_event||write_miss_event;
end else if(CACHE_CONFIG>=4) begin:g_nway
    // 4 = SA4 (four ways, tree pseudo-LRU). 5 = the same core at two ways, only to check it against SA2.
    wire [3:0] hit_way_vec_unused; wire [1:0] replacement_way_unused;
    dcache_nway_core #(.LINE_COUNT(LINE_COUNT),.WAYS((CACHE_CONFIG==5)?2:4),
                       .LINE_WORDS(LINE_WORDS),.FAST_HIT(FAST_HIT)) u_core(
        .clk(clk),.reset_n(reset_n),.req_valid(req_valid),.req_write(req_write),.req_addr(req_addr),
        .req_wdata(req_wdata),.req_wstrb(req_wstrb),.req_ready(req_ready),.rsp_valid(rsp_valid),
        .rsp_rdata(rsp_rdata),.rsp_error(rsp_error),.refill_req_valid(refill_req_valid),
        .refill_req_addr(refill_req_addr),.refill_req_ready(refill_req_ready),
        .refill_rsp_valid(refill_rsp_valid),.refill_rsp_data(refill_rsp_data),
        .refill_rsp_last(refill_rsp_last),.refill_rsp_error(refill_rsp_error),
        .mem_wr_valid(mem_wr_valid),.mem_wr_addr(mem_wr_addr),.mem_wr_data(mem_wr_data),
        .mem_wr_strb(mem_wr_strb),.mem_wr_ready(mem_wr_ready),.mem_wr_rsp_valid(mem_wr_rsp_valid),
        .mem_wr_rsp_error(mem_wr_rsp_error),.access_count(access_count),.read_count(read_count),
        .write_count(write_count),.hit_count(hit_count),.miss_count(miss_count),
        .read_hit_count(read_hit_count),.read_miss_count(read_miss_count),
        .write_hit_count(write_hit_count),.write_miss_count(write_miss_count),
        .main_hit_count(main_hit_count),.victim_hit_count(victim_hit_count),
        .true_miss_count(true_miss_count),.read_access_event(read_access_event),
        .read_hit_event(read_hit_event),.read_miss_event(read_miss_event),
        .write_access_event(write_access_event),.write_hit_event(write_hit_event),
        .write_miss_event(write_miss_event),.main_hit_event(main_hit_event),
        .victim_hit_event(victim_hit_event),.true_miss_event(true_miss_event),
        .hit_way_vec_dbg(hit_way_vec_unused),.replacement_way_dbg(replacement_way_unused));
end else begin:g_dse
    wire hit_way0_unused,hit_way1_unused,replacement_way_unused;
    wire [VICTIM_ENTRIES-1:0] victim_hit_vec_unused;
    dcache_dse_core #(.LINE_COUNT(LINE_COUNT),.CACHE_CONFIG(CACHE_CONFIG),
                      .LINE_WORDS(LINE_WORDS),
                      .VICTIM_ENTRIES(VICTIM_ENTRIES),.FAST_HIT(FAST_HIT)) u_core(
        .clk(clk),.reset_n(reset_n),.req_valid(req_valid),.req_write(req_write),.req_addr(req_addr),
        .req_wdata(req_wdata),.req_wstrb(req_wstrb),.req_ready(req_ready),.rsp_valid(rsp_valid),
        .rsp_rdata(rsp_rdata),.rsp_error(rsp_error),.refill_req_valid(refill_req_valid),
        .refill_req_addr(refill_req_addr),.refill_req_ready(refill_req_ready),
        .refill_rsp_valid(refill_rsp_valid),.refill_rsp_data(refill_rsp_data),
        .refill_rsp_last(refill_rsp_last),.refill_rsp_error(refill_rsp_error),
        .mem_wr_valid(mem_wr_valid),.mem_wr_addr(mem_wr_addr),.mem_wr_data(mem_wr_data),
        .mem_wr_strb(mem_wr_strb),.mem_wr_ready(mem_wr_ready),.mem_wr_rsp_valid(mem_wr_rsp_valid),
        .mem_wr_rsp_error(mem_wr_rsp_error),.access_count(access_count),.read_count(read_count),
        .write_count(write_count),.hit_count(hit_count),.miss_count(miss_count),
        .read_hit_count(read_hit_count),.read_miss_count(read_miss_count),
        .write_hit_count(write_hit_count),.write_miss_count(write_miss_count),
        .main_hit_count(main_hit_count),.victim_hit_count(victim_hit_count),
        .true_miss_count(true_miss_count),.read_access_event(read_access_event),
        .read_hit_event(read_hit_event),.read_miss_event(read_miss_event),
        .write_access_event(write_access_event),.write_hit_event(write_hit_event),
        .write_miss_event(write_miss_event),.main_hit_event(main_hit_event),
        .victim_hit_event(victim_hit_event),.true_miss_event(true_miss_event),
        .hit_way0_dbg(hit_way0_unused),.hit_way1_dbg(hit_way1_unused),
        .victim_hit_vec_dbg(victim_hit_vec_unused),.replacement_way_dbg(replacement_way_unused));
end
endgenerate
endmodule
