"""2026-10-13: report whether every output of a binary AIGER file (an ABC &sat -z result) is the constant-0 literal,
i.e. every proof obligation was proved. Prints "ALL_PROVED n" or "NOT_PROVED k of n" and exits 0 / 1.
usage: python aig_outputs_zero.py file.aig"""
import sys

d = open(sys.argv[1], "rb").read()
nl = d.index(b"\n")
hdr = d[:nl].split()
if hdr[0] != b"aig":
    sys.exit("not a binary AIGER file: %r" % hdr[0])
M, I, L, O, A = map(int, hdr[1:6])
pos = nl + 1
for _ in range(L):                       # latch lines (none expected) precede the outputs
    pos = d.index(b"\n", pos) + 1
lits = []
for _ in range(O):
    e = d.index(b"\n", pos)
    lits.append(int(d[pos:e].split()[0]))
    pos = e + 1
open_ = sum(1 for x in lits if x != 0)
if open_ == 0:
    print("ALL_PROVED %d outputs constant 0" % O)
    sys.exit(0)
print("NOT_PROVED %d of %d outputs not constant 0" % (open_, O))
sys.exit(1)
