"""Where does global-routing overflow sit? Reads an OpenROAD -congestion_report_file (fp_tools/grt_congestion.tcl).

Prints: total overflow by direction, a coarse ASCII map of the die (one character per tile, overflow summed; macro
tiles marked from the macro placement cfg + LEF sizes), the 15 worst tiles, and which design blocks own the nets
through the worst tiles (by hierarchical net name: u_icache / u_dcache / u_core / ...; buffered nets net123 /
_01234_ count as "other").

    python asic/fp_tools/congestion_map.py <report> <macro_placement.cfg> [tile_um=100]
"""
import collections
import re
import sys
from pathlib import Path

rpt, cfg = Path(sys.argv[1]), Path(sys.argv[2])
T = float(sys.argv[3]) if len(sys.argv) > 3 else 100.0
A = Path(__file__).resolve().parents[1]
size = {}
for lef in (A / "soc_dm_4kb" / "macros" / "lef").glob("*.lef"):
    t = lef.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"MACRO (\S+).*?SIZE ([\d.]+) BY ([\d.]+)", t, re.S)
    if m:
        size[m.group(1)] = (float(m.group(2)), float(m.group(3)))
hdr = cfg.read_text(encoding="utf-8").splitlines()
die = re.search(r"die (\d+) x (\d+)", " ".join(hdr[:3]))
W, H = (float(die.group(1)), float(die.group(2))) if die else (3400.0, 3400.0)
macros = []
for ln in hdr:
    if ln.strip() and not ln.startswith("#"):
        inst, x, y, o = ln.split()[:4]
        kind = "2kbyte" if "u_ram" in inst or "ram" in inst.lower() and "cache" not in inst.lower() else "1kbyte"
        macros.append((inst, float(x), float(y), o))
tot = collections.Counter()
hv = collections.Counter()
owners = collections.defaultdict(collections.Counter)
blocks = re.compile(r"u_soc\.(u_icache|u_dcache|u_core|u_cache_axi_master|u_observability|u_perf\w*|u_axi_ram\w*|u_\w+)")
text = rpt.read_text(encoding="utf-8", errors="replace")
for rec in text.split("violation type: ")[1:]:
    d = "H" if rec.startswith("Horizontal") else "V"
    ov = int(re.search(r"overflow:(\d+)", rec).group(1))
    m = re.search(r"bbox = \( ([\d.]+), ([\d.]+) \) - \( ([\d.]+), ([\d.]+)\)", rec)
    x, y = (float(m.group(1)) + float(m.group(3))) / 2, (float(m.group(2)) + float(m.group(4))) / 2
    k = (int(x // T), int(y // T))
    tot[k] += ov
    hv[d] += ov
    for b in blocks.findall(rec):
        owners[k][b] += 1
print("overflow H %d, V %d, total %d over %d records" % (hv["H"], hv["V"], sum(tot.values()), text.count("violation type")))
nx, ny = int(W // T) + 1, int(H // T) + 1
mtile = set()
for inst, x, y, o in macros:
    w, h = (397.5, 479.78) if o in ("E", "W", "FE", "FW") else (479.78, 397.5)
    if "ram" in inst.lower() and "cache" not in inst.lower():
        w, h = 683.1, 416.54          # 2 KiB macro (approximate; only used to draw the map)
    for i in range(int(x // T), int((x + w) // T) + 1):
        for j in range(int(y // T), int((y + h) // T) + 1):
            mtile.add((i, j))
print("map (top = high y), tile %g um; . = 0, digit = overflow/10 capped 9, # = > 99, m = macro tile without overflow" % T)
for j in range(ny - 1, -1, -1):
    row = ""
    for i in range(nx):
        v = tot.get((i, j), 0)
        row += ("m" if (i, j) in mtile else ".") if v == 0 else ("#" if v > 99 else str(min(9, v // 10)) if v >= 10 else "+")
    print("%5d %s" % (j * T, row))
print("worst tiles:")
for k, v in tot.most_common(15):
    print("  x %4d-%4d y %4d-%4d  overflow %4d  %s" % (k[0] * T, (k[0] + 1) * T, k[1] * T, (k[1] + 1) * T, v,
                                                     ", ".join("%s %d" % kv for kv in owners[k].most_common(4))))
