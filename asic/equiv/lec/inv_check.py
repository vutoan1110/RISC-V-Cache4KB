"""FLOW_JOURNAL Incident 89: one-hot invariant of the re-encoded FSM registers, on gold.

    python inv_check.py mk     gold_inv.aig inv_proof.aig     # outputs "not exactly one hot(D)" per group
    python inv_check.py reset  gold_inv.aig pairs.json        # reset code of each group is one-hot

gold_inv.aig (evert.py --inv) has every bit of each group's Q driven by an exact one-hot decoder
and exposes the D bits as lec_inv_<group>_<bit>. If ABC proves every output of inv_proof.aig
constant 0, then "Q one-hot => D one-hot" for all inputs and all other state; with a one-hot reset
code the registers are one-hot in every reachable state, which is what the LEC assumes.
"""
import json
import random
import re
import sys
from collections import defaultdict

exec(open(__file__.replace("inv_check.py", "aigsim.py")).read().split("g_path, t_path = sys.argv")[0])


def raw(path):
    d = open(path, "rb").read()
    nl = d.index(b"\n")
    M, I, L, O, A = map(int, d[:nl].split()[1:6])
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
    return M, I, A, olits, d[pos:p]


def enc(x):
    out = bytearray()
    while x & ~0x7F:
        out.append((x & 0x7F) | 0x80)
        x >>= 7
    out.append(x)
    return bytes(out)


mode = sys.argv[1]
I_, outs, ands, ins, onames = read_aig(sys.argv[2])
groups = defaultdict(dict)
for k, n in onames.items():
    m = re.match(r"lec_inv_(.+)_(\d+)$", n)
    if m:
        groups[m.group(1)][int(m.group(2))] = outs[k]

if mode == "mk":
    M, I, A, olits, andbytes = raw(sys.argv[2])
    new = bytearray()
    nxt = [M]

    def AND(a, b):
        nxt[0] += 1
        lhs = 2 * nxt[0]
        r0, r1 = max(a, b), min(a, b)
        new.extend(enc(lhs - r0) + enc(r0 - r1))
        return lhs

    def OR(a, b):
        return AND(a ^ 1, b ^ 1) ^ 1

    res = []
    for gname in sorted(groups):
        ds = [groups[gname][b] for b in sorted(groups[gname])]
        none = 1                                  # literal 1 = true
        for x in ds:
            none = AND(none, x ^ 1)               # all zero
        two = 0                                   # literal 0 = false
        for i in range(len(ds)):
            for j in range(i + 1, len(ds)):
                two = OR(two, AND(ds[i], ds[j]))
        res.append(OR(none, two))
        print("group %-15s %2d bits -> check output" % (gname, len(ds)))
    Mn = nxt[0]
    An = A + (Mn - M)
    hdr = ("aig %d %d 0 %d %d\n" % (Mn, I, len(res), An)).encode()
    open(sys.argv[3], "wb").write(hdr + b"".join(b"%d\n" % x for x in res) + andbytes + bytes(new))
    print("wrote %s: %d outputs, all must be 0" % (sys.argv[3], len(res)))

if mode == "reset":
    P = json.load(open(sys.argv[3]))
    pin = {v: k for k, v in ins.items()}
    reset_pis = [pin["reset_n"]]
    for k, (i, j) in enumerate(P["pairs"]):
        if any(n.replace(" [", "[") in ("\\reset_sync_q", "\\reset_meta_q") for n in P["gold"][i]["names"]):
            reset_pis.append(pin["lec_q_p%05d" % k])
    nb = 256
    mask = (1 << nb) - 1
    rnd = random.Random(5)
    pis = [0 if k in reset_pis else rnd.getrandbits(nb) for k in range(I_)]
    o = simulate(I_, outs, ands, pis, mask)
    oidx = {}
    for k, n in onames.items():
        oidx[n] = k
    ok = True
    for gname in sorted(groups):
        vals = []
        for b in sorted(groups[gname]):
            v = o[oidx["lec_inv_%s_%d" % (gname, b)]]
            vals.append(1 if v == mask else (0 if v == 0 else None))
        good = None not in vals and sum(vals) == 1
        ok &= good
        print("group %-15s reset code (bit0..) %s -> %s" % (gname, vals, "one-hot" if good else "NOT one-hot"))
    sys.exit(0 if ok else 1)
