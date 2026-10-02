"""SA2 / DM_VC4 wide floorplan (2026-10-02, FLOW_JOURNAL Incident 96): the DM R14 macro grid scaled by S about the
core origin (12, 12) -- macro sizes unchanged, so every channel between macros and the top band widen -- and the
die / core grown by the same factor. Reason: RUDY maps of the density-42 placements put 25-35 % more wire demand
than DM into the SAME channels (p99 11.1-11.5 vs 8.8 um/um2), and global routing overflows there (GRT-0118).
Writes asic/<design>/macro_placement_wide.cfg and config_wide.json (= config.json + new DIE/CORE_AREA + the wide
placement); checks that no two macros overlap and every macro sits inside the core."""
import json
import re

A = "E:/Projects/RISCV-research/asic/"
S = 1.15
SIZE = {"axi_ram": (683.1, 416.54), "cache": (479.78, 397.5)}
DIE_OLD = (3665, 2900)
CORE_OLD = (12, 12, 3653, 2888)
W = round(12 + S * (CORE_OLD[2] - 12) + 12)
H = round(12 + S * (CORE_OLD[3] - 12) + 12)

for d, tag in (("soc_sa2_4kb", "SA2"), ("soc_vc4_4kb", "DM_VC4")):
    src = open(A + d + "/macro_placement.cfg", encoding="utf-8").read()
    out, boxes = [], []
    for line in src.splitlines():
        m = re.match(r"^(\S+)\s+([\d.]+)\s+([\d.]+)\s+(\S+)\s*$", line)
        if not m:
            continue
        name, x, y, o = m.group(1), float(m.group(2)), float(m.group(3)), m.group(4)
        nx, ny = round(12 + S * (x - 12), 2), round(12 + S * (y - 12), 2)
        w, h = SIZE["axi_ram"] if "u_axi_ram" in name else SIZE["cache"]
        boxes.append((name, nx, ny, nx + w, ny + h))
        out.append("%-66s %8.2f %8.2f   %s" % (name, nx, ny, o))
    assert len(out) == 16, len(out)
    for i, a in enumerate(boxes):
        assert a[1] >= 12 and a[2] >= 12 and a[3] <= W - 12 and a[4] <= H - 12, ("outside core", a)
        for b in boxes[i + 1:]:
            assert a[3] <= b[1] or b[3] <= a[1] or a[4] <= b[2] or b[4] <= a[2], ("overlap", a, b)
    hdr = ("# %s WIDE floorplan (2026-10-02, FLOW_JOURNAL Incident 96): macro_placement.cfg (= the DM R14 grid) with every\n"
           "# coordinate scaled by %.2f about the core origin (12, 12); macro sizes unchanged, so the channels between\n"
           "# macros and the top band are %.0f %% wider; die %d x %d um (DM %d x %d). Reason: at the DM floorplan the\n"
           "# density-42 placement still overflows global routing in the macro channels (RUDY p99 +25-35 %% vs DM).\n"
           % (tag, S, 100 * (S - 1) * 2.6, W, H, DIE_OLD[0], DIE_OLD[1]))
    open(A + d + "/macro_placement_wide.cfg", "w", encoding="utf-8", newline="\n").write(hdr + "\n".join(out) + "\n")
    c = json.load(open(A + d + "/config.json", encoding="utf-8"))
    c["//EXPERIMENT"] = c.get("//EXPERIMENT", "") + (" WIDE floorplan variant (2026-10-02): DIE_AREA %d x %d, macro "
                                                     "coordinates x%.2f (macro_placement_wide.cfg)." % (W, H, S))
    c["DIE_AREA"] = [0, 0, W, H]
    c["CORE_AREA"] = [12, 12, W - 12, H - 12]
    c["MACRO_PLACEMENT_CFG"] = "dir::macro_placement_wide.cfg"
    open(A + d + "/config_wide.json", "w", encoding="utf-8", newline="\n").write(json.dumps(c, indent=4) + "\n")
    gaps = sorted(set(round(b[1] - a[3], 1) for a in boxes for b in boxes if abs(a[2] - b[2]) < 1 and b[1] > a[3]))
    print("%s: die %d x %d (%.2f mm2, DM %.2f), min horizontal gap in a row %.1f um" % (
        d, W, H, W * H / 1e6, DIE_OLD[0] * DIE_OLD[1] / 1e6, min(gaps)))
