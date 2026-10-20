"""FLOW_JOURNAL Incident 89: cofactor an AIGER file - replace chosen primary inputs (by symbol name)
by constants; everything else unchanged (the input stays, unused). A case split over all values of
the chosen inputs covers the whole input space, so proving every cofactor proves the original.
usage: python cofactor.py in.aig out.aig name=0,name=1,..."""
import sys

src, dst, spec = sys.argv[1:4]
fix = {}
for kv in spec.split(","):
    k, v = kv.split("=")
    fix[k] = int(v)
d = open(src, "rb").read()
nl = d.index(b"\n")
M, I, L, O, A = map(int, d[:nl].split()[1:6])
assert L == 0
pos = nl + 1
olits = []
for _ in range(O):
    e = d.index(b"\n", pos)
    olits.append(int(d[pos:e]))
    pos = e + 1


def dec():
    global pos
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
    lhs = 2 * (I + k + 1)
    r0 = lhs - dec()
    r1 = r0 - dec()
    ands.append((r0, r1))
symtab = d[pos:]
ins = {}
for line in symtab.split(b"\n"):
    if line[:1] == b"i" and b" " in line:
        h, _, n = line.partition(b" ")
        if h[1:].isdigit():
            ins[n.decode("latin1")] = int(h[1:])
sub = {}
for n, v in fix.items():
    var = ins[n] + 1
    sub[var] = v


def s(l):
    v = l >> 1
    if v in sub:
        return sub[v] ^ (l & 1)
    return l


def enc(x):
    out = bytearray()
    while x & ~0x7F:
        out.append((x & 0x7F) | 0x80)
        x >>= 7
    out.append(x)
    return bytes(out)


body = bytearray()
for k, (a, b) in enumerate(ands):
    lhs = 2 * (I + k + 1)
    a, b = s(a), s(b)
    r0, r1 = max(a, b), min(a, b)
    body += enc(lhs - r0) + enc(r0 - r1)
outs = [s(o) for o in olits]
open(dst, "wb").write(("aig %d %d 0 %d %d\n" % (M, I, O, A)).encode() + b"".join(b"%d\n" % x for x in outs)
                      + bytes(body) + symtab)
print("%s: %d inputs fixed" % (dst, len(fix)))
