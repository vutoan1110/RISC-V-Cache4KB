"""Name-only fix-up for the SoC-level R16 checks (called from the .ys through Yosys `exec`).

R15 added a generate branch (CACHE_CONFIG >= 4 -> g_nway) in front of g_dse in icache.v / dcache.v. Yosys then
names the DSE core's flattened objects u_soc.u_icache.genblk1.g_dse.* where the R14 gold has
u_soc.u_icache.g_dse.*, so equiv_make pairs none of the cache registers and the induction cannot close
(2026-10-06: 209 unproven output cells, the run was stopped). This rewrites the gate's RTLIL text
"genblk1.g_dse" -> "g_dse": object names only, no cell, connection or parameter changes. It refuses to run if
the input already holds a name that the rewrite would produce (a collision), or if it finds nothing to rewrite.

    python3 rename_genblk.py <in.il> <out.il>
"""
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
txt = open(src, encoding="utf-8").read()
n = txt.count("genblk1.g_dse")
if n == 0:
    sys.exit("rename_genblk: no 'genblk1.g_dse' in %s" % src)
# collision: any object path containing ".g_dse." / "\g_dse." that is not preceded by "genblk1"
clash = re.findall(r"(?<!genblk1)[.\\]g_dse\.", txt)
if clash:
    sys.exit("rename_genblk: %d names already use g_dse outside genblk1 -- rename would collide" % len(clash))
open(dst, "w", encoding="utf-8").write(txt.replace("genblk1.g_dse", "g_dse"))
print("rename_genblk: %d occurrences of genblk1.g_dse -> g_dse (%s -> %s)" % (n, src, dst))
