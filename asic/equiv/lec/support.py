"""FLOW_JOURNAL Incident 89: structural input support of named outputs in two AIGs; prints the
inputs that only one side depends on (mapped back to RTL register names via pairs.json).
usage: python support.py gold.aig gate.aig pairs.json out_name [out_name ...]"""
import json
import sys

exec(open(__file__.replace("support.py", "aigsim.py")).read().split("g_path, t_path = sys.argv")[0])
g, t, pj = sys.argv[1:4]
names = sys.argv[4:]
P = json.load(open(pj))


def label(pi_name):
    if pi_name.startswith("lec_q_p"):
        i, j = P["pairs"][int(pi_name[7:])]
        return pi_name + " " + (P["gold"][i]["names"] or ["?"])[0]
    if pi_name.startswith("lec_q_g"):
        return pi_name + " gold-only " + (P["gold"][P["gold_only"][int(pi_name[7:])]]["names"] or ["?"])[0]
    return pi_name


def supports(path):
    I, outs, ands, ins, onames = read_aig(path)
    oidx = {v: k for k, v in onames.items()}
    res = {}
    for n in names:
        lit = outs[oidx[n]]
        seen, stack, sup = set(), [lit >> 1], set()
        while stack:
            v = stack.pop()
            if v in seen or v == 0:
                continue
            seen.add(v)
            if v <= I:
                sup.add(ins.get(v - 1, "pi%d" % (v - 1)))
            else:
                a, b = ands[v - I - 1]
                stack.append(a >> 1)
                stack.append(b >> 1)
        res[n] = sup
    return res


sg, st = supports(g), supports(t)
for n in names:
    a, b = sg[n], st[n]
    print("== %s: gold support %d, gate support %d" % (n, len(a), len(b)))
    for x in sorted(a - b)[:15]:
        print("   gold only:", label(x))
    for x in sorted(b - a)[:15]:
        print("   gate only:", label(x))
