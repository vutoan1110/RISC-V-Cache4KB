"""Ring floorplans for the DSE builds (2026-10-03, NHAT_KY.md section 8).

Why: the OpenRAM macros obstruct met1-met4 (LEF OBS), so in the DM-style 4 x 4 macro grid every vertical route
between logic in different macro rows must squeeze through the narrow vertical gaps between macros, and the
tag-array clusters of SA2 / DM_VC4 (5,120 flops each, nets >= 500 um 5-6x DM's) end up at channel junctions.
A ring keeps all 16 macros on the periphery and leaves ONE contiguous logic region in the middle:
  - bottom row: RAM banks 0-3, orientation FS (port-0 pins din0/dout0/wmask0 move to the top edge, facing in);
  - top row:    RAM banks 4-7, orientation N  (port-0 pins on the bottom edge, facing in);
    (the RAM wrapper leaves port 1 unused: csb1 = 1, dout1 open)
  - left column:  I$ data banks (lane 0 at the bottom), orientation N  (port-1 control addr1/csb1 on the right
    edge, facing in; dout1 / din0 on the top / bottom edges reach the middle through the gaps);
  - right column: D$ data banks, orientation FN (mirrored, so their port-1 control faces in as well).
Usage: python make_ring_fp.py <design dir name> <tag> <W> <H> [e=100] [c=120] [base config=config_wide.json]
  e = core-edge-to-macro margin, c = spacing between the rows and the columns; the row gaps and column gaps are
  whatever is left, spread evenly. Writes <design>/macro_placement_<tag>.cfg and <design>/config_<tag>.json
  (= the base config with the new DIE/CORE_AREA and placement file) and checks: inside the core, no overlap
  including the 10 um halo, every instance of the base config's placement placed exactly once.
  For soc_dm_4kb the base is config_R14_FINAL.json and the three knobs that the SA2 / DM_VC4 builds carry are
  added too (PL_TARGET_DENSITY_PCT 42, SYNTH_OPT_DFF_SAT, GRT_ALLOW_CONGESTION), so the three ring configs
  differ only in what the RTL forces (sources, macro instance names, EQY script; DM_VC4's power-connection skip).
"""
import json
import re
import sys

A = "E:/Projects/RISCV-research/asic/"
d, tag, W, H = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
e = float(sys.argv[5]) if len(sys.argv) > 5 else 100.0
c = float(sys.argv[6]) if len(sys.argv) > 6 else 120.0
RAM = (683.1, 416.54)
CACHE = (479.78, 397.5)
HALO = 10.0
base = sys.argv[7] if len(sys.argv) > 7 else "config_wide.json"
cfg = json.load(open(A + d + "/" + base, encoding="utf-8"))
mp = cfg["MACRO_PLACEMENT_CFG"].replace("dir::", "")
names = [ln.split()[0] for ln in open(A + d + "/" + mp, encoding="utf-8")
         if ln.strip() and not ln.startswith("#")]
ram = sorted([n for n in names if "u_axi_ram" in n], key=lambda n: int(re.search(r"g_bank\[(\d+)\]", n).group(1)))
ic = [n for n in names if "u_icache" in n]
dc = [n for n in names if "u_dcache" in n]


def lane_key(n):    # SA2: way, pair; VC4: lane
    return [int(x) for x in re.findall(r"(?:way|g_bank\[)(\d+)", n)]


ic.sort(key=lane_key)
dc.sort(key=lane_key)
assert len(ram) == 8 and len(ic) == 4 and len(dc) == 4, (len(ram), len(ic), len(dc))
x0, y0, x1, y1 = 12.0, 12.0, W - 12.0, H - 12.0
place = []
# rows of RAM
row_w = 4 * RAM[0]
gR = (x1 - x0 - 2 * e - row_w) / 3
assert gR >= 40, ("row gap too small", gR)
yb = y0 + e
yt = y1 - e - RAM[1]
for k in range(4):
    x = x0 + e + k * (RAM[0] + gR)
    place.append((ram[k], x, yb, "FS", RAM))
    place.append((ram[4 + k], x, yt, "N", RAM))
# columns of cache macros between the rows
col_lo = yb + RAM[1] + c
col_hi = yt - c
gC = (col_hi - col_lo - 4 * CACHE[1]) / 3
assert gC >= 40, ("column gap too small", gC)
for k in range(4):
    y = col_lo + k * (CACHE[1] + gC)
    place.append((ic[k], x0 + e, y, "N", CACHE))
    place.append((dc[k], x1 - e - CACHE[0], y, "FN", CACHE))
# checks
assert sorted(p[0] for p in place) == sorted(names)
boxes = [(n, round(x, 2), round(y, 2), round(x + s[0], 2), round(y + s[1], 2)) for n, x, y, o, s in place]
for i, a in enumerate(boxes):
    assert a[1] >= x0 and a[2] >= y0 and a[3] <= x1 and a[4] <= y1, ("outside core", a)
    for b in boxes[i + 1:]:
        sep = (a[3] + HALO <= b[1] - HALO or b[3] + HALO <= a[1] - HALO or
               a[4] + HALO <= b[2] - HALO or b[4] + HALO <= a[2] - HALO)
        assert sep, ("overlap incl. halo", a, b)
center_w = (x1 - e - CACHE[0] - c) - (x0 + e + CACHE[0] + c)
center_h = col_hi - col_lo
hdr = ("# %s RING floorplan %s (2026-10-03, NHAT_KY.md section 8; fp_tools/make_ring_fp.py %s %s %.0f %.0f %.0f %.0f):\n"
       "# die %.0f x %.0f um (%.2f mm2); RAM rows bottom (FS) / top (N), I$ column left (N), D$ column right (FN);\n"
       "# core-edge margin %.0f, row/column spacing %.0f, row gap %.1f, column gap %.1f; open middle %.0f x %.0f um.\n"
       % (d, tag, d, tag, W, H, e, c, W, H, W * H / 1e6, e, c, gR, gC, center_w, center_h))
out = A + d + "/macro_placement_%s.cfg" % tag
open(out, "w", encoding="utf-8", newline="\n").write(
    hdr + "".join("%-66s %8.2f %8.2f   %s\n" % (n, x, y, o) for n, x, y, o, s in place))
if d == "soc_dm_4kb":
    cfg["//RING_KNOBS"] = ("2026-10-03: the knobs the SA2 / DM_VC4 builds carry, added so the three ring builds "
                           "differ only in RTL: PL_TARGET_DENSITY_PCT 42 (DM's E15 value is 55), "
                           "SYNTH_OPT_DFF_SAT (measured neutral on DM: -1 flop, +0.08 % area), GRT_ALLOW_CONGESTION.")
    cfg["PL_TARGET_DENSITY_PCT"] = 42
    cfg["SYNTH_OPT_DFF_SAT"] = True
    cfg["GRT_ALLOW_CONGESTION"] = True
cfg["//EXPERIMENT"] = cfg.get("//EXPERIMENT", "") + (
    " RING floorplan %s (2026-10-03): DIE_AREA %.0f x %.0f, macros on the periphery "
    "(macro_placement_%s.cfg)." % (tag, W, H, tag))
cfg["DIE_AREA"] = [0, 0, W, H]
cfg["CORE_AREA"] = [12, 12, W - 12, H - 12]
cfg["MACRO_PLACEMENT_CFG"] = "dir::macro_placement_%s.cfg" % tag
open(A + d + "/config_%s.json" % tag, "w", encoding="utf-8", newline="\n").write(
    json.dumps(cfg, indent=4, ensure_ascii=True) + "\n")
print("%s %s: die %.0f x %.0f = %.2f mm2, row gap %.1f, column gap %.1f, middle %.0f x %.0f = %.2f mm2" % (
    d, tag, W, H, W * H / 1e6, gR, gC, center_w, center_h, center_w * center_h / 1e6))
