"""FLOW_JOURNAL Incident 89 negative control for the step-A substitution: a WRONG pure multiplier
(outputs 5 and 6 of the good one swapped).  Substituting it must make the 34-output &cec fail.
usage: python mk_badmul.py good.aig bad.aig"""
import sys

d = open(sys.argv[1], "rb").read()
nl = d.index(b"\n")
M, I, L, O, A = map(int, d[:nl].split()[1:6])
lines = d[nl + 1:].split(b"\n", O)
outs, rest = lines[:O], lines[O]
outs[5], outs[6] = outs[6], outs[5]
open(sys.argv[2], "wb").write(d[:nl + 1] + b"\n".join(outs) + b"\n" + rest)
print("%s: outputs 5 and 6 swapped" % sys.argv[2])
