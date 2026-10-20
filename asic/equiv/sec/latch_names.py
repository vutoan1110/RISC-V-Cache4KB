"""FLOW_JOURNAL Incident 86: list the latches left in an AIGER file (symbol table), grouped by
side (gold/gate) and by RTL signal name, to see which register pairs signal correspondence
could not merge.  usage: python latch_names.py reduced.aig"""
import re
import sys
from collections import Counter

data = open(sys.argv[1], "rb").read()
# the symbol table follows the binary section: lines "l<idx> <name>" (also i/o), then "c" comment
names = []
for line in data.split(b"\n"):
    if line[:1] == b"l" and b" " in line:
        head, _, name = line.partition(b" ")
        if head[1:].isdigit():
            names.append(name.decode("latin1"))
print("latches with symbols:", len(names))
side = Counter()
groups = Counter()
for n in names:
    s = "gold" if "gold" in n.split(".")[0] else ("gate" if "gate" in n.split(".")[0] else "other")
    side[s] += 1
    key = re.sub(r"\[\d+\]", "[]", n)
    key = re.sub(r"\$\d+", "$N", key)
    groups[(s, key[:110])] += 1
print(dict(side))
for (s, k), c in groups.most_common(70):
    print("%6d  %-5s %s" % (c, s, k))
