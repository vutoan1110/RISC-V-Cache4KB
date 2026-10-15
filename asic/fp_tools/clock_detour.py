"""Clock-net detour after global routing: guide length vs HPWL of the net's instance origins (read-only).
usage: python clock_detour.py <def> <guide> [prefix=clknet_] [top=12]"""
import sys, collections, re
deff, guide = sys.argv[1], sys.argv[2]
pref = sys.argv[3] if len(sys.argv) > 3 else "clknet_"
top = int(sys.argv[4]) if len(sys.argv) > 4 else 12
pos = {}; nets = {}; sect = None; cur = None; units = 1000
with open(deff) as f:
    for ln in f:
        s = ln.strip()
        if s.startswith("UNITS DISTANCE MICRONS"): units = int(s.split()[3])
        if s.startswith("COMPONENTS"): sect = "C"; continue
        if s.startswith("END COMPONENTS"): sect = None; continue
        if s.startswith("NETS") or s.startswith("SPECIALNETS"): sect = "N" if s.startswith("NETS") else "S"; continue
        if s.startswith("END NETS"): sect = None; continue
        if sect == "C" and s.startswith("- "):
            m = re.search(r"\(\s*(-?\d+)\s+(-?\d+)\s*\)", s)
            if m: pos[s.split()[1]] = (int(m.group(1)), int(m.group(2)))
        elif sect == "N":
            if s.startswith("- "):
                name = s.split()[1]
                cur = name if name.startswith(pref) else None
                if cur: nets[cur] = []
            if cur:
                for inst, pin in re.findall(r"\(\s*(\S+)\s+(\S+)\s*\)", s):
                    nets[cur].append(inst)
            if s.endswith(";"): cur = None
glen = collections.Counter(); cur = None
with open(guide) as f:
    for ln in f:
        p = ln.split()
        if len(p) == 1 and p[0] not in "()":
            cur = p[0] if p[0] in nets else None
        elif cur and len(p) == 5 and p[4] != "li1":
            x1, y1, x2, y2 = map(int, p[:4])
            glen[cur] += max(x2 - x1, y2 - y1)
rows = []
for n, insts in nets.items():
    xy = [pos[i] for i in insts if i in pos]
    if len(xy) < 2: continue
    hp = (max(x for x, _ in xy) - min(x for x, _ in xy) + max(y for _, y in xy) - min(y for _, y in xy)) / units
    rows.append((glen[n] / units - hp, n, hp, glen[n] / units, len(xy)))
rows.sort(reverse=True)
tot_h = sum(r[2] for r in rows); tot_g = sum(r[3] for r in rows)
print(f"{len(rows)} nets '{pref}*': HPWL sum {tot_h/1000:.1f} mm, guide sum {tot_g/1000:.1f} mm; nets with guide > 3 x HPWL + 200 um: {sum(1 for r in rows if r[3] > 3*r[2] + 200)}")
for ex, n, hp, g, k in rows[:top]:
    print(f"  {n:28s} pins {k:3d} HPWL {hp:7.0f} um  guide {g:7.0f} um  excess {ex:7.0f}")
