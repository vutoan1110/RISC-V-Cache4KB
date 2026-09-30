"""FLOW_JOURNAL Incident 89 (Option A): cut-and-substitute proof of the ALU multiplier.

The AIGs come from build_pair on *_x.il (alu.mul_a / alu.mul_b / alu.product exposed, not cut).

    python mulsub.py extract side.aig pure.aig
        The pure multiplier of one side: the cone of product[0..63], cut at the AIG nodes of the
        operand nets mul_a[0..32] / mul_b[0..32] (which become the 66 inputs A0..A32, B0..B32).
        FAILS if the cone reaches any other input (the cut would then be incomplete).
    python mulsub.py subst gold.aig gate.aig targets.txt pure_gold.aig gold_cone.aig gate_sub.aig
        gold_cone = the target outputs of gold, unchanged.
        gate_sub  = the target outputs of gate, where EVERY use of the node of product[k] is replaced by
                    pure_gold's output k evaluated on gate's own operand nodes.
        Sound because extract+`&cec pure_gold pure_gate` proves pure_gold(A,B) == pure_gate(A,B) for
        all A, B, and product_gate[k] == pure_gate_k(mul_a_gate, mul_b_gate) exactly (extract checks the
        cut is complete), so gate_sub computes the same function as gate for every output that reads a
        product node - including consumers that opt_merge made share such a node (e.g. the AND op).
"""
import sys

exec(open(__file__.replace("mulsub.py", "aigsim.py")).read().split("g_path, t_path = sys.argv")[0])
BASE = "u_soc.u_core.u_pipeline.datapath.alu."


def load(path):
    I, outs, ands, ins, onames = read_aig(path)
    oidx = {v: k for k, v in onames.items()}
    opa = [outs[oidx[BASE + "mul_a[%d]" % k]] for k in range(33)]
    opb = [outs[oidx[BASE + "mul_b[%d]" % k]] for k in range(33)]
    prod = [outs[oidx[BASE + "product[%d]" % k]] for k in range(64)]
    return I, outs, ands, ins, onames, oidx, opa, opb, prod


def enc(x):
    out = bytearray()
    while x & ~0x7F:
        out.append((x & 0x7F) | 0x80)
        x >>= 7
    out.append(x)
    return bytes(out)


class Builder:
    """emit a new AIG with nI inputs; AND nodes numbered after the inputs, strashed."""

    def __init__(self, nI):
        self.nI = nI
        self.ands = []                  # (a, b) literals
        self.hash = {}

    def AND(self, a, b):
        if a == 0 or b == 0 or a == (b ^ 1):
            return 0
        if a == 1:
            return b
        if b == 1 or a == b:
            return a
        if a < b:
            a, b = b, a
        key = (a, b)
        if key in self.hash:
            return self.hash[key]
        lit = 2 * (self.nI + len(self.ands) + 1)
        self.ands.append((a, b))
        self.hash[key] = lit
        return lit

    def write(self, path, outs, sym_in=None, sym_out=None):
        M = self.nI + len(self.ands)
        body = bytearray()
        for k, (a, b) in enumerate(self.ands):
            lhs = 2 * (self.nI + k + 1)
            body += enc(lhs - a) + enc(a - b)
        sym = b""
        if sym_in:
            sym += b"".join(b"i%d %s\n" % (k, n.encode()) for k, n in enumerate(sym_in))
        if sym_out:
            sym += b"".join(b"o%d %s\n" % (k, n.encode()) for k, n in enumerate(sym_out))
        open(path, "wb").write(("aig %d %d 0 %d %d\n" % (M, self.nI, len(outs), len(self.ands))).encode()
                               + b"".join(b"%d\n" % o for o in outs) + bytes(body) + sym)


def copy_cone(I, ands, roots, b, leaf):
    """iterative DFS copy of the cones of `roots` (literals) into builder b.
    leaf(var) -> literal in b for a var that must not be expanded (or None to expand / map PI)."""
    memo = {0: 0}

    def get(lit):
        return memo[lit >> 1] ^ (lit & 1)

    for r in roots:
        stack = [r >> 1]
        while stack:
            v = stack[-1]
            if v in memo:
                stack.pop()
                continue
            lf = leaf(v)
            if lf is not None:
                memo[v] = lf
                stack.pop()
                continue
            if v <= I:
                raise KeyError(v)
            a, c = ands[v - I - 1]
            pend = [x >> 1 for x in (a, c) if (x >> 1) not in memo]
            if pend:
                stack.extend(pend)
                continue
            memo[v] = b.AND(get(a), get(c))
            stack.pop()
    return [get(r) for r in roots]


if sys.argv[1] == "extract":
    src, dst = sys.argv[2:4]
    I, outs, ands, ins, onames, oidx, opa, opb, prod = load(src)
    opmap = {}
    for k, l in enumerate(opa + opb):
        if l > 1 and (l >> 1) not in opmap:
            opmap[l >> 1] = 2 * (k + 1) ^ (l & 1)     # var value = input_k XOR complement
    const_ops = [k for k, l in enumerate(opa + opb) if l <= 1]
    b = Builder(66)
    leaks = set()

    def leaf(v):
        if v in opmap:
            return opmap[v]
        if v <= I:
            leaks.add(ins.get(v - 1, "pi%d" % (v - 1)))
            return 0
        return None

    po = copy_cone(I, ands, prod, b, leaf)
    names_in = ["A%d" % k for k in range(33)] + ["B%d" % k for k in range(33)]
    b.write(dst, po, names_in, ["P%d" % k for k in range(64)])
    print("%s: pure multiplier, %d AND nodes; constant operand bits %s; LEAKS %d %s"
          % (dst, len(b.ands), const_ops, len(leaks), sorted(leaks)[:8]))
    sys.exit(1 if leaks else 0)

if sys.argv[1] == "subst":
    gsrc, tsrc, tfile, pure, gdst, tdst = sys.argv[2:8]
    targets = [l.strip() for l in open(tfile) if l.strip()]
    # gold cone, unchanged
    I, outs, ands, ins, onames, oidx, opa, opb, prod = load(gsrc)
    b = Builder(I)
    go = copy_cone(I, ands, [outs[oidx[n]] for n in targets], b,
                   lambda v: (2 * v) if v <= I else None)
    b.write(gdst, go, [ins.get(k, "pi%d" % k) for k in range(I)], targets)
    print("%s: %d outputs, %d AND nodes" % (gdst, len(go), len(b.ands)))
    # gate with product nodes substituted
    TI, touts, tands, tins, tonames, toidx, topa, topb, tprod = load(tsrc)
    assert TI == I and all(tins.get(k) == ins.get(k) for k in range(I)), "input order differs"
    PI_, pouts, pands, pins, ponames = read_aig(pure)
    assert PI_ == 66 and len(pouts) == 64
    b = Builder(I)
    # 1. operand literals of gate, copied into b
    opl = copy_cone(I, tands, topa + topb, b, lambda v: (2 * v) if v <= I else None)
    # 2. instantiate pure gold multiplier on them
    pmemo = {0: 0}
    for k in range(66):
        pmemo[k + 1] = opl[k]

    def pget(l):
        return pmemo[l >> 1] ^ (l & 1)

    for k, (a, c) in enumerate(pands):
        pmemo[66 + k + 1] = b.AND(pget(a), pget(c))
    newprod = [pget(o) for o in pouts]
    # 3. copy gate targets; any product node var -> substituted literal
    sub = {}
    for k, l in enumerate(tprod):
        if l > 1:
            v = l >> 1
            val = newprod[k] ^ (l & 1)            # var value = product_k XOR complement
            if v in sub and sub[v] != val:
                print("  note: two product bits share node %d" % v)
            sub.setdefault(v, val)

    def tleaf(v):
        if v in sub:
            return sub[v]
        if v <= I:
            return 2 * v
        return None

    to = copy_cone(I, tands, [touts[toidx[n]] for n in targets], b, tleaf)
    b.write(tdst, to, [ins.get(k, "pi%d" % k) for k in range(I)], targets)
    print("%s: %d outputs, %d AND nodes, %d product nodes substituted" % (tdst, len(to), len(b.ands), len(sub)))
