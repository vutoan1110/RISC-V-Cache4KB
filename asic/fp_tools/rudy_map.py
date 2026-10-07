# RUDY wire-demand map of a placed ODB (NHAT_KY.md section 8: where do SA2 / DM_VC4 congest?).
# Each net spreads its HPWL uniformly over its bounding box (width/height floored at one tile), summed on a
# TILE-um grid; demand density = um of wire per um^2. Prints the grid as a coarse ASCII heat map (macros as #),
# the hottest tiles, and how much demand falls inside channels between macros vs open core.
# Run: openroad -python -exit rudy_map.py <odb> <label> [tile_um]
import sys

import odb

path, label = sys.argv[1], sys.argv[2]
TILE = float(sys.argv[3]) if len(sys.argv) > 3 else 100.0
db = odb.dbDatabase.create()
odb.read_db(db, path)
block = db.getChip().getBlock()
dbu = block.getDefUnits()
die = block.getDieArea()
W, H = die.xMax() / dbu, die.yMax() / dbu
nx, ny = int(W // TILE) + 1, int(H // TILE) + 1
grid = [[0.0] * nx for _ in range(ny)]
macro = [[False] * nx for _ in range(ny)]
for inst in block.getInsts():
    if inst.getMaster().getType() == "BLOCK":
        bb = inst.getBBox()
        for j in range(int(bb.yMin() / dbu // TILE), int(bb.yMax() / dbu // TILE) + 1):
            for i in range(int(bb.xMin() / dbu // TILE), int(bb.xMax() / dbu // TILE) + 1):
                if 0 <= i < nx and 0 <= j < ny:
                    macro[j][i] = True
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
    w, h = max(x1 - x0, TILE), max(y1 - y0, TILE)
    hp = (x1 - x0) + (y1 - y0)
    dens = hp / (w * h)          # um of wire per um^2 over the bbox
    i0, i1 = int(x0 // TILE), int((x0 + w) // TILE)
    j0, j1 = int(y0 // TILE), int((y0 + h) // TILE)
    for j in range(max(j0, 0), min(j1, ny - 1) + 1):
        for i in range(max(i0, 0), min(i1, nx - 1) + 1):
            grid[j][i] += dens * TILE * TILE
vals = [grid[j][i] / (TILE * TILE) for j in range(ny) for i in range(nx) if not macro[j][i]]
vals.sort()
p50, p95, p99, mx = vals[len(vals) // 2], vals[int(len(vals) * 0.95)], vals[int(len(vals) * 0.99)], vals[-1]
print("%s: tile %.0f um, %dx%d; demand um/um2 over non-macro tiles: median %.3f p95 %.3f p99 %.3f max %.3f"
      % (label, TILE, nx, ny, p50, p95, p99, mx))
ref = float(sys.argv[4]) if len(sys.argv) > 4 else p99
print("ASCII map (top = high y): '#' macro, ' ' < 25 %% of %.3f, '.' < 50 %%, ':' < 75 %%, '*' < 100 %%, '@' >= 100 %%" % ref)
for j in range(ny - 1, -1, -1):
    row = ""
    for i in range(nx):
        if macro[j][i]:
            row += "#"
            continue
        r = grid[j][i] / (TILE * TILE) / ref
        row += " " if r < 0.25 else "." if r < 0.5 else ":" if r < 0.75 else "*" if r < 1.0 else "@"
    print("  |" + row + "|")
hot = sorted(((grid[j][i] / (TILE * TILE), i, j) for j in range(ny) for i in range(nx) if not macro[j][i]),
             reverse=True)[:8]
print("hottest tiles (x0,y0 um: demand):", ", ".join("(%.0f,%.0f: %.3f)" % (i * TILE, j * TILE, v) for v, i, j in hot))
