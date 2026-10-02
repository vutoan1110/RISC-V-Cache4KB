# FLOW_JOURNAL Incident 96: which logic sits in a congested region of a placed ODB?
# Counts the instances whose origin lies in each given box, grouped by hierarchical prefix of the instance
# name (first DEPTH dot-separated levels; ABC's anonymous cells "_123_" are grouped as <anon>), and the
# share of the region's std-cell area per group. Also prints, for the whole die, where the named flops of
# a few groups sit (bounding box + centroid).
# Run: openroad -python -exit region_cells.py <odb> <label> x0,y0,x1,y1 [x0,y0,x1,y1 ...]
import collections
import re
import sys

import odb

path, label = sys.argv[1], sys.argv[2]
boxes = [tuple(float(v) for v in b.split(",")) for b in sys.argv[3:]]
DEPTH = int(__import__('os').environ.get('DEPTH', '6'))
db = odb.dbDatabase.create()
odb.read_db(db, path)
block = db.getChip().getBlock()
dbu = block.getDefUnits()


def group(name):
    n = name.replace("\\", "")
    if re.match(r"^_\d+_$", n) or n.startswith("ANTENNA") or n.startswith("PHY_") or n.startswith("TAP_"):
        return "<anon/phys>"
    if n.startswith("FILLER") or n.startswith("clkbuf") or n.startswith("clkload") or n.startswith("delaybuf"):
        return "<clock/fill>"
    if n.startswith("rebuffer") or n.startswith("split") or n.startswith("wire") or n.startswith("max_cap") \
            or n.startswith("max_length") or n.startswith("hold") or n.startswith("input") or n.startswith("output"):
        return "<repair buf>"
    parts = re.split(r"\.", n)
    g = ".".join(parts[:DEPTH])
    g = re.sub(r"\[\d+\]", "[*]", g)
    return g


stats = [collections.Counter() for _ in boxes]
area = [collections.Counter() for _ in boxes]
tot_area = [0.0 for _ in boxes]
where = collections.defaultdict(list)
for inst in block.getInsts():
    m = inst.getMaster()
    if m.getType() == "BLOCK":
        continue
    x, y = inst.getLocation()
    x, y = x / dbu, y / dbu
    g = group(inst.getName())
    if g == "<anon/phys>" and m.isSequential():
        for it in inst.getITerms():
            if it.isOutputSignal() and it.getNet() is not None:
                g = "FF " + group(it.getNet().getName())
                break
    elif g == "<anon/phys>":
        for it in inst.getITerms():
            if it.isOutputSignal() and it.getNet() is not None:
                nn = group(it.getNet().getName())
                if not nn.startswith("<"):
                    g = "C " + nn
                break
    a = m.getWidth() * m.getHeight() / dbu / dbu
    if m.isSequential() if hasattr(m, "isSequential") else False:
        where[g].append((x, y))
    for k, (x0, y0, x1, y1) in enumerate(boxes):
        if x0 <= x < x1 and y0 <= y < y1:
            stats[k][g] += 1
            area[k][g] += a
            tot_area[k] += a
for k, b in enumerate(boxes):
    print("%s box %s: %d cells, %.0f um2 std-cell area (%.1f %% of the box)" % (
        label, b, sum(stats[k].values()), tot_area[k], 100 * tot_area[k] / ((b[2] - b[0]) * (b[3] - b[1]))))
    for g, a in area[k].most_common(22):
        print("   %6.1f %%  %6d cells  %s" % (100 * a / tot_area[k], stats[k][g], g))
