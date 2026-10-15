module regfile
(
    input         clk   ,
    input         we    ,
    input  [4:0]  rs1   ,
    input  [4:0]  rs2   ,
    input  [4:0]  rd    ,
    input  [31:0] wd    ,
`ifndef __openlane__
    input  [4:0]  rs1_next ,   // FPGA: the rs1 / rs2 fields instr_d takes at the next edge (read-ahead address)
    input  [4:0]  rs2_next ,
`endif
    output [31:0] rd1_d ,
    output [31:0] rd2_d
);

`ifdef __openlane__
reg [31:0] regs [31:0];

always @(posedge clk) begin
    if (we && (rd != 5'd0)) begin
        regs[rd] <= wd ;
    end
    else begin
        regs[rd] <= regs[rd] ;
    end
end

assign rd1_d = (rs1 == 5'd0) ? 32'd0 : (we && rd == rs1) ? wd : regs[rs1];
assign rd2_d = (rs2 == 5'd0) ? 32'd0 : (we && rd == rs2) ? wd : regs[rs2];
`else
// FPGA (2026-10-08, review A1): two M9K copies with a synchronous read instead of 1,024 flip-flops. q* = contents
// before the write of the edge that loaded the address (old data); that write is bypassed from *_q; the write of the
// current cycle is bypassed as in the asynchronous version. Same value as the asynchronous array in every cycle.
(* ramstyle = "M9K" *) reg [31:0] mem1 [0:31];
(* ramstyle = "M9K" *) reg [31:0] mem2 [0:31];
reg  [31:0] q1, q2;
reg         wr_q;
reg  [4:0]  rd_q;
reg  [31:0] wd_q;
wire        wr = we && (rd != 5'd0);

always @(posedge clk) begin
    if (wr) begin
        mem1[rd] <= wd;
        mem2[rd] <= wd;
    end
    q1   <= mem1[rs1_next];
    q2   <= mem2[rs2_next];
    wr_q <= wr;
    rd_q <= rd;
    wd_q <= wd;
end

assign rd1_d = (rs1 == 5'd0) ? 32'd0 : (we && rd == rs1) ? wd : (wr_q && rd_q == rs1) ? wd_q : q1;
assign rd2_d = (rs2 == 5'd0) ? 32'd0 : (we && rd == rs2) ? wd : (wr_q && rd_q == rs2) ? wd_q : q2;

// synthesis translate_off
// Checker: the old asynchronous array beside the new one; any difference of a read stops the simulation.
reg [31:0] ref_regs [31:0];
always @(posedge clk)
    if (we && (rd != 5'd0)) ref_regs[rd] <= wd;
wire [31:0] ref_rd1 = (rs1 == 5'd0) ? 32'd0 : (we && rd == rs1) ? wd : ref_regs[rs1];
wire [31:0] ref_rd2 = (rs2 == 5'd0) ? 32'd0 : (we && rd == rs2) ? wd : ref_regs[rs2];
always @(negedge clk) begin
    if ((rd1_d !== ref_rd1 && ref_rd1 !== 32'bx) || (rd2_d !== ref_rd2 && ref_rd2 !== 32'bx))
        $fatal(1, "regfile M9K checker: rd1 %h / %h, rd2 %h / %h (rs1 %0d rs2 %0d) at %0t",
               rd1_d, ref_rd1, rd2_d, ref_rd2, rs1, rs2, $time);
end
// synthesis translate_on
`endif

endmodule
