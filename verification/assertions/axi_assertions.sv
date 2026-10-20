`timescale 1ns/1ps

module axi_assertions #(
    // Words per cache line, which is the refill burst length. Fixing this at
    // four would flag every legal longer refill as a protocol error.
    parameter integer LINE_WORDS = 4
) (
    input wire clk,
    input wire reset_n,
    input wire [31:0] araddr,
    input wire [7:0] arlen,
    input wire [2:0] arsize,
    input wire [1:0] arburst,
    input wire arvalid,
    input wire arready,
    input wire [31:0] rdata,
    input wire rlast,
    input wire rvalid,
    input wire rready,
    input wire [31:0] awaddr,
    input wire [7:0] awlen,
    input wire [2:0] awsize,
    input wire [1:0] awburst,
    input wire awvalid,
    input wire awready,
    input wire [31:0] wdata,
    input wire [3:0] wstrb,
    input wire wlast,
    input wire wvalid,
    input wire wready,
    input wire bvalid,
    input wire bready,
    // unused (kept for interface stability)
    input wire native_write_rsp_valid,
    output reg [31:0] assertion_checks
);

reg prev_ar_stall, prev_aw_stall, prev_w_stall;
reg [31:0] prev_araddr, prev_awaddr, prev_wdata;
reg [7:0] prev_arlen, prev_awlen;
reg [2:0] prev_arsize, prev_awsize;
reg [1:0] prev_arburst, prev_awburst;
reg [3:0] prev_wstrb;
reg prev_wlast;
reg read_active;
reg [3:0] read_beats;   // up to 16 beats per refill
reg write_draining;

wire ar_fire = arvalid && arready;
wire r_fire  = rvalid && rready;
wire aw_fire = awvalid && awready;
wire b_fire  = bvalid && bready;

always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        prev_ar_stall <= 0;
        prev_aw_stall <= 0;
        prev_w_stall  <= 0;
        read_active   <= 0;
        read_beats    <= 0;
        write_draining <= 0;
        assertion_checks <= 0;
    end
    else begin
        assertion_checks <= assertion_checks + 1'b1;
        if(prev_ar_stall && (!arvalid || araddr !== prev_araddr ||
           arlen !== prev_arlen || arsize !== prev_arsize || arburst !== prev_arburst))
            $fatal(1, "AXI AR payload changed under backpressure");
        if(prev_aw_stall && (!awvalid || awaddr !== prev_awaddr ||
           awlen !== prev_awlen || awsize !== prev_awsize || awburst !== prev_awburst))
            $fatal(1, "AXI AW payload changed under backpressure");
        if(prev_w_stall && (!wvalid || wdata !== prev_wdata ||
           wstrb !== prev_wstrb || wlast !== prev_wlast))
            $fatal(1, "AXI W payload changed under backpressure");

        prev_ar_stall <= arvalid && !arready;
        prev_aw_stall <= awvalid && !awready;
        prev_w_stall  <= wvalid && !wready;
        if(arvalid) begin
            prev_araddr <= araddr; prev_arlen <= arlen;
            prev_arsize <= arsize; prev_arburst <= arburst;
        end
        if(awvalid) begin
            prev_awaddr <= awaddr; prev_awlen <= awlen;
            prev_awsize <= awsize; prev_awburst <= awburst;
        end
        if(wvalid) begin
            prev_wdata <= wdata; prev_wstrb <= wstrb; prev_wlast <= wlast;
        end

        if(ar_fire) begin
            if(read_active)
                $fatal(1, "more than one AXI read outstanding");
            if(arlen != 8'(LINE_WORDS-1) || arsize != 3'd2 || arburst != 2'b01)
                $fatal(1, "cache refill is not a %0d-beat 32-bit INCR burst (arlen=%0d)",
                       LINE_WORDS, arlen);
            read_active <= 1'b1;
            read_beats <= 0;
        end
        if(r_fire) begin
            if(!read_active)
                $fatal(1, "AXI R beat without active refill");
            if(rlast !== (read_beats == (LINE_WORDS-1)))
                $fatal(1, "AXI RLAST is not on beat %0d of %0d (beat=%0d)",
                       LINE_WORDS, LINE_WORDS, read_beats);
            if(read_beats == (LINE_WORDS-1)) begin
                read_active <= 1'b0;
                read_beats <= 0;
            end
            else begin
                read_beats <= read_beats + 1'b1;
            end
        end
        // Posted-write ordering: a read must not start while a store is
        // still draining, so RAM always sees stores before any later load.
        if(aw_fire)
            write_draining <= 1'b1;
        else if(b_fire)
            write_draining <= 1'b0;
        if(ar_fire && (write_draining && !b_fire))
            $fatal(1, "AXI read started while a store was still draining to memory");
    end
end

endmodule
