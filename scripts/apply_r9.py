#!/usr/bin/env python3
"""R9 (NHAT_KY.md 2026-09-26): cycle-exact timing restructuring for the ss corner.

    python scripts/apply_r9.py          # apply (fails if any anchor is missing)

Every change moves a decode that sat on a critical path one pipeline stage
earlier and registers it with EXACTLY the enable, flush and reset of the
registers it is decoded from, so its value equals the old combinational one
in every cycle (argued per item below, checked every simulated cycle by the
equivalence checker added to datapath.v, and by the full chain: Embench,
CoreMark and random-diff must stay byte-identical, i.e. CPI unchanged).

R9a  forward_a_e / forward_b_e (was: hazard_unit, combinational in EX from
     instr_e[19:15], instr_m[11:7], reg_wr_m, instr_w[11:7], reg_wr_w).
     On every edge with !stall_pipe: instr_e <= flush_e ? 0 : instr_d,
     instr_m <= instr_e, reg_wr_m <= reg_wr_e, instr_w <= instr_m,
     reg_wr_w <= reg_wr_m (all reset to 0). So the next value of the old
     function is flush_e ? 00 : f(instr_d[19:15], instr_e[11:7], reg_wr_e,
     instr_m[11:7], reg_wr_m) -- registered under !stall_pipe, reset 00.
R9b  W stage: rd_data_final decoded valid_w, instr_w[6:0], instr_w[14:12];
     result_w decoded result_src_w. Now one-hot kinds registered at M->W
     from valid_m/instr_m and result_src_m (instr_w <= instr_m,
     valid_w <= valid_m, result_src_w <= result_src_m, all !stall_pipe).
R9c  M stage: is_upper_m / is_link_m decoded valid_m && instr_m opcode; now
     registered at E->M from valid_e/instr_e (instr_m <= instr_e,
     valid_m <= valid_e under !stall_pipe).
"""
import re
import sys

def edit(path, pairs):
    # Some sources are CRLF (hazard_unit.v) or mixed (riscv_core.v). Each
    # anchor is tried as written (LF) and with CRLF; exactly one variant must
    # match exactly once, and the replacement keeps that variant's line ends.
    s = open(path, newline="").read()
    for old, new in pairs:
        hits = [(o, n) for o, n in ((old, new), (old.replace("\n", "\r\n"), new.replace("\n", "\r\n")))
                if s.count(o) == 1]
        if len(hits) != 1 or (old.replace("\n", "\r\n") == old and s.count(old) != 1):
            sys.exit("[FAIL] %s: anchor LF x%d / CRLF x%d:\n%s" % (
                path, s.count(old), s.count(old.replace("\n", "\r\n")), old[:200]))
        s = s.replace(*hits[0])
    open(path, "w", newline="").write(s)
    print("[OK] %s: %d edit(s)" % (path, len(pairs)))

# ---------------------------------------------------------------- controller
edit("hdl/controller.v", [
    ("    output reg       reg_wr_m        ,\n",
     "    output reg       reg_wr_e        ,  // R9: datapath registers the forward selects\n"
     "    output reg       reg_wr_m        ,\n"),
    ("    output reg [1:0] result_src_w    ,\n",
     "    output reg [1:0] result_src_m    ,  // R9: datapath registers the W result select\n"
     "    output reg [1:0] result_src_w    ,\n"),
])
# the internal declarations of the two regs go: they are ports now
edit("hdl/controller.v", [
    ("reg        reg_wr_e     ;\n", ""),
    ("reg [1:0] result_src_m ;\n", ""),
])

# ---------------------------------------------------------------- hazard unit
edit("hdl/hazard_unit.v", [
    ("    input      [4:0] rs1_e           ,\n"
     "    input      [4:0] rs2_e           ,\n"
     "    input      [4:0] rd_m            ,\n"
     "    input      [4:0] rd_w            ,\n", ""),
    ("    input            reg_wr_m        ,\n"
     "    input            reg_wr_w        ,\n", ""),
    ("    output reg [1:0] forward_a_e     ,\n"
     "    output reg [1:0] forward_b_e     ,\n", ""),
    ("always @(*) begin\n"
     "    if(((rs1_e == rd_m) && reg_wr_m) && (rs1_e != 0))      forward_a_e = 2'b10 ;\n"
     "    else if(((rs1_e == rd_w) && reg_wr_w) && (rs1_e != 0)) forward_a_e = 2'b01 ;\n"
     "    else                                                   forward_a_e = 2'b00 ;\n"
     "end\n\n"
     "always @(*) begin\n"
     "    if(((rs2_e == rd_m) && reg_wr_m) && (rs2_e != 0))      forward_b_e = 2'b10 ;\n"
     "    else if(((rs2_e == rd_w) && reg_wr_w) && (rs2_e != 0)) forward_b_e = 2'b01 ;\n"
     "    else                                                   forward_b_e = 2'b00 ;\n"
     "end\n",
     "// R9 (NHAT_KY.md 2026-09-26): the EX forwarding selects are no longer\n"
     "// decoded here in EX; datapath.v registers them one stage early.\n"),
])

# ---------------------------------------------------------------- riscv_core
edit("hdl/riscv_core.v", [
    ("wire        reg_wr_m;\n",
     "wire        reg_wr_m;\nwire        reg_wr_e;       // R9\nwire [1:0]  result_src_m;   // R9\n"),
    # controller instance
    ("    .reg_wr_m     (reg_wr_m),\n",
     "    .reg_wr_e     (reg_wr_e),\n    .reg_wr_m     (reg_wr_m),\n"),
    ("    .result_src_w (result_src_w),\n",
     "    .result_src_m (result_src_m),\n    .result_src_w (result_src_w),\n"),
    # datapath instance
    ("    .reg_wr_m         (reg_wr_m),\n",
     "    .reg_wr_e         (reg_wr_e),\n    .reg_wr_m         (reg_wr_m),\n"),
    ("    .result_src_w     (result_src_w),\n",
     "    .result_src_m     (result_src_m),\n    .result_src_w     (result_src_w),\n"),
])

# ---------------------------------------------------------------- datapath
edit("hdl/datapath.v", [
    # ports
    ("    input      [1:0]  result_src_w    ,\n",
     "    input      [1:0]  result_src_m    ,  // R9b\n    input      [1:0]  result_src_w    ,\n"),
    ("    input             reg_wr_m        ,\n",
     "    input             reg_wr_e        ,  // R9a\n    input             reg_wr_m        ,\n"),
    # R9a: forward selects become registers (names kept: testbenches probe them)
    ("wire [1:0]  forward_a_e;\nwire [1:0]  forward_b_e;\n",
     "reg  [1:0]  forward_a_e;   // R9a: registered, see below\nreg  [1:0]  forward_b_e;\n"),
    # hazard unit loses its forwarding ports
    ("    .rs1_e           (instr_e[19:15])  ,\n"
     "    .rs2_e           (instr_e[24:20])  ,\n"
     "    .rd_m            (instr_m[11:7])   ,\n"
     "    .rd_w            (instr_w[11:7])   ,\n", ""),
    ("    .reg_wr_m        (reg_wr_m)        ,\n"
     "    .reg_wr_w        (reg_wr_w)        ,\n", ""),
    ("    .forward_a_e     (forward_a_e)     ,\n"
     "    .forward_b_e     (forward_b_e)     ,\n", ""),
    # R9c: M-stage decodes registered at E->M
    ("wire        is_upper_m;\nwire        is_link_m;\n",
     "reg         is_upper_m;    // R9c: registered at E->M, see below\nreg         is_link_m;\n"),
    ("assign is_upper_m = valid_m && ((instr_m[6:0] == 7'b0110111) ||\n"
     "                                  (instr_m[6:0] == 7'b0010111));\n"
     "assign is_link_m  = valid_m && ((instr_m[6:0] == 7'b1101111) ||\n"
     "                                 (instr_m[6:0] == 7'b1100111));\n",
     "// R9_BLOCK\n"),
    # R9b: W-stage result and load extraction from registered one-hot selects
    ("assign result_w = (result_src_w == 2'b11) ? upper_w       :\n"
     "                  (result_src_w == 2'b10) ? pc_plus4_w    :\n"
     "                  (result_src_w == 2'b01) ? rd_data_final :\n"
     "                                            alu_result_w  ;\n",
     "// R9b: one-hot result select registered at M->W (was decoded from result_src_w)\n"
     "assign result_w = ({32{rsel_w[3]}} & upper_w)       |\n"
     "                  ({32{rsel_w[2]}} & pc_plus4_w)    |\n"
     "                  ({32{rsel_w[1]}} & rd_data_final) |\n"
     "                  ({32{rsel_w[0]}} & alu_result_w)  ;\n"),
])
R9_BLOCK = r"""// ---------------------------------------------------------------------------
// R9 (NHAT_KY.md 2026-09-26): decodes moved off the ss-critical paths.
// Each register below is loaded under exactly the enable (!stall_pipe), flush
// and reset of the registers it replaces the decode of, so it holds the same
// value as the old combinational decode in every cycle; the simulation-only
// checker at the end of this block compares them every cycle.

// R9a -- EX forwarding selects. At an edge with !stall_pipe the pipeline does
// instr_e <= flush_e ? 0 : instr_d, instr_m <= instr_e, reg_wr_m <= reg_wr_e,
// instr_w <= instr_m, reg_wr_w <= reg_wr_m, so the old select of the next
// cycle is flush_e ? 00 : f(instr_d rs, instr_e rd, reg_wr_e, instr_m rd,
// reg_wr_m). A flushed E slot has rs = 0, which never forwards.
wire [4:0] r9_rs1_d = instr_d[19:15];
wire [4:0] r9_rs2_d = instr_d[24:20];
wire [1:0] fwd_a_next = ((r9_rs1_d == instr_e[11:7]) && reg_wr_e && (r9_rs1_d != 5'd0)) ? 2'b10 :
                        ((r9_rs1_d == instr_m[11:7]) && reg_wr_m && (r9_rs1_d != 5'd0)) ? 2'b01 :
                                                                                         2'b00;
wire [1:0] fwd_b_next = ((r9_rs2_d == instr_e[11:7]) && reg_wr_e && (r9_rs2_d != 5'd0)) ? 2'b10 :
                        ((r9_rs2_d == instr_m[11:7]) && reg_wr_m && (r9_rs2_d != 5'd0)) ? 2'b01 :
                                                                                         2'b00;
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        forward_a_e <= 2'b00;
        forward_b_e <= 2'b00;
    end
    else if(!stall_pipe) begin
        forward_a_e <= flush_e ? 2'b00 : fwd_a_next;
        forward_b_e <= flush_e ? 2'b00 : fwd_b_next;
    end
end

// R9c -- M-stage result kind (instr_m <= instr_e, valid_m <= valid_e).
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        is_upper_m <= 1'b0;
        is_link_m  <= 1'b0;
    end
    else if(!stall_pipe) begin
        is_upper_m <= valid_e && ((instr_e[6:0] == 7'b0110111) ||
                                  (instr_e[6:0] == 7'b0010111));
        is_link_m  <= valid_e && ((instr_e[6:0] == 7'b1101111) ||
                                  (instr_e[6:0] == 7'b1100111));
    end
end

// R9b -- W-stage selects (instr_w <= instr_m, valid_w <= valid_m,
// load_byte_offset_w <= mem_byte_offset_m, result_src_w <= result_src_m).
// ld_kind_w one-hot {LHU, LBU, LH, LB}; all zero for LW, any other funct3 and
// any non-load, which all pass rd_data_w through unchanged.
reg  [3:0]  ld_kind_w;
reg  [3:0]  ld_lane_w;        // one-hot byte offset, reset = lane 0
reg  [3:0]  rsel_w;           // one-hot {upper, pc+4, load, alu}, reset = alu
wire        r9_is_load_m = valid_m && (instr_m[6:0] == 7'b0000011);
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        ld_kind_w <= 4'b0000;
        ld_lane_w <= 4'b0001;
        rsel_w    <= 4'b0001;
    end
    else if(!stall_pipe) begin
        ld_kind_w <= {r9_is_load_m && (instr_m[14:12] == 3'b101),
                      r9_is_load_m && (instr_m[14:12] == 3'b100),
                      r9_is_load_m && (instr_m[14:12] == 3'b001),
                      r9_is_load_m && (instr_m[14:12] == 3'b000)};
        ld_lane_w <= 4'b0001 << mem_byte_offset_m;
        rsel_w    <= {result_src_m == 2'b11, result_src_m == 2'b10,
                      result_src_m == 2'b01, result_src_m == 2'b00};
    end
end
"""

LOAD_NEW = r"""always @(*) begin
    // R9b: byte lane and load kind come from registered one-hot selects
    load_byte = ({8{ld_lane_w[0]}} & rd_data_w[7:0])   |
                ({8{ld_lane_w[1]}} & rd_data_w[15:8])  |
                ({8{ld_lane_w[2]}} & rd_data_w[23:16]) |
                ({8{ld_lane_w[3]}} & rd_data_w[31:24]);

    if(load_byte_offset_w[1] == 1'b0)
        load_half = rd_data_w[15:0];
    else
        load_half = rd_data_w[31:16];

    rd_data_final = ld_kind_w[0] ? {{24{load_byte[7]}},  load_byte} : // LB
                    ld_kind_w[1] ? {{16{load_half[15]}}, load_half} : // LH
                    ld_kind_w[2] ? {24'b0, load_byte}               : // LBU
                    ld_kind_w[3] ? {16'b0, load_half}               : // LHU
                                   rd_data_w;                         // LW / other / not a load
end
"""

CHECKER = r"""
// R9 equivalence checker -- simulation only (hidden from Quartus by
// translate_off and from every OpenLane tool, lint included, by __openlane__).
// Recomputes each decode exactly as the RTL did before R9 and stops the
// simulation on the first cycle where a registered select differs.
`ifndef __openlane__
// synthesis translate_off
reg  [1:0]  r9_ref_fwd_a, r9_ref_fwd_b;
reg  [7:0]  r9_ref_byte;
reg  [15:0] r9_ref_half;
reg  [31:0] r9_ref_rd_data_final;
reg  [31:0] r9_ref_result_w;
reg         r9_ref_is_upper_m, r9_ref_is_link_m;
always @(*) begin
    if((instr_e[19:15] == instr_m[11:7]) && reg_wr_m && (instr_e[19:15] != 0))      r9_ref_fwd_a = 2'b10;
    else if((instr_e[19:15] == instr_w[11:7]) && reg_wr_w && (instr_e[19:15] != 0)) r9_ref_fwd_a = 2'b01;
    else                                                                             r9_ref_fwd_a = 2'b00;
    if((instr_e[24:20] == instr_m[11:7]) && reg_wr_m && (instr_e[24:20] != 0))      r9_ref_fwd_b = 2'b10;
    else if((instr_e[24:20] == instr_w[11:7]) && reg_wr_w && (instr_e[24:20] != 0)) r9_ref_fwd_b = 2'b01;
    else                                                                             r9_ref_fwd_b = 2'b00;

    r9_ref_is_upper_m = valid_m && ((instr_m[6:0] == 7'b0110111) || (instr_m[6:0] == 7'b0010111));
    r9_ref_is_link_m  = valid_m && ((instr_m[6:0] == 7'b1101111) || (instr_m[6:0] == 7'b1100111));

    case(load_byte_offset_w)
        2'b00: r9_ref_byte = rd_data_w[7:0];
        2'b01: r9_ref_byte = rd_data_w[15:8];
        2'b10: r9_ref_byte = rd_data_w[23:16];
        default: r9_ref_byte = rd_data_w[31:24];
    endcase
    r9_ref_half = load_byte_offset_w[1] ? rd_data_w[31:16] : rd_data_w[15:0];
    if(valid_w && (instr_w[6:0] == 7'b0000011)) begin
        case(instr_w[14:12])
            3'b000:  r9_ref_rd_data_final = {{24{r9_ref_byte[7]}}, r9_ref_byte};
            3'b001:  r9_ref_rd_data_final = {{16{r9_ref_half[15]}}, r9_ref_half};
            3'b100:  r9_ref_rd_data_final = {24'b0, r9_ref_byte};
            3'b101:  r9_ref_rd_data_final = {16'b0, r9_ref_half};
            default: r9_ref_rd_data_final = rd_data_w;
        endcase
    end
    else
        r9_ref_rd_data_final = rd_data_w;
    r9_ref_result_w = (result_src_w == 2'b11) ? upper_w              :
                      (result_src_w == 2'b10) ? pc_plus4_w           :
                      (result_src_w == 2'b01) ? r9_ref_rd_data_final :
                                                alu_result_w;
end
always @(posedge clk) begin
    if(reset_n && ((forward_a_e !== r9_ref_fwd_a) || (forward_b_e !== r9_ref_fwd_b) ||
                   (is_upper_m !== r9_ref_is_upper_m) || (is_link_m !== r9_ref_is_link_m) ||
                   (rd_data_final !== r9_ref_rd_data_final) || (result_w !== r9_ref_result_w)))
        $fatal(1, "R9 equivalence broken at %0t: fwd_a %b/%b fwd_b %b/%b upper %b/%b link %b/%b rd_final %h/%h result_w %h/%h",
               $time, forward_a_e, r9_ref_fwd_a, forward_b_e, r9_ref_fwd_b, is_upper_m, r9_ref_is_upper_m,
               is_link_m, r9_ref_is_link_m, rd_data_final, r9_ref_rd_data_final, result_w, r9_ref_result_w);
end
// synthesis translate_on
`endif
"""

s = open("hdl/datapath.v", newline="").read()
if s.count("// R9_BLOCK\n") != 1:
    sys.exit("[FAIL] R9 block placeholder")
s = s.replace("// R9_BLOCK\n", R9_BLOCK)
m = re.search(r"always @\(\*\) begin\n    case\(load_byte_offset_w\).*?\nend\n(?=// --- CSR registers ---)", s, re.S)
if not m or s.count("case(load_byte_offset_w)") != 1:
    sys.exit("[FAIL] old load extraction block not found exactly once")
s = s[:m.start()] + LOAD_NEW + s[m.end():]
end = s.rindex("endmodule")
s = s[:end] + CHECKER.lstrip("\n") + "\n" + s[end:]
open("hdl/datapath.v", "w", newline="").write(s)
print("[OK] hdl/datapath.v: R9 block, load extraction, checker")
