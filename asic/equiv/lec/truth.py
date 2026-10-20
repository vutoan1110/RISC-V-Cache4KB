"""FLOW_JOURNAL Incident 89: exhaustive truth table of one output over its (small) structural
support, gold vs gate.  usage: python truth.py gold.aig gate.aig pairs.json out_name"""
import itertools
import json
import sys

exec(open(__file__.replace("truth.py", "aigsim.py")).read().split("g_path, t_path = sys.argv")[0])
exec(open(__file__.replace("truth.py", "support.py")).read().split("g, t, pj = sys.argv[1:4]")[0].split("exec(open")[0])
g, t, pj, name = sys.argv[1:5]
P = json.load(open(pj))


def label(n):
    if n.startswith("lec_q_p"):
        i, j = P["pairs"][int(n[7:])]
        return (P["gold"][i]["names"] or ["?"])[0]
    return n


def cone(path):
    I, outs, ands, ins, onames = read_aig(path)
    oidx = {v: k for k, v in onames.items()}
    lit = outs[oidx[name]]
    seen, stack, sup = set(), [lit >> 1], set()
    while stack:
        v = stack.pop()
        if v in seen or v == 0:
            continue
        seen.add(v)
        if v <= I:
            sup.add(v - 1)
        else:
            a, b = ands[v - I - 1]
            stack += [a >> 1, b >> 1]
    return I, outs, ands, ins, oidx, sup


gI, gO, gA, gin, goi, gs = cone(g)
tI, tO, tA, tin, toi, ts = cone(t)
sup = sorted(gs | ts)
names = [gin.get(k, "pi%d" % k) for k in sup]
print("support:", [label(n) for n in names])
n = len(sup)
mask = (1 << (1 << n)) - 1
pis_g = [0] * gI
for b, k in enumerate(sup):
    v = 0
    for r in range(1 << n):
        if (r >> b) & 1:
            v |= 1 << r
    pis_g[k] = v
og = simulate(gI, gO, gA, pis_g, mask)[goi[name]]
ot = simulate(tI, tO, tA, pis_g, mask)[toi[name]]
print("row  " + " ".join("%s" % label(x)[-18:] for x in names) + "  gold gate")
for r in range(1 << n):
    a, b = (og >> r) & 1, (ot >> r) & 1
    if a != b:
        print("%3d  " % r + " ".join("%18d" % ((r >> i) & 1) for i in range(n)) + "   %d    %d  <-- DIFF" % (a, b))
print("differing rows: %d of %d" % (bin(og ^ ot).count("1"), 1 << n))
