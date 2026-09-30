#!/usr/bin/env python3
"""R11 (candidate, NHAT_KY_RTL 2026-09-26): L0 hot hit as compare-then-select.

Evidence (FLOW_JOURNAL Incident 77): after R10a the worst max_ss path of r10A is
pc_f[6] -> hot-index decode -> 2.7 ns buffer tree -> AND-OR mux of hot_tag ->
compare -> or4/or4/or3 -> hit (15.2 ns after pc_f). The hot index bits select
25 tag bits x L0_ENTRIES before anything is compared, so they carry the
biggest fanout of the fetch path and sit at its start.

R11 compares every hot entry with the live block first (the compare does not
depend on the hot index), then selects one of L0_ENTRIES precomputed bits with
the hot index: the index bits drive L0_ENTRIES loads at the end of the path
instead of 25 x L0_ENTRIES at its start. Same function:
    hot_entry_hit[i] == hot_valid[i] && hot_mvalid[i] && hot_tag[i] == blk
    hot_hit = hot_entry_hit[hot_index]
            == hot_valid[hot_index] && hot_mvalid[hot_index] && hot_tag[hot_index] == blk.
The per-entry match is a (* keep *) net for Yosys/ABC only (ASIC), like R10b,
so ABC cannot fold it back into mux-then-compare; Quartus sees no attribute.

    python scripts/apply_r11.py [root]
"""
import os
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
path = os.path.join(ROOT, "hdl/cache/icache_controller.v")
s = open(path, newline="").read()
nl = "\r\n" if "\r\n" in s else "\n"
t = s.replace("\r\n", "\n")
old = ("assign hot_hit        = hot_valid[hot_index] && hot_mvalid[hot_index] &&\n"
       "                        (hot_tag[hot_index] == request_block[27:L0_IDX_BITS]);\n")
new = ("// R11 -- compare every hot entry with the live block first, then select one\n"
       "// precomputed bit with the hot index: the index bits drive L0_ENTRIES loads at\n"
       "// the end of the fetch path instead of 25 x L0_ENTRIES tag-mux loads at its\n"
       "// start. The per-entry match is kept for Yosys/ABC only (see R10 fix 2).\n"
       "`ifdef __openlane__\n"
       "`define R11_KEEP (* keep *)\n"
       "`else\n"
       "`define R11_KEEP\n"
       "`endif\n"
       "wire [L0_ENTRIES-1:0] hot_entry_hit;\n"
       "genvar hot_e;\n"
       "generate\n"
       "for(hot_e = 0; hot_e < L0_ENTRIES; hot_e = hot_e + 1) begin : g_hot_cmp\n"
       "    `R11_KEEP wire hot_entry_match = (hot_tag[hot_e] == request_block[27:L0_IDX_BITS]);\n"
       "    assign hot_entry_hit[hot_e] = hot_valid[hot_e] && hot_mvalid[hot_e] && hot_entry_match;\n"
       "end\n"
       "endgenerate\n"
       "`undef R11_KEEP\n"
       "assign hot_hit        = hot_entry_hit[hot_index];\n")
if t.count(old) != 1:
    sys.exit("[FAIL] icache_controller.v: hot_hit anchor x%d" % t.count(old))
t = t.replace(old, new)
open(path, "w", newline="").write(t.replace("\n", nl))
print("[OK] %s: R11 compare-then-select hot hit" % path)
