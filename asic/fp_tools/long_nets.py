# FLOW_JOURNAL Incident 96: who owns the 500+ um std-cell nets? Each long net is attributed to the RTL name of
# the first named flop it touches (driver or sink, via that flop's Q net), or to its own name when it has one;
# grouped at DEPTH hierarchy levels with array indices folded.
# Run: openroad -python -exit long_nets.py <odb> <label> [min_um]
import collections
import re
import sys

import odb

path, label = sys.argv[1], sys.argv[2]
MIN = float(sys.argv[3]) if len(sys.argv) > 3 else 500.0
DEPTH = 6
db = odb.dbDatabase.create()
odb.read_db(db, path)
block = db.getChip().getBlock()
dbu = block.getDefUnits()


def grp(n):
    n = n.replace("\\", "")
    if re.match(r"^(_\d+_|net\d+|clknet.*|split\d+|rebuffer\d+|wire\d+|max_cap\d+|fanout\d+|max_length\d+)$", n):
        return None
    n = re.sub(r"\[\d+\]", "[*]", n)
    return ".".join(n.split(".")[:DEPTH])


qname = {}
for inst in block.getInsts():
    if inst.getMaster().isSequential():
        for it in inst.getITerms():
            if it.isOutputSignal() and it.getNet() is not None:
                qname[inst.getName()] = grp(it.getNet().getName())
                break
own = collections.Counter()
cnt = collections.Counter()
for net in block.getNets():
    if net.getSigType() in ("POWER", "GROUND", "CLOCK"):
        continue
    xs, ys, g = [], [], grp(net.getName())
    macro = False
    for it in net.getITerms():
        ok, x, y = it.getAvgXY()
        if ok:
            xs.append(x / dbu)
            ys.append(y / dbu)
        inst = it.getInst()
        if inst.getMaster().getType() == "BLOCK":
            macro = True
        if g is None and inst.getName() in qname and qname[inst.getName()]:
            g = "FF " + qname[inst.getName()]
    if len(xs) < 2 or macro:
        continue
    h = (max(xs) - min(xs)) + (max(ys) - min(ys))
    if h < MIN:
        continue
    g = g or "<unattributed>"
    own[g] += h
    cnt[g] += 1
t = sum(own.values())
print("%s: std-only nets >= %.0f um: %.3f m in %d nets" % (label, MIN, t / 1e6, sum(cnt.values())))
for g, v in own.most_common(18):
    print("   %6.1f %%  %7.0f mm  %5d nets  %s" % (100 * v / t, v / 1e3, cnt[g], g))
