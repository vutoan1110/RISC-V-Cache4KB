"""FLOW_JOURNAL Incident 89: random simulation of the two pure multipliers (66 inputs A0..A32, B0..B32),
free and with the RTL relation mul_a[32] = mul_a_signed & src_a[31] (so A32 => A31, B32 => B31).
usage: python puresim.py pure_gold.aig pure_gate.aig"""
import random
import sys

exec(open(__file__.replace("puresim.py", "aigsim.py")).read().split("g_path, t_path = sys.argv")[0])
g = read_aig(sys.argv[1])
t = read_aig(sys.argv[2])
nb = 64 * 64
mask = (1 << nb) - 1
for mode in ("free", "constrained"):
    rnd = random.Random(3)
    tot = 0
    bad = set()
    for rep in range(4):
        pis = [rnd.getrandbits(nb) for _ in range(66)]
        if mode == "constrained":
            pis[32] &= pis[31]            # A32 <= A31
            pis[65] &= pis[64]            # B32 <= B31
        og = simulate(g[0], g[1], g[2], pis, mask)
        ot = simulate(t[0], t[1], t[2], pis, mask)
        for k in range(64):
            if og[k] != ot[k]:
                bad.add(k)
        tot += nb
    print("%-12s %d patterns: outputs differing %s" % (mode, tot, sorted(bad)))
