"""R12 proof harness generator (NHAT_KY_RTL 2026-09-26).

R12 replaces two one-hot AND-OR selects with muxes on the encoded registers
they copy. It is correct iff, in every reachable state of the core,
    A1  rsel_w    == 4'b0001 << result_src_w
    A2  ld_lane_w == 4'b0001 << load_byte_offset_w
This proves both by k-induction on the PRE-R12 RTL at riscv_core level (the
controller owns result_src_w, the datapath owns rsel_w). The live RTL is copied,
not edited: modules are renamed and only gain fv_* output ports that expose
existing signals. --mutant breaks rsel_w's update (negative control).

    python gen.py <research root> <outdir> [--mutant]
"""
import os
import re
import sys

root, out = sys.argv[1], sys.argv[2]
mutant = "--mutant" in sys.argv
os.makedirs(out, exist_ok=True)


def rd(p):
    return open(os.path.join(root, p), newline="").read().replace("\r\n", "\n")


def drop_sim_only(s):
    return re.sub(r"`ifndef __openlane__\n// synthesis translate_off\n.*?// synthesis translate_on\n`endif\n",
                  "", s, flags=re.S)


# datapath copy
d = drop_sim_only(rd("hdl/datapath.v"))
assert d.count("module datapath #(") == 1
d = d.replace("module datapath #(", "module datapath_fv #(")
i = d.index("module datapath_fv #(")
j = d.index("\n);", i)   # first ");" after the header ends the port list
d = d[:j] + ("\n    ,output wire [3:0] fv_rsel_w\n    ,output wire [3:0] fv_ld_lane_w\n"
             "    ,output wire [1:0] fv_lbo_w") + d[j:]
e = d.rindex("endmodule")
d = d[:e] + ("assign fv_rsel_w = rsel_w;\nassign fv_ld_lane_w = ld_lane_w;\n"
             "assign fv_lbo_w = load_byte_offset_w;\n") + d[e:]
if mutant:
    old = "        rsel_w    <= {result_src_m == 2'b11, result_src_m == 2'b10,\n"
    assert d.count(old) == 1
    d = d.replace(old, "        rsel_w    <= {result_src_m == 2'b11, result_src_m == 2'b11,  // MUTANT\n")
open(os.path.join(out, "datapath_fv.v"), "w", newline="\n").write(d)

# riscv_core copy
c = rd("hdl/riscv_core.v")
assert c.count("module riscv_core #(") == 1 and c.count("\ndatapath #(") == 1
c = c.replace("module riscv_core #(", "module riscv_core_fv #(").replace("\ndatapath #(", "\ndatapath_fv #(")
i = c.index("module riscv_core_fv #(")
j = c.index("\n);", i)
c = c[:j] + ("\n    ,output wire [3:0] fv_rsel_w\n    ,output wire [3:0] fv_ld_lane_w\n"
             "    ,output wire [1:0] fv_lbo_w\n    ,output wire [1:0] fv_result_src_w") + c[j:]
k = c.index("\ndatapath_fv #(")
m = c.index("\n);", k)
c = c[:m] + ("\n    ,.fv_rsel_w(fv_rsel_w), .fv_ld_lane_w(fv_ld_lane_w), .fv_lbo_w(fv_lbo_w)") + c[m:]
e = c.rindex("endmodule")
c = c[:e] + "assign fv_result_src_w = result_src_w;\n" + c[e:]
open(os.path.join(out, "riscv_core_fv.v"), "w", newline="\n").write(c)

top = """// R12 proof harness (generated): riscv_core with every input free.
module fv_top(
    input wire clk, input wire reset_n, input wire irq_timer,
    input wire [31:0] instr, input wire [31:0] rd_data, input wire stall_pipe
);
wire [3:0] rsel_w, ld_lane_w; wire [1:0] lbo_w, result_src_w;
riscv_core_fv u_core(
    .clk(clk), .reset_n(reset_n), .irq_timer(irq_timer), .instr(instr),
    .rd_data(rd_data), .stall_pipe(stall_pipe),
    .fv_rsel_w(rsel_w), .fv_ld_lane_w(ld_lane_w), .fv_lbo_w(lbo_w), .fv_result_src_w(result_src_w));
always @(*) begin
    if(reset_n) begin
        assert(rsel_w    == (4'b0001 << result_src_w));   // A1
        assert(ld_lane_w == (4'b0001 << lbo_w));          // A2
    end
end
endmodule
"""
open(os.path.join(out, "fv_top.sv"), "w", newline="\n").write(top)
print("[OK] harness in", out, "(mutant)" if mutant else "")
