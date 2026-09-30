"""FLOW_JOURNAL Incident 86, SEC: wrappers gold_w / gate_w with the top-level ports of the cut
design. The only logic they add is identical on both sides: reset_n is forced low in the first
cycle (`seen` starts at 0), so gold and gate both leave cycle 0 in their reset state. Every
other flop starts at 0 (setundef -zero -init in the miter script) on both sides.

usage: python3 make_wrap.py design_cut.il wrap.v
"""
import sys

ports = []
in_top = False
for l in open(sys.argv[1]):
    l = l.rstrip("\n")
    if l == "module \\soc_asic_top":
        in_top = True
    elif in_top and l == "end":
        break
    elif in_top and l.startswith("  wire ") and (" input " in l or " output " in l):
        p = l.split()
        w = int(p[p.index("width") + 1]) if "width" in p else 1
        d = "input" if "input" in p else "output"
        ports.append((int(p[p.index(d) + 1]), d, w, p[-1].lstrip("\\")))
ports.sort()
assert any(n == "reset_n" and d == "input" for _, d, _, n in ports)
assert any(n == "clk" and d == "input" for _, d, _, n in ports)

out = []
for side in ("gold", "gate"):
    decl = ",\n".join("    %s %s%s" % (d, "" if w == 1 else "[%d:0] " % (w - 1), n) for _, d, w, n in ports)
    conn = ",\n".join("        .%s(%s)" % (n, "reset_n & seen" if n == "reset_n" else n) for _, _, _, n in ports)
    out.append("module %s_w (\n%s\n);\n    reg seen = 1'b0;\n    always @(posedge clk) seen <= 1'b1;\n"
               "    %s u (\n%s\n    );\nendmodule\n" % (side, decl, side, conn))
open(sys.argv[2], "w", newline="\n").write("\n".join(out))
print("%d ports; wrappers written to %s" % (len(ports), sys.argv[2]))
