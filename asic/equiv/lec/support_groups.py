"""FLOW_JOURNAL Incident 89: input support of one output, grouped by RTL register name.
usage: python support_groups.py x.aig pairs.json out_name"""
import json
import re
import sys
from collections import Counter

exec(open(__file__.replace("support_groups.py", "aigsim.py")).read().split("g_path, t_path = sys.argv")[0])
path, pj, name = sys.argv[1:4]
P = json.load(open(pj))
I, outs, ands, ins, onames = read_aig(path)
oidx = {v: k for k, v in onames.items()}
seen, stack, sup = set(), [outs[oidx[name]] >> 1], set()
while stack:
    v = stack.pop()
    if v in seen or v == 0:
        continue
    seen.add(v)
    if v <= I:
        sup.add(ins.get(v - 1, "pi%d" % (v - 1)))
    else:
        a, b = ands[v - I - 1]
        stack += [a >> 1, b >> 1]
c = Counter()
for n in sup:
    if n.startswith("lec_q_p"):
        i, j = P["pairs"][int(n[7:])]
        n = (P["gold"][i]["names"] or ["?"])[0]
    c[re.sub(r" ?\[\d+\]", "[]", n)] += 1
print("%s: %d inputs, %d AND nodes in cone" % (name, len(sup), len([v for v in seen if v > I])))
for k, v in c.most_common():
    print("%5d  %s" % (v, k))
