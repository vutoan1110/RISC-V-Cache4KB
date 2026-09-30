`timescale 1ns/1ps
// ASIC view only: follows one word of the macro-backed main memory (+word
// index): every write committed to it, its stored value after each change,
// and every read beat that returns it. Diagnostic only.
module ram_word_probe;
`define RW tb_benchmark_snapshot.dut.u_axi_ram
integer cyc = 0;
reg [10:0] w;
reg [31:0] last_mem;
initial if (!$value$plusargs("word=%d", w)) w = 797;
wire [31:0] mem_now = (w[10:9] == 2'd0) ? `RW.g_bank[0].u_bank.mem[w[8:0]] :
                      (w[10:9] == 2'd1) ? `RW.g_bank[1].u_bank.mem[w[8:0]] :
                      (w[10:9] == 2'd2) ? `RW.g_bank[2].u_bank.mem[w[8:0]] :
                                          `RW.g_bank[3].u_bank.mem[w[8:0]];
always @(posedge `RW.clk) begin
    cyc <= cyc + 1;
    if (`RW.wr_state == `RW.WR_COMMIT && {`RW.wr_bank_r, `RW.wr_bank_off_r} == w)
        $display("[WPROBE] c%0d commit write word %0d data=%h strb=%b", cyc, w,
                 `RW.wr_data_r, `RW.wr_strb_r);
    if (mem_now !== last_mem)
        $display("[WPROBE] c%0d stored value now %h", cyc, mem_now);
    last_mem <= mem_now;
    if (`RW.s_axi_rvalid && `RW.s_axi_rready && {`RW.rd_bank_q, `RW.rd_bank_addr_q} == w)
        $display("[WPROBE] c%0d read beat of word %0d returns %h (beat %0d)", cyc, w,
                 `RW.s_axi_rdata, `RW.rd_beat_q);
end
endmodule
