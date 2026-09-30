"""FLOW_JOURNAL Incident 89: which FREE gold-only flops influence the gold outputs that differ from
gate? For each free flop, flip its Q input (all patterns) and record which of the listed gold
outputs change.  usage: python sensitivity.py gold.aig pairs.json spec.json sim.txt"""
import json
import random
import sys

exec(open(__file__.replace("sensitivity.py", "aigsim.py")).read().split("g_path, t_path = sys.argv")[0])
aig, pj, sj, simf = sys.argv[1:5]
P = json.load(open(pj))
S = json.load(open(sj))
I, outs, ands, ins, onames = read_aig(aig)
pin = {v: k for k, v in ins.items()}
oidx = {v: k for k, v in onames.items()}
diff_names = [l.split()[2] for l in open(simf) if l.startswith("DIFF")]
dcols = [oidx[n] for n in diff_names]
W = 4
nb = 64 * W
mask = (1 << nb) - 1
rnd = random.Random(1)
pis = [rnd.getrandbits(nb) for _ in range(I)]
for k, v in S["const"].items():
    pis[pin["lec_q_g%05d" % int(k)]] = mask if v else 0
for k, p in S["dup"].items():
    pis[pin["lec_q_g%05d" % int(k)]] = pis[pin["lec_q_p%05d" % p]]
base = simulate(I, outs, ands, pis, mask)
free = [k for k in range(len(P["gold_only"])) if str(k) not in S["const"] and str(k) not in S["dup"]]
print("free gold-only flops: %d, differing outputs: %d" % (len(free), len(dcols)))
for k in free:
    q = pin["lec_q_g%05d" % k]
    p2 = list(pis)
    p2[q] ^= mask
    o = simulate(I, outs, ands, p2, mask)
    hit = [diff_names[j] for j, c in enumerate(dcols) if o[c] != base[c]]
    anyhit = sum(1 for c in range(len(o)) if o[c] != base[c])
    if hit or anyhit:
        print("%-70s affects %d listed / %d total outputs: %s" % (P["gold"][P["gold_only"][k]]["names"][:1], len(hit), anyhit, hit[:4]))
