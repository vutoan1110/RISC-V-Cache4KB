"""FLOW_JOURNAL Incident 89: bit-parallel random simulation of two combinational AIGER files with
identical PI/PO order; lists every output position that differs on some pattern.
usage: python aigsim.py gold.aig gate.aig [words=4] [seed=1] [fix=name=0|1,...]

fix: optional comma-separated input constraints by symbol name (e.g. to tie an input to a constant).
"""
import random
import sys


def read_aig(path):
    d = open(path, "rb").read()
    nl = d.index(b"\n")
    hdr = d[:nl].split()
    assert hdr[0] == b"aig", "binary AIGER only"
    M, I, L, O, A = map(int, hdr[1:6])
    assert L == 0, "combinational only"
    pos = nl + 1
    outs = []
    for _ in range(O):
        e = d.index(b"\n", pos)
        outs.append(int(d[pos:e]))
        pos = e + 1

    def dec():
        nonlocal pos
        x, sh = 0, 0
        while True:
            b = d[pos]
            pos += 1
            x |= (b & 0x7F) << sh
            if not b & 0x80:
                return x
            sh += 7

    ands = []
    for k in range(A):
        lhs = 2 * (I + L + k + 1)
        d0 = dec()
        d1 = dec()
        r0 = lhs - d0
        r1 = r0 - d1
        ands.append((r0, r1))
    ins, onames = {}, {}
    for line in d[pos:].split(b"\n"):
        if line[:1] in (b"i", b"o") and b" " in line:
            h, _, n = line.partition(b" ")
            if h[1:].isdigit():
                (ins if line[:1] == b"i" else onames)[int(h[1:])] = n.decode("latin1")
    return I, outs, ands, ins, onames


def simulate(I, outs, ands, pis, mask):
    val = [0] * (I + len(ands) + 1)
    for k in range(I):
        val[k + 1] = pis[k]

    def lit(l):
        v = val[l >> 1]
        return (v ^ mask) if (l & 1) else v

    base = I + 1
    for k, (a, b) in enumerate(ands):
        val[base + k] = lit(a) & lit(b)
    return [lit(o) for o in outs]


g_path, t_path = sys.argv[1], sys.argv[2]
words = int(sys.argv[3]) if len(sys.argv) > 3 else 4
seed = int(sys.argv[4]) if len(sys.argv) > 4 else 1
fix = {}
if len(sys.argv) > 5 and sys.argv[5]:
    for kv in sys.argv[5].split(","):
        k, v = kv.split("=")
        fix[k] = int(v)
gI, gO, gA, gin, gon = read_aig(g_path)
tI, tO, tA, tin, ton = read_aig(t_path)
assert gI == tI and len(gO) == len(tO)
nbits = 64 * words
mask = (1 << nbits) - 1
rnd = random.Random(seed)
pis = []
for k in range(gI):
    name = gin.get(k, "")
    if name in fix:
        pis.append(mask if fix[name] else 0)
    else:
        pis.append(rnd.getrandbits(nbits))
go = simulate(gI, gO, gA, pis, mask)
to = simulate(tI, tO, tA, pis, mask)
bad = [k for k in range(len(go)) if go[k] != to[k]]
print("inputs %d, outputs %d, patterns %d: %d outputs differ" % (gI, len(go), nbits, len(bad)))
for k in bad:
    print("DIFF %d %s" % (k, gon.get(k, "?")))
