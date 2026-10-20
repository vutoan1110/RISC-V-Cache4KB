"""FLOW_JOURNAL Incident 89 (Option A): algebraic proof that a word-level multiplier network (the
$and/$not/$fa/$alu cells that Yosys maccmap builds for the ALU $macc/$mul) computes
    product[63:0] == signed33(A) * signed33(B)  (mod 2^64)
on its operand bits.  The network is read from an RTLIL snapshot taken right after the techmap iteration
in which maccmap ran (the CSA grouping is then fixed and visible as word-level cells).

Method: backward rewriting over the ring Z/2^64 with Boolean (multilinear) polynomials.  Start from
P = sum_k 2^k * product[k] and substitute every cell output bit, in reverse topological order, by the exact
integer polynomial of the cell:
    $fa   : Y_i := A_i + B_i + C_i - 2*X_i   (exact integer identity of a full adder), then
            X_i := A_i B_i + A_i C_i + B_i C_i - 2 A_i B_i C_i   (only if X_i is still present)
    $alu/$add/$sub : sum_{k<W} 2^k Y_k := A' + B'' + CI  (A', B'' extended, B'' = ~B if BI), allowed only
            when P contains the Y bits exactly as c * sum 2^k Y_k with c * 2^W == 0 (mod 2^64)
    bitwise/fine-grained gates : their exact polynomials (and: ab, not: 1-a, xor: a+b-2ab, ...)
A multilinear polynomial over Z/2^64 is a unique representation of a function {0,1}^n -> Z/2^64, so
P == spec (coefficient-wise) iff the 64 product bits equal the spec for every operand value.  The proof is
complete (no sampling).  Negative controls: --neg-spec unsigned (wrong spec) and --mutate (break one
$fa input) must both FAIL.

usage: python macc_alg.py snapshot.il[.gz] --a <wire> --b <wire> --p <wire> [--a-alt <wire>] [--b-alt <wire>]
                          [--neg-spec unsigned] [--mutate]
  --a/--b: 33-bit operand wires (bit 32 = sign extension bit); --a-alt/--b-alt: optional 32-bit wires
  whose bits are also accepted as operand bits 0..31 (the $macc may read src_a instead of mul_a[31:0]).
"""
import argparse
import sys
from collections import defaultdict

MOD = 1 << 64
MASK = MOD - 1

ap = argparse.ArgumentParser()
ap.add_argument("il")
ap.add_argument("--module", default=r"\soc_asic_top")
ap.add_argument("--a", required=True)
ap.add_argument("--b", required=True)
ap.add_argument("--p", required=True)
ap.add_argument("--a-alt", default=None)
ap.add_argument("--b-alt", default=None)
ap.add_argument("--neg-spec", default=None, choices=[None, "unsigned"])
ap.add_argument("--mutate", default=None, choices=[None, "pp", "ci"])
ap.add_argument("--max-monomials", type=int, default=200000)
args = ap.parse_args()

# ---------------------------------------------------------------- RTLIL parsing (one module)
wires = {}          # name -> (width, offset, upto)
cells = []          # (type, name, params{}, conns{port: [bits]})
aliases = []        # (lhs bits, rhs bits)


def parse_const(tok):
    if "'" in tok:
        w, bits = tok.split("'", 1)
        w = int(w)
        bits = bits[-w:] if len(bits) >= w else bits
        return [("C", ch) for ch in reversed(bits)] + [("C", "0")] * (w - len(bits))
    v = int(tok)
    return [("C", "1" if (v >> k) & 1 else "0") for k in range(32)]


def wire_bits(name, lo=None, hi=None):
    if name not in wires:
        raise KeyError("unknown wire %s" % name)
    w, off, upto = wires[name]
    if lo is None:
        idx = list(range(off, off + w))
    else:
        if upto:
            raise NotImplementedError("upto wire %s" % name)
        a, b = (hi, lo) if hi is not None else (lo, lo)
        idx = list(range(min(a, b), max(a, b) + 1))
    return [(name, k) for k in idx]


def parse_sig(toks, pos):
    """parse one sigspec starting at toks[pos]; return (bits LSB-first, new pos)."""
    t = toks[pos]
    if t == "{":
        pos += 1
        chunks = []
        while toks[pos] != "}":
            bits, pos = parse_sig(toks, pos)
            chunks.append(bits)
        pos += 1
        out = []
        for c in reversed(chunks):          # concatenation is MSB-first
            out += c
        return out, pos
    if t[0] in "\\$":
        pos += 1
        if pos < len(toks) and toks[pos].startswith("["):
            sel = toks[pos].strip("[]")
            pos += 1
            if ":" in sel:
                hi, lo = map(int, sel.split(":"))
                return wire_bits(t, lo, hi), pos
            return wire_bits(t, int(sel)), pos
        return wire_bits(t), pos
    return parse_const(t), pos + 1


def tokenize(line):
    return line.replace("{", " { ").replace("}", " } ").split()


import gzip
with (gzip.open(args.il, "rt", encoding="latin1") if args.il.endswith(".gz") else open(args.il, "r", encoding="latin1")) as f:
    in_mod = False
    cur = None
    depth_other = 0
    pending_lines = []
    for raw in f:
        line = raw.strip()
        if not line or line.startswith("attribute") or line.startswith("#"):
            continue
        tk = line.split()
        if tk[0] == "module":
            in_mod = args.module is None or tk[1] == args.module
            if in_mod and args.module is None:
                args.module = tk[1]
            continue
        if not in_mod:
            continue
        if depth_other:
            if tk[0] == "end":
                depth_other -= 1
            elif tk[0] in ("switch", "case", "process", "memory"):
                pass
            continue
        if tk[0] == "wire":
            w, off, upto = 1, 0, False
            k = 1
            while k < len(tk) - 1:
                if tk[k] == "width":
                    w = int(tk[k + 1]); k += 2
                elif tk[k] == "offset":
                    off = int(tk[k + 1]); k += 2
                elif tk[k] == "upto":
                    upto = True; k += 1
                elif tk[k] in ("input", "output", "inout"):
                    k += 2
                elif tk[k] == "signed":
                    k += 1
                else:
                    k += 1
            wires[tk[-1]] = (w, off, upto)
        elif tk[0] == "cell":
            cur = [tk[1], tk[2], {}, {}]
        elif tk[0] == "parameter" and cur is not None:
            v = tk[-1]
            try:
                cur[2][tk[-2].lstrip("\\")] = int(v.split("'")[1], 2) if "'" in v else int(v)
            except ValueError:
                cur[2][tk[-2].lstrip("\\")] = v
        elif tk[0] == "connect" and cur is not None:
            toks = tokenize(line)
            pending_lines.append(("cellconn", cur, toks[1].lstrip("\\"), toks))
        elif tk[0] == "connect":
            pending_lines.append(("alias", None, None, tokenize(line)))
        elif tk[0] == "end":
            if cur is not None:
                cells.append(cur)
                cur = None
            else:
                in_mod = False
        elif tk[0] in ("process", "memory"):
            depth_other = 1 if tk[0] == "process" else 0
            if tk[0] == "memory":
                continue

for kind, cell, port, toks in pending_lines:
    if kind == "cellconn":
        bits, _ = parse_sig(toks, 2)
        cell[3][port] = bits
    else:
        lhs, p = parse_sig(toks, 1)
        rhs, _ = parse_sig(toks, p)
        assert len(lhs) == len(rhs), toks
        aliases.append((lhs, rhs))
print("parsed module %s: %d wires, %d cells, %d connects" % (args.module, len(wires), len(cells), len(aliases)))

# ---------------------------------------------------------------- canonical bits (union-find)
parent = {}


def find(x):
    root = x
    while parent.get(root, root) != root:
        root = parent[root]
    while parent.get(x, x) != root:
        parent[x], x = root, parent[x]
    return root


def union(a, b):
    ra, rb = find(a), find(b)
    if ra == rb:
        return
    if ra[0] == "C" and rb[0] == "C":
        raise ValueError("constant conflict %s %s" % (ra, rb))
    if ra[0] == "C":
        parent[rb] = ra
    else:
        parent[ra] = rb


for lhs, rhs in aliases:
    for a, b in zip(lhs, rhs):
        union(a, b)

OUTPORTS = {"$fa": ("X", "Y"), "$alu": ("X", "Y", "CO"), "$lcu": ("P", "G", "CO")}
driver = {}          # canonical bit -> (cell index, port, bit index)
multi = set()
for ci, (typ, name, par, con) in enumerate(cells):
    outs = OUTPORTS.get(typ, ("Y", "Q"))
    for port in outs:
        for k, b in enumerate(con.get(port, [])):
            cb = find(b)
            if cb[0] == "C":
                continue
            if cb in driver:
                multi.add(cb)             # fatal only if the multiplier cone reads it (checked below)
            driver[cb] = (ci, port, k)

# ---------------------------------------------------------------- leaves, roots
A = [find(b) for b in wire_bits(args.a)]
B = [find(b) for b in wire_bits(args.b)]
P = [find(b) for b in wire_bits(args.p)][:64]
assert len(A) == 33 and len(B) == 33 and len(P) == 64, (len(A), len(B), len(P))
leafname = {}
for k, b in enumerate(A):
    leafname[b] = "A%d" % k
for k, b in enumerate(B):
    leafname[b] = "B%d" % k
if args.a_alt:
    for k, b in enumerate(wire_bits(args.a_alt)[:32]):
        cb = find(b)
        if cb != A[k]:
            if cb in leafname:
                raise ValueError("a-alt bit %d aliases another leaf" % k)
            leafname[cb] = "A%d" % k
if args.b_alt:
    for k, b in enumerate(wire_bits(args.b_alt)[:32]):
        cb = find(b)
        if cb != B[k]:
            if cb in leafname:
                raise ValueError("b-alt bit %d aliases another leaf" % k)
            leafname[cb] = "B%d" % k
if len({b for b in A + B}) != 66:
    raise ValueError("operand bits are not 66 distinct nets")

# ---------------------------------------------------------------- cone units and topological order
BITWISE1 = {"$not", "$pos", "$buf"}
BITWISE2 = {"$and", "$or", "$xor", "$xnor"}
FINE = {"$_AND_", "$_OR_", "$_XOR_", "$_XNOR_", "$_NOT_", "$_BUF_", "$_NAND_", "$_NOR_", "$_ANDNOT_",
        "$_ORNOT_", "$_MUX_"}
WORD = {"$alu", "$add", "$sub"}


def ext(bits, width, signed):
    bits = list(bits[:width])
    if len(bits) < width:
        fill = bits[-1] if (signed and bits) else ("C", "0")
        bits += [fill] * (width - len(bits))
    return bits


def unit_of(cb):
    if cb in multi:
        raise ValueError("multiplier cone reads multi-driven net %s" % (cb,))
    ci, port, k = driver[cb]
    typ = cells[ci][0]
    if typ in WORD:
        return (ci, -1)
    if typ == "$lcu":
        raise NotImplementedError("$lcu in cone")
    return (ci, k)


def unit_inputs(u):
    ci, k = u
    typ, name, par, con = cells[ci]
    if typ in WORD:
        W = par["Y_WIDTH"]
        ins = ext(con["A"], W, par.get("A_SIGNED", 0)) + ext(con["B"], W, par.get("B_SIGNED", 0))
        ins += con.get("CI", []) + con.get("BI", [])
        return ins
    if typ == "$fa":
        return [con["A"][k], con["B"][k], con["C"][k]]
    if typ in BITWISE1 or typ in BITWISE2:
        W = par["Y_WIDTH"]
        ins = [ext(con["A"], W, par.get("A_SIGNED", 0))[k]]
        if typ in BITWISE2:
            ins.append(ext(con["B"], W, par.get("B_SIGNED", 0))[k])
        return ins
    if typ == "$mux":
        return [con["A"][k], con["B"][k], con["S"][0]]
    if typ in FINE:
        return [con[p][0] for p in ("A", "B", "S") if p in con]
    raise NotImplementedError("cell type %s (%s) in cone" % (typ, name))


order = []           # units in topological order (inputs before outputs)
state = {}
cone_types = defaultdict(int)
stack = [(unit_of(b), 0) for b in P if b[0] != "C" and b not in leafname]
for p in P:
    if p[0] != "C" and p not in leafname and p not in driver:
        raise ValueError("product bit %s undriven" % (p,))
while stack:
    u, st = stack.pop()
    if st == 0:
        if u in state:
            continue
        state[u] = 1
        stack.append((u, 1))
        for b in unit_inputs(u):
            cb = find(b)
            if cb[0] == "C" or cb in leafname:
                continue
            if cb not in driver:
                raise ValueError("LEAK: cone reaches undriven/non-operand net %s via %s" % (cb, cells[u[0]][1]))
            v = unit_of(cb)
            if state.get(v) == 1 and v not in order:
                if v != u:
                    pass
            if v not in state:
                stack.append((v, 0))
    else:
        order.append(u)
        cone_types[cells[u[0]][0]] += 1
print("cone: %d units; by cell type: %s" % (len(order), dict(cone_types)))
cfgs = sorted({(cells[u[0]][0], tuple(sorted(cells[u[0]][2].items()))) for u in order})
for t, p in cfgs:
    print("   cell config: %s %s" % (t, " ".join("%s=%s" % kv for kv in p)))

# ---------------------------------------------------------------- optional mutation (negative control)
# (structure-preserving bugs, so the rewriting stays small and the proof must FAIL with a clear diff:
#  pp = one partial-product AND reads the wrong multiplier bit; ci = the final adder gets carry-in 1)
leaf_by_name = {nm: cb for cb, nm in leafname.items() if cb in set(A + B)}
if args.mutate == "pp":
    for u in order:
        typ, name, par, con = cells[u[0]]
        if typ == "$and" and u[1] < len(con["B"]):
            nb = leafname.get(find(con["B"][u[1]]), "")
            if nb.startswith("B") and int(nb[1:]) < 31:
                con["B"] = list(con["B"])
                con["B"][u[1]] = leaf_by_name["B%d" % (int(nb[1:]) + 1)]
                print("MUTATION: %s.B[%d] rewired %s -> B%d" % (name, u[1], nb, int(nb[1:]) + 1))
                break
elif args.mutate == "ci":
    for u in order:
        typ, name, par, con = cells[u[0]]
        if typ == "$alu":
            con["CI"] = [("C", "1")]
            print("MUTATION: %s.CI tied to 1" % name)
            break

# ---------------------------------------------------------------- polynomial machinery
var_id = {}
var_name = []


def V(cb):
    cb = find(cb)
    if cb[0] == "C":
        return None
    if cb not in var_id:
        var_id[cb] = len(var_name)
        var_name.append(leafname.get(cb, "%s[%d]" % cb))
    return var_id[cb]


def lit(b):
    """polynomial (dict) of one input bit"""
    cb = find(b)
    if cb[0] == "C":
        if cb[1] == "1":
            return {frozenset(): 1}
        if cb[1] == "0":
            return {}
        raise ValueError("x/z constant in cone")
    return {frozenset([V(cb)]): 1}


def padd(p, q, c=1):
    r = dict(p)
    for m, v in q.items():
        r[m] = (r.get(m, 0) + c * v) & MASK
        if not r[m]:
            del r[m]
    return r


def pmul(p, q):
    r = {}
    for m1, v1 in p.items():
        for m2, v2 in q.items():
            m = m1 | m2
            r[m] = (r.get(m, 0) + v1 * v2) & MASK
            if not r[m]:
                del r[m]
    return r


ONE = {frozenset(): 1}


def pnot(p):
    return padd(ONE, p, -1)


def pxor(p, q):
    return padd(padd(p, q), pmul(p, q), -2)


def por(p, q):
    return padd(padd(p, q), pmul(p, q), -1)


poly = {}
occ = defaultdict(set)


def add_term(m, c):
    c &= MASK
    if not c:
        return
    v = (poly.get(m, 0) + c) & MASK
    if v:
        if m not in poly:
            for x in m:
                occ[x].add(m)
        poly[m] = v
    else:
        if m in poly:
            del poly[m]
            for x in m:
                occ[x].discard(m)


def substitute(x, q):
    ms = list(occ.get(x, ()))
    for m in ms:
        c = poly.pop(m)
        for y in m:
            occ[y].discard(m)
        rest = m - {x}
        for qm, qc in q.items():
            add_term(rest | qm, c * qc)
    occ.pop(x, None)


for k, b in enumerate(P):
    for m, c in lit(b).items():
        add_term(m, c << k)

peak = len(poly)
for u in reversed(order):
    ci, k = u
    typ, name, par, con = cells[ci]
    if typ == "$fa":
        a, bb, c = (lit(con[p][k]) for p in ("A", "B", "C"))
        y = V(con["Y"][k]) if find(con["Y"][k])[0] != "C" else None
        x = V(con["X"][k]) if find(con["X"][k])[0] != "C" else None
        if y is not None and occ.get(y):
            q = padd(padd(a, bb), c)
            if x is not None:
                q = padd(q, {frozenset([x]): 1}, -2)
            else:
                q = padd(q, pmul(pmul(a, bb), ONE), 0)
                raise NotImplementedError("fa with constant carry output")
            substitute(y, q)
        if x is not None and occ.get(x):
            ab, ac, bc = pmul(a, bb), pmul(a, c), pmul(bb, c)
            q = padd(padd(padd(ab, ac), bc), pmul(ab, c), -2)
            substitute(x, q)
    elif typ in WORD:
        W = par["Y_WIDTH"]
        ybits = [find(b) for b in con["Y"]]
        yv = [var_id.get(b) for b in ybits]
        for port in ("X", "CO"):
            for b in con.get(port, []):
                cb = find(b)
                if cb in var_id and occ.get(var_id[cb]):
                    raise NotImplementedError("%s.%s used in the cone" % (name, port))
        present = [v for v in yv if v is not None and occ.get(v)]
        if present:
            cY0 = None
            for kk, v in enumerate(yv):
                if v is None or not occ.get(v):
                    coef = 0
                else:
                    ms = occ[v]
                    if ms != {frozenset([v])}:
                        raise NotImplementedError("%s.Y[%d] appears non-linearly" % (name, kk))
                    coef = poly[frozenset([v])]
                if cY0 is None:
                    cY0 = coef
                if coef != (cY0 << kk) & MASK:
                    raise NotImplementedError("%s.Y coefficients are not c*2^k (bit %d)" % (name, kk))
            if (cY0 << W) & MASK:
                raise NotImplementedError("%s: c*2^W != 0 mod 2^64 (W=%d)" % (name, W))
            for v in present:
                m = frozenset([v])
                add_term(m, -poly[m])
                occ.pop(v, None)
            Aw = ext(con["A"], W, par.get("A_SIGNED", 0))
            Bw = ext(con["B"], W, par.get("B_SIGNED", 0))
            if typ == "$alu":
                bi, cin = lit(con["BI"][0]), lit(con["CI"][0])
                if bi not in ({}, ONE):
                    raise NotImplementedError("non-constant BI")
                inv = bi == ONE
            else:
                inv = typ == "$sub"
                cin = ONE if inv else {}
            tot = {}
            for kk in range(W):
                tot = padd(tot, lit(Aw[kk]), 1 << kk)
                bk = lit(Bw[kk])
                tot = padd(tot, pnot(bk) if inv else bk, 1 << kk)
            tot = padd(tot, cin)
            for m, c in tot.items():
                add_term(m, cY0 * c)
    else:
        outs = {}
        if typ in BITWISE1 or typ in BITWISE2 or typ == "$mux":
            W = par.get("Y_WIDTH", par.get("WIDTH"))
            ins = [lit(b) for b in unit_inputs(u)]
            ybit = con["Y"][k]
        else:
            ins = [lit(b) for b in unit_inputs(u)]
            ybit = con["Y"][0]
        t = typ.strip("$_").lower()
        if t in ("and",):
            q = pmul(ins[0], ins[1])
        elif t in ("or",):
            q = por(ins[0], ins[1])
        elif t in ("xor",):
            q = pxor(ins[0], ins[1])
        elif t in ("xnor",):
            q = pnot(pxor(ins[0], ins[1]))
        elif t in ("not",):
            q = pnot(ins[0])
        elif t in ("pos", "buf"):
            q = ins[0]
        elif t == "nand":
            q = pnot(pmul(ins[0], ins[1]))
        elif t == "nor":
            q = pnot(por(ins[0], ins[1]))
        elif t == "andnot":
            q = pmul(ins[0], pnot(ins[1]))
        elif t == "ornot":
            q = por(ins[0], pnot(ins[1]))
        elif t == "mux":
            q = padd(ins[0], pmul(ins[2], padd(ins[1], ins[0], -1)))
        else:
            raise NotImplementedError(typ)
        cy = find(ybit)
        if cy[0] != "C" and cy in var_id and occ.get(var_id[cy]):
            substitute(var_id[cy], q)
    peak = max(peak, len(poly))
    if len(poly) > args.max_monomials:
        print("RESULT: NOT PROVED - polynomial blow-up (%d monomials > %d) at %s" % (len(poly), args.max_monomials, name))
        sys.exit(3)

left = {var_name[x] for m in poly for x in m if not var_name[x][:1] in "AB" or not var_name[x][1:].isdigit()}
if left:
    print("FAIL: non-operand variables remain:", sorted(left)[:10])
    sys.exit(2)

# ---------------------------------------------------------------- spec
spec = {}


def leaf_poly(prefix, n, signed):
    p = {}
    for k in range(n):
        name = "%s%d" % (prefix, k)
        cb = [b for b, nm in leafname.items() if nm == name]
        vid = V(cb[0])
        w = -(1 << k) if (signed and k == n - 1) else (1 << k)
        p = padd(p, {frozenset([vid]): 1}, w)
    return p


signed = args.neg_spec != "unsigned"
spec = pmul(leaf_poly("A", 33, signed), leaf_poly("B", 33, signed))
# the netlist may use a-alt/b-alt nets for bits 0..31: map every leaf variable to its operand name
by_name = defaultdict(set)
for cb, nm in leafname.items():
    if cb in var_id:
        by_name[nm].add(var_id[cb])
canon_var = {}
for nm, vs in by_name.items():
    r = min(vs)
    for v in vs:
        canon_var[v] = r


def canon_poly(p):
    r = {}
    for m, c in p.items():
        mm = frozenset(canon_var.get(x, x) for x in m)
        r[mm] = (r.get(mm, 0) + c) & MASK
        if not r[mm]:
            del r[mm]
    return r


diff = padd(canon_poly(poly), canon_poly(spec), -1)
print("final polynomial: %d monomials (peak %d); spec: %d monomials; spec=%s%s"
      % (len(poly), peak, len(spec), "signed33*signed33" if signed else "UNSIGNED (negative control)",
         "; MUTATED netlist (%s, negative control)" % args.mutate if args.mutate else ""))
if diff:
    ex = sorted(diff.items(), key=lambda t: len(t[0]))[:5]
    print("RESULT: NOT PROVED - %d monomials differ, e.g. %s"
          % (len(diff), [("*".join(sorted(var_name[x] for x in m)) or "1", hex(c)) for m, c in ex]))
    sys.exit(1)
print("RESULT: PROVED  sum_k 2^k product[k] == signed33(A)*signed33(B) (mod 2^64)")
