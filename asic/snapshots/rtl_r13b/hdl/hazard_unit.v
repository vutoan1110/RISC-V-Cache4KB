module hazard_unit 
(
    input      [4:0] rs1_d           ,
    input      [4:0] rs2_d           ,
    input            use_rs1_d       ,
    input            use_rs2_d       ,
    input      [4:0] rd_e            ,
    input      [1:0] result_src_e    ,
    input            mul_e           ,   // R13b
    input            pc_src_e        ,
    input            irq_flush       ,
    input            cache_stall     ,
    output           stall_f         ,
    output           stall_d         ,
    output           flush_d         ,
    output           flush_e         ,
    output           load_use_hazard
);

// R9 (NHAT_KY_RTL 2026-09-26): the EX forwarding selects are no longer
// decoded here in EX; datapath.v registers them one stage early.

assign load_use_hazard =
    ((result_src_e == 2'b01) || mul_e) &&   // R13b: load or multiply in E
    (rd_e != 5'd0) &&
    ((use_rs1_d && (rs1_d == rd_e)) ||
     (use_rs2_d && (rs2_d == rd_e)));

assign stall_f = load_use_hazard | cache_stall;
assign stall_d = load_use_hazard | cache_stall;

// flush_d: only on an older (EX/IRQ) redirect. A fetch-stage prediction must
// NOT flush Decode -- the branch/JAL is entering IF/ID and has to survive to
// update the BHT and to write its link register. That is why this unit is not
// given the fetch redirect at all.
assign flush_d = (pc_src_e | irq_flush) & ~cache_stall;

// flush_e: on load-use (bubble), EX redirect (mispredict/JALR/mret), or IRQ
assign flush_e = load_use_hazard | ((pc_src_e | irq_flush) & ~cache_stall);

endmodule
