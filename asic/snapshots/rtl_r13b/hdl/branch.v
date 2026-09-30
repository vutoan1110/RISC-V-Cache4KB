module branch
(
    input      [31:0] reg1           ,
    input      [31:0] reg2           ,
    input             branch_en      ,
    input      [2:0]  funct3         ,
    output reg        branch_taken_e
);

// R13a-3 (FLOW_JOURNAL Incident 93, cycle-exact): the same function as the
// behavioural ==, <, $signed <, written as a log-depth comparator for the ss corner.
// ABC with the area strategy had turned the <, >= of the original into a ripple
// chain of a2111o gates (7-9 ns at max_ss, inside the EX redirect loop). Here a
// parallel-prefix tree combines (lt, eq) pairs in five levels; every level is a
// (* keep *) net, which ABC treats as a cut point, so it cannot re-chain it.
// Bits [30:0] share one tree (position 31 is padded with lt=0 / eq=1); bit 31,
// which differs between signed and unsigned, is combined last.
(* keep *) wire [31:0] lt0, eq0;
(* keep *) wire [15:0] lt1, eq1;
(* keep *) wire [7:0]  lt2, eq2;
(* keep *) wire [3:0]  lt3, eq3;
(* keep *) wire [1:0]  lt4, eq4;
assign lt0 = {1'b0, ~reg1[30:0] & reg2[30:0]};
assign eq0 = {1'b1, ~(reg1[30:0] ^ reg2[30:0])};
genvar i;
generate
    for(i = 0; i < 16; i = i + 1) begin : g_l1
        assign lt1[i] = lt0[2*i+1] | (eq0[2*i+1] & lt0[2*i]);
        assign eq1[i] = eq0[2*i+1] & eq0[2*i];
    end
    for(i = 0; i < 8; i = i + 1) begin : g_l2
        assign lt2[i] = lt1[2*i+1] | (eq1[2*i+1] & lt1[2*i]);
        assign eq2[i] = eq1[2*i+1] & eq1[2*i];
    end
    for(i = 0; i < 4; i = i + 1) begin : g_l3
        assign lt3[i] = lt2[2*i+1] | (eq2[2*i+1] & lt2[2*i]);
        assign eq3[i] = eq2[2*i+1] & eq2[2*i];
    end
    for(i = 0; i < 2; i = i + 1) begin : g_l4
        assign lt4[i] = lt3[2*i+1] | (eq3[2*i+1] & lt3[2*i]);
        assign eq4[i] = eq3[2*i+1] & eq3[2*i];
    end
endgenerate
wire lt_low  = lt4[1] | (eq4[1] & lt4[0]);    // reg1[30:0] < reg2[30:0]
wire eq_low  = eq4[1] & eq4[0];               // reg1[30:0] == reg2[30:0]
wire eq_31   = ~(reg1[31] ^ reg2[31]);
wire cmp_eq  = eq_31 & eq_low;
wire cmp_ltu = (~reg1[31] & reg2[31]) | (eq_31 & lt_low);
wire cmp_lts = (reg1[31] & ~reg2[31]) | (eq_31 & lt_low);

always @(branch_en, funct3, cmp_eq, cmp_ltu, cmp_lts) begin
    if (branch_en) begin
        case (funct3)
            3'b000:  branch_taken_e =  cmp_eq  ; //beq
            3'b001:  branch_taken_e = ~cmp_eq  ; //bne
            3'b100:  branch_taken_e =  cmp_lts ; //blt
            3'b101:  branch_taken_e = ~cmp_lts ; //bge
            3'b110:  branch_taken_e =  cmp_ltu ; //bltu
            3'b111:  branch_taken_e = ~cmp_ltu ; //bgeu
            default: branch_taken_e = 0        ;
        endcase
    end
    else begin
        branch_taken_e = 0 ;
    end
end

// (R13a-3's simulation reference check lives in datapath.v, sampled on the clock edge.)

endmodule
