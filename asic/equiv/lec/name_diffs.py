"""FLOW_JOURNAL Incident 89: map aigsim DIFF lines (lec_d_pNNNNN outputs) back to RTL register names
and group them.  usage: python name_diffs.py sim.txt pairs.json"""
import json
import re
import sys
from collections import Counter

P = json.load(open(sys.argv[2]))
c = Counter()
other = []
for line in open(sys.argv[1]):
    if not line.startswith("DIFF"):
        continue
    _, k, name = line.split()
    if name.startswith("lec_d_p"):
        i, j = P["pairs"][int(name[7:])]
        nm = (P["gold"][i]["names"] or ["?"])[0]
        c[re.sub(r" ?\[\d+\]", "[]", nm)] += 1
    else:
        other.append(name)
for k, v in c.most_common():
    print("%5d  %s" % (v, k))
print("non-register outputs:", len(other), other[:20])
