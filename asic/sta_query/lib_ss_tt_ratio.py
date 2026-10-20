#!/usr/bin/env python3
"""ss / tt delay ratio of every sky130_fd_sc_hd cell (2026-10-15 ss study).

    python lib_ss_tt_ratio.py <tt.lib> <ss.lib> [--slew 0.2] [--load 0.005] [--top 60]

For every cell and timing arc (cell_rise / cell_fall tables), the delay is interpolated at one input slew (ns) and
one output load (pF) in both libraries; the cell's ratio is ss / tt of its slowest arc. The 4-high transistor
stacks (or4, nor4, a2111o, ...) are expected at the top: at 1.60 V / 100 C their stacked PMOS loses much more than a
2-stack, which is how a path of the same depth becomes far longer at ss than the tt-driven mapping assumed.
"""
import argparse
import bisect
import re


def parse(path):
    txt = open(path, encoding="utf-8", errors="replace").read()
    cells = {}
    for m in re.finditer(r'\n\s*cell\s*\(\s*"?([\w]+)"?\s*\)\s*\{', txt):
        name = m.group(1)
        start = m.end()
        depth, i = 1, start
        while depth and i < len(txt):
            c = txt[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            i += 1
        cells[name] = txt[start:i]
    return cells


def tables(body):
    out = []
    for m in re.finditer(r'(cell_rise|cell_fall)\s*\(\s*"?(\w+)"?\s*\)\s*\{(.*?)\}', body, re.S):
        t = m.group(3)
        i1 = re.search(r'index_1\s*\(\s*"([^"]+)"', t)
        i2 = re.search(r'index_2\s*\(\s*"([^"]+)"', t)
        v = re.search(r'values\s*\((.*?)\)\s*;', t, re.S)
        if not (i1 and i2 and v):
            continue
        x1 = [float(x) for x in i1.group(1).split(",")]
        x2 = [float(x) for x in i2.group(1).split(",")]
        rows = [[float(x) for x in r.split(",")] for r in re.findall(r'"([^"]+)"', v.group(1))]
        out.append((x1, x2, rows))
    return out


def interp(x, xs, ys):
    j = min(max(bisect.bisect_left(xs, x), 1), len(xs) - 1)
    x0, x1 = xs[j - 1], xs[j]
    return ys[j - 1] + (ys[j] - ys[j - 1]) * (x - x0) / (x1 - x0)


def value(tab, slew, load):
    x1, x2, rows = tab           # index_1 = input slew, index_2 = load (sky130 hd template del_1_7_7)
    col = [interp(load, x2, r) for r in rows]
    return interp(slew, x1, col)


ap = argparse.ArgumentParser()
ap.add_argument("tt")
ap.add_argument("ss")
ap.add_argument("--slew", type=float, default=0.2)
ap.add_argument("--load", type=float, default=0.005)
ap.add_argument("--top", type=int, default=60)
a = ap.parse_args()
tt, ss = parse(a.tt), parse(a.ss)
res = []
for name, body in tt.items():
    if name not in ss:
        continue
    t_tt, t_ss = tables(body), tables(ss[name])
    if not t_tt or len(t_tt) != len(t_ss):
        continue
    d_tt = max(value(t, a.slew, a.load) for t in t_tt)
    d_ss = max(value(t, a.slew, a.load) for t in t_ss)
    if d_tt > 0:
        res.append((d_ss / d_tt, name.replace("sky130_fd_sc_hd__", ""), d_tt, d_ss))
res.sort(reverse=True)
print("slew %.3f ns, load %.4f pF; %d cells" % (a.slew, a.load, len(res)))
print("%-22s %7s %8s %8s" % ("cell", "ss/tt", "tt ns", "ss ns"))
for r, n, dt, ds in res[: a.top]:
    print("%-22s %7.2f %8.3f %8.3f" % (n, r, dt, ds))
med = sorted(r for r, *_ in res)[len(res) // 2]
print("median ratio %.2f" % med)
