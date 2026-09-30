`timescale 1ns/1ps
// ASIC-view checker, elaborated as a second top next to tb_benchmark_snapshot
// by tb/compile_asic_view.do and scripts/run_ablation.py --asic-view.
//
// The macro-backed memories had never been simulated before the ASIC-view
// runs, and the first run found the main-memory wrapper committing 91 of 115
// writes to the previous write's address. This fails the run the moment the
// wrapper commits a write to an address other than the one accepted on AW.
//
// X checks were tried and removed. regfile.v has no reset, so a function
// prologue that saves a never-written callee-saved register stores X to the
// stack and the epilogue loads it back. The FPGA view does exactly the same
// (depthconv: 14 X stores to the same stack addresses in both views, X in the
// L0 buffer in both, and both PASS with minstret 2131), so X on its own is not
// evidence of a memory fault. Correctness of the ASIC view is judged against
// the FPGA view instead: same minstret, same data-access counts, both
// self-checks passing.
module asic_view_checker;

`define SOC tb_benchmark_snapshot.dut
`define AR  tb_benchmark_snapshot.dut.u_axi_ram

integer    cyc = 0;
integer    writes = 0;
reg [31:0] last_aw_addr;

always @(posedge `SOC.clk) begin
    cyc <= cyc + 1;
    if (`AR.s_axi_awvalid && `AR.s_axi_awready)
        last_aw_addr <= `AR.s_axi_awaddr;
    if (`AR.wr_state == `AR.WR_COMMIT) begin
        writes = writes + 1;
        if ({`AR.wr_bank_r, `AR.wr_bank_off_r} !== last_aw_addr[12:2])
            $fatal(1, "ASIC_VIEW_CHECK cycle %0d: write accepted at %h committed to word %h",
                   cyc, last_aw_addr, {`AR.wr_bank_r, `AR.wr_bank_off_r});
    end
end

final $display("ASIC_VIEW_CHECK writes=%0d all at the accepted address", writes);

endmodule
