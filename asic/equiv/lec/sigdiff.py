"""FLOW_JOURNAL Incident 89: where do two pure multiplier AIGs (same 66 PIs, same 64 POs) differ
structurally?  Every AND node of both is simulated on the same random patterns; a node whose signature
(up to complement) has no partner in the other AIG is "unmatched".  Prints, per AIG, the number of
unmatched nodes, their level histogram and the outputs that are unmatched.  A few unmatched nodes means
SAT sweeping (fraig / &cec) should work; a large unmatched band means the adder trees were built in a
different order and internal equivalences are missing (the hard case for CEC).
usage: python sigdiff.py a.aig b.aig [words=64]"""
import random
import sys

exec(open(__file__.replace("sigdiff.py", "aigsim.py")).read().split("g_path, t_path = sys.argv")[0])


def sigs(path, pis, mask):
    I, outs, ands, ins, onames = read_aig(path)
    val = [0] * (I + len(ands) + 1)
    lev = [0] * (I + len(ands) + 1)
    for k in range(I):
        val[k + 1] = pis[k]

    def lit(l):
        v = val[l >> 1]
        return (v ^ mask) if (l & 1) else v

    base = I + 1
    for k, (a, b) in enumerate(ands):
        val[base + k] = lit(a) & lit(b)
        lev[base + k] = 1 + max(lev[a >> 1], lev[b >> 1])
    return I, outs, ands, val, lev


def canon(v, mask):
    return min(v, v ^ mask)


words = int(sys.argv[3]) if len(sys.argv) > 3 else 64
nbits = 64 * words
mask = (1 << nbits) - 1
rnd = random.Random(5)
pis = [rnd.getrandbits(nbits) for _ in range(66)]
A = sigs(sys.argv[1], pis, mask)
B = sigs(sys.argv[2], pis, mask)
setA = {canon(v, mask) for v in A[3][A[0] + 1:]}
setB = {canon(v, mask) for v in B[3][B[0] + 1:]}
for tag, X, other in (("A", A, setB), ("B", B, setA)):
    I, outs, ands, val, lev = X
    un = [n for n in range(I + 1, I + 1 + len(ands)) if canon(val[n], mask) not in other]
    hist = {}
    for n in un:
        hist[lev[n]] = hist.get(lev[n], 0) + 1
    uo = [k for k, o in enumerate(outs) if (o >> 1) > I and canon(val[o >> 1], mask) not in other]
    print("%s %s: %d AND, %d unmatched" % (tag, sys.argv[1] if tag == "A" else sys.argv[2], len(ands), len(un)))
    print("   unmatched by level:", " ".join("L%d:%d" % (l, hist[l]) for l in sorted(hist)))
    print("   unmatched outputs :", uo)

if len(sys.argv) > 4:                    # debug: show the first few unmatched low-level nodes of A
    I, outs, ands, val, lev = A
    ins = read_aig(sys.argv[1])[3]

    def expr(l, depth):
        n, c = l >> 1, l & 1
        if n == 0:
            s = "0"
        elif n <= I:
            s = ins.get(n - 1, "i%d" % (n - 1))
        elif depth == 0:
            s = "n%d" % n
        else:
            a, b = ands[n - I - 1]
            s = "(%s & %s)" % (expr(a, depth - 1), expr(b, depth - 1))
        return ("!" + s) if c else s

    shown = 0
    for n in range(I + 1, I + 1 + len(ands)):
        if lev[n] <= int(sys.argv[4]) and canon(val[n], mask) not in setB:
            print("   n%d L%d = %s" % (n, lev[n], expr(2 * n, 3)))
            shown += 1
            if shown >= 12:
                break
