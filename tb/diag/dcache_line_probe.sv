`timescale 1ns/1ps
// ASIC view only: follows one D-cache line (+idx) in the SRAM-backed data
// array: every write into it, its stored words after each change, and every
// cycle the array is read at that index, with the rd_line the controller sees.
module dcache_line_probe;
`define DD tb_benchmark_snapshot.dut.u_dcache.g_dm_baseline
integer cyc = 0;
reg [7:0] idx;
initial if (!$value$plusargs("idx=%h", idx)) idx = 8'hC7;
wire [127:0] stored = {`DD.u_data_ram.u_ram.g_bank[3].u_bank.mem[idx],
                       `DD.u_data_ram.u_ram.g_bank[2].u_bank.mem[idx],
                       `DD.u_data_ram.u_ram.g_bank[1].u_bank.mem[idx],
                       `DD.u_data_ram.u_ram.g_bank[0].u_bank.mem[idx]};
reg [127:0] last_stored;
reg         rd_prev = 1'b0;
always @(posedge `DD.u_data_ram.clk) begin
    cyc <= cyc + 1;
    if (`DD.u_data_ram.wr_en && `DD.u_data_ram.wr_index == idx)
        $display("[LPROBE] c%0d write idx %h word %0d data %h (state %0d)", cyc, idx,
                 `DD.u_data_ram.wr_word, `DD.u_data_ram.wr_data, `DD.u_controller.state);
    if (stored !== last_stored)
        $display("[LPROBE] c%0d stored line now %h", cyc, stored);
    last_stored <= stored;
    if (rd_prev)
        $display("[LPROBE] c%0d   rd_line seen %h (state %0d)", cyc,
                 `DD.u_data_ram.rd_line, `DD.u_controller.state);
    rd_prev <= `DD.u_data_ram.rd_en && `DD.u_data_ram.rd_index == idx;
end
endmodule
