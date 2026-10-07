"""STRATA floorplans (2026-10-03, NHAT_KY.md section 8).

Why: in the SA2 / DM_VC4 builds the worst setup paths are LONG-WIRE half-cycle paths: the SRAM dout launches on
the falling clock edge, and the DSE core writes each AXI refill beat straight into the lane macros (DM gathers it
in refill_line_accum first), so RAM dout -> RAM read mux -> AXI -> refill -> lane-macro din0 must fit in ~10 ns;
the cache read path (lane dout1 -> pipeline) is a half-cycle path as well. On ring1 the RAM read mux sat in the
bottom RAM row while half the banks were in the top row: the worst path zig-zagged ~8 mm (55 repeaters, 8.0 ns).
The tag-array clusters, on the other hand, need open space (they congest the channels of the DM-style grid).
Strata, bottom to top (all rows centred):
  RAM row A (banks 0-3, FS: port-0 pins on its top edge)
  RAM channel  (the RAM controller; both RAM rows face it)
  RAM row B (banks 4-7, N: port-0 pins on its bottom edge)   [the RAM wrapper leaves port 1 unused]
  D$ row (lanes, N: din0 on the bottom edge towards the RAM, dout1 on the top edge)
  I$ row (lanes, N: din0 below, dout1 on the top edge towards the logic band)
  logic band (CPU, tag arrays, AXI, peripherals): open space.
Usage: python make_strata_fp.py <design dir> <tag> <W> <H> [base config] [e=100] [ram_ch=220] [g_bd=140] [g_di=180]
  W x H die; e = core-edge margin; ram_ch = RAM channel height; g_bd = gap RAM row B -> D$ row; g_di = gap D$ row ->
  I$ row; the row gaps between macros of a row are whatever is left, spread evenly (RAM) / 100 um (cache).
Writes <design>/macro_placement_<tag>.cfg and <design>/config_<tag>.json; checks inside-core, no overlap
(10 um halo), every instance of the base config's placement placed once.
"""
import json
import re
import sys

A = "E:/Projects/RISCV-research/asic/"
d, tag, W, H = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
base = sys.argv[5] if len(sys.argv) > 5 else "config_wide.json"
e = float(sys.argv[6]) if len(sys.argv) > 6 else 100.0
ram_ch = float(sys.argv[7]) if len(sys.argv) > 7 else 220.0
g_bd = float(sys.argv[8]) if len(sys.argv) > 8 else 140.0
g_di = float(sys.argv[9]) if len(sys.argv) > 9 else 180.0
RAM = (683.1, 416.54)
CACHE = (479.78, 397.5)
HALO = 10.0
GC = 100.0
cfg = json.load(open(A + d + "/" + base, encoding="utf-8"))
mp = cfg["MACRO_PLACEMENT_CFG"].replace("dir::", "")
names = [ln.split()[0] for ln in open(A + d + "/" + mp, encoding="utf-8") if ln.strip() and not ln.startswith("#")]
ram = sorted([n for n in names if "u_axi_ram" in n], key=lambda n: int(re.search(r"g_bank\[(\d+)\]", n).group(1)))


def lane_key(n):
    return [int(x) for x in re.findall(r"(?:way|g_bank\[)(\d+)", n)]


ic = sorted([n for n in names if "u_icache" in n], key=lane_key)
dc = sorted([n for n in names if "u_dcache" in n], key=lane_key)
assert len(ram) == 8 and len(ic) == 4 and len(dc) == 4
x0, y0, x1, y1 = 12.0, 12.0, W - 12.0, H - 12.0
gR = (x1 - x0 - 2 * e - 4 * RAM[0]) / 3
assert gR >= 60, ("RAM row gap too small", gR)
place = []
ya = y0 + e
yb = ya + RAM[1] + ram_ch
for k in range(4):
    x = x0 + e + k * (RAM[0] + gR)
    place.append((ram[k], x, ya, "FS", RAM))
    place.append((ram[4 + k], x, yb, "N", RAM))
crow = 4 * CACHE[0] + 3 * GC
cx = (W - crow) / 2
yd = yb + RAM[1] + g_bd
yi = yd + CACHE[1] + g_di
for k in range(4):
    place.append((dc[k], cx + k * (CACHE[0] + GC), yd, "N", CACHE))
    place.append((ic[k], cx + k * (CACHE[0] + GC), yi, "N", CACHE))
band = y1 - e - (yi + CACHE[1])
assert band >= 600, ("logic band too thin", band)
assert sorted(p[0] for p in place) == sorted(names)
boxes = [(n, round(x, 2), round(y, 2), round(x + s[0], 2), round(y + s[1], 2)) for n, x, y, o, s in place]
for i, a in enumerate(boxes):
    assert a[1] >= x0 and a[2] >= y0 and a[3] <= x1 and a[4] <= y1, ("outside core", a)
    for b in boxes[i + 1:]:
        assert (a[3] + HALO <= b[1] - HALO or b[3] + HALO <= a[1] - HALO or
                a[4] + HALO <= b[2] - HALO or b[4] + HALO <= a[2] - HALO), ("overlap incl. halo", a, b)
hdr = ("# %s STRATA floorplan %s (2026-10-03, NHAT_KY.md section 8; fp_tools/make_strata_fp.py %s %s %.0f %.0f %s %.0f %.0f %.0f %.0f):\n"
       "# die %.0f x %.0f um (%.2f mm2); bottom to top: RAM row A (FS), RAM channel %.0f, RAM row B (N), gap %.0f, D$ row (N),\n"
       "# gap %.0f, I$ row (N), logic band %.0f um; RAM row gap %.1f, cache row gap %.0f.\n"
       % (d, tag, d, tag, W, H, base, e, ram_ch, g_bd, g_di, W, H, W * H / 1e6, ram_ch, g_bd, g_di, band, gR, GC))
open(A + d + "/macro_placement_%s.cfg" % tag, "w", encoding="utf-8", newline="\n").write(
    hdr + "".join("%-66s %8.2f %8.2f   %s\n" % (n, x, y, o) for n, x, y, o, s in place))
if d == "soc_dm_4kb":
    cfg["//RING_KNOBS"] = ("2026-10-03: the knobs the SA2 / DM_VC4 builds carry, added so the three builds differ only "
                           "in RTL: PL_TARGET_DENSITY_PCT 42 (DM's E15 value is 55), SYNTH_OPT_DFF_SAT (measured neutral "
                           "on DM), GRT_ALLOW_CONGESTION.")
    cfg["PL_TARGET_DENSITY_PCT"] = 42
    cfg["SYNTH_OPT_DFF_SAT"] = True
    cfg["GRT_ALLOW_CONGESTION"] = True
cfg["//EXPERIMENT"] = cfg.get("//EXPERIMENT", "") + (
    " STRATA floorplan %s (2026-10-03): DIE_AREA %.0f x %.0f (macro_placement_%s.cfg)." % (tag, W, H, tag))
cfg["DIE_AREA"] = [0, 0, W, H]
cfg["CORE_AREA"] = [12, 12, W - 12, H - 12]
cfg["MACRO_PLACEMENT_CFG"] = "dir::macro_placement_%s.cfg" % tag
open(A + d + "/config_%s.json" % tag, "w", encoding="utf-8", newline="\n").write(
    json.dumps(cfg, indent=4, ensure_ascii=True) + "\n")
print("%s %s: die %.0f x %.0f = %.2f mm2, RAM row gap %.1f, logic band %.0f um" % (d, tag, W, H, W * H / 1e6, gR, band))
