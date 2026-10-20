"""FLOW_JOURNAL Incident 89: the gold-only flops (bits synthesis removed) for the register-mapped LEC.

    python const_check.py analyze gold_god.aig pairs.json spec.json
    python const_check.py mkproof gold_god_tied.aig spec.json proof.aig

analyze:
  * dup: a gold-only flop whose public names are also names of a gate flop already paired with
    another gold flop is a duplicate synthesis merged -> {"dup": {gold_only_k: pair_k}}.
  * const: reset value = D of the flop with every reset source asserted (top reset_n and the
    reset synchroniser flops at 0) over random patterns. Candidates C = flops whose reset value is a
    constant. Greatest fixpoint by simulation: with the Q of every flop in C tied to its value and
    EVERYTHING else random (including reset), drop any flop whose D ever differs from its value.
    -> {"const": {gold_only_k: value}}. The survivors are then PROVED by `mkproof` + ABC.
mkproof: from the gold AIG built WITH the const ties (evert.py --spec) and with gold-only D exposed,
  keep one output per const flop, D xor value; ABC must prove every output constant 0. Together
  with "reset value == value" this is an induction: the flops never leave their values.
"""
import json
import random
import sys

sys.setrecursionlimit(10000)
exec(open(__file__.replace("const_check.py", "aigsim.py")).read().split("g_path, t_path = sys.argv")[0])


def pi_index(ins):
    return {v: k for k, v in ins.items()}


if sys.argv[1] == "analyze":
    aig, pj, out = sys.argv[2:5]
    P = json.load(open(pj))
    I, outs, ands, ins, onames = read_aig(aig)
    pin = pi_index(ins)
    oidx = {v: k for k, v in onames.items()}
    gold, gate = P["gold"], P["gate"]

    def norm(n):
        return n.replace(" [", "[")

    # duplicates
    gate_name = {}
    for j, f in enumerate(gate):
        for n in f["names"]:
            gate_name.setdefault(norm(n), set()).add(j)
    pair_of_gate = {j: k for k, (i, j) in enumerate(P["pairs"])}
    dup = {}
    for k, i in enumerate(P["gold_only"]):
        cand = set()
        for n in gold[i]["names"]:
            cand |= gate_name.get(norm(n), set())
        if len(cand) == 1:
            dup[k] = pair_of_gate[cand.pop()]
    # reset sources
    reset_pis = [pin["reset_n"]] if "reset_n" in pin else []
    for k, (i, j) in enumerate(P["pairs"]):
        if any(norm(n) in ("\\reset_sync_q", "\\reset_meta_q") for n in gold[i]["names"]):
            reset_pis.append(pin["lec_q_p%05d" % k])
    print("reset sources:", [ins[p] for p in reset_pis])
    W = 16
    nb = 64 * W
    mask = (1 << nb) - 1
    rnd = random.Random(7)

    def run(ties, forced):
        pis = []
        for k in range(I):
            if k in ties:
                pis.append(mask if ties[k] else 0)
            elif k in forced:
                pis.append(mask if forced[k] else 0)
            else:
                pis.append(rnd.getrandbits(nb))
        return simulate(I, outs, ands, pis, mask)

    dout = {k: oidx["lec_d_g%05d" % k] for k in range(len(P["gold_only"]))}
    rv = {}
    for rep in range(4):
        o = run({}, {p: 0 for p in reset_pis})
        for k, oi in dout.items():
            v = o[oi]
            val = 0 if v == 0 else (1 if v == mask else None)
            if rep == 0:
                rv[k] = val
            elif rv.get(k) != val:
                rv[k] = None
    C = {k: v for k, v in rv.items() if v is not None and k not in dup}
    print("gold-only %d: dup %d, reset-constant candidates %d" % (len(P["gold_only"]), len(dup), len(C)))
    while True:
        drop = set()
        ties = {pin["lec_q_g%05d" % k]: v for k, v in C.items()}
        for rep in range(8):
            o = run(ties, {})
            for k, v in C.items():
                if o[dout[k]] != (mask if v else 0):
                    drop.add(k)
        if not drop:
            break
        for k in drop:
            del C[k]
        print("  dropped %d, %d left" % (len(drop), len(C)))
    free = [k for k in range(len(P["gold_only"])) if k not in C and k not in dup]
    if "--fdup" not in sys.argv:
        # the simulation-based functional-duplicate search below proposed nonsense partners on this
        # design (Incident 89); it is off by default. Real merged duplicates come from the name-based
        # search above and from RTL-justified entries in spec_manual.py.
        json.dump({"const": {str(k): v for k, v in sorted(C.items())}, "dup": {str(k): v for k, v in sorted(dup.items())},
                   "free": free}, open(out, "w"), indent=1)
        print("const %d, dup %d, free %d" % (len(C), len(dup), len(free)))
        sys.exit(0)
    # functional duplicates: synthesis (opt_merge) merged a gold flop into another flop with the same
    # D and reset, whose NAME differs. Find a paired flop whose gold D equals this flop's D on every
    # pattern; the tie is justified later by the lec_d_x comparison (D of the duplicate vs gate D of
    # the partner) inside the LEC itself. Two sub-passes: Q of the candidate independent, then Q
    # of the candidate made equal to the partner's Q (for hold-type D = en ? x : Q).
    dpo = {k: oidx["lec_d_p%05d" % k] for k in range(len(P["pairs"]))}
    qpi = {k: pin["lec_q_p%05d" % k] for k in range(len(P["pairs"]))}
    ties = {pin["lec_q_g%05d" % k]: v for k, v in C.items()}
    for k, p in dup.items():
        ties[pin["lec_q_g%05d" % k]] = None     # placeholder, replaced below by partner's pattern
    seeds = [11, 12, 13]
    sigs = []
    for sd in seeds:
        rnd = random.Random(sd)
        pis = [rnd.getrandbits(nb) for _ in range(I)]
        for k, v in C.items():
            pis[pin["lec_q_g%05d" % k]] = mask if v else 0
        for k, p in dup.items():
            pis[pin["lec_q_g%05d" % k]] = pis[qpi[p]]
        sigs.append((pis, simulate(I, outs, ands, pis, mask)))
    byd = {}
    for k in range(len(P["pairs"])):
        byd.setdefault(tuple(o[dpo[k]] for _, o in sigs), k)
    fdup = {}
    for k in list(free):
        key_ = tuple(o[dout[k]] for _, o in sigs)
        if key_ in byd:
            fdup[k] = byd[key_]
    # second sub-pass (hold-type flops, D = en ? x : Q): every flop Q shares ONE random vector per
    # pattern set, so a duplicate and its partner see the same own-Q. Only a candidate search; the
    # lec_d_x comparison in the LEC is the proof.
    rest = [k for k in free if k not in fdup]
    qall = [pin[n] for n in pin if n.startswith("lec_q_")]
    sigs2 = []
    for sd in (21, 22, 23):
        rnd = random.Random(sd)
        pis = [rnd.getrandbits(nb) for _ in range(I)]
        shared = rnd.getrandbits(nb)
        for q in qall:
            pis[q] = shared
        for k, v in C.items():
            pis[pin["lec_q_g%05d" % k]] = mask if v else 0
        sigs2.append(simulate(I, outs, ands, pis, mask))
    byd2 = {}
    for k in range(len(P["pairs"])):
        byd2.setdefault(tuple(o[dpo[k]] for o in sigs2), k)
    for k in rest:
        key_ = tuple(o[dout[k]] for o in sigs2)
        if key_ in byd2:
            fdup[k] = byd2[key_]
    for k, p in fdup.items():
        dup[k] = p
    free = [k for k in free if k not in fdup]
    print("functional duplicates found: %d" % len(fdup))
    for k, p in list(fdup.items())[:40]:
        print("  fdup", gold[P["gold_only"][k]]["names"][:1], "->", gold[P["pairs"][p][0]]["names"][:1])
    json.dump({"const": {str(k): v for k, v in sorted(C.items())}, "dup": {str(k): v for k, v in sorted(dup.items())},
               "free": free}, open(out, "w"), indent=1)
    print("const %d, dup %d, free %d" % (len(C), len(dup), len(free)))
    for k in free[:40]:
        print("  free", gold[P["gold_only"][k]]["names"][:2])
    sys.exit(0)

if sys.argv[1] == "prune":
    # python const_check.py prune proof_sat.aig spec_in.json spec_out.json
    # proof_sat.aig = proof.aig after ABC `&sat -a -z`: an output that became literal 0 is PROVED
    # (D == value under the ties); every other const flop is demoted to free.
    aig, sin, sout = sys.argv[2:5]
    S = json.load(open(sin))
    d = open(aig, "rb").read()
    nl = d.index(b"\n")
    M, I, L, O, A = map(int, d[:nl].split()[1:6])
    pos = nl + 1
    olits = []
    for _ in range(O):
        e = d.index(b"\n", pos)
        olits.append(int(d[pos:e]))
        pos = e + 1
    keys = sorted(int(k) for k in S["const"])
    assert len(keys) == O, (len(keys), O)
    bad = [k for k, l in zip(keys, olits) if l != 0]
    for k in bad:
        del S["const"][str(k)]
        S["free"].append(k)
    S["free"] = sorted(set(S["free"]))
    json.dump(S, open(sout, "w"), indent=1)
    print("const outputs %d: proved %d, NOT proved %d -> demoted; const now %d" % (O, O - len(bad), len(bad), len(S["const"])))
    sys.exit(0)

if sys.argv[1] == "mkproof":
    aig, sj, out = sys.argv[2:5]
    S = json.load(open(sj))
    d = open(aig, "rb").read()
    nl = d.index(b"\n")
    M, I, L, O, A = map(int, d[:nl].split()[1:6])
    pos = nl + 1
    olits = []
    for _ in range(O):
        e = d.index(b"\n", pos)
        olits.append(int(d[pos:e]))
        pos = e + 1
    body_start = pos
    # find end of AND section = start of symbol table / comments: re-parse by decoding A deltas
    p = body_start
    for _ in range(2 * A):
        while d[p] & 0x80:
            p += 1
        p += 1
    ands_bytes = d[body_start:p]
    onames = {}
    for line in d[p:].split(b"\n"):
        if line[:1] == b"o" and b" " in line:
            h, _, n = line.partition(b" ")
            if h[1:].isdigit():
                onames[n.decode("latin1")] = int(h[1:])
    new = []
    for k, v in sorted(((int(k), v) for k, v in S["const"].items())):
        new.append(olits[onames["lec_d_g%05d" % k]] ^ v)
    hdr = ("aig %d %d %d %d %d\n" % (M, I, L, len(new), A)).encode()
    open(out, "wb").write(hdr + b"".join(b"%d\n" % x for x in new) + ands_bytes)
    print("proof miter: %d outputs (D xor value), all must be 0" % len(new))
