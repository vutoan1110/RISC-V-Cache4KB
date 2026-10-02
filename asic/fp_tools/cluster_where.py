# FLOW_JOURNAL Incident 96: where do the big flop arrays sit, and how dense is the placement around them?
# For every flop whose Q net name matches one of the patterns: centroid, 10-90 % x/y range; then the
# std-cell utilisation of the box spanning that range and of the 150 um tiles inside it (max / mean).
# Run: openroad -python -exit cluster_where.py <odb> <label> <regex> [<regex> ...]
import re
import sys

import odb

path, label = sys.argv[1], sys.argv[2]
pats = sys.argv[3:]
db = odb.dbDatabase.create()
odb.read_db(db, path)
block = db.getChip().getBlock()
dbu = block.getDefUnits()
T = 150.0
cells = []
pos = {p: [] for p in pats}
for inst in block.getInsts():
    m = inst.getMaster()
    if m.getType() == "BLOCK":
        continue
    x, y = inst.getLocation()
    x, y = x / dbu, y / dbu
    a = m.getWidth() * m.getHeight() / dbu / dbu
    cells.append((x, y, a))
    if m.isSequential():
        for it in inst.getITerms():
            if it.isOutputSignal() and it.getNet() is not None:
                n = it.getNet().getName().replace("\\", "")
                for p in pats:
                    if re.search(p, n):
                        pos[p].append((x, y))
                break
tiles = {}
for x, y, a in cells:
    k = (int(x // T), int(y // T))
    tiles[k] = tiles.get(k, 0.0) + a
for p in pats:
    v = pos[p]
    if not v:
        print("%s %s: no flops" % (label, p))
        continue
    xs = sorted(q[0] for q in v)
    ys = sorted(q[1] for q in v)
    n = len(v)
    x0, x1 = xs[n // 10], xs[(9 * n) // 10]
    y0, y1 = ys[n // 10], ys[(9 * n) // 10]
    cx, cy = sum(xs) / n, sum(ys) / n
    ks = [(i, j) for i in range(int(x0 // T), int(x1 // T) + 1) for j in range(int(y0 // T), int(y1 // T) + 1)]
    us = [tiles.get(k, 0.0) / (T * T) for k in ks]
    print("%s %-45s %5d flops centroid (%6.0f,%6.0f) 10-90%% x %6.0f..%6.0f y %6.0f..%6.0f (%4.0f x %4.0f um) "
          "tile util mean %4.1f %% max %4.1f %%" % (label, p, n, cx, cy, x0, x1, y0, y1, x1 - x0, y1 - y0,
                                                    100 * sum(us) / len(us), 100 * max(us)))
