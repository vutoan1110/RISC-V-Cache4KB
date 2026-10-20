module aludec
(
    input            opb5,      
    input      [2:0] funct3,
    input      [6:0] funct7,   
    input            alu_op,
    output reg [3:0] alu_ctrl
);

always @(alu_op, funct3, opb5, funct7) begin
    case(alu_op)
    0: alu_ctrl = 4'b0000; 
    1: begin
        case(funct3)
        3'b000: begin
            if (opb5) begin
                if (funct7 == 7'b0000000) alu_ctrl = 4'b0000; // ADD
                else if (funct7 == 7'b0100000) alu_ctrl = 4'b0001; // SUB
                else if (funct7 == 7'b0000001) alu_ctrl = 4'b1010; // MUL
                else alu_ctrl = 4'b0000;
            end else begin
                alu_ctrl = 4'b0000; // ADDI
            end
        end
        3'b001: begin
            if (opb5 && funct7 == 7'b0000001) alu_ctrl = 4'b1100; // MULH
            else alu_ctrl = 4'b0101; // SLL, SLLI
        end
        3'b010: begin
            if (opb5 && funct7 == 7'b0000001) alu_ctrl = 4'b1101; // MULHSU
            else alu_ctrl = 4'b1000; // SLT, SLTI
        end
        3'b011: begin
            if (opb5 && funct7 == 7'b0000001) alu_ctrl = 4'b1011; // MULHU
            else alu_ctrl = 4'b1001; // SLTU, SLTIU
        end
        3'b100: alu_ctrl = 4'b0010; // XOR, XORI
        3'b101: begin
            if (funct7 == 7'b0000000) alu_ctrl = 4'b0110; // SRL, SRLI
            else if (funct7 == 7'b0100000) alu_ctrl = 4'b0111; // SRA, SRAI
            else alu_ctrl = 4'b0000;
        end
        3'b110: alu_ctrl = 4'b0011; // OR, ORI
        3'b111: alu_ctrl = 4'b0100; // AND, ANDI
        default: alu_ctrl = 4'b0000;
        endcase
    end
    default: alu_ctrl = 4'b0000;
    endcase
end

endmodule
