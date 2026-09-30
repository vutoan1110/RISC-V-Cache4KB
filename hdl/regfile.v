module regfile
(
    input         clk   , 
    input         we    ,
    input  [4:0]  rs1   ,
    input  [4:0]  rs2   ,
    input  [4:0]  rd    ,
    input  [31:0] wd    ,
    output [31:0] rd1_d ,
    output [31:0] rd2_d
);

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

endmodule
