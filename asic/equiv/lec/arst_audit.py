"""2026-10-13: structural audit of the asynchronous resets for the register-mapped LEC.

The mapped D-function proof runs on async2sync models: a reset is only seen at a clock edge, so a reset that asserts
between two edges is outside that proof. This audit closes the structural part of that gap on the flattened models
BEFORE async2sync (gold_pre.il = RTL + fsm, and a gate model = the final netlist with the formal PDK cell models):
for every flop bit present on both sides (paired by public Q name), it checks that
  * both have an asynchronous reset or neither has one,
  * both resets resolve (through aliases and $not / $_NOT_ / $buf / $_BUF_ cells) to the same root signal,
  * both are active at the same level of that root and load the same value.
Then, whenever the root reset is active (also between clock edges), both sides hold the same value in every paired
bit, and the clocked mapped proof covers everything after the reset is released. Unpaired bits are listed (on the
gold side these are the bits synthesis removed, covered by the constant / duplicate proofs of the LEC).
Streams the RTLIL; no Yosys, SAT or simulation.
usage: python arst_audit.py gold_pre.il gate_pre.il out.json"""
import json
import re
import sys
from collections import Counter, defaultdict

FLOP_FINE = {   # fine-grained flop cells: (async reset?, active level, value)
    "$_DFF_P_": (False, None, None), "$_DFF_N_": (False, None, None),
    "$_DFF_PN0_": (True, 0, 0), "$_DFF_PN1_": (True, 0, 1), "$_DFF_PP0_": (True, 1, 0), "$_DFF_PP1_": (True, 1, 1),
    "$_DFF_NN0_": (True, 0, 0), "$_DFF_NN1_": (True, 0, 1), "$_DFF_NP0_": (True, 1, 0), "$_DFF_NP1_": (True, 1, 1),
}
KEEP = {"$not", "$_NOT_", "$buf", "$_BUF_", "$pos"}
# evert.py MANUAL_ALIASES: the UART receive register is named rx_data_reg in RTL and rx_data_o after synthesis
MANUAL_ALIASES = {"\\u_soc.u_uart.u_uart_core.rx_block.rx_data_reg[%d]" % i:
                  "\\u_soc.u_uart.u_uart_core.rx_block.rx_data_o[%d]" % i for i in range(5)}
TOK = re.compile(r"\{|\}|\d+'[01xzm-]*|[\\$][^\s\[\]{}]+(?:\s*\[\d+(?::\d+)?\])?")


class Model:
    def __init__(self, path):
        self.width, self.offset = {}, {}
        self.cells = []                      # (type, params, conns)
        self.connects = []
        top, cur, depth = None, None, 0
        in_top = False
        for line in open(path, encoding="utf-8", errors="replace"):
            s = line.rstrip("\n")
            if s.startswith("module "):
                in_top = False
                if top is None or s.split()[1] == "\\soc_asic_top":
                    in_top = s.split()[1] == "\\soc_asic_top"
                continue
            if not in_top:
                continue
            if s.startswith("  wire "):
                p = s.split()
                name = p[-1]
                w = int(p[p.index("width") + 1]) if "width" in p else 1
                o = int(p[p.index("offset") + 1]) if "offset" in p else 0
                self.width[name], self.offset[name] = w, o
            elif s.startswith("  cell "):
                p = s.split()
                keep = p[1] in KEEP or "dff" in p[1].lower() or "latch" in p[1].lower()
                cur = (p[1], {}, {}) if keep else None   # logic cells are not needed: keeps the 0.5 GB gate model small
            elif s.startswith("    parameter ") and cur is not None:
                p = s.split(None, 2)
                cur[1][p[1]] = p[2]
            elif s.startswith("    connect ") and cur is not None:
                p = s.split(None, 2)
                cur[2][p[1]] = p[2]
            elif s == "  end" and cur is not None:
                self.cells.append(cur)
                cur = None
            elif s.startswith("  connect "):
                a, b = self.split2(s[len("  connect "):])
                self.connects.append((a, b))
            elif s == "end":
                in_top = False

    @staticmethod
    def split2(text):
        """split 'sigA sigB' of a module-level connect into the two sigspecs (token based, see bits())"""
        toks = text.split()
        if toks[0] == "{":
            depth, k = 0, 0
            for k, t in enumerate(toks):
                depth += (t == "{") - (t == "}")
                if depth == 0:
                    break
            k += 1
        else:
            k = 1
            if k < len(toks) and re.match(r"^\[\d+(?::\d+)?\]$", toks[k]):
                k += 1
        if k >= len(toks):
            raise ValueError("cannot split connect: " + text[:80])
        return " ".join(toks[:k]), " ".join(toks[k:])

    def bits(self, sig):
        """sigspec -> list of bits, LSB first; a bit is (name, index) or ('const', '0'|'1'|'x').
        RTLIL writes identifiers as whitespace-free tokens (they may contain '[' and ']', e.g. g_bank[0]); a bit
        select is a separate token ' [n]' / ' [n:m]'; a concatenation is '{ item ... }', most significant item first."""
        toks = sig.split()
        items, i, depth = [], 0, 0             # items of the outermost level, MSB first
        stack = [[]]
        while i < len(toks):
            t = toks[i]
            if t == "{":
                stack.append([])
            elif t == "}":
                inner = stack.pop()
                bits_ = []
                for it in reversed(inner):       # MSB-first items -> LSB-first bits
                    bits_.extend(it)
                stack[-1].append(bits_)
            elif re.match(r"^\d+'[01xzm-]*$", t):
                n, v = t.split("'")
                n = int(n)
                v = v.rjust(n, "0")[-n:] if v else "0" * n
                stack[-1].append([("const", ch) for ch in reversed(v)])
            elif re.match(r"^-?\d+$", t):          # plain integer constant: 32 bits
                v = int(t) & 0xFFFFFFFF
                stack[-1].append([("const", str((v >> k) & 1)) for k in range(32)])
            elif t[0] in "\\$":
                name = t
                sel = None
                if i + 1 < len(toks):
                    m = re.match(r"^\[(\d+)(?::(\d+))?\]$", toks[i + 1])
                    if m:
                        sel = (int(m.group(1)), None if m.group(2) is None else int(m.group(2)))
                        i += 1
                if sel is None:
                    o = self.offset.get(name, 0)
                    stack[-1].append([(name, o + k) for k in range(self.width.get(name, 1))])
                elif sel[1] is None:
                    stack[-1].append([(name, sel[0])])
                else:
                    a, b = sel
                    stack[-1].append([(name, k) for k in (range(b, a + 1) if a >= b else range(b, a - 1, -1))])
            else:
                raise ValueError("unexpected sigspec token %r in %r" % (t, sig[:120]))
            i += 1
        top = stack[0]
        out = []
        for it in reversed(top):               # a top level with several items is a concatenation too
            out.extend(it)
        return out


def analyse(path):
    m = Model(path)
    parent = {}

    def find(x):
        while parent.get(x, x) != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            if ra[0] == "const":
                ra, rb = rb, ra
            parent[ra] = rb                     # constants stay roots
    for a, b in m.connects:
        for x, y in zip(m.bits(a), m.bits(b)):
            union(x, y)
    for typ, par, con in m.cells:               # buffers are aliases (the formal cell models drive Q through buf)
        if typ in ("$buf", "$_BUF_", "$pos"):
            for x, z in zip(m.bits(con.get("\\A", "")), m.bits(con.get("\\Y", ""))):
                union(z, x)
    inv_drv = {}                                # output bit root -> (input bit, inverted)
    flops = []                                  # (q bit, has_arst, arst bit, level, value)
    types = Counter()
    for typ, par, con in m.cells:
        if typ in ("$buf", "$_BUF_", "$pos"):
            continue
        if typ in ("$not", "$_NOT_"):
            a, y = m.bits(con.get("\\A", "")), m.bits(con.get("\\Y", ""))
            for x, z in zip(a, y):
                inv_drv[find(z)] = (x, True)
        elif typ in ("$adff", "$dff"):
            types[typ] += 1
            q = m.bits(con["\\Q"])
            if typ == "$adff":
                pol = int(par["\\ARST_POLARITY"].strip().split("'")[-1][-1]) if "'" in par["\\ARST_POLARITY"] else int(par["\\ARST_POLARITY"])
                val = par["\\ARST_VALUE"].strip()
                vbits = val.split("'")[1][::-1] if "'" in val else bin(int(val))[2:][::-1]
                rst = m.bits(con["\\ARST"])[0]
                for k, qb in enumerate(q):
                    flops.append((qb, True, rst, pol, vbits[k] if k < len(vbits) else "0"))
            else:
                for qb in q:
                    flops.append((qb, False, None, None, None))
        elif typ in FLOP_FINE:
            types[typ] += 1
            has, lvl, val = FLOP_FINE[typ]
            qb = m.bits(con["\\Q"])[0]
            rst = m.bits(con["\\R"])[0] if has else None
            flops.append((qb, has, rst, lvl, str(val) if has else None))
        elif "dff" in typ.lower() or "latch" in typ.lower():
            types["UNSUPPORTED " + typ] += 1

    def resolve(bit):
        inv, seen = 0, 0
        r = find(bit)
        while r in inv_drv and seen < 10000:
            src, i = inv_drv[r]
            inv ^= int(i)
            r = find(src)
            seen += 1
        return r, inv
    def bitname(x):
        # as evert.py: "\name [3]" of a wide wire and "\name[3]" (a 1-bit wire literally named with brackets) are the
        # same RTL bit; a 1-bit wire is named without an index
        n = x[0] if m.width.get(x[0], 1) == 1 and m.offset.get(x[0], 0) == 0 and x[1] == 0 else "%s [%d]" % x
        n = n.replace(" [", "[")
        return MANUAL_ALIASES.get(n, n)
    names = defaultdict(set)                    # root of a Q bit -> public names of its alias class
    for x in list(parent) + [f[0] for f in flops]:
        if x[0] != "const" and x[0].startswith("\\") and find(x)[0] != "const":
            names[find(x)].add(bitname(x))
    info = {}
    for qb, has, rst, lvl, val in flops:
        key = find(qb)
        if key[0] == "const":
            types["Q tied to a constant (anomaly)"] += 1
            continue
        if has:
            root, inv = resolve(rst)
            active_root_level = lvl ^ inv
            info[key] = ("ARST", bitname(root), active_root_level, val)
        else:
            info[key] = ("NONE", None, None, None)
    by_name = {}
    for key, rec in info.items():
        for n in names.get(key, {bitname(key)}):
            by_name[n] = rec
    return by_name, types


gold, gtypes = analyse(sys.argv[1])
gate, ttypes = analyse(sys.argv[2])
common = sorted(set(gold) & set(gate))
mism = [(n, gold[n], gate[n]) for n in common if gold[n] != gate[n]]
roots = Counter((r[1], r[2]) for r in list(gold.values()) + list(gate.values()) if r[0] == "ARST")
summary = {
    "gold_flop_cells": dict(gtypes), "gate_flop_cells": dict(ttypes),
    "gold_named_bits": len(gold), "gate_named_bits": len(gate), "paired_names": len(common),
    "paired_with_async_reset": sum(1 for n in common if gold[n][0] == "ARST"),
    "paired_without_async_reset": sum(1 for n in common if gold[n][0] == "NONE"),
    "mismatches": len(mism), "reset_roots_and_active_levels": {"%s active %s" % k: v for k, v in roots.items()},
    "gold_only_names": len(set(gold) - set(gate)), "gate_only_names": len(set(gate) - set(gold)),
    "first_mismatches": [[n, list(a), list(b)] for n, a, b in mism[:20]],
    "verdict": "PASS" if not mism and not any(k.startswith("UNSUPPORTED") or "anomaly" in k
                                              for k in list(gtypes) + list(ttypes)) else "FAIL",
}
json.dump(summary, open(sys.argv[3], "w"), indent=1)
for k, v in summary.items():
    if k != "first_mismatches":
        print("%s: %s" % (k, v))
for n, a, b in mism[:10]:
    print("MISMATCH", n, a, b)
sys.exit(0 if summary["verdict"] == "PASS" else 1)
