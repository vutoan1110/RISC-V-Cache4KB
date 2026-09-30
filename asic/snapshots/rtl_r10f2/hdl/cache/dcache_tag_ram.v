module dcache_tag_ram #(
    parameter LINE_COUNT  = 64,
    parameter INDEX_WIDTH = 6,
    parameter TAG_WIDTH   = 22
)(
    input  wire                   clk,
    input  wire                   reset_n,

    // Synchronous tag port: rd_tag is the tag of the index presented one
    // cycle earlier. There is no combinational path from rd_index to rd_tag.
    input  wire                   rd_en,
    input  wire [INDEX_WIDTH-1:0] rd_index,
    output reg  [TAG_WIDTH-1:0]   rd_tag,

    // Combinational valid port. The hot-buffer path consults it in the same
    // cycle it accepts a request, so it cannot be registered. See
    // CLAUDE_AUTONOMY_LOG.md entry 4.
    input  wire [INDEX_WIDTH-1:0] valid_rd_index,
    output wire                   valid_rd,

    input  wire                   wr_en,
    input  wire [INDEX_WIDTH-1:0] wr_index,
    input  wire [TAG_WIDTH-1:0]   wr_tag,
    input  wire                   wr_valid
);

// Tags need no reset; the packed valid vector clears all lines at once.
reg [TAG_WIDTH-1:0] tag_mem [0:LINE_COUNT-1];
reg [LINE_COUNT-1:0] valid_bits;

assign valid_rd = valid_bits[valid_rd_index];

// A tag write and a tag read of the same index never coincide: reads are
// issued from ST_IDLE and every write happens with req_ready low. No
// write-forwarding is needed.
always @(posedge clk) begin
    if(rd_en)
        rd_tag <= tag_mem[rd_index];
    if(wr_en && wr_valid)
        tag_mem[wr_index] <= wr_tag;
end

always @(posedge clk or negedge reset_n) begin
    if(!reset_n)
        valid_bits <= {LINE_COUNT{1'b0}};
    else if(wr_en)
        valid_bits[wr_index] <= wr_valid;
end

endmodule
