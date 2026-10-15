"""Cell composition of a die box from a DEF (read-only).
usage: python region_cells.py <def> x0 y0 x1 y1        (um)
Counts the placed instances in the box (fill / decap / tap excluded) by cell family, by resizer-inserted name prefix
(fanout, max_cap, wire, hold, clock buffers, antenna diodes) and flops by name prefix."""
import sys, re, collections
deff = sys.argv[1]
x0, y0, x1, y1 = (float(v) for v in sys.argv[2:6])
cnt, fam, hier, n_all = collections.Counter(), collections.Counter(), collections.Counter(), 0
sect = None
with open(deff) as f:
    for ln in f:
        s = ln.strip()
        if s.startswith("COMPONENTS"):
            sect = "C"; continue
        if s.startswith("END COMPONENTS"):
            break
        if sect == "C" and s.startswith("- "):
            m = re.match(r"- (\S+) (\S+) .*?(?:PLACED|FIXED) \( (-?\d+) (-?\d+) \)", s)
            if not m:
                continue
            x, y = int(m.group(3)) / 1000, int(m.group(4)) / 1000
            if not (x0 <= x < x1 and y0 <= y < y1):
                continue
            inst, cell = m.group(1), m.group(2)
            c = cell.replace("sky130_fd_sc_hd__", "")
            if c.startswith(("fill", "decap", "tap")):
                continue
            n_all += 1
            fam[re.sub(r"_\d+$", "", c)] += 1
            if c.startswith(("df", "edf", "sdf")):
                name = inst.replace("\\", "")
                parts = re.split(r"[./]", name)
                hier[".".join(parts[:4])] += 1
            if inst.startswith(("wire", "max_cap", "fanout", "split", "hold", "rebuffer", "clkbuf", "clkload", "ANTENNA", "input", "output")):
                cnt[re.match(r"[A-Za-z_]+", inst).group(0)] += 1
print("instances (no fill/decap/tap): %d in %.0f x %.0f um" % (n_all, x1 - x0, y1 - y0))
print("by family:", fam.most_common(14))
print("inserted-cell prefixes:", cnt.most_common(10))
print("flops by hierarchy prefix:", hier.most_common(14))
