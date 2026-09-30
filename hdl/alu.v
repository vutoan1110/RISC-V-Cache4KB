module alu(
    input      [31:0] src_a,
    input      [31:0] src_b,
    input      [3:0]  alu_ctrl,
    output reg [31:0] alu_result
);

localparam ADD    = 4'b0000;
localparam SUB    = 4'b0001;
localparam XOR    = 4'b0010;
localparam OR     = 4'b0011;
localparam AND    = 4'b0100;
localparam SLL    = 4'b0101;
localparam SRL    = 4'b0110;
localparam SRA    = 4'b0111;
localparam SLT    = 4'b1000;
localparam SLTU   = 4'b1001;
localparam MUL    = 4'b1010;
localparam MULHU  = 4'b1011;
localparam MULH   = 4'b1100;
localparam MULHSU = 4'b1101;

wire [4:0] shamt = src_b[4:0];

// RV32 multiplies (R7, NHAT_KY_RTL 2026-09-25): ONE signed 33x33 multiplier
// instead of three 32x32 ones (signed*signed, unsigned*unsigned,
// signed*unsigned). Each operand gets a 33rd bit that is its sign bit when
// the op treats it as signed and 0 otherwise; the 66-bit signed product then
// holds the exact 64-bit result of every variant in [63:0]. MUL (low word)
// is the same for any signedness. Same results, a third of the multiplier
// logic, and the forwarded operands drive one array instead of three.
wire mul_a_signed = (alu_ctrl == MULH) || (alu_ctrl == MULHSU);
wire mul_b_signed = (alu_ctrl == MULH);
wire signed [32:0] mul_a   = {mul_a_signed & src_a[31], src_a};
wire signed [32:0] mul_b   = {mul_b_signed & src_b[31], src_b};
wire signed [65:0] product = mul_a * mul_b;

always @(*) begin
    case (alu_ctrl)
        ADD:    alu_result = src_a + src_b;
        SUB:    alu_result = src_a - src_b;
        XOR:    alu_result = src_a ^ src_b;
        OR:     alu_result = src_a | src_b;
        AND:    alu_result = src_a & src_b;
        SLL:    alu_result = src_a << shamt;
        SRL:    alu_result = src_a >> shamt;
        SRA:    alu_result = $signed(src_a) >>> shamt;
        SLT:    alu_result = ($signed(src_a) < $signed(src_b)) ? 32'd1 : 32'd0;
        SLTU:   alu_result = (src_a < src_b) ? 32'd1 : 32'd0;

        // RV32M
        MUL:    alu_result = product[31:0];
        MULHU:  alu_result = product[63:32];
        MULH:   alu_result = product[63:32];
        MULHSU: alu_result = product[63:32];

        default: alu_result = 32'd0;
    endcase
end

endmodule
