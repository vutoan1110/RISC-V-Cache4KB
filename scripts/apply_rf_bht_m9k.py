#!/usr/bin/env python3
"""Register file and branch history table into M9K on the FPGA (review item A1, 2026-10-08).

FPGA only: every change is under `ifndef __openlane__`; the code the ASIC flow reads (`__openlane__` defined) keeps its
tokens, so the ASIC netlist is checked to stay byte-identical. Cycle-exact by construction:

  regfile    two simple-dual-port copies (one per read port). The read address registered at an edge is the rs field
             instr_d takes at that edge (the D input of instr_d), so the data of the instruction in decode is ready in
             decode as with the asynchronous array. The RAM returns the contents before the write of that edge (old
             data); that write is bypassed from registered copies of we / rd / wd, and the write of the current cycle is
             bypassed as before (write-through). x0 reads 0.
  bht_2bit   counters in two copies (fetch read, update read) addressed by the D inputs of pc_f and pc_e. A valid bit
             per entry, in flip-flops with the asynchronous reset, keeps "reset returns every entry to
             BHT_RESET_STATE": an entry not written since reset reads BHT_RESET_STATE. The update of the last edge is
             bypassed to both reads.

A simulation-only checker (translate_off) keeps the old arrays beside the new ones and stops the simulation on the
first cycle in which an output differs.

    python scripts/apply_rf_bht_m9k.py <research root>          # e.g. a copy first (dry run), then the live tree
"""
import hashlib
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")


def rd(p):
    return (root / p).read_text(encoding="utf-8").replace("\r\n", "\n")


def wr(p, s):
    (root / p).write_text(s, encoding="utf-8", newline="\n")


# ---------------------------------------------------------------- regfile.v
old_rf = rd("hdl/regfile.v")
assert old_rf.count("module regfile") == 1 and "regs[rs1]" in old_rf and "rs1_next" not in old_rf, "regfile.v is not the expected version"
new_rf = """module regfile
(
    input         clk   ,
    input         we    ,
    input  [4:0]  rs1   ,
    input  [4:0]  rs2   ,
    input  [4:0]  rd    ,
    input  [31:0] wd    ,
`ifndef __openlane__
    input  [4:0]  rs1_next ,   // FPGA: the rs1 / rs2 fields instr_d takes at the next edge (read-ahead address)
    input  [4:0]  rs2_next ,
`endif
    output [31:0] rd1_d ,
    output [31:0] rd2_d
);

`ifdef __openlane__
reg [31:0] regs [31:0];

always @(posedge clk) begin
    if (we && (rd != 5'd0)) begin
        regs[rd] <= wd ;
    end
    else begin
        regs[rd] <= regs[rd] ;
    end
end

assign rd1_d = (rs1 == 5'd0) ? 32'd0 : (we && rd == rs1) ? wd : regs[rs1];
assign rd2_d = (rs2 == 5'd0) ? 32'd0 : (we && rd == rs2) ? wd : regs[rs2];
`else
// FPGA (2026-10-08, review A1): two M9K copies with a synchronous read instead of 1,024 flip-flops. q* = contents
// before the write of the edge that loaded the address (old data); that write is bypassed from *_q; the write of the
// current cycle is bypassed as in the asynchronous version. Same value as the asynchronous array in every cycle.
(* ramstyle = "M9K" *) reg [31:0] mem1 [0:31];
(* ramstyle = "M9K" *) reg [31:0] mem2 [0:31];
reg  [31:0] q1, q2;
reg         wr_q;
reg  [4:0]  rd_q;
reg  [31:0] wd_q;
wire        wr = we && (rd != 5'd0);

always @(posedge clk) begin
    if (wr) begin
        mem1[rd] <= wd;
        mem2[rd] <= wd;
    end
    q1   <= mem1[rs1_next];
    q2   <= mem2[rs2_next];
    wr_q <= wr;
    rd_q <= rd;
    wd_q <= wd;
end

assign rd1_d = (rs1 == 5'd0) ? 32'd0 : (we && rd == rs1) ? wd : (wr_q && rd_q == rs1) ? wd_q : q1;
assign rd2_d = (rs2 == 5'd0) ? 32'd0 : (we && rd == rs2) ? wd : (wr_q && rd_q == rs2) ? wd_q : q2;

// synthesis translate_off
// Checker: the old asynchronous array beside the new one; any difference of a read stops the simulation.
reg [31:0] ref_regs [31:0];
always @(posedge clk)
    if (we && (rd != 5'd0)) ref_regs[rd] <= wd;
wire [31:0] ref_rd1 = (rs1 == 5'd0) ? 32'd0 : (we && rd == rs1) ? wd : ref_regs[rs1];
wire [31:0] ref_rd2 = (rs2 == 5'd0) ? 32'd0 : (we && rd == rs2) ? wd : ref_regs[rs2];
always @(negedge clk) begin
    if ((rd1_d !== ref_rd1 && ref_rd1 !== 32'bx) || (rd2_d !== ref_rd2 && ref_rd2 !== 32'bx))
        $fatal(1, "regfile M9K checker: rd1 %h / %h, rd2 %h / %h (rs1 %0d rs2 %0d) at %0t",
               rd1_d, ref_rd1, rd2_d, ref_rd2, rs1, rs2, $time);
end
// synthesis translate_on
`endif

endmodule
"""
# ---------------------------------------------------------------- bht_2bit.v
old_bht = rd("hdl/predictor/bht_2bit.v")
anchor_ports = "    input  wire                        clk,\n    input  wire                        reset_n,\n    input  wire [31:0]                 fetch_pc,\n"
anchor_mem = "wire [BHT_INDEX_BITS-1:0] update_index;\nreg  [1:0] bht_mem [0:BHT_ENTRIES-1];\n"
anchor_read = "assign fetch_state  = bht_mem[fetch_index];\n"
anchor_gen_start = "// Generated per-entry update: one sequential driver each, and the whole\n"
anchor_gen_end = "endgenerate\n"
for a in (anchor_ports, anchor_mem, anchor_read, anchor_gen_start, anchor_gen_end):
    assert old_bht.count(a) == 1, ("bht_2bit.v anchor", a[:50])
assert "fetch_pc_next" not in old_bht
b = old_bht.replace(anchor_ports, anchor_ports +
                    "`ifndef __openlane__\n"
                    "    input  wire [31:0]                 fetch_pc_next,    // FPGA: pc_f at the next edge (read-ahead address)\n"
                    "    input  wire [31:0]                 update_pc_next,   // FPGA: pc_e at the next edge\n"
                    "`endif\n")
b = b.replace(anchor_mem, "wire [BHT_INDEX_BITS-1:0] update_index;\n`ifdef __openlane__\nreg  [1:0] bht_mem [0:BHT_ENTRIES-1];\n`endif\n")
b = b.replace(anchor_read, "`ifdef __openlane__\n" + anchor_read + "`endif\n")
i = b.index(anchor_gen_start)
j = b.index(anchor_gen_end, i) + len(anchor_gen_end)
fpga = """`else
// FPGA (2026-10-08, review A1): counters in two M9K copies (fetch read, update read) instead of 512 flip-flops. The
// read addresses registered at an edge are the indices pc_f / pc_e take at that edge; q* = contents before the write
// of that edge, which is bypassed from upd_*_q. valid[] (flip-flops, asynchronous reset) makes an entry not written
// since reset read BHT_RESET_STATE, as the reset of the old table did. Same value as the old table in every cycle.
(* ramstyle = "M9K" *) reg [1:0] cnt_f [0:BHT_ENTRIES-1];
(* ramstyle = "M9K" *) reg [1:0] cnt_u [0:BHT_ENTRIES-1];
reg  [BHT_ENTRIES-1:0]    valid;
reg  [1:0]                qf, qu;
reg                       upd_q;
reg  [BHT_INDEX_BITS-1:0] upd_idx_q;
reg  [1:0]                upd_val_q;
wire [BHT_INDEX_BITS-1:0] fetch_index_next  = fetch_pc_next[BHT_INDEX_BITS+1:2];
wire [BHT_INDEX_BITS-1:0] update_index_next = update_pc_next[BHT_INDEX_BITS+1:2];
wire [1:0] cur_u = !valid[update_index] ? BHT_RESET_STATE :
                   (upd_q && upd_idx_q == update_index) ? upd_val_q : qu;
wire [1:0] new_u = next_counter_state(cur_u, actual_taken);

assign fetch_state = !valid[fetch_index] ? BHT_RESET_STATE :
                     (upd_q && upd_idx_q == fetch_index) ? upd_val_q : qf;

always @(posedge clk) begin
    if(update_en) begin
        cnt_f[update_index] <= new_u;
        cnt_u[update_index] <= new_u;
    end
    qf <= cnt_f[fetch_index_next];
    qu <= cnt_u[update_index_next];
end

always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        valid     <= {BHT_ENTRIES{1'b0}};
        upd_q     <= 1'b0;
        upd_idx_q <= {BHT_INDEX_BITS{1'b0}};
        upd_val_q <= 2'b00;
    end
    else begin
        if(update_en)
            valid[update_index] <= 1'b1;
        upd_q     <= update_en;
        upd_idx_q <= update_index;
        upd_val_q <= new_u;
    end
end

// synthesis translate_off
// Checker: the old table beside the new one (same reset, same update); a difference stops the simulation. Compared
// at the edge that consumes the values, inside the reset structure of the table, so reset_n stays an asynchronous
// reset only (a level test of reset_n in a clocked block is SYNCASYNCNET in lint_asic).
reg [1:0] ref_mem [0:BHT_ENTRIES-1];
integer ref_i;
always @(posedge clk or negedge reset_n) begin
    if(!reset_n) begin
        for(ref_i = 0; ref_i < BHT_ENTRIES; ref_i = ref_i + 1)
            ref_mem[ref_i] <= BHT_RESET_STATE;
    end
    else begin
        if(fetch_state !== ref_mem[fetch_index] || (update_en && cur_u !== ref_mem[update_index]))
            $fatal(1, "bht_2bit M9K checker: fetch %b / %b (index %0d), update %b / %b (index %0d) at %0t",
                   fetch_state, ref_mem[fetch_index], fetch_index, cur_u, ref_mem[update_index], update_index, $time);
        if(update_en)
            ref_mem[update_index] <= next_counter_state(ref_mem[update_index], actual_taken);
    end
end
// synthesis translate_on
`endif
"""
b = b[:i] + "`ifdef __openlane__\n" + b[i:j] + fpga + b[j:]
# ---------------------------------------------------------------- datapath.v
d = rd("hdl/datapath.v")
a_bht = "// --- BHT Instance ---\n"
a_bht_ports = "            .fetch_pc      (pc_f),\n"
a_rf_ports = "    .wd    (result_w)       ,\n"
for a in (a_bht, a_bht_ports, a_rf_ports):
    assert d.count(a) == 1, ("datapath.v anchor", a)
assert "instr_d_next" not in d
d = d.replace(a_bht,
              "`ifndef __openlane__\n"
              "// FPGA read-ahead addresses of the register file and the BHT in M9K (2026-10-08, review A1): the D inputs of\n"
              "// instr_d, pc_f and pc_e, written as their always blocks below load them (enable !stall_pipe, flush, stall).\n"
              "wire [31:0] instr_d_next = stall_pipe ? instr_d : flush_d ? 32'h0000_0000 : stall_d ? instr_d : instr;\n"
              "wire [31:0] pc_f_next    = stall_pipe ? pc_f : irq_accept ? csr_mtvec : !stall_f ? pc_next : pc_f;\n"
              "wire [31:0] pc_e_next    = stall_pipe ? pc_e : flush_e ? 32'h0000_0000 : pc_d;\n"
              "`endif\n\n" + a_bht)
d = d.replace(a_bht_ports, a_bht_ports +
              "`ifndef __openlane__\n"
              "            .fetch_pc_next (pc_f_next),\n"
              "            .update_pc_next(pc_e_next),\n"
              "`endif\n")
d = d.replace(a_rf_ports, a_rf_ports +
              "`ifndef __openlane__\n"
              "    .rs1_next (instr_d_next[19:15]),\n"
              "    .rs2_next (instr_d_next[24:20]),\n"
              "`endif\n")
wr("hdl/regfile.v", new_rf)
wr("hdl/predictor/bht_2bit.v", b)
wr("hdl/datapath.v", d)
for p in ("hdl/regfile.v", "hdl/predictor/bht_2bit.v", "hdl/datapath.v"):
    print("%s  %s" % (hashlib.sha256((root / p).read_bytes()).hexdigest()[:16], p))
