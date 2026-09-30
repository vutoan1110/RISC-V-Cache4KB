// Instruction-cache tag storage.
//
// The tags are read strictly synchronously: there is no combinational path from
// rd_index to rd_tag. That is what lets this array be a real memory rather than
// a mux tree over flip-flops, and it is the shape a hardened SRAM macro or an
// M9K block can take.
//
// The valid bits are deliberately NOT part of that array. They are control
// state, not data: reset has to clear all of them at once, and the controller
// has to read one in the same cycle it accepts a request, because that is what
// keeps the L0 hot buffer coherent. Sixty-four flip-flops is the right price for
// that. Splitting them out is the whole reason the 0-cycle hot-buffer path
// survives the move to synchronous tags.
module icache_tag_ram #(
    parameter LINE_COUNT  = 64,
    parameter INDEX_WIDTH = 6,
    parameter TAG_WIDTH   = 22
)(
    input  wire                   clk,
    input  wire                   reset_n,

    // Synchronous tag port. rd_tag is valid the cycle after rd_en.
    input  wire                   rd_en,
    input  wire [INDEX_WIDTH-1:0] rd_index,
    output reg  [TAG_WIDTH-1:0]   rd_tag,

    // Combinational valid port, read in the request cycle.
    input  wire [INDEX_WIDTH-1:0] valid_rd_index,
    output wire                   valid_rd,

    input  wire                   wr_en,
    input  wire [INDEX_WIDTH-1:0] wr_index,
    input  wire [TAG_WIDTH-1:0]   wr_tag,
    input  wire                   wr_valid
);

// Tags need no reset; a cleared valid bit makes their contents irrelevant.
reg [TAG_WIDTH-1:0] tag_mem    [0:LINE_COUNT-1];
// Packed, like dcache_tag_ram.v, so the reset is one assignment rather than
// a loop. Verilator refuses to unroll a 256-iteration delayed assignment to
// an array (%Error-BLKLOOPINIT), so the unpacked form linted clean at 64
// lines and failed OpenLane's own lint the moment the 4 KiB build was
// attempted. The two tag RAMs were inconsistent; this makes them match.
reg [LINE_COUNT-1:0] valid_bits;

assign valid_rd = valid_bits[valid_rd_index];

// A tag write and a tag read of the same index in the same cycle cannot happen:
// the controller only issues a read in ST_IDLE, and every tag write happens in a
// state where req_ready is low. The read therefore needs no write-forwarding.
always @(posedge clk) begin
    if(rd_en)
        rd_tag <= tag_mem[rd_index];
    if(wr_en && wr_valid)
        tag_mem[wr_index] <= wr_tag;
end

always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        valid_bits <= {LINE_COUNT{1'b0}};
    end
    else if(wr_en) begin
        valid_bits[wr_index] <= wr_valid;
    end
end

endmodule
