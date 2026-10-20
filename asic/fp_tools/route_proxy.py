# NHAT_KY.md section 8: cheap routability proxies of a placed ODB, to rank floorplan / placement variants
# before paying for global routing. Per TILE x TILE um tile outside macros:
#   util  = std-cell area / tile area (tap + fill cells excluded)
#   pins  = signal pins of std cells per 100 um2 (local pin-access pressure: li1/met1 overflow)
#   rudy  = um of wire per um2 (each net's HPWL spread over its bbox, as rudy_map.py)
# Prints p95 / p99 / max of each, the number of tiles above fixed thresholds, and the total HPWL.
# Run: openroad -python -exit route_proxy.py <odb> <label> [tile_um]
import sys

import odb

path, label = sys.argv[1], sys.argv[2]
T = float(sys.argv[3]) if len(sys.argv) > 3 else 150.0
db = odb.dbDatabase.create()
odb.read_db(db, path)
block = db.getChip().getBlock()
dbu = block.getDefUnits()
die = block.getDieArea()
W, H = die.xMax() / dbu, die.yMax() / dbu
nx, ny = int(W // T) + 1, int(H // T) + 1
util = [[0.0] * nx for _ in range(ny)]
pins = [[0] * nx for _ in range(ny)]
rudy = [[0.0] * nx for _ in range(ny)]
blocked = [[0.0] * nx for _ in range(ny)]
for inst in block.getInsts():
    m = inst.getMaster()
    bb = inst.getBBox()
    if m.getType() == "BLOCK":
        x0, y0, x1, y1 = bb.xMin() / dbu, bb.yMin() / dbu, bb.xMax() / dbu, bb.yMax() / dbu
        for j in range(int(y0 // T), int(y1 // T) + 1):
            for i in range(int(x0 // T), int(x1 // T) + 1):
                if 0 <= i < nx and 0 <= j < ny:
                    ox = max(0.0, min(x1, (i + 1) * T) - max(x0, i * T))
                    oy = max(0.0, min(y1, (j + 1) * T) - max(y0, j * T))
                    blocked[j][i] += ox * oy
        continue
    name = m.getName()
    if "tapvpwrvgnd" in name or "fill" in name or "decap" in name:
        continue
    x, y = (bb.xMin() + bb.xMax()) / 2 / dbu, (bb.yMin() + bb.yMax()) / 2 / dbu
    i, j = int(x // T), int(y // T)
    util[j][i] += m.getWidth() * m.getHeight() / dbu / dbu
    for it in inst.getITerms():
        if it.getNet() is not None and it.getNet().getSigType() not in ("POWER", "GROUND"):
            pins[j][i] += 1
hpwl = 0.0
for net in block.getNets():
    if net.getSigType() in ("POWER", "GROUND"):
        continue
    xs, ys = [], []
    for it in net.getITerms():
        ok, x, y = it.getAvgXY()
        if ok:
            xs.append(x / dbu)
            ys.append(y / dbu)
    if len(xs) < 2:
        continue
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    hpwl += (x1 - x0) + (y1 - y0)
    w, h = max(x1 - x0, T), max(y1 - y0, T)
    dens = ((x1 - x0) + (y1 - y0)) / (w * h)
    for j in range(max(int(y0 // T), 0), min(int((y0 + h) // T), ny - 1) + 1):
        for i in range(max(int(x0 // T), 0), min(int((x0 + w) // T), nx - 1) + 1):
            rudy[j][i] += dens * T * T
U, P, R = [], [], []
for j in range(ny):
    for i in range(nx):
        free = T * T - blocked[j][i]
        if free < 0.5 * T * T:      # mostly macro: skip
            continue
        U.append(util[j][i] / free)
        P.append(100.0 * pins[j][i] / free)
        R.append(rudy[j][i] / (T * T))


def q(v, f):
    v = sorted(v)
    return v[min(len(v) - 1, int(f * len(v)))]


print("%-28s tiles %4d  util p95 %5.1f%% p99 %5.1f%% max %5.1f%% (>60%%: %3d)  pins/100um2 p99 %5.2f max %5.2f "
      "(>10: %3d)  rudy p99 %6.3f max %6.3f (>12: %3d)  HPWL %.3f m" % (
          label, len(U), 100 * q(U, .95), 100 * q(U, .99), 100 * max(U), sum(1 for u in U if u > 0.6),
          q(P, .99), max(P), sum(1 for p in P if p > 10), q(R, .99), max(R), sum(1 for r in R if r > 12), hpwl / 1e6))
