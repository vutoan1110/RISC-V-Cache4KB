"""FLOW_JOURNAL Incident 89: check pure multiplier AIGs (66 inputs A0..A32, B0..B32; 64 outputs) against
integer arithmetic: P = signed33(A) * signed33(B) mod 2^64.  usage: python mulref.py x.aig [y.aig ...]"""
import random
import sys

exec(open(__file__.replace("mulref.py", "aigsim.py")).read().split("g_path, t_path = sys.argv")[0])
N = 2048
rnd = random.Random(11)
vecs = []
for _ in range(N):
    a = rnd.getrandbits(33)
    b = rnd.getrandbits(33)
    if rnd.random() < 0.25:
        a = (1 << 33) - 1 - rnd.getrandbits(4)          # corner: near -1
    vecs.append((a, b))
mask = (1 << N) - 1


def s33(x):
    return x - (1 << 33) if x >> 32 else x


for path in sys.argv[1:]:
    I, outs, ands, ins, onames = read_aig(path)
    assert I == 66 and len(outs) == 64, (I, len(outs))
    pis = []
    for k in range(66):
        v = 0
        for j, (a, b) in enumerate(vecs):
            bit = (a >> k) & 1 if k < 33 else (b >> (k - 33)) & 1
            v |= bit << j
        pis.append(v)
    o = simulate(I, outs, ands, pis, mask)
    bad = 0
    for j, (a, b) in enumerate(vecs):
        p = (s33(a) * s33(b)) & ((1 << 64) - 1)
        got = sum(((o[k] >> j) & 1) << k for k in range(64))
        bad += got != p
    print("%-28s %d vectors vs signed33*signed33: %d mismatches" % (path, N, bad))
