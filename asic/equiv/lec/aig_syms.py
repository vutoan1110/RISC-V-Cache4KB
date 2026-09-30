"""FLOW_JOURNAL Incident 89: compare the PI/PO symbol tables of two AIGER files position by
position (ABC's two-circuit &cec pairs inputs and outputs by ORDER, so the orders must agree).
usage: python aig_syms.py a.aig b.aig"""
import sys


def syms(p):
    d = open(p, "rb").read()
    ins, outs = {}, {}
    for line in d.split(b"\n"):
        if line[:1] in (b"i", b"o") and b" " in line:
            h, _, n = line.partition(b" ")
            if h[1:].isdigit():
                (ins if line[:1] == b"i" else outs)[int(h[1:])] = n.decode("latin1")
    return [ins[k] for k in sorted(ins)], [outs[k] for k in sorted(outs)]


ai, ao = syms(sys.argv[1])
bi, bo = syms(sys.argv[2])
print("inputs %d / %d, outputs %d / %d" % (len(ai), len(bi), len(ao), len(bo)))
di = [k for k, (x, y) in enumerate(zip(ai, bi)) if x != y]
do = [k for k, (x, y) in enumerate(zip(ao, bo)) if x != y]
print("input positions that differ: %d, output positions that differ: %d" % (len(di), len(do)))
for k in di[:5]:
    print("  in ", k, ai[k], "|", bi[k])
for k in do[:5]:
    print("  out", k, ao[k], "|", bo[k])
sys.exit(1 if (di or do or len(ai) != len(bi) or len(ao) != len(bo)) else 0)
