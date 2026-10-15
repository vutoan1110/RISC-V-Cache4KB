"""Per-gcell routing demand from OpenROAD global-route guides (read-only analysis).
usage: python guide_demand.py <guide> [<guide2>]  -> prints the hottest windows (and the difference guide2 - guide).
A guide rectangle longer than one gcell along the layer's preferred direction counts one track in every gcell it covers;
pin-access patches are not counted. Load = demand / nominal tracks per gcell (gcell 6.9 um; GRT adjustment and the power
grid not subtracted), summed over met1-met4 in 8 x 8 gcell windows (55 um), so 256 = every nominal track in use."""
import sys, collections
G = 6900          # gcell size in DBU (6.9 um, from the guide grid)
PREF = {"met1": "H", "met2": "V", "met3": "H", "met4": "V", "met5": "H"}
CAP = {"met1": 6.9 / 0.34, "met2": 6.9 / 0.46, "met3": 6.9 / 0.68, "met4": 6.9 / 0.92, "met5": 6.9 / 3.4}


def load(path):
    dem = {l: collections.Counter() for l in PREF}
    netlen = collections.Counter()
    net = None
    with open(path) as f:
        for ln in f:
            s = ln.split()
            if len(s) == 1 and s[0] not in "()":
                net = s[0]
            elif len(s) == 5 and s[4] in PREF:
                x1, y1, x2, y2 = (int(v) // G for v in s[:4])
                x2 = (int(s[2]) - 1) // G
                y2 = (int(s[3]) - 1) // G
                l = s[4]
                if PREF[l] == "H":
                    if x2 > x1:
                        for y in range(y1, y2 + 1):
                            for x in range(x1, x2 + 1):
                                dem[l][(x, y)] += 1
                        netlen[net] += (x2 - x1) * (y2 - y1 + 1)
                else:
                    if y2 > y1:
                        for x in range(x1, x2 + 1):
                            for y in range(y1, y2 + 1):
                                dem[l][(x, y)] += 1
                        netlen[net] += (y2 - y1) * (x2 - x1 + 1)
    return dem, netlen


def windows(dem, w=8):
    """Sum of demand/capacity over all layers met1-met4, in w x w gcell windows (55 um)."""
    acc = collections.Counter()
    for l in ("met1", "met2", "met3", "met4"):
        for (x, y), d in dem[l].items():
            acc[(x // w, y // w)] += d / CAP[l]
    return acc


a, na = load(sys.argv[1])
wa = windows(a)
print("total demand (tracks*gcells) per layer:", {l: sum(a[l].values()) for l in PREF})
print("hottest 55-um windows (x0,y0 um): load")
for (wx, wy), v in wa.most_common(12):
    print("  (%5.0f,%5.0f) %.1f" % (wx * 8 * 6.9, wy * 8 * 6.9, v))
if len(sys.argv) > 2:
    b, nb = load(sys.argv[2])
    wb = windows(b)
    print("total demand per layer (2nd):", {l: sum(b[l].values()) for l in PREF})
    diff = collections.Counter({k: wb[k] - wa.get(k, 0) for k in wb})
    print("largest demand increase, 55-um windows (x0,y0 um): +delta (before -> after)")
    for (wx, wy), v in diff.most_common(15):
        print("  (%5.0f,%5.0f) +%.1f (%.1f -> %.1f)" % (wx * 8 * 6.9, wy * 8 * 6.9, v, wa.get((wx, wy), 0), wb[(wx, wy)]))
    # coarse 10 x 10 picture of the increase (each cell = die/10)
    mx = max(k[0] for k in wb) + 1
    my = max(k[1] for k in wb) + 1
    grid = [[0.0] * 10 for _ in range(10)]
    for (wx, wy), v in diff.items():
        grid[min(9, wy * 10 // my)][min(9, wx * 10 // mx)] += v
    print("demand increase by die tenth (top row = top of die):")
    for r in reversed(grid):
        print("  " + " ".join("%6.0f" % v for v in r))
    grown = collections.Counter({n: nb[n] - na.get(n, 0) for n in nb})
    print("nets with the largest guide growth:", grown.most_common(12))
    new = [n for n in nb if n not in na]
    print("new nets: %d, their guide length %d; removed nets %d" % (
        len(new), sum(nb[n] for n in new), sum(1 for n in na if n not in nb)))
