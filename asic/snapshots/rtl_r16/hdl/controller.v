module controller
(
    input            clk             ,
    input            reset_n         ,
    input      [6:0] op              ,
    input      [2:0] funct3          ,
    input      [6:0] funct7          ,
    input            flush_e         ,
    input            stall_pipe      ,
    input            valid_d         ,
    output reg [1:0] result_src_e    ,
    output reg [1:0] result_src_m    ,  // R9: datapath registers the W result select
    output reg [1:0] result_src_w    ,
    output reg       mem_wr_m        ,
    output reg       mem_rd_m        ,
    output reg       alu_src_e       ,
    output reg       reg_wr_e        ,  // R9: datapath registers the forward selects
    output reg       reg_wr_m        ,
    output reg       reg_wr_w        , 
    output reg       jump_e          ,
    output     [2:0] imm_src_d       ,
    output reg [3:0] alu_ctrl_e,
    output reg       use_rs1_d,
    output reg       use_rs2_d
);

wire       alu_op       ;

// Decode-stage source-operand usage. These signals prevent false
// load-use hazards when instr[24:20] is an immediate field rather than rs2.
always @(*) begin
    use_rs1_d = 1'b0;
    use_rs2_d = 1'b0;

    if (valid_d) begin
        case (op)
            7'b0110011: begin use_rs1_d = 1'b1; use_rs2_d = 1'b1; end // R-type
            7'b0100011: begin use_rs1_d = 1'b1; use_rs2_d = 1'b1; end // store
            7'b1100011: begin use_rs1_d = 1'b1; use_rs2_d = 1'b1; end // branch
            7'b0000011: begin use_rs1_d = 1'b1; use_rs2_d = 1'b0; end // load
            7'b0010011: begin use_rs1_d = 1'b1; use_rs2_d = 1'b0; end // I-type ALU
            7'b1100111: begin use_rs1_d = 1'b1; use_rs2_d = 1'b0; end // JALR
            7'b1110011: begin
                // CSR register forms use rs1. Immediate CSR forms use zimm.
                use_rs1_d = (funct3 == 3'b001) ||
                            (funct3 == 3'b010) ||
                            (funct3 == 3'b011);
                use_rs2_d = 1'b0;
            end
            default: begin use_rs1_d = 1'b0; use_rs2_d = 1'b0; end
        endcase
    end
end
wire [1:0] result_src_d ;
wire       mem_wr_d     ;
wire       alu_src_d    ;
wire       reg_wr_d     ;
wire       jump_d       ;
wire [3:0] alu_ctrl_d   ;
reg        mem_wr_e     ;
reg        mem_rd_e     ;


maindec maindec(
    .op         (op)           ,
    .result_src (result_src_d) ,
    .mem_wr     (mem_wr_d)     ,
    .alu_src    (alu_src_d)    ,
    .reg_wr     (reg_wr_d)     ,
    .jump       (jump_d)       ,
    .imm_src    (imm_src_d)    ,
    .alu_op     (alu_op)
);

aludec aludec(
    .opb5     (op[5])      ,
    .funct3   (funct3)     ,
    .funct7   (funct7)     ,
    .alu_op   (alu_op)     ,
    .alu_ctrl (alu_ctrl_d)
);

always @(posedge clk, negedge reset_n) begin
    if(!reset_n) begin
        result_src_e <= 0 ;
        mem_wr_e     <= 0 ;
        mem_rd_e     <= 0 ;
        alu_src_e    <= 0 ;
        reg_wr_e     <= 0 ;
        jump_e       <= 0 ;
        alu_ctrl_e   <= 0 ;
        result_src_m <= 0 ;
        mem_wr_m     <= 0 ;
        mem_rd_m     <= 0 ;
        reg_wr_m     <= 0 ;
        result_src_w <= 0 ;
        reg_wr_w     <= 0 ;
    end
    else begin
        if(!stall_pipe) begin
            if(!flush_e && valid_d) begin
                result_src_e <= result_src_d ;
                mem_wr_e     <= mem_wr_d     ;
                mem_rd_e     <= (result_src_d == 2'b01) ;
                alu_src_e    <= alu_src_d    ;
                reg_wr_e     <= reg_wr_d     ;
                jump_e       <= jump_d       ;
                alu_ctrl_e   <= alu_ctrl_d   ;
            end
            else begin
                result_src_e <= 0 ;
                mem_wr_e     <= 0 ;
                mem_rd_e     <= 0 ;
                alu_src_e    <= 0 ;
                reg_wr_e     <= 0 ;
                jump_e       <= 0 ;
                alu_ctrl_e   <= 0 ;
            end
            result_src_m <= result_src_e ;
            mem_wr_m     <= mem_wr_e     ;
            mem_rd_m     <= mem_rd_e     ;
            reg_wr_m     <= reg_wr_e     ;
            result_src_w <= result_src_m ;
            reg_wr_w     <= reg_wr_m     ;
        end
    end
end

endmodule
