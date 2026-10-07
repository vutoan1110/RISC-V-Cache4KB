#!/usr/bin/env python3
"""R10 fix 1 (NHAT_KY.md 2026-09-26): the R10a CHECKER (simulation only) took
the line index of hot entry e as hot_tag[e][INDEX_WIDTH-L0B-1:0] ++ e. With
INDEX_WIDTH == L0B (8-line caches in tb_cache_event_accounting and three SoC
testbenches) that part-select is [-1:0] and Questa's vopt refused the design,
which aborted the directed regression after 54 tests. The controller itself
already handles that case (generate g_hot_li_none). The checker now rebuilds
the entry's 28-bit block address {hot_tag[e], e} and takes its low INDEX_WIDTH
bits, which is valid for every INDEX_WIDTH >= L0B. Design logic: untouched
(the block is inside `ifndef __openlane__` + translate_off).

    python scripts/apply_r10_fix1.py [root]
"""
import os
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
path = os.path.join(ROOT, "hdl/cache/icache.v")
s = open(path, newline="").read()
old = """    integer r10_e;
    reg     r10_inv_ok;
    always @(*) begin
        r10_inv_ok = 1'b1;
        for(r10_e = 0; r10_e < L0_ENTRIES; r10_e = r10_e + 1)
            if(u_controller.hot_mvalid[r10_e] !==
               u_tag_ram.valid_bits[{u_controller.hot_tag[r10_e][INDEX_WIDTH-R10_L0B-1:0],
                                     r10_e[R10_L0B-1:0]}])
                r10_inv_ok = 1'b0;
    end
"""
new = """    integer    r10_e;
    reg        r10_inv_ok;
    reg [27:0] r10_blk;   // block address held by hot entry r10_e
    always @(*) begin
        r10_inv_ok = 1'b1;
        r10_blk    = 28'd0;
        for(r10_e = 0; r10_e < L0_ENTRIES; r10_e = r10_e + 1) begin
            r10_blk = {u_controller.hot_tag[r10_e], r10_e[R10_L0B-1:0]};
            if(u_controller.hot_mvalid[r10_e] !== u_tag_ram.valid_bits[r10_blk[INDEX_WIDTH-1:0]])
                r10_inv_ok = 1'b0;
        end
    end
"""
if "\r\n" in s:
    sys.exit("[FAIL] icache.v is CRLF; fix expects LF")
if s.count(old) != 1:
    sys.exit("[FAIL] icache.v: checker anchor x%d" % s.count(old))
s = s.replace(old, new)
open(path, "w", newline="").write(s)
print("[OK] %s: R10a checker line index rebuilt from the block address" % path)
