"""FLOW_JOURNAL Incident 89: keep only selected outputs of an AIGER file (all inputs and AND nodes
kept; unused logic is swept by ABC). Used to cut the multiplier cone (the outputs the SAT pass
could not close) out of both LEC sides, same outputs in the same order.
usage: python outsel.py in.aig out.aig name1,name2,...   or   @file_with_names"""
import sys

src, dst, sel = sys.argv[1:4]
names = [l.strip() for l in open(sel[1:])] if sel.startswith("@") else sel.split(",")
names = [n for n in names if n]
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
p = pos
for _ in range(2 * A):
    while d[p] & 0x80:
        p += 1
    p += 1
andbytes = d[pos:p]
ins, outs = {}, {}
for line in d[p:].split(b"\n"):
    if line[:1] in (b"i", b"o") and b" " in line:
        h, _, n = line.partition(b" ")
        if h[1:].isdigit():
            (ins if line[:1] == b"i" else outs)[int(h[1:])] = n
oidx = {v.decode("latin1"): k for k, v in outs.items()}
new = [olits[oidx[n]] for n in names]
sym = b"".join(b"i%d %s\n" % (k, v) for k, v in sorted(ins.items()))
sym += b"".join(b"o%d %s\n" % (k, n.encode()) for k, n in enumerate(names))
open(dst, "wb").write(("aig %d %d 0 %d %d\n" % (M, I, len(new), A)).encode() +
                      b"".join(b"%d\n" % x for x in new) + andbytes + sym)
print("%s: kept %d of %d outputs" % (dst, len(new), O))
