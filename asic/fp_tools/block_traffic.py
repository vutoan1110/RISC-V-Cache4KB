# NHAT_KY.md section 8: block-to-block wire traffic of a placed design.
# Every flop is labelled with the RTL block of its Q net name (cache tag arrays / victim buffer / rest of the
# cache, core, RAM controller, other); every other std cell takes the label of the nearest flop in the netlist
# graph (multi-source BFS over signal nets with <= 64 pins). Macros are labelled by their kind. Each net's
# HPWL is then charged to the pair (driver label -> farthest-sink label) and summed; printed for nets
# >= MIN um and for all nets, plus the centroid of each label's cells.
# Run: openroad -python -exit block_traffic.py <odb> <label> [min_um]
import collections
import re
import sys

import odb

path, label = sys.argv[1], sys.argv[2]
MIN = float(sys.argv[3]) if len(sys.argv) > 3 else 500.0
db = odb.dbDatabase.create()
odb.read_db(db, path)
block = db.getChip().getBlock()
dbu = block.getDefUnits()


def lab_of(n):
    n = n.replace("\\", "")
    for c, k in (("u_icache", "I$"), ("u_dcache", "D$")):
        if c in n:
            if re.search(r"tag_(way\d|mem)|valid_(way\d|bits)|tag_epoch", n):
                return k + ".tag"
            if re.search(r"\.vc_|victim|swap_", n):
                return k + ".vc"
            if "hot_" in n:
                return k + ".hot"
            return k + ".ctl"
    if "u_core" in n:
        return "core"
    if "u_axi_ram" in n:
        return "ram"
    return "other"


insts = list(block.getInsts())
idx = {inst.getName(): i for i, inst in enumerate(insts)}
lab = [None] * len(insts)
xy = [None] * len(insts)
frontier = collections.deque()
for i, inst in enumerate(insts):
    m = inst.getMaster()
    bb = inst.getBBox()
    xy[i] = ((bb.xMin() + bb.xMax()) / 2 / dbu, (bb.yMin() + bb.yMax()) / 2 / dbu)
    n = inst.getName()
    if m.getType() == "BLOCK":
        lab[i] = "M:" + ("RAM" if "axi_ram" in n else "I$" if "icache" in n else "D$")
    elif m.isSequential():
        for it in inst.getITerms():
            if it.isOutputSignal() and it.getNet() is not None:
                lab[i] = lab_of(it.getNet().getName())
                frontier.append(i)
                break
nets = []
for net in block.getNets():
    if net.getSigType() in ("POWER", "GROUND", "CLOCK"):
        continue
    its = list(net.getITerms())
    if len(its) < 2:
        continue
    drv, sinks = None, []
    for it in its:
        i = idx[it.getInst().getName()]
        if it.isOutputSignal():
            drv = i
        else:
            sinks.append(i)
    nets.append((drv, sinks, len(its)))
adj = [[] for _ in insts]
for k, (d, s, n) in enumerate(nets):
    if n > 64:
        continue
    for i in ([d] if d is not None else []) + s:
        adj[i].append(k)
while frontier:
    i = frontier.popleft()
    for k in adj[i]:
        d, s, _ = nets[k]
        for j in ([d] if d is not None else []) + s:
            if lab[j] is None:
                lab[j] = lab[i]
                frontier.append(j)
tr_long = collections.Counter()
tr_all = collections.Counter()
for d, s, _ in nets:
    if d is None or not s:
        continue
    pts = [xy[d]] + [xy[j] for j in s]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    h = (max(xs) - min(xs)) + (max(ys) - min(ys))
    far = max(s, key=lambda j: abs(xy[j][0] - xy[d][0]) + abs(xy[j][1] - xy[d][1]))
    key = "%s -> %s" % (lab[d] or "?", lab[far] or "?")
    tr_all[key] += h
    if h >= MIN:
        tr_long[key] += h
tl = sum(tr_long.values())
print("%s: nets >= %.0f um: %.3f m; all nets %.3f m" % (label, MIN, tl / 1e6, sum(tr_all.values()) / 1e6))
for k, v in tr_long.most_common(16):
    print("   %5.1f %%  %6.0f mm (all lengths %6.0f mm)  %s" % (100 * v / tl, v / 1e3, tr_all[k] / 1e3, k))
cent = collections.defaultdict(lambda: [0.0, 0.0, 0])
for i, l in enumerate(lab):
    if l and not l.startswith("M:"):
        c = cent[l]
        c[0] += xy[i][0]
        c[1] += xy[i][1]
        c[2] += 1
print("   centroids: " + ", ".join("%s (%.0f,%.0f) n=%d" % (l, c[0] / c[2], c[1] / c[2], c[2])
                                    for l, c in sorted(cent.items())))
