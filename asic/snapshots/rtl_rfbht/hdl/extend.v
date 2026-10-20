module extend
(
    input      [31:7] instr_d  ,
    input      [2:0]  immsrc_d ,
    output reg [31:0] immext_d
);

always @(immsrc_d, instr_d) begin
    immext_d = 0 ;
    case(immsrc_d)
        3'b000:  immext_d = {{20{instr_d[31]}}, instr_d[31:20]}                                    ; //I_type
        3'b001:  immext_d = {{20{instr_d[31]}}, instr_d[31:25], instr_d[11:7]}                     ; //S_type 
        3'b010:  immext_d = {{20{instr_d[31]}}, instr_d[7], instr_d[30:25], instr_d[11:8], 1'b0}   ; //B_type 
        3'b011:  immext_d = {{12{instr_d[31]}}, instr_d[19:12], instr_d[20], instr_d[30:21], 1'b0} ; //J_type 
        3'b100:  immext_d = {instr_d[31:12], 12'b0}                                                ; //U_type
        default: immext_d = 0                                                                      ;
    endcase
end

endmodule
