"""Structural logic depth (cells) on a flat sky130 netlist (FLOW_JOURNAL Incident 76).

    python netlist_depth.py <netlist.v> <report>

report "reg:<regex>"   longest cell path from any register/port to the D pins
                       of the registers whose Q net matches <regex>
report "from:<net-regex>:<reg-regex>"
                       longest cell path from nets matching <net-regex> to the
                       D pins of the registers whose Q net matches <reg-regex>
Pre-PnR use only: counts cells, not delay, so it compares logic SHAPE
(e.g. an enable at the base of a ripple chain vs in the final select).
"""
import re
import sys
from functools import lru_cache

sys.setrecursionlimit(100000)
OUT_PINS = {"X", "Y", "Q", "Q_N", "SUM", "COUT", "HI", "LO", "GCLK"}
text = open(sys.argv[1], errors="replace").read()
driver = {}      # net -> cell name
cell_in = {}     # cell -> [input nets]
cell_type = {}
reg_d = {}       # register Q net -> D net
for m in re.finditer(r"^\s*(sky130_fd_sc_hd__\w+)\s+(\S+)\s*\((.*?)\);", text, re.M | re.S):
    ctype, cname, body = m.group(1), m.group(2), m.group(3)
    pins = re.findall(r"\.(\w+)\(\s*(\\?\S+?(?:\[\d+\])?)\s*\)", body)
    cell_type[cname] = ctype
    ins = []
    is_reg = re.match(r"sky130_fd_sc_hd__(df|edf|sdf|dl)", ctype) is not None
    dnet = None
    for p, n in pins:
        n = n.lstrip("\\")
        if p in OUT_PINS:
            driver[n] = cname
            if is_reg and p == "Q":
                qnet = n
        else:
            ins.append(n)
            if p == "D":
                dnet = n
    cell_in[cname] = ins
    if is_reg and dnet is not None:
        reg_d[qnet] = dnet
regs = set(c for c, t in cell_type.items() if re.match(r"sky130_fd_sc_hd__(df|edf|sdf|dl)", t))


@lru_cache(maxsize=None)
def depth(net):
    c = driver.get(net)
    if c is None or c in regs:
        return 0
    return 1 + max((depth(n) for n in cell_in[c]), default=0)


def depth_from(src_re):
    src = re.compile(src_re)

    @lru_cache(maxsize=None)
    def d(net):
        if src.search(net):
            return 0
        c = driver.get(net)
        if c is None or c in regs:
            return -10**9
        return 1 + max((d(n) for n in cell_in[c]), default=-10**9)
    return d


rep = sys.argv[2]
if rep.startswith("reg:"):
    rx = re.compile(rep[4:])
    ds = sorted((depth(dn), q) for q, dn in reg_d.items() if rx.search(q))
    print("regs %d  max depth %d  median %d  worst %s" % (len(ds), ds[-1][0], ds[len(ds) // 2][0], ds[-1][1]))
elif rep.startswith("from:"):
    _, srx, rrx = rep.split(":", 2)
    d = depth_from(srx)
    rx = re.compile(rrx)
    ds = sorted((d(dn), q) for q, dn in reg_d.items() if rx.search(q))
    ds = [x for x in ds if x[0] >= 0]
    if ds:
        print("regs reached %d  max depth after source %d  median %d  worst %s"
              % (len(ds), ds[-1][0], ds[len(ds) // 2][0], ds[-1][1]))
    else:
        print("no register reached from", srx)
elif rep.startswith("net:"):
    # "net:<src-regex>:<exact target net>" longest cell path from src nets to one net
    _, srx, tgt = rep.split(":", 2)
    d = depth_from(srx)
    print("depth after source to %s: %d   (total from regs: %d)" % (tgt, d(tgt), depth(tgt)))
