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
// R13b (FLOW_JOURNAL Incident 93): the RV32M multiplier moved out of the single-cycle ALU
// into a two-stage E/M pipeline in datapath.v (partial products in E, final sum in M).
// The MUL* codes return 0 here; datapath.v selects the pipelined product in W.

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
        MUL:    alu_result = 32'd0;
        MULHU:  alu_result = 32'd0;
        MULH:   alu_result = 32'd0;
        MULHSU: alu_result = 32'd0;

        default: alu_result = 32'd0;
    endcase
end

endmodule
