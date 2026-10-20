"""Std-cell area waterfall of a PD run: where every um2 comes from.

Categories by instance name (OpenROAD naming) and master:
  logic       synthesised cells (Yosys names), split into as-synthesised area + resizer upsizing delta
  tap / diode / clock tree / hold / port buffers / repair_design buffers / repair_timing buffers / macro pin buffers
Fill and decap cells are excluded (they are not in design__instance__area__stdcell).

usage: python area_waterfall.py <hd_area.tsv> <label>=<def>,<synth netlist> ...
"""
import re
import sys
from collections import defaultdict

area = {}
for line in open(sys.argv[1]):
    c, a = line.split()
    area[c] = float(a)
area.setdefault("sky130_fd_sc_hd__tapvpwrvgnd_1", 0.46 * 2.72)   # physical-only, no liberty area


def norm(n):
    return n.replace("\\", "").strip()


def synth_cells(path):
    cells = {}
    rx = re.compile(r"^\s*(sky130_fd_sc_hd__\S+)\s+(\S+)\s*\(")
    with open(path, errors="replace") as fh:
        for line in fh:
            m = rx.match(line)
            if m:
                cells[norm(m.group(2))] = m.group(1)
    return cells


def def_cells(path):
    cells = {}
    inside = False
    rx = re.compile(r"^\s*-\s+(\S+)\s+(\S+)")
    with open(path, errors="replace") as fh:
        for line in fh:
            if line.startswith("COMPONENTS"):
                inside = True
                continue
            if line.startswith("END COMPONENTS"):
                break
            if inside:
                m = rx.match(line)
                if m:
                    cells[norm(m.group(1))] = m.group(2)
    return cells


RULES = [
    ("fill",        lambda n, c: re.search(r"__(fill|decap)_", c) is not None),
    ("macro",       lambda n, c: c.startswith("sky130_sram")),
    ("tap",         lambda n, c: "tapvpwrvgnd" in c),
    ("diode",       lambda n, c: "diode" in c),
    ("clock_tree",  lambda n, c: re.match(r"^(clkbuf_|clkload|delaybuf_|cts_)", n) is not None),
    ("hold",        lambda n, c: re.match(r"^hold\d+", n) is not None),
    ("port_buf",    lambda n, c: re.match(r"^(input|output)\d+$", n) is not None),
    ("macro_pin",   lambda n, c: n.startswith("macro_pin_")),
    ("rd_wire",     lambda n, c: re.match(r"^wire\d+", n) is not None),
    ("rd_maxcap",   lambda n, c: re.match(r"^max_cap\d+", n) is not None),
    ("rd_maxlen",   lambda n, c: re.match(r"^max_length\d+", n) is not None),
    ("rd_fanout",   lambda n, c: re.match(r"^(fanout|load_slew)\d+", n) is not None),
    ("rt_rebuffer", lambda n, c: re.match(r"^(rebuffer|split|place)\d+", n) is not None),
]

cols = []
for arg in sys.argv[2:]:
    label, paths = arg.split("=", 1)
    dpath, spath = paths.split(",")
    d = def_cells(dpath)
    s = synth_cells(spath)
    acc = defaultdict(float)
    cnt = defaultdict(int)
    other = defaultdict(int)
    for n, c in d.items():
        cat = next((k for k, f in RULES if f(n, c)), None)
        if cat is None:
            if n in s:
                cat = "logic"
                acc["logic_synth"] += area.get(s[n], 0.0)
                acc["logic_resize"] += area.get(c, 0.0) - area.get(s[n], 0.0)
                cnt["logic"] += 1
                continue
            cat = "other"
            other[re.sub(r"\d+", "#", n)[:24]] += 1
        acc[cat] += area.get(c, 0.0)
        cnt[cat] += 1
    synth_total = sum(area.get(c, 0.0) for c in s.values())
    missing = sum(1 for n in s if n not in d)
    cols.append((label, acc, cnt, synth_total, missing, other))

cats = ["logic_synth", "logic_resize", "tap", "diode", "clock_tree", "hold", "port_buf", "macro_pin",
        "rd_wire", "rd_maxcap", "rd_maxlen", "rd_fanout", "rt_rebuffer", "other"]
print(f"{'um2':14s}" + "".join(f"{c[0]:>22s}" for c in cols))
for k in cats:
    row = f"{k:14s}"
    for label, acc, cnt, *_ in cols:
        n = cnt.get(k.replace("_synth", "").replace("logic_resize", "logic"), 0) if k != "logic_resize" else ""
        row += f"{acc.get(k, 0.0):14,.0f} ({n if n != '' else '':>5})"
    print(row)
tot = [sum(v for k, v in acc.items() if k not in ("fill", "macro")) for _, acc, *_ in cols]
print(f"{'TOTAL stdcell':14s}" + "".join(f"{t:14,.0f}{'':8s}" for t in tot))
for label, acc, cnt, synth_total, missing, other in cols:
    print(f"{label}: synth netlist total {synth_total:,.0f} um2; synth cells absent after PnR {missing};"
          f" top 'other': {sorted(other.items(), key=lambda x: -x[1])[:6]}")
