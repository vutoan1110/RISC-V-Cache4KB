"""U2 floorplans (2026-10-03, FLOW_JOURNAL Incident 96): strata with the cache rows folded into two 2x2 clusters.

strata1 (RAM rows, D$ row, I$ row, logic band on top) met timing (DM_VC4 post-CTS repair +1.809 ns nom_tt: the
half-cycle refill and read paths became short) but global routing overflowed by 233,074: the two full-width cache
rows walled the logic band off from the RAM area -- vertical routes between them had only 3 x 100 um row gaps and
the two side strips (OpenRAM blocks met1-met4; met5 is horizontal only), and placement split the logic across the
wall (I$ tags packed in the band's left corner at up to 91 % utilisation, D$ tags down in the RAM channel).
U2, bottom to top:
  RAM row A (banks 0-3, FS) / RAM channel / RAM row B (banks 4-7, N)        (as strata)
  I$ 2x2 cluster at the left, D$ 2x2 cluster at the right, right above RAM row B, both N
      (lanes 0,1 in the lower row, 2,3 in the upper row; SA2: way0 pair 0,1 / way1 pair 0,1)
  a central corridor between the clusters (the vertical connection band <-> RAM area, and logic room)
  logic band on top.
Usage: python make_u2_fp.py <design dir> <tag> <W> <H> [base config] [e=100] [ram_ch=220] [g1=150] [gin=120] [corient=N]
  corient = N (default) or R: R rotates every cache macro by 90 deg (left column of a cluster E = R270, right
  column W = R90), so a 2x2 cluster is 2 x 397.5 + 100 um wide instead of 2 x 479.78 + 100 (wider corridor).
  g1 = gap RAM row B -> clusters, gin = gap between the two rows of a cluster; the column gap inside a cluster is
  100 um. Writes <design>/macro_placement_<tag>.cfg and config_<tag>.json, with the usual checks.
"""
import json
import re
import sys

A = "E:/Projects/RISCV-research/asic/"
d, tag, W, H = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
base = sys.argv[5] if len(sys.argv) > 5 else "config_wide.json"
e = float(sys.argv[6]) if len(sys.argv) > 6 else 100.0
ram_ch = float(sys.argv[7]) if len(sys.argv) > 7 else 220.0
g1 = float(sys.argv[8]) if len(sys.argv) > 8 else 150.0
gin = float(sys.argv[9]) if len(sys.argv) > 9 else 120.0
corient = sys.argv[10] if len(sys.argv) > 10 else "N"
# F (2026-10-06): lower cache row N, upper row FS. The macro's port-0 bus (din0 / dout0 / wmask0, bottom edge) of
# the upper row then faces the logic band instead of the gap between the rows, which keeps only the two rows'
# dout1 (top edge in N) there. SA2 drives port 1 of every cache macro (two lanes per macro); with all-N rows its
# inter-row gap overflowed (sa2U2aG50: 3,588, hot spot on the D$ cluster, fp_tools/congestion_map.py).
assert corient in ("N", "R", "F")
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
CS = CACHE if corient in ("N", "F") else (CACHE[1], CACHE[0])     # footprint after the orientation
cw = 2 * CS[0] + GC
yc0 = yb + RAM[1] + g1
yc1 = yc0 + CS[1] + gin
for cache, xl in ((ic, x0 + e), (dc, x1 - e - cw)):
    for k, n in enumerate(cache):
        o = ("N" if corient == "N" else ("N" if k < 2 else "FS") if corient == "F" else
             ("E" if k % 2 == 0 else "W"))
        place.append((n, xl + (k % 2) * (CS[0] + GC), yc0 if k < 2 else yc1, o, CS))
corridor = (x1 - e - cw) - (x0 + e + cw)
band = y1 - e - (yc1 + CS[1])
assert corridor >= 500 and band >= 600, ("corridor / band too small", corridor, band)
assert sorted(p[0] for p in place) == sorted(names)
boxes = [(n, round(x, 2), round(y, 2), round(x + s[0], 2), round(y + s[1], 2)) for n, x, y, o, s in place]
for i, a in enumerate(boxes):
    assert a[1] >= x0 and a[2] >= y0 and a[3] <= x1 and a[4] <= y1, ("outside core", a)
    for b in boxes[i + 1:]:
        assert (a[3] + HALO <= b[1] - HALO or b[3] + HALO <= a[1] - HALO or
                a[4] + HALO <= b[2] - HALO or b[4] + HALO <= a[2] - HALO), ("overlap incl. halo", a, b)
hdr = ("# %s corridor floorplan %s (fp_tools/make_u2_fp.py %s %s %.0f %.0f %s %.0f %.0f %.0f %.0f):\n"
       "# die %.0f x %.0f um (%.2f mm2); RAM row A (FS) / channel %.0f / RAM row B (N); I$ 2x2 left, D$ 2x2 right (N),\n"
       "# gap %.0f above RAM row B; central corridor %.0f um; logic band %.0f um; RAM row gap %.1f; cache orientation %s.\n"
       % (d, tag, d, tag, W, H, base, e, ram_ch, g1, gin, W, H, W * H / 1e6, ram_ch, g1, corridor, band, gR,
          corient))
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
    " Corridor floorplan %s: DIE_AREA %.0f x %.0f (macro_placement_%s.cfg)." % (tag, W, H, tag))
cfg["DIE_AREA"] = [0, 0, W, H]
cfg["CORE_AREA"] = [12, 12, W - 12, H - 12]
cfg["MACRO_PLACEMENT_CFG"] = "dir::macro_placement_%s.cfg" % tag
open(A + d + "/config_%s.json" % tag, "w", encoding="utf-8", newline="\n").write(
    json.dumps(cfg, indent=4, ensure_ascii=True) + "\n")
print("%s %s: die %.0f x %.0f = %.2f mm2, corridor %.0f um, logic band %.0f um, RAM row gap %.1f" % (
    d, tag, W, H, W * H / 1e6, corridor, band, gR))
