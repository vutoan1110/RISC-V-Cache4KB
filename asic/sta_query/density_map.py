"""2026-10-20 DM_VC4 congestion study: standard-cell placement density per bin from a DEF.
    python density_map.py <def> <sky130_fd_sc_hd merged or cell LEF> [bin um, default 200] [x0 x1 y0 y1 window, um]
Cell area = LEF SIZE; fill / tap / decap cells are counted separately. Density = cell area / bin area (macro area is
not subtracted: bins that overlap a macro read low). Prints the bins of the window (default: whole die)."""
import re
import sys
from collections import defaultdict

deff, leff = sys.argv[1], sys.argv[2]
B = float(sys.argv[3]) if len(sys.argv) > 3 else 200.0
win = list(map(float, sys.argv[4:8])) if len(sys.argv) > 7 else None
size = {}
cur = None
for line in open(leff, encoding="utf-8", errors="replace"):
    m = re.match(r"\s*MACRO\s+(\S+)", line)
    if m:
        cur = m.group(1)
    m = re.match(r"\s*SIZE\s+([\d.]+)\s+BY\s+([\d.]+)", line)
    if m and cur:
        size[cur] = float(m.group(1)) * float(m.group(2))
area = defaultdict(float)
filler = defaultdict(float)
inside = False
unknown = set()
pat = re.compile(r"^\s*-\s+(\S+)\s+(\S+).*?\+\s+(?:PLACED|FIXED)\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)")
for line in open(deff, encoding="utf-8", errors="replace"):
    if line.startswith("COMPONENTS"):
        inside = True
        continue
    if line.startswith("END COMPONENTS"):
        break
    if not inside:
        continue
    m = pat.match(line)
    if not m:
        continue
    master = m.group(2)
    if master not in size:
        unknown.add(master)
        continue
    x, y = int(m.group(3)) / 1000.0, int(m.group(4)) / 1000.0
    k = (int(x // B), int(y // B))
    if re.search(r"__(fill|tapvpwrvgnd|decap|fakediode)", master):
        filler[k] += size[master]
    else:
        area[k] += size[master]
print(f"unknown masters (macros etc.): {sorted(unknown)[:6]}")
keys = sorted(set(area) | set(filler))
xs = sorted({k[0] for k in keys})
ys = sorted({k[1] for k in keys}, reverse=True)
if win:
    xs = [i for i in xs if win[0] <= i * B < win[1]]
    ys = [j for j in ys if win[2] <= j * B < win[3]]
print("logic cell density % (rows = y bin start, top first; columns = x bin start)")
print("      " + "".join(f"{i*B:6.0f}" for i in xs))
for j in ys:
    print(f"{j*B:6.0f}" + "".join(f"{100*area[(i, j)]/(B*B):6.1f}" for i in xs))
