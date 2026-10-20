"""R16 (review item M1, 2026-10-03): FAST_HIT -- the DSE / N-way cache cores answer a main-array hit in ST_LOOKUP.

Why: the published comparison confounds organisation with controller depth. An access that misses the L0 hot buffer
but hits the main array costs ONE extra cycle in the five-state DM controller (ST_IDLE -> ST_HIT_RESP) and TWO in
the DSE / N-way cores (ST_IDLE -> ST_LOOKUP -> ST_HIT_RESP / ST_CPU_RESP). In ST_LOOKUP those cores already hold
both the registered tag (read in ST_IDLE) and the bank line (read in ST_IDLE: bank_rd_en is set on every accept
that is not an L0 hit), so with FAST_HIT=1 a main hit is answered there and the core returns to ST_IDLE; the L0
fill that ST_HIT_RESP / ST_CPU_RESP performed is done in the same ST_LOOKUP cycle (stores are unchanged: their
commit path, and the only other L0 writer, runs in ST_WRITE_REQ / ST_WRITE_RESP). FAST_HIT=0 (default) is the
original RTL; the change is proved equivalent for FAST_HIT=0 (scripts/r16_fasthit/, formal step).

    python scripts/r16_fasthit/apply_r16.py <tree root>      (patches <root>/hdl and <root>/tb in place)
Every edit is an exact, unique anchor (assert count == 1); a second application fails on purpose.
"""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])


def edit(rel, pairs):
    p = root / rel
    s = p.read_text(encoding="utf-8")
    for old, new in pairs:
        n = s.count(old)
        assert n == 1, "%s: anchor found %d times:\n%s" % (rel, n, old)
        s = s.replace(old, new)
    p.write_text(s, encoding="utf-8", newline="\n")
    print("patched %s (%d edits)" % (rel, len(pairs)))


PARAM_DOC = ("    // R16 (review M1): 1 answers a main-array hit in ST_LOOKUP (one extra cycle, as in the five-state\n"
             "    // DM controller) instead of in the following response state (two). 0 = the original core.\n")

# ---------------------------------------------------------------- icache_dse_core.v
edit("hdl/cache/icache_dse_core.v", [
    ("    parameter L0_ENTRIES      = 8\n)(",
     "    parameter L0_ENTRIES      = 8,\n" + PARAM_DOC + "    parameter FAST_HIT        = 0\n)("),
    ("wire fast_main_hit_event = main_hit_accept_event;\n",
     "wire fast_main_hit_event = main_hit_accept_event;\n"
     "// R16: with FAST_HIT a main-array hit is answered in ST_LOOKUP (registered tag and bank line are both there).\n"
     "wire fast_lookup_hit = (FAST_HIT != 0) && lookup_active && main_hit;\n"),
    ("assign rsp_valid = fast_main_hit_event || (state == ST_HIT_RESP) ||",
     "assign rsp_valid = fast_main_hit_event || fast_lookup_hit || (state == ST_HIT_RESP) ||"),
    ("                  select_line_word(hot_hit_line, req_addr[OFFSET_BITS-1:2]) :\n"
     "                  (main_read_response ?\n"
     "                   select_line_word(refill_way ? bank1_rd_line : bank0_rd_line,",
     "                  select_line_word(hot_hit_line, req_addr[OFFSET_BITS-1:2]) :\n"
     "                  fast_lookup_hit ?\n"
     "                  select_line_word(main_hit1 ? bank1_rd_line : bank0_rd_line, request_word) :\n"
     "                  (main_read_response ?\n"
     "                   select_line_word(refill_way ? bank1_rd_line : bank0_rd_line,"),
    ("assign rsp_error = fast_main_hit_event ? 1'b0 : rsp_error_reg;",
     "assign rsp_error = (fast_main_hit_event || fast_lookup_hit) ? 1'b0 : rsp_error_reg;"),
    ("                        replace_way[request_index] <= main_hit0 ? 1'b1 : 1'b0;\n"
     "                    state <= ST_HIT_RESP;\n",
     "                        replace_way[request_index] <= main_hit0 ? 1'b1 : 1'b0;\n"
     "                    if(FAST_HIT != 0) begin\n"
     "                        // R16: the ST_HIT_RESP L0 fill, done here because the response leaves now\n"
     "                        hot_valid[request_hot_index] <= 1'b1;\n"
     "                        hot_tag[request_hot_index] <= request_block[BLOCK_WIDTH-1:L0_IDX_BITS];\n"
     "                        hot_line[request_hot_index] <=\n"
     "                            main_hit1 ? bank1_rd_line : bank0_rd_line;\n"
     "                        hot_way[request_hot_index] <= main_hit1;\n"
     "                        state <= ST_IDLE;\n"
     "                    end else\n"
     "                        state <= ST_HIT_RESP;\n"),
])

# ---------------------------------------------------------------- icache_nway_core.v
edit("hdl/cache/icache_nway_core.v", [
    ("    parameter L0_ENTRIES      = 8\n)(",
     "    parameter L0_ENTRIES      = 8,\n" + PARAM_DOC + "    parameter FAST_HIT        = 0\n)("),
    ("wire fast_main_hit_event = main_hit_accept_event;\n",
     "wire fast_main_hit_event = main_hit_accept_event;\n"
     "// R16: with FAST_HIT a main-array hit is answered in ST_LOOKUP (registered tags and bank lines are both there).\n"
     "wire fast_lookup_hit = (FAST_HIT != 0) && lookup_active && main_hit;\n"),
    ("wire [LINE_WIDTH-1:0] refill_way_line = bank_rd_flat[refill_way[WAY_BITS-1:0]*LINE_WIDTH +: LINE_WIDTH];\n",
     "wire [LINE_WIDTH-1:0] refill_way_line = bank_rd_flat[refill_way[WAY_BITS-1:0]*LINE_WIDTH +: LINE_WIDTH];\n"
     "wire [LINE_WIDTH-1:0] hit_way_line = bank_rd_flat[hit_way[WAY_BITS-1:0]*LINE_WIDTH +: LINE_WIDTH];\n"),
    ("assign rsp_valid = fast_main_hit_event || (state == ST_HIT_RESP) ||",
     "assign rsp_valid = fast_main_hit_event || fast_lookup_hit || (state == ST_HIT_RESP) ||"),
    ("                  select_line_word(hot_hit_line, req_addr[OFFSET_BITS-1:2]) :\n"
     "                  (main_read_response ? select_line_word(refill_way_line, request_word)",
     "                  select_line_word(hot_hit_line, req_addr[OFFSET_BITS-1:2]) :\n"
     "                  fast_lookup_hit ? select_line_word(hit_way_line, request_word) :\n"
     "                  (main_read_response ? select_line_word(refill_way_line, request_word)"),
    ("assign rsp_error = fast_main_hit_event ? 1'b0 : rsp_error_reg;",
     "assign rsp_error = (fast_main_hit_event || fast_lookup_hit) ? 1'b0 : rsp_error_reg;"),
    ("                    plru_v[request_index*3 +: 3] <= plru_touch(plru_req, hit_way);\n"
     "                    state <= ST_HIT_RESP;\n",
     "                    plru_v[request_index*3 +: 3] <= plru_touch(plru_req, hit_way);\n"
     "                    if(FAST_HIT != 0) begin\n"
     "                        // R16: the ST_HIT_RESP L0 fill, done here because the response leaves now\n"
     "                        hot_valid[request_hot_index] <= 1'b1;\n"
     "                        hot_tag[request_hot_index] <= request_block[BLOCK_WIDTH-1:L0_IDX_BITS];\n"
     "                        hot_line[request_hot_index] <= hit_way_line;\n"
     "                        hot_way[request_hot_index] <= hit_way;\n"
     "                        state <= ST_IDLE;\n"
     "                    end else\n"
     "                        state <= ST_HIT_RESP;\n"),
])


def dcache_fill_block(text, way_expr, line_expr_old, line_expr_new):
    """The L0 fill of ST_CPU_RESP, with the response way replaced by the hit way (ST_LOOKUP)."""
    m = re.search(r"            ST_CPU_RESP: begin\n                if\(main_read_response\) begin\n(.*?)\n"
                  r"                end\n                state<=ST_IDLE;\n", text, re.S)
    assert m, "ST_CPU_RESP fill block not found"
    body = m.group(1)
    assert body.count(line_expr_old) >= 6, (line_expr_old, body.count(line_expr_old))
    body = body.replace(line_expr_old, line_expr_new)
    body = re.sub(r"\brefill_way\b", way_expr, body)
    assert "refill_way" not in body
    return "\n".join(("        " + ln) if ln.strip() else ln for ln in body.split("\n"))


# ---------------------------------------------------------------- dcache_dse_core.v
p = root / "hdl/cache/dcache_dse_core.v"
src = p.read_text(encoding="utf-8")
fill = dcache_fill_block(src, "main_hit1", "refill_way ? bank1_rd_line : bank0_rd_line",
                         "main_hit1 ? bank1_rd_line : bank0_rd_line")
edit("hdl/cache/dcache_dse_core.v", [
    ("    parameter LINE_WORDS = 4\n)(",
     "    parameter LINE_WORDS = 4,\n" + PARAM_DOC + "    parameter FAST_HIT = 0\n)("),
    ("assign rsp_valid = fast_load_main_event || (state == ST_CPU_RESP);",
     "// R16: with FAST_HIT a main-array LOAD hit is answered in ST_LOOKUP (stores keep their write path).\n"
     "wire fast_lookup_load_hit = (FAST_HIT != 0) && lookup_active && main_hit && !request_write;\n"
     "assign rsp_valid = fast_load_main_event || fast_lookup_load_hit || (state == ST_CPU_RESP);"),
    ("                   select_line_word(hot_hit_line, req_addr[OFFSET_BITS-1:2]) :\n"
     "                   (main_read_response ?",
     "                   select_line_word(hot_hit_line, req_addr[OFFSET_BITS-1:2]) :\n"
     "                   fast_lookup_load_hit ?\n"
     "                   select_line_word(main_hit1 ? bank1_rd_line : bank0_rd_line, request_word) :\n"
     "                   (main_read_response ?"),
    ("assign rsp_error = fast_load_main_event ? 1'b0 : rsp_error_reg;",
     "assign rsp_error = (fast_load_main_event || fast_lookup_load_hit) ? 1'b0 : rsp_error_reg;"),
    ("                    end else begin\n"
     "                        refill_way<=main_hit1;\n"
     "                        main_read_response<=1'b1;\n"
     "                        state<=ST_CPU_RESP;\n"
     "                    end\n",
     "                    end else begin\n"
     "                        refill_way<=main_hit1;\n"
     "                        main_read_response<=1'b1;\n"
     "                        if(FAST_HIT != 0) begin\n"
     "                            // R16: the ST_CPU_RESP L0 fill, done here because the response leaves now\n"
     + fill + "\n"
     "                            state<=ST_IDLE;\n"
     "                        end else\n"
     "                            state<=ST_CPU_RESP;\n"
     "                    end\n"),
])

# ---------------------------------------------------------------- dcache_nway_core.v
p = root / "hdl/cache/dcache_nway_core.v"
src = p.read_text(encoding="utf-8")
fill = dcache_fill_block(src, "hit_way", "refill_way_line", "hit_way_line")
edit("hdl/cache/dcache_nway_core.v", [
    ("    parameter WAYS = 4,\n    parameter LINE_WORDS = 4\n)(",
     "    parameter WAYS = 4,\n    parameter LINE_WORDS = 4,\n" + PARAM_DOC + "    parameter FAST_HIT = 0\n)("),
    ("assign rsp_valid = fast_load_main_event || (state == ST_CPU_RESP);",
     "// R16: with FAST_HIT a main-array LOAD hit is answered in ST_LOOKUP (stores keep their write path).\n"
     "wire fast_lookup_load_hit = (FAST_HIT != 0) && lookup_active && main_hit && !request_write;\n"
     "assign rsp_valid = fast_load_main_event || fast_lookup_load_hit || (state == ST_CPU_RESP);"),
    ("                   select_line_word(hot_hit_line, req_addr[OFFSET_BITS-1:2]) :\n"
     "                   (main_read_response ? select_line_word(refill_way_line, request_word)",
     "                   select_line_word(hot_hit_line, req_addr[OFFSET_BITS-1:2]) :\n"
     "                   fast_lookup_load_hit ? select_line_word(hit_way_line, request_word) :\n"
     "                   (main_read_response ? select_line_word(refill_way_line, request_word)"),
    ("assign rsp_error = fast_load_main_event ? 1'b0 : rsp_error_reg;",
     "assign rsp_error = (fast_load_main_event || fast_lookup_load_hit) ? 1'b0 : rsp_error_reg;"),
    ("                    end else begin\n"
     "                        refill_way<=hit_way;\n"
     "                        main_read_response<=1'b1;\n"
     "                        state<=ST_CPU_RESP;\n"
     "                    end\n",
     "                    end else begin\n"
     "                        refill_way<=hit_way;\n"
     "                        main_read_response<=1'b1;\n"
     "                        if(FAST_HIT != 0) begin\n"
     "                            // R16: the ST_CPU_RESP L0 fill, done here because the response leaves now\n"
     + fill + "\n"
     "                            state<=ST_IDLE;\n"
     "                        end else\n"
     "                            state<=ST_CPU_RESP;\n"
     "                    end\n"),
])

# ---------------------------------------------------------------- plumbing: wrappers, tops, benchmark testbench
edit("hdl/cache/icache.v", [
    ("    parameter L0_ENTRIES = 8\n)(",
     "    parameter L0_ENTRIES = 8,\n"
     "    // R16 (review M1): DSE / N-way cores answer a main-array hit in ST_LOOKUP; the DM controller ignores it.\n"
     "    parameter FAST_HIT = 0\n)("),
    ("                       .LINE_WORDS(LINE_WORDS),.L0_ENTRIES(L0_ENTRIES)) u_core(",
     "                       .LINE_WORDS(LINE_WORDS),.L0_ENTRIES(L0_ENTRIES),.FAST_HIT(FAST_HIT)) u_core("),
    ("                      .VICTIM_ENTRIES(VICTIM_ENTRIES),\n                      .L0_ENTRIES(L0_ENTRIES)) u_core(",
     "                      .VICTIM_ENTRIES(VICTIM_ENTRIES),\n                      .L0_ENTRIES(L0_ENTRIES),.FAST_HIT(FAST_HIT)) u_core("),
])
edit("hdl/cache/dcache.v", [
    ("    parameter VICTIM_ENTRIES=4\n)(",
     "    parameter VICTIM_ENTRIES=4,\n"
     "    // R16 (review M1): DSE / N-way cores answer a main-array load hit in ST_LOOKUP; the DM controller ignores it.\n"
     "    parameter FAST_HIT=0\n)("),
    ("                       .LINE_WORDS(LINE_WORDS)) u_core(",
     "                       .LINE_WORDS(LINE_WORDS),.FAST_HIT(FAST_HIT)) u_core("),
    ("                      .VICTIM_ENTRIES(VICTIM_ENTRIES)) u_core(",
     "                      .VICTIM_ENTRIES(VICTIM_ENTRIES),.FAST_HIT(FAST_HIT)) u_core("),
])
edit("hdl/soc_top.v", [
    ("    parameter integer CACHE_LINE_WORDS = 4,\n",
     "    parameter integer CACHE_LINE_WORDS = 4,\n"
     "    // R16 (review M1): 1 = DSE / N-way caches answer main-array hits in ST_LOOKUP (no effect on CACHE_CONFIG 0).\n"
     "    parameter integer CACHE_FAST_HIT = 0,\n"),
    ("    .L0_ENTRIES     (L0_ENTRIES)\n) u_icache (",
     "    .L0_ENTRIES     (L0_ENTRIES),\n    .FAST_HIT       (CACHE_FAST_HIT)\n) u_icache ("),
    ("    .VICTIM_ENTRIES (VICTIM_ENTRIES)\n) u_dcache (",
     "    .VICTIM_ENTRIES (VICTIM_ENTRIES),\n    .FAST_HIT       (CACHE_FAST_HIT)\n) u_dcache ("),
])
edit("hdl/board/de2_115_top.v", [
    ("    parameter integer CACHE_LINE_WORDS        = 4,\n",
     "    parameter integer CACHE_LINE_WORDS        = 4,\n    // R16 (review M1): see soc_top.v\n"
     "    parameter integer CACHE_FAST_HIT          = 0,\n"),
    ("    .CACHE_LINE_WORDS       (CACHE_LINE_WORDS),\n",
     "    .CACHE_LINE_WORDS       (CACHE_LINE_WORDS),\n    .CACHE_FAST_HIT         (CACHE_FAST_HIT),\n"),
])
edit("tb/benchmark_snapshot_tb.sv", [
    ("parameter integer CACHE_LINE_WORDS=4,\n",
     "parameter integer CACHE_LINE_WORDS=4,\n parameter integer CACHE_FAST_HIT=0,   // R16 (review M1)\n"),
    (".CACHE_LINE_WORDS(CACHE_LINE_WORDS),",
     ".CACHE_LINE_WORDS(CACHE_LINE_WORDS),.CACHE_FAST_HIT(CACHE_FAST_HIT),"),
])

# ---------------------------------------------------------------- sim-only per-cycle checkers (rule D.3)
CHK_DOC = ("// R16 sim-only per-cycle checker (rule D.3). With FAST_HIT a main hit is answered in ST_LOOKUP from the bank\n"
           "// line read in ST_IDLE; the original core answered one cycle later from the line read in ST_LOOKUP at the\n"
           "// same index. The next cycle the bank output holds that ST_LOOKUP read: the fast answer must equal its word,\n"
           "// and with FAST_HIT no main hit may reach the old response state any more.\n")


def checker(fast_sig, way_expr, way_bits, line_of_way, resp_state, data_sig):
    return ("`ifndef __openlane__\n// synthesis translate_off\n" + CHK_DOC +
            "reg r16_pend;\nreg [%d:0] r16_way;\nreg [WORD_BITS-1:0] r16_widx;\nreg [31:0] r16_word;\n" % (way_bits - 1) +
            "always @(posedge clk or negedge reset_n) begin\n"
            "    if(!reset_n) begin\n        r16_pend <= 1'b0;\n    end else begin\n"
            "        if(r16_pend && (select_line_word(%s, r16_widx) !== r16_word))\n" % line_of_way +
            "            $fatal(1, \"R16 FAST_HIT: ST_LOOKUP answer %%h is not the word the old response state reads\", r16_word);\n"
            "        if((FAST_HIT != 0) && (state == %s) && main_read_response)\n" % resp_state +
            "            $fatal(1, \"R16 FAST_HIT: a main hit reached %s\");\n" % resp_state +
            "        r16_pend <= %s;\n        r16_way <= %s;\n" % (fast_sig, way_expr) +
            "        r16_widx <= request_word;\n        r16_word <= %s;\n    end\nend\n" % data_sig +
            "// synthesis translate_on\n`endif\n\nendmodule")


edit("hdl/cache/icache_dse_core.v", [("\nendmodule", "\n" + checker(
    "fast_lookup_hit", "main_hit1", 1, "r16_way[0] ? bank1_rd_line : bank0_rd_line", "ST_HIT_RESP", "rsp_data"))])
edit("hdl/cache/dcache_dse_core.v", [("\nendmodule", "\n" + checker(
    "fast_lookup_load_hit", "main_hit1", 1, "r16_way[0] ? bank1_rd_line : bank0_rd_line", "ST_CPU_RESP", "rsp_rdata"))])
edit("hdl/cache/icache_nway_core.v", [("\nendmodule", "\n" + checker(
    "fast_lookup_hit", "hit_way", 2, "bank_rd_flat[r16_way[WAY_BITS-1:0]*LINE_WIDTH +: LINE_WIDTH]", "ST_HIT_RESP",
    "rsp_data"))])
edit("hdl/cache/dcache_nway_core.v", [("\nendmodule", "\n" + checker(
    "fast_lookup_load_hit", "hit_way", 2, "bank_rd_flat[r16_way[WAY_BITS-1:0]*LINE_WIDTH +: LINE_WIDTH]", "ST_CPU_RESP",
    "rsp_rdata"))])
