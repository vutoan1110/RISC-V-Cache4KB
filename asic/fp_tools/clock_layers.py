"""Per-layer length of long guide boxes (> 2 gcells: routing segments, not pin access) of non-leaf clock nets.
usage: python clock_layers.py <guide> [prefix=clknet_]"""
import sys, collections
g = sys.argv[1]; pref = sys.argv[2] if len(sys.argv) > 2 else "clknet_"
tot = collections.Counter(); cur = None; nets = set()
for ln in open(g):
    p = ln.split()
    if len(p) == 1 and p[0] not in "()":
        cur = p[0] if (p[0].startswith(pref) and "leaf" not in p[0]) else None
        if cur: nets.add(cur)
        continue
    if cur and len(p) == 5:
        x1, y1, x2, y2 = (int(v) / 1000 for v in p[:4])
        L = max(x2 - x1, y2 - y1)
        if L > 14: tot[p[4]] += L
print(f"{len(nets)} non-leaf '{pref}' nets; long-segment length by layer (um): " + ", ".join(f"{l} {tot[l]:.0f}" for l in ("met1", "met2", "met3", "met4", "met5")))
