"""2026-10-20 DM_VC4 congestion study: summarise an OpenROAD global-route congestion report (grt_hotspot.sh) by area.
    python congestion_bins.py <congestion.rpt> [bin um, default 200]
Prints total overflow per direction, the hottest bins (overflow sum, H / V split) and the most frequent net name groups
in the hottest bins (bus names with indices stripped)."""
import re
import sys
from collections import Counter, defaultdict

path = sys.argv[1]
B = float(sys.argv[2]) if len(sys.argv) > 2 else 200.0
rows, cur = [], {}
for line in open(path, encoding="utf-8", errors="replace"):
    line = line.strip()
    if line.startswith("violation type:"):
        cur = {"dir": "H" if "Horizontal" in line else "V"}
    elif line.startswith("srcs:"):
        cur["nets"] = [n[4:] for n in line[5:].split()]
    elif line.startswith("congestion information:"):
        m = re.search(r"capacity:(\d+) usage:(\d+) overflow:(\d+)", line)
        cur["cap"], cur["use"], cur["ovf"] = map(int, m.groups())
    elif line.startswith("bbox"):
        x1, y1, x2, y2 = map(float, re.findall(r"-?\d+(?:\.\d+)?", line)[:4])
        cur["x"], cur["y"] = (x1 + x2) / 2, (y1 + y2) / 2
        rows.append(cur)
tot = Counter()
for r in rows:
    tot[r["dir"]] += r["ovf"]
print(f"{len(rows)} congested gcells, overflow H {tot['H']} V {tot['V']}, zero-capacity gcells {sum(r['cap'] == 0 for r in rows)}")
bins = defaultdict(lambda: Counter())
nets = defaultdict(Counter)
for r in rows:
    k = (int(r["x"] // B), int(r["y"] // B))
    bins[k][r["dir"]] += r["ovf"]
    bins[k]["n"] += 1
    for n in r["nets"]:
        g = re.sub(r"\?\[\d+\?\]", "[]", n)
        g = re.sub(r"^(net|_)\d+_?$", "<repair/synth net>", g)
        g = re.sub(r"clknet_\S+", "<clock net>", g)
        nets[k][g] += 1
print(f"hottest {B:.0f} um bins (x0-x1, y0-y1: overflow H/V, gcells):")
for k, c in sorted(bins.items(), key=lambda kv: -(kv[1]["H"] + kv[1]["V"]))[:15]:
    top = ", ".join(f"{g} {n}" for g, n in nets[k].most_common(5))
    print(f"  x {k[0]*B:5.0f}-{(k[0]+1)*B:5.0f} y {k[1]*B:5.0f}-{(k[1]+1)*B:5.0f}: H {c['H']:4d} V {c['V']:4d} ({c['n']:4d})  {top}")
