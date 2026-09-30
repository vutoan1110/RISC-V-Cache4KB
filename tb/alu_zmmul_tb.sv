`timescale 1ns/1ps

module tb_alu_zmmul;

reg  [31:0] src_a;
reg  [31:0] src_b;
reg  [3:0]  alu_ctrl;
wire [31:0] alu_result;
integer checks;

localparam ADD    = 4'b0000;
localparam SUB    = 4'b0001;
localparam XOR_OP = 4'b0010;
localparam OR_OP  = 4'b0011;
localparam AND_OP = 4'b0100;
localparam SLL    = 4'b0101;
localparam SRL    = 4'b0110;
localparam SRA    = 4'b0111;
localparam SLT    = 4'b1000;
localparam SLTU   = 4'b1001;
localparam MUL    = 4'b1010;
localparam MULHU  = 4'b1011;
localparam MULH   = 4'b1100;
localparam MULHSU = 4'b1101;

alu dut (
    .src_a(src_a), .src_b(src_b), .alu_ctrl(alu_ctrl),
    .alu_result(alu_result)
);

task automatic expect_alu;
    input [3:0] ctrl;
    input [31:0] a;
    input [31:0] b;
    input [31:0] expected;
    input string label_text;
begin
    alu_ctrl = ctrl;
    src_a = a;
    src_b = b;
    #1;
    checks = checks + 1;
    if(alu_result !== expected)
        $fatal(1, "%s: a=%08x b=%08x expected=%08x got=%08x",
               label_text, a, b, expected, alu_result);
end
endtask

task automatic check_mul_vector;
    input [31:0] a;
    input [31:0] b;
    longint signed signed_a;
    longint signed signed_b;
    longint signed unsigned_b_as_signed64;
    longint signed product_ss;
    longint unsigned product_uu;
    longint signed product_su;
begin
    signed_a = $signed(a);
    signed_b = $signed(b);
    unsigned_b_as_signed64 = {32'h0000_0000, b};
    product_ss = signed_a * signed_b;
    product_uu = {32'h0000_0000, a} * {32'h0000_0000, b};
    product_su = signed_a * unsigned_b_as_signed64;

    expect_alu(MUL,    a, b, product_ss[31:0],  "MUL low product");
    expect_alu(MULH,   a, b, product_ss[63:32], "MULH signed high product");
    expect_alu(MULHU,  a, b, product_uu[63:32], "MULHU unsigned high product");
    expect_alu(MULHSU, a, b, product_su[63:32], "MULHSU signed/unsigned high product");
end
endtask

initial begin
    checks = 0;
    src_a = 0;
    src_b = 0;
    alu_ctrl = ADD;

    // RV32I ALU corner behavior. Immediate and register forms share this ALU.
    expect_alu(ADD,    32'hffff_ffff, 32'h0000_0001, 32'h0000_0000, "ADD wrap");
    expect_alu(SUB,    32'h0000_0000, 32'h0000_0001, 32'hffff_ffff, "SUB wrap");
    expect_alu(AND_OP, 32'h8000_0001, 32'h7fff_ffff, 32'h0000_0001, "AND");
    expect_alu(OR_OP,  32'h8000_0000, 32'h0000_0001, 32'h8000_0001, "OR");
    expect_alu(XOR_OP, 32'hffff_ffff, 32'h8000_0000, 32'h7fff_ffff, "XOR");
    expect_alu(SLT,    32'h8000_0000, 32'h0000_0001, 32'h0000_0001, "SLT signed");
    expect_alu(SLTU,   32'h8000_0000, 32'h0000_0001, 32'h0000_0000, "SLTU unsigned");
    expect_alu(SLL,    32'h0000_0001, 32'h0000_001f, 32'h8000_0000, "SLL shamt31");
    expect_alu(SRL,    32'h8000_0000, 32'h0000_001f, 32'h0000_0001, "SRL shamt31");
    expect_alu(SRA,    32'h8000_0000, 32'h0000_001f, 32'hffff_ffff, "SRA shamt31");

    check_mul_vector(32'h0000_0000, 32'h0000_0000);
    check_mul_vector(32'h0000_0001, 32'h0000_0001);
    check_mul_vector(32'hffff_ffff, 32'hffff_ffff);
    check_mul_vector(32'hffff_ffff, 32'h0000_0001);
    check_mul_vector(32'h8000_0000, 32'h0000_0001);
    check_mul_vector(32'h8000_0000, 32'hffff_ffff);
    check_mul_vector(32'hffff_ffff, 32'hffff_ffff);
    check_mul_vector(32'h8000_0000, 32'h8000_0000);
    check_mul_vector(32'h7fff_ffff, 32'h7fff_ffff);

    $display("[PASS] RV32I ALU directed corner regression (%0d checks)", checks);
    $display("[PASS] Zmmul full-width corner regression");
    $finish;
end

endmodule
