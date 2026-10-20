"""Local cell and pin density of a placed DEF, to see detailed-routing hot spots before paying for detailed routing
(read-only, runs on Windows; the DEF has no cell sizes, so they come from the standard-cell LEF).
usage: python pin_hotspots.py <def> <lef> [tile_um=20] [top=8]
Per tile_um x tile_um tile (tap / fill / decap cells and macros excluded):
  util = standard-cell area / tile area,  pins = signal pins per 100 um2 (pin-access pressure on li1 / met1).
Prints p99 / p99.9 / max of both and the densest tiles (x0, y0 in um) with their instance count."""
import collections
import re
import sys

deff, leff = sys.argv[1], sys.argv[2]
T = float(sys.argv[3]) if len(sys.argv) > 3 else 20.0
TOP = int(sys.argv[4]) if len(sys.argv) > 4 else 8
size, npins = {}, {}
macro = None
in_pin = False
use_signal = True
with open(leff, errors="replace") as f:
    for ln in f:
        s = ln.split()
        if not s:
            continue
        if s[0] == "MACRO":
            macro = s[1]
            npins[macro] = 0
        elif macro and s[0] == "SIZE":
            size[macro] = (float(s[1]), float(s[3]))
        elif macro and s[0] == "PIN":
            in_pin, use_signal = True, True
        elif in_pin and s[0] == "USE" and s[1].rstrip(";") in ("POWER", "GROUND"):
            use_signal = False
        elif in_pin and s[0] == "END" and len(s) > 1 and s[1] != macro:
            if use_signal:
                npins[macro] += 1
            in_pin = False
        elif macro and s[0] == "END" and len(s) > 1 and s[1] == macro:
            macro = None
util = collections.Counter()
pins = collections.Counter()
cnt = collections.Counter()
unknown = collections.Counter()
sect = None
with open(deff, errors="replace") as f:
    for ln in f:
        s = ln.strip()
        if s.startswith("COMPONENTS"):
            sect = "C"
            continue
        if s.startswith("END COMPONENTS"):
            break
        if sect != "C" or not s.startswith("- "):
            continue
        m = re.match(r"- (\S+) (\S+) .*?(?:PLACED|FIXED) \( (-?\d+) (-?\d+) \)", s)
        if not m:
            continue
        cell = m.group(2)
        if re.search(r"tapvpwrvgnd|__fill|decap", cell):
            continue
        if cell not in size:
            unknown[cell] += 1
            continue
        w, h = size[cell]
        x, y = int(m.group(3)) / 1000 + w / 2, int(m.group(4)) / 1000 + h / 2
        k = (int(x // T), int(y // T))
        util[k] += w * h / (T * T)
        pins[k] += npins.get(cell, 0) * 100.0 / (T * T)
        cnt[k] += 1


def pct(vals, p):
    v = sorted(vals)
    return v[min(len(v) - 1, int(p * len(v)))] if v else 0.0


u, p = list(util.values()), list(pins.values())
print("%s: %d occupied %.0f-um tiles; util p99 %.2f p99.9 %.2f max %.2f; pins/100um2 p99 %.1f p99.9 %.1f max %.1f%s" % (
    deff.replace("\\", "/").split("/runs/")[-1], len(u), T, pct(u, .99), pct(u, .999), max(u), pct(p, .99), pct(p, .999),
    max(p), ("; cells not in the LEF: %d" % sum(unknown.values())) if unknown else ""))
for k, v in pins.most_common(TOP):
    print("   tile (%5.0f, %5.0f): pins %.1f / 100 um2, util %.2f, %d cells" % (k[0] * T, k[1] * T, v, util[k], cnt[k]))
