"""FLOW_JOURNAL Incident 89: list the outputs of a (reduced) miter AIG that are not literal 0, i.e.
not proved, with their names (taken from the named LEC AIG with the same output order) grouped by
RTL register.  usage: python open_outputs.py reduced.aig named.aig pairs.json [--list]"""
import json
import re
import sys
from collections import Counter

red, named, pj = sys.argv[1:4]
P = json.load(open(pj))
d = open(red, "rb").read()
nl = d.index(b"\n")
M, I, L, O, A = map(int, d[:nl].split()[1:6])
pos = nl + 1
lits = []
for _ in range(O):
    e = d.index(b"\n", pos)
    lits.append(int(d[pos:e]))
    pos = e + 1
exec(open(__file__.replace("open_outputs.py", "aig_syms.py")).read().split("ai, ao = syms")[0])
_, onames = syms(named)
assert len(onames) == O, (len(onames), O)
open_ = [k for k, l in enumerate(lits) if l != 0]
c = Counter()
for k in open_:
    n = onames[k]
    if n.startswith("lec_d_p"):
        i, j = P["pairs"][int(n[7:])]
        n = (P["gold"][i]["names"] or ["?"])[0]
    elif n.startswith("lec_d_x"):
        n = "dup-check " + (P["gold"][P["gold_only"][int(n[7:])]]["names"] or ["?"])[0]
    c[re.sub(r" ?\[\d+\]", "[]", n)] += 1
    if "--list" in sys.argv:
        print("OPEN %d %s %s" % (k, onames[k], n))
print("outputs %d, open (not proved) %d" % (O, len(open_)))
for k, v in c.most_common():
    print("%5d  %s" % (v, k))
