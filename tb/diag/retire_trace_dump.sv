`timescale 1ns/1ps
// Writes the architectural retirement stream (order, pc, instr, rd, wdata) of
// tb_benchmark_snapshot to a file named by +trace_file, so two builds of the
// same program -- e.g. the FPGA view and the ASIC view -- can be diffed to the
// first retired instruction on which they disagree. Diagnostic only.
module retire_trace_dump;
`define RSOC tb_benchmark_snapshot.dut
integer fd = 0;
string  fname;
initial begin
    if (!$value$plusargs("trace_file=%s", fname)) fname = "retire_trace.txt";
    fd = $fopen(fname, "w");
end
always @(posedge `RSOC.clk)
    if (fd != 0 && `RSOC.retire_valid)
        $fwrite(fd, "%0d %h %h %0d %h %h\n", `RSOC.retire_order, `RSOC.retire_pc,
                `RSOC.retire_instr, `RSOC.retire_rd_addr, `RSOC.retire_rd_wdata, `RSOC.retire_rs1_rdata);
final if (fd != 0) $fclose(fd);
endmodule
