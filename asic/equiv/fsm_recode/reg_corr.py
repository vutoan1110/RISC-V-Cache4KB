"""FLOW_JOURNAL Incident 86: register correspondence between gold (RTL + fsm) and gate
(final netlist through EQY's gate front end), read straight from the RTLIL files.

A register bit's names = every public wire bit on its net, where the net is the flop's Q bit,
or, for an async-reset flop after async2sync, the Y bit of the $mux async2sync put behind it
(B = the flop's Q). Module-level `connect` aliases are followed.

usage: python3 reg_corr.py gold.il gate.il
"""
import re
import sys
from collections import defaultdict

TOK = re.compile(r"\{|\}|\d+'[01xzm-]+|[\\$]\S+(?: \[\d+(?::\d+)?\])?")


def parse(path):
    width, cells, conns, cur = {}, [], [], None
    for line in open(path):
        if line.startswith("  wire "):
            p = line.split()
            w = int(p[p.index("width") + 1]) if "width" in p else 1
            off = int(p[p.index("offset") + 1]) if "offset" in p else 0
            width[p[-1]] = (w, off)
        elif line.startswith("  cell "):
            p = line.split()
            cur = (p[1], p[2], {})
            cells.append(cur)
        elif line.startswith("    connect ") and cur is not None:
            _, port, sig = line.split(None, 2)
            cur[2][port] = sig.strip()
        elif line.startswith("  end"):
            cur = None
        elif line.startswith("  connect "):
            rest = line[len("  connect "):].strip()
            conns.append(rest)
    return width, cells, conns


def expand(sig, width):
    """sigspec -> list of bit ids, LSB first (constants -> None)."""
    out = []
    for t in TOK.findall(sig):
        if t in "{}":
            continue
        if "'" in t and t[0].isdigit():
            out = [None] * len(t.split("'")[1]) + out
            continue
        m = re.match(r"^(\S+)(?: \[(\d+)(?::(\d+))?\])?$", t)
        name, hi, lo = m.group(1), m.group(2), m.group(3)
        w, off = width.get(name, (1, 0))
        if hi is None:
            idx = list(range(off, off + w))
        elif lo is None:
            idx = [int(hi)]
        else:
            idx = list(range(int(lo), int(hi) + 1))
        # a 1-bit wire is one bit however it is referenced (\n or \n [0])
        bits_ = [name if w == 1 else "%s[%d]" % (name, i) for i in idx]
        out = bits_ + out           # later chunks are less significant in {a b}: prepend earlier
    return out


def expand_concat(sig, width):
    # {a b c}: a is MSB. expand() above builds LSB-first by prepending each chunk.
    return expand(sig, width)


def split_connect(rest):
    # "lhs rhs": the first sigspec is either {...} or one chunk
    s = rest
    if s.startswith("{"):
        d = 0
        for i, ch in enumerate(s):
            d += ch == "{"
            d -= ch == "}"
            if d == 0:
                return s[:i + 1], s[i + 1:].strip()
    m = re.match(r"^(\S+(?: \[\d+(?::\d+)?\])?) (.*)$", s)
    return m.group(1), m.group(2)


def reg_names(path):
    width, cells, conns = parse(path)
    alias = defaultdict(set)
    for rest in conns:
        a, b = split_connect(rest)
        for x, y in zip(expand(a, width), expand(b, width)):
            if x and y:
                alias[x].add(y)
                alias[y].add(x)
    q = {}
    for t, n, pc in cells:
        if re.match(r"^\$(a|s|al|)dff(e|ce|sr|sre)?$|^\$ff$", t) and "\\Q" in pc:
            for b in expand(pc["\\Q"], width):
                if b:
                    q[b] = n
    for t, n, pc in cells:
        if t == "$mux" and "async2sync" in n:
            for bb, yb in zip(expand(pc.get("\\B", ""), width), expand(pc.get("\\Y", ""), width)):
                if bb in q:
                    q.pop(bb)
                    q[yb] = n

    def closure(b):
        seen, todo = {b}, [b]
        while todo:
            x = todo.pop()
            for y in alias.get(x, ()):
                if y not in seen:
                    seen.add(y)
                    todo.append(y)
        return seen

    regs, anon = set(), 0
    for net in q:
        pub = [x for x in closure(net) if x.startswith("\\")]
        if pub:
            regs.update(pub)
        else:
            anon += 1
    return regs, len(q), anon


g_regs, g_n, g_anon = reg_names(sys.argv[1])
t_regs, t_n, t_anon = reg_names(sys.argv[2])
print("gold: %d register bits, %d without a public name" % (g_n, g_anon))
print("gate: %d register bits, %d without a public name" % (t_n, t_anon))
both = g_regs & t_regs
print("public register-bit names on both sides: %d" % len(both))
only_g = sorted(g_regs - t_regs)
only_t = sorted(t_regs - g_regs)
print("gold register names absent from gate's register names: %d" % len(only_g))
for x in only_g[:60]:
    print("   gold-only", x)
print("gate register names absent from gold's register names: %d" % len(only_t))
for x in only_t[:60]:
    print("   gate-only", x)


def reg_nets(path):
    """list of (set of public names) per register bit"""
    width, cells, conns = parse(path)
    alias = defaultdict(set)
    for rest in conns:
        a, b = split_connect(rest)
        for x, y in zip(expand(a, width), expand(b, width)):
            if x and y:
                alias[x].add(y)
                alias[y].add(x)
    q = {}
    for t, n, pc in cells:
        if re.match(r"^\$(a|s|al|)dff(e|ce|sr|sre)?$|^\$ff$", t) and "\Q" in pc:
            for b in expand(pc["\Q"], width):
                if b:
                    q[b] = n
    for t, n, pc in cells:
        if t == "$mux" and "async2sync" in n:
            for bb, yb in zip(expand(pc.get("\B", ""), width), expand(pc.get("\Y", ""), width)):
                if bb in q:
                    q.pop(bb)
                    q[yb] = n
    out = []
    for net in q:
        seen, todo = {net}, [net]
        while todo:
            x = todo.pop()
            for y in alias.get(x, ()):
                if y not in seen:
                    seen.add(y)
                    todo.append(y)
        out.append(frozenset(x for x in seen if x.startswith("\\")))
    return out


gn = reg_nets(sys.argv[1])
tn = reg_nets(sys.argv[2])
t_all = set().union(*tn)
g_all = set().union(*gn)
g_unmatched = [s for s in gn if not (s & t_all)]
t_unmatched = [s for s in tn if not (s & g_all)]
print("\nNET LEVEL: gold register bits with no gate register name on the net: %d" % len(g_unmatched))
import collections
c = collections.Counter(re.sub(r"\[\d+\]", "[]", min(s) if s else "?") for s in g_unmatched)
for k, v in c.most_common(60):
    print("  %5d  %s" % (v, k))
print("NET LEVEL: gate register bits with no gold register name on the net: %d" % len(t_unmatched))
for s in t_unmatched[:20]:
    print("   ", sorted(s)[:3])
