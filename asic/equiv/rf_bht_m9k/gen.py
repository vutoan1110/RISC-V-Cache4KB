"""Proof harness generator for the register file / BHT in M9K (review A1, 2026-10-08).

The FPGA versions (no `__openlane__`) must give the same read data as the previous arrays in every cycle when their
read-ahead inputs follow the datapath protocol (the next value of the register the module reads). Proved by
k-induction (`sat -tempinduct`) on two harnesses, each with the previous module (`*_old`, the ASIC branch of the same
file) and the new one side by side, the datapath registers modelled (async reset to 0, loaded from the read-ahead
input at every edge), and as invariants the array contents (valid entries) plus the outputs.

    python gen.py <file with the new hdl/ tree> <outdir> [--mutant]
A third harness checks the protocol itself on a copy of datapath.v (FPGA view): instr_d, pc_f and pc_e equal, one edge
later, the read-ahead values instr_d_next, pc_f_next and pc_e_next.
--mutant drops the write bypass of the register file, the valid check of the BHT fetch read and the flush of
instr_d_next (negative control: all three proofs must fail with a counterexample). Dropping stall_pipe from pc_f_next
is NOT a usable mutant: it proves, since stall_f already holds pc_f whenever stall_pipe is set.
"""
import os
import re
import sys

new_root, out = sys.argv[1], sys.argv[2]
mutant = "--mutant" in sys.argv
os.makedirs(out, exist_ok=True)


def rd(p):
    return open(os.path.join(new_root, p), newline="").read().replace("\r\n", "\n")


def drop_sim_only(s):
    return re.sub(r"// synthesis translate_off\n.*?// synthesis translate_on\n", "", s, flags=re.S)


def branch(s, asic):
    """Resolve `ifdef/`ifndef __openlane__ blocks for one side (no other macros in these files)."""
    out_lines, stack = [], []
    for ln in s.split("\n"):
        t = ln.strip()
        if t in ("`ifdef __openlane__", "`ifndef __openlane__"):
            want = asic if t.startswith("`ifdef") else not asic
            stack.append([want, want])
            continue
        if t == "`else" and stack:
            stack[-1][1] = not stack[-1][0]
            continue
        if t == "`endif" and stack:
            stack.pop()
            continue
        if all(on for _, on in stack):
            out_lines.append(ln)
    return "\n".join(out_lines)


rf = drop_sim_only(rd("hdl/regfile.v"))
bht = drop_sim_only(rd("hdl/predictor/bht_2bit.v"))

rf_old = branch(rf, True).replace("module regfile", "module regfile_old", 1)
rf_old = rf_old.replace("    output [31:0] rd2_d\n);", "    output [31:0] rd2_d\n    ,output [1023:0] fv_mem\n);", 1)
rf_old = rf_old.replace("\nendmodule", "\ngenvar fi;\ngenerate for (fi = 0; fi < 32; fi = fi + 1) begin : g_fv\n"
                        "    assign fv_mem[fi*32 +: 32] = (fi == 0) ? 32'd0 : regs[fi];\nend endgenerate\nendmodule", 1)
rf_new = branch(rf, False).replace("module regfile", "module regfile_new", 1)
rf_new = rf_new.replace("    output [31:0] rd2_d\n);", "    output [31:0] rd2_d\n    ,output [1023:0] fv_mem1\n    ,output [1023:0] fv_mem2\n);", 1)
rf_new = rf_new.replace("\nendmodule", "\ngenvar fi;\ngenerate for (fi = 0; fi < 32; fi = fi + 1) begin : g_fv\n"
                        "    assign fv_mem1[fi*32 +: 32] = (fi == 0) ? 32'd0 : mem1[fi];\n"
                        "    assign fv_mem2[fi*32 +: 32] = (fi == 0) ? 32'd0 : mem2[fi];\nend endgenerate\nendmodule", 1)
if mutant:
    a = "(wr_q && rd_q == rs1) ? wd_q : q1;"
    assert rf_new.count(a) == 1
    rf_new = rf_new.replace(a, "q1;  // MUTANT: no bypass of the write of the last edge")

bht_old = branch(bht, True).replace("module bht_2bit", "module bht_2bit_old", 1)
bht_new = branch(bht, False).replace("module bht_2bit", "module bht_2bit_new", 1)
for name, s in (("old", bht_old), ("new", bht_new)):
    assert "    input  wire                        actual_taken\n);" in s, name
bht_old = bht_old.replace("    input  wire                        actual_taken\n);",
                          "    input  wire                        actual_taken\n    ,output wire [511:0] fv_mem\n);", 1)
bht_old = bht_old.replace("\nendmodule", "\ngenvar fi;\ngenerate for (fi = 0; fi < BHT_ENTRIES; fi = fi + 1) begin : g_fv\n"
                          "    assign fv_mem[fi*2 +: 2] = bht_mem[fi];\nend endgenerate\nendmodule", 1)
bht_new = bht_new.replace("    input  wire                        actual_taken\n);",
                          "    input  wire                        actual_taken\n    ,output wire [511:0] fv_cf\n"
                          "    ,output wire [511:0] fv_cu\n    ,output wire [255:0] fv_valid\n);", 1)
bht_new = bht_new.replace("\nendmodule", "\ngenvar fi;\ngenerate for (fi = 0; fi < BHT_ENTRIES; fi = fi + 1) begin : g_fv\n"
                          "    assign fv_cf[fi*2 +: 2] = cnt_f[fi];\n    assign fv_cu[fi*2 +: 2] = cnt_u[fi];\nend endgenerate\n"
                          "assign fv_valid = valid;\nendmodule", 1)
if mutant:
    a = "assign fetch_state = !valid[fetch_index] ? BHT_RESET_STATE :"
    assert bht_new.count(a) == 1
    bht_new = bht_new.replace(a, "assign fetch_state = 1'b0 ? BHT_RESET_STATE :  // MUTANT: valid bit ignored\n")

# Protocol: in the datapath (FPGA view), the read-ahead addresses are the values instr_d, pc_f and pc_e take at the
# next edge. Checked on a copy of datapath.v with the assertions appended.
dp = drop_sim_only(rd("hdl/datapath.v"))
if mutant:
    a = "wire [31:0] instr_d_next = stall_pipe ? instr_d : flush_d ? 32'h0000_0000 : stall_d ? instr_d : instr;"
    assert dp.count(a) == 1
    dp = dp.replace(a, "wire [31:0] instr_d_next = stall_pipe ? instr_d : stall_d ? instr_d : instr;  // MUTANT: flush_d dropped")
k = dp.rstrip().rfind("endmodule")
dp = dp[:k] + """// formal: protocol of the read-ahead addresses
reg        fv_past_ok;
reg [31:0] fv_instr_d_next_q, fv_pc_f_next_q, fv_pc_e_next_q;
always @(posedge clk or negedge reset_n)
    if (!reset_n) fv_past_ok <= 1'b0;
    else begin
        fv_past_ok        <= 1'b1;
        fv_instr_d_next_q <= instr_d_next;
        fv_pc_f_next_q    <= pc_f_next;
        fv_pc_e_next_q    <= pc_e_next;
    end
always @* if (reset_n && fv_past_ok) begin
    assert (instr_d == fv_instr_d_next_q);
    assert (pc_f == fv_pc_f_next_q);
    assert (pc_e == fv_pc_e_next_q);
end
""" + dp[k:]
open(os.path.join(out, "datapath_fv.v"), "w", newline="\n").write(dp)

open(os.path.join(out, "rf_old.v"), "w", newline="\n").write(rf_old)
open(os.path.join(out, "rf_new.v"), "w", newline="\n").write(rf_new)
open(os.path.join(out, "bht_old.v"), "w", newline="\n").write(bht_old)
open(os.path.join(out, "bht_new.v"), "w", newline="\n").write(bht_new)

open(os.path.join(out, "fv_rf.sv"), "w", newline="\n").write("""module fv_rf(input clk, input reset_n, input we, input [4:0] rd, input [31:0] wd,
             input [4:0] a1_next, input [4:0] a2_next);
    // datapath model: instr_d (rs fields) loads the read-ahead value at every edge, async reset to 0
    reg [4:0] rs1, rs2;
    always @(posedge clk or negedge reset_n)
        if (!reset_n) begin rs1 <= 5'd0; rs2 <= 5'd0; end
        else begin rs1 <= a1_next; rs2 <= a2_next; end
    wire [31:0] o1, o2, n1, n2;
    wire [1023:0] m_old, m1, m2;
    regfile_old u_old(.clk(clk), .we(we), .rs1(rs1), .rs2(rs2), .rd(rd), .wd(wd), .rd1_d(o1), .rd2_d(o2), .fv_mem(m_old));
    regfile_new u_new(.clk(clk), .we(we), .rs1(rs1), .rs2(rs2), .rd(rd), .wd(wd), .rs1_next(a1_next), .rs2_next(a2_next),
                      .rd1_d(n1), .rd2_d(n2), .fv_mem1(m1), .fv_mem2(m2));
    always @* begin
        assert (m1 == m_old);
        assert (m2 == m_old);
        if (reset_n) begin
            assert (n1 == o1);
            assert (n2 == o2);
        end
    end
endmodule
""")
open(os.path.join(out, "fv_bht.sv"), "w", newline="\n").write("""module fv_bht(input clk, input reset_n, input [31:0] fpc_next, input [31:0] upc_next,
              input update_en, input actual_taken);
    // datapath model: pc_f / pc_e load the read-ahead value at every edge, async reset to 0
    reg [31:0] fpc, upc;
    always @(posedge clk or negedge reset_n)
        if (!reset_n) begin fpc <= 32'd0; upc <= 32'd0; end
        else begin fpc <= fpc_next; upc <= upc_next; end
    wire [7:0] fi_o, fi_n;
    wire [1:0] fs_o, fs_n;
    wire pt_o, pt_n;
    wire [511:0] m_old, cf, cu;
    wire [255:0] valid;
    bht_2bit_old u_old(.clk(clk), .reset_n(reset_n), .fetch_pc(fpc), .fetch_index(fi_o), .fetch_state(fs_o),
                       .predict_taken(pt_o), .update_en(update_en), .update_pc(upc), .actual_taken(actual_taken),
                       .fv_mem(m_old));
    bht_2bit_new u_new(.clk(clk), .reset_n(reset_n), .fetch_pc(fpc), .fetch_pc_next(fpc_next), .update_pc_next(upc_next),
                       .fetch_index(fi_n), .fetch_state(fs_n), .predict_taken(pt_n), .update_en(update_en),
                       .update_pc(upc), .actual_taken(actual_taken), .fv_cf(cf), .fv_cu(cu), .fv_valid(valid));
    genvar i;
    generate for (i = 0; i < 256; i = i + 1) begin : g_inv
        always @* begin
            if (reset_n) begin
                assert (valid[i] ? (cf[i*2 +: 2] == m_old[i*2 +: 2] && cu[i*2 +: 2] == m_old[i*2 +: 2])
                                 : (m_old[i*2 +: 2] == 2'b01));
            end
        end
    end endgenerate
    always @* begin
        if (reset_n) begin
            assert (fi_n == fi_o);
            assert (fs_n == fs_o);
            assert (pt_n == pt_o);
        end
    end
endmodule
""")
print("written", out, "mutant" if mutant else "real")
