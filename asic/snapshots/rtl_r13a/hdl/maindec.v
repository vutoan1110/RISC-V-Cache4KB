module maindec
(
    input  [6:0] op         ,
    output       reg_wr     ,
    output [2:0] imm_src    ,
    output       alu_src    ,
    output       mem_wr     ,
    output [1:0] result_src ,
    output       alu_op     ,
    output       jump
);

reg [9:0] controls ;

assign {reg_wr, imm_src, alu_src, mem_wr, result_src, alu_op, jump} = controls ;

always @(*) begin
    case(op)
        7'b0000011: controls = 10'b1_000_1_0_01_0_0 ; // lw
        7'b0100011: controls = 10'b0_001_1_1_00_0_0 ; // sw
        7'b0110011: controls = 10'b1_000_0_0_00_1_0 ; // R_type
        7'b1100011: controls = 10'b0_010_0_0_00_0_0 ; // branch
        7'b0010011: controls = 10'b1_000_1_0_00_1_0 ; // I_type
        7'b1101111: controls = 10'b1_011_0_0_10_0_1 ; // jal
        7'b1100111: controls = 10'b1_000_1_0_10_0_1 ; // jalr
        7'b0110111: controls = 10'b1_100_1_0_11_1_0 ; // lui
        7'b0010111: controls = 10'b1_100_1_0_11_1_0 ; // auipc
        7'b1110011: controls = 10'b1_000_0_0_00_0_0 ; // csr / mret subset
        default:    controls = 10'b0_000_0_0_00_0_0 ;
    endcase
end

endmodule
