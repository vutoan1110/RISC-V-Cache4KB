`timescale 1ns/1ps

module cache_assertions (
    input wire clk,
    input wire reset_n,
    input wire [31:0] i_access,
    input wire [31:0] i_hit,
    input wire [31:0] i_miss,
    input wire [31:0] d_access,
    input wire [31:0] d_read,
    input wire [31:0] d_write,
    input wire [31:0] d_hit,
    input wire [31:0] d_miss,
    input wire [31:0] d_read_hit,
    input wire [31:0] d_read_miss,
    input wire [31:0] d_write_hit,
    input wire [31:0] d_write_miss,
    input wire d_write_miss_event,
    input wire d_refill_req_valid,
    input wire d_tag_write_enable,
    output reg [31:0] assertion_checks
);

always @(posedge clk or negedge reset_n) begin
    if(!reset_n)
        assertion_checks <= 0;
    else begin
        assertion_checks <= assertion_checks + 1'b1;
        #1;
        if(i_access !== i_hit + i_miss)
            $fatal(1, "I-cache access != hit + miss");
        if(d_access !== d_hit + d_miss || d_access !== d_read + d_write)
            $fatal(1, "D-cache access accounting invariant failed");
        if(d_read !== d_read_hit + d_read_miss)
            $fatal(1, "D-cache read accounting invariant failed");
        if(d_write !== d_write_hit + d_write_miss)
            $fatal(1, "D-cache write accounting invariant failed");
        if(d_write_miss_event && (d_refill_req_valid || d_tag_write_enable))
            $fatal(1, "store miss attempted refill/allocation");
    end
end

endmodule
