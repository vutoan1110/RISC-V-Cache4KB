#!/usr/bin/env python3
"""R10 (NHAT_KY.md 2026-09-26): cycle-exact timing restructuring for the ss corner.

    python scripts/apply_r10.py [root]   # apply (fails if any anchor is missing)

Evidence (NHAT_KY.md 2026-09-26, signoff STA of r9_ecf4 at max_ss):
  * the worst path is pc_f -> L0 hot-buffer hit -> stall_pipe -> retire_event
    -> csr_minstret; 7 ns of it (11.1 -> 18.1 ns) is the LINE_COUNT:1 mux that
    reads the tag RAM's valid bit at the live index for the hot hit, and the
    same path through the hot-tag compare alone is 2.2 ns shorter;
  * 265 of the 2,657 violating endpoints are counters whose late enable was
    folded by ABC into the BASE of a ripple carry chain (csr_minstret: 20 AND
    cells after retire_event; perf pipe_fill_drain: 26 cells, ~13 ns).

R10a  icache_controller: hot_hit read `tag_valid_rd`, the tag RAM's valid
      bit at the live index. It matters only when the hot tag matches, i.e.
      when the live line IS the line hot entry hot_index holds, so the bit is
      tracked per hot entry instead (hot_mvalid, L0_ENTRIES flops):
        - reset: 0 (valid_bits reset to 0);
        - a hot fill (lookup hit, or refill_success) sets it: on a lookup hit
          the line's valid bit is 1 (request_hit needs lookup_valid_q, which
          is the valid bit read in ST_IDLE, and no tag write happens between
          ST_IDLE and ST_LOOKUP); on refill_success the tag RAM sets it in the
          same edge;
        - every tag-RAM valid write (tag_wr_en, index miss_index) is copied to
          the one hot entry that can hold that line, miss_hot_index, when the
          line-index bits kept in its tag match. A fill and a write in the
          same edge only happen on refill_success, where both give 1.
      Invariant: hot_mvalid[e] == valid_bits[line index of hot entry e], so
      hot_valid[i] && hot_mvalid[i] && tag_match == hot_valid[i] &&
      tag_valid_rd && tag_match in every cycle. tag_valid_rd still feeds
      lookup_valid_q (registered). Checked every simulated cycle, invariant
      and hot hit, by the checker added to icache.v.
R10b  counters with late enables: the +1 is a (* keep *) net, so synthesis
      builds it from the counter's own flops and the enable meets it only in
      the final select. The logic function is unchanged (X + 1'b1 in a 32-bit
      context == X + 32'd1). Applied only to counters present in the signed-off
      netlist (csr_minstret and the 36 perf counters; the two victim counters
      are constant in the DM build and fold away as before); load_stall_count,
      control_redirect_count and retire_order_q are left alone because a kept
      net would resurrect counters synthesis currently removes as unused.
Also: the R9 checker's final line claimed "0 mismatches" even when a $fatal
had fired (final blocks run after $fatal); it now reports matched cycles.
"""
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."


def edit(path, pairs):
    # Sources are LF or CRLF. Each anchor is tried as written (LF) and with
    # CRLF; exactly one variant must match exactly once, and the replacement
    # keeps that variant's line ends.
    path = os.path.join(ROOT, path)
    s = open(path, newline="").read()
    for old, new in pairs:
        crlf = (old.replace("\n", "\r\n"), new.replace("\n", "\r\n"))
        hits = [(o, n) for o, n in ((old, new), crlf) if s.count(o) == 1]
        if "\n" not in old:
            hits = hits[:1]
        if len(hits) != 1:
            sys.exit("[FAIL] %s: anchor LF x%d / CRLF x%d:\n%s" % (
                path, s.count(old), s.count(crlf[0]), old[:200]))
        s = s.replace(*hits[0])
    open(path, "w", newline="").write(s)
    print("[OK] %s: %d edit(s)" % (path, len(pairs)))


# ------------------------------------------------------------------ R10a
edit("hdl/cache/icache_controller.v", [
    ("reg [127:0]           hot_line [0:L0_ENTRIES-1];\n",
     "reg [127:0]           hot_line [0:L0_ENTRIES-1];\n"
     "// R10a -- main-array valid bit of the line each hot entry holds. The hot hit\n"
     "// used to read the tag RAM's valid bit at the live index: a LINE_COUNT:1 mux\n"
     "// on the fetch critical path. That bit only matters when the hot tag matches,\n"
     "// i.e. when the live line IS the hot entry's line, so it is kept per hot\n"
     "// entry instead: set on a fill (the line is valid then) and following every\n"
     "// tag-RAM valid write to that line. Checked every cycle by icache.v.\n"
     "reg [L0_ENTRIES-1:0]  hot_mvalid;\n"),
    ("assign hot_hit        = hot_valid[hot_index] && tag_valid_rd &&\n"
     "                        (hot_tag[hot_index] == request_block[27:L0_IDX_BITS]);\n",
     "assign hot_hit        = hot_valid[hot_index] && hot_mvalid[hot_index] &&\n"
     "                        (hot_tag[hot_index] == request_block[27:L0_IDX_BITS]);\n"),
    ("// The hot buffer answers in the request cycle. It is qualified by the main\n"
     "// array's valid bit, not by its tag: the tag is no longer readable in this\n"
     "// cycle, and icache_dse_core has never used it here either.\n",
     "// The hot buffer answers in the request cycle. It is qualified by the main\n"
     "// array's valid bit (its per-entry copy, hot_mvalid), not by its tag: the\n"
     "// tag is no longer readable in this cycle, and icache_dse_core has never\n"
     "// used it here either.\n"),
])

R10A_BLOCK = """
// R10a -- hot_mvalid upkeep. Line miss_index can only sit in hot entry
// miss_hot_index (its low index bits are the hot index); it is there when the
// line-index bits kept in that entry's tag match.
localparam HOT_LI_BITS = INDEX_WIDTH - L0_IDX_BITS;
wire hot_holds_miss_line;
generate
if(HOT_LI_BITS > 0) begin : g_hot_li
    assign hot_holds_miss_line =
        (hot_tag[miss_hot_index][HOT_LI_BITS-1:0] == miss_index[INDEX_WIDTH-1:L0_IDX_BITS]);
end
else begin : g_hot_li_none
    assign hot_holds_miss_line = 1'b1;
end
endgenerate
// A hot fill: exactly the two places the main always block writes hot_line.
wire hot_fill = (lookup_active && request_hit) || refill_success;

// synthesis translate_off
initial if(INDEX_WIDTH < L0_IDX_BITS)
    $fatal(1, "%m: R10a needs INDEX_WIDTH >= log2(L0_ENTRIES), got %0d < %0d",
           INDEX_WIDTH, L0_IDX_BITS);
// synthesis translate_on

always @(posedge clk or negedge reset_n) begin
    if(!reset_n)
        hot_mvalid <= {L0_ENTRIES{1'b0}};
    else if(hot_fill)
        hot_mvalid[miss_hot_index] <= 1'b1;
    else if(tag_wr_en && hot_holds_miss_line)
        hot_mvalid[miss_hot_index] <= tag_wr_valid;
end

"""
path = os.path.join(ROOT, "hdl/cache/icache_controller.v")
s = open(path, newline="").read()
nl = "\r\n" if "\r\n" in s else "\n"
if s.count("endmodule") != 1:
    sys.exit("[FAIL] icache_controller.v: endmodule count %d" % s.count("endmodule"))
end = s.rindex("endmodule")
s = s[:end] + R10A_BLOCK.lstrip("\n").replace("\n", nl) + s[end:]
open(path, "w", newline="").write(s)
print("[OK] %s: hot_mvalid upkeep block" % path)

R10A_CHECKER = """
    // R10a equivalence checker -- simulation only (hidden from Quartus by
    // translate_off and from every OpenLane tool by __openlane__). Every cycle
    // it checks the invariant that makes hot_mvalid exact (each bit equals the
    // tag RAM's valid bit of the line its hot entry holds) and that the hot
    // hit equals its pre-R10a form, which read tag_valid_rd at the live index.
`ifndef __openlane__
    // synthesis translate_off
    // same as the controller's L0_IDX_BITS (clog2 above == $clog2)
    localparam R10_L0B = (L0_ENTRIES > 1) ? clog2(L0_ENTRIES) : 1;
    integer r10_e;
    reg     r10_inv_ok;
    always @(*) begin
        r10_inv_ok = 1'b1;
        for(r10_e = 0; r10_e < L0_ENTRIES; r10_e = r10_e + 1)
            if(u_controller.hot_mvalid[r10_e] !==
               u_tag_ram.valid_bits[{u_controller.hot_tag[r10_e][INDEX_WIDTH-R10_L0B-1:0],
                                     r10_e[R10_L0B-1:0]}])
                r10_inv_ok = 1'b0;
    end
    wire r10_ref_hot_hit = u_controller.hot_valid[u_controller.hot_index] && tag_valid_rd &&
                           (u_controller.hot_tag[u_controller.hot_index] ==
                            u_controller.request_block[27:R10_L0B]);
    reg [63:0] r10_checks;
    always @(posedge clk or negedge reset_n) begin
        if(!reset_n)
            r10_checks <= 64'd0;
        else if(!r10_inv_ok || (u_controller.hot_hit !== r10_ref_hot_hit))
            $fatal(1, "R10a equivalence broken at %0t: hot_hit %b/%b invariant %b",
                   $time, u_controller.hot_hit, r10_ref_hot_hit, r10_inv_ok);
        else
            r10_checks <= r10_checks + 64'd1;
    end
    final
        $display("R10_EQUIV %m: %0d cycles matched", r10_checks);
    // synthesis translate_on
`endif
"""
edit("hdl/cache/icache.v", [
    ("    assign main_hit_count=hit_count;\n",
     R10A_CHECKER.lstrip("\n") + "\n    assign main_hit_count=hit_count;\n"),
])

# ------------------------------------------------------------------ R10b
KEEP_NOTE = (
    "// R10b -- every increment below is a kept net: synthesis builds the +1 from\n"
    "// the counter's own flops, and the late enables (counter_clear/freeze come\n"
    "// straight from an APB write, the events from the pipeline) meet it only in\n"
    "// the final select. Without the cut ABC folded the enable into the base of a\n"
    "// ripple carry chain (26 cells, ~13 ns at ss). Same logic, different shape.\n")
path = os.path.join(ROOT, "hdl/perf_counters.v")
s = open(path, newline="").read()
if "\r\n" in s:
    sys.exit("[FAIL] perf_counters.v is CRLF; R10b expects LF")
# some increments sit behind a case label ("9'b000000001:" / "default:")
incs = re.findall(r"^(\s+(?:\S+:\s+)?)(\w+)(\s*)<= \2 \+ 1'b1;$", s, re.M)
names = [n for _, n, _ in incs]
if len(names) != 36 or len(set(names)) != 36:
    sys.exit("[FAIL] perf_counters.v: expected 36 distinct increments, got %d" % len(names))
for n in names:
    s, k = re.subn(r"^(\s+(?:\S+:\s+)?)%s(\s*)<= %s \+ 1'b1;$" % (n, n), r"\g<1>%s\g<2><= %s_inc;" % (n, n), s, flags=re.M)
    if k != 1:
        sys.exit("[FAIL] perf_counters.v: %s replaced %d times" % (n, k))
anchor = "always @(posedge clk or negedge reset_n) begin\n    if(!reset_n) begin\n        mcycle_count "
if s.count(anchor) != 1:
    sys.exit("[FAIL] perf_counters.v: counter always-block anchor x%d" % s.count(anchor))
decls = KEEP_NOTE + "".join("(* keep *) wire [31:0] %s_inc = %s + 32'd1;\n" % (n, n) for n in names) + "\n"
s = s.replace(anchor, decls + anchor)
open(path, "w", newline="").write(s)
print("[OK] %s: %d kept increments" % (path, len(names)))

edit("hdl/datapath.v", [
    ("// --- CSR registers ---\n",
     "// R10b -- the retire-gated increment is a kept net, so the late retire enable\n"
     "// meets it only in the final select instead of at the base of a ripple carry\n"
     "// chain (20 cells after retire_event in r9_ecf4). Same logic, different shape.\n"
     "(* keep *) wire [31:0] csr_minstret_inc = csr_minstret + 32'd1;\n"
     "// --- CSR registers ---\n"),
    ("        if(!stall_pipe && valid_w)\n            csr_minstret <= csr_minstret + 1'b1;\n",
     "        if(!stall_pipe && valid_w)\n            csr_minstret <= csr_minstret_inc;\n"),
    # R9 checker wording (see the docstring)
    ('    $display("R9_EQUIV %m: %0d cycles checked, 0 mismatches", r9_checks);\n',
     '    $display("R9_EQUIV %m: %0d cycles matched", r9_checks);\n'),
])
print("[DONE] R10 applied under", os.path.abspath(ROOT))
