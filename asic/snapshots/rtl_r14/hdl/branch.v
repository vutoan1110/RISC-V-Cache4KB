module branch 
(
    input      [31:0] reg1           ,
    input      [31:0] reg2           ,
    input             branch_en      ,
    input      [2:0]  funct3         ,
    output reg        branch_taken_e
);

always @(branch_en, funct3, reg1, reg2) begin
    if (branch_en) begin
        case (funct3)
            3'b000:  branch_taken_e = (reg1 == reg2)                   ; //beq
            3'b001:  branch_taken_e = (reg1 != reg2)                   ; //bne
            3'b100:  branch_taken_e = ($signed(reg1) < $signed(reg2))  ; //blt 
            3'b101:  branch_taken_e = ($signed(reg1) >= $signed(reg2)) ; //bge 
            3'b110:  branch_taken_e = (reg1 < reg2)                    ; //bltu
            3'b111:  branch_taken_e = (reg1 >= reg2)                   ; //bgeu
            default: branch_taken_e = 0                                ;
        endcase
    end
    else begin
        branch_taken_e = 0 ;
    end
end

endmodule
