"""FLOW_JOURNAL Incident 89 (Option A): register-mapped combinational LEC of RTL+fsm (gold) vs the
final netlist (gate).

    python evert.py pair gold_flat.il gate_flat.il pairs.json
    python evert.py cut  <side>_flat.il <gold|gate> pairs.json <side>_lec.il

`pair`: every flop bit of each side gets the set of public names on its net (its Q, or, for an
async-reset flop after async2sync, the output of the reset mux async2sync put behind it; module
`connect` aliases are followed). A gold bit and a gate bit whose name sets intersect form a pair;
ambiguous matches are refused. MANUAL_ALIASES adds pairs whose names differ for a documented reason.

`cut`: each flop bit is removed and replaced by an input port lec_q_<id> driving its Q bit; each
PAIRED bit also gets an output port lec_d_<id> carrying its D bit, so the miter compares the
next-state functions. Bits without a partner become input ports on BOTH sides (unused on the
other side) and their D is not compared. All ports are renumbered in name order, so both sides
have the identical interface in the identical order.

Soundness of the overall argument (sequential equivalence from reset): (1) both sides start in the
same state (all flops 0, reset forced in cycle 0 - as in ../sec); (2) the combinational check below
proves outputs and next states of paired flops equal whenever paired states are equal; unpaired
flops must be shown not to matter (they are free inputs here, so passing with them free is
stronger than needed).
"""
import json
import re
import sys
from collections import defaultdict

TOK = re.compile(r"\{|\}|\d+'[01xzm-]+|[\\$]\S+(?: \[\d+(?::\d+)?\])?")

# gold name -> gate name, one bit each. rx_block.sv:175-181: rx_data_o[4:0] == rx_data_reg[4:0]
# in all four cases, so synthesis kept one register and named it after the output port.
MANUAL_ALIASES = {"\\u_soc.u_uart.u_uart_core.rx_block.rx_data_reg[%d]" % i:
                  "\\u_soc.u_uart.u_uart_core.rx_block.rx_data_o[%d]" % i for i in range(5)}


def load(path):
    lines = open(path).read().split("\n")
    start = next(i for i, l in enumerate(lines) if l == "module \\soc_asic_top")
    end = next(i for i in range(start + 1, len(lines)) if lines[i] == "end")
    return lines, start, end


def widths(body):
    w = {}
    for l in body:
        if l.startswith("  wire "):
            p = l.split()
            w[p[-1]] = (int(p[p.index("width") + 1]) if "width" in p else 1,
                        int(p[p.index("offset") + 1]) if "offset" in p else 0)
            assert "upto" not in p, l
    return w


def bits(sig, width):
    """sigspec -> list of single-bit RTLIL texts, LSB first."""
    out = []
    for t in TOK.findall(sig):
        if t in "{}":
            continue
        if "'" in t and t[0].isdigit():
            v = t.split("'")[1]                  # MSB first
            out = ["1'" + c for c in reversed(v)] + out
            continue
        m = re.match(r"^(\S+)(?: \[(\d+)(?::(\d+))?\])?$", t)
        name, hi, lo = m.group(1), m.group(2), m.group(3)
        w, off = width.get(name, (1, 0))
        if hi is None:
            idx = list(range(off, off + w))
        elif lo is None:
            idx = [int(hi)]
        else:
            idx = list(range(int(lo), int(hi) + 1))
        # RTLIL writes bit selects with the absolute index (start_offset included)
        out = [name if w == 1 else "%s [%d]" % (name, i) for i in idx] + out
    return out


def key(b):
    """canonical id of a wire bit (text form) for alias/equality."""
    return b


def split_connect(rest):
    s = rest
    if s.startswith("{"):
        d = 0
        for i, ch in enumerate(s):
            d += ch == "{"
            d -= ch == "}"
            if d == 0:
                return s[:i + 1], s[i + 1:].strip()
    m = re.match(r"^(\S+(?: \[\d+(?::\d+)?\])?) (.*)$", s)
    return m.group(1), m.group(2)


def scan(path):
    """-> list of flop bits: dict(cell, i, q, d, names) ; plus (lines, start, end, width)"""
    lines, start, end = load(path)
    body = lines[start + 1:end]
    width = widths(body)
    cells, conns, cur = [], [], None
    for l in body:
        if l.startswith("  cell "):
            p = l.split()
            cur = (p[1], p[2], {})
            cells.append(cur)
        elif l.startswith("    connect ") and cur is not None:
            _, port, sig = l.split(None, 2)
            cur[2][port] = sig.strip()
        elif l.startswith("  end"):
            cur = None
        elif l.startswith("  connect "):
            conns.append(l[len("  connect "):].strip())
    alias = defaultdict(set)
    for rest in conns:
        a, b = split_connect(rest)
        for x, y in zip(bits(a, width), bits(b, width)):
            if not x.startswith("1'") and not y.startswith("1'"):
                alias[x].add(y)
                alias[y].add(x)
    flops = []
    qbit_index = {}
    for t, n, pc in cells:
        if t in ("$dff", "$_DFF_P_"):        # coarse (RTL side) or fine-grained (synthesised N1)
            assert set(pc) >= {"\\D", "\\Q"} and ("\\CLK" in pc or "\\C" in pc), n
            qs, ds = bits(pc["\\Q"], width), bits(pc["\\D"], width)
            assert len(qs) == len(ds), n
            for i, (q, d) in enumerate(zip(qs, ds)):
                qbit_index[q] = len(flops)
                flops.append({"cell": n, "i": i, "q": q, "d": d, "obs": {q}})
        else:
            assert "dff" not in t.lower() and "latch" not in t.lower() and t not in ("$ff", "$_FF_"), (t, n)
    # async2sync reset mux: one data input is the flop Q, its output is the observable register value
    for t, n, pc in cells:
        if t in ("$mux", "$_MUX_") and "async2sync" in n:      # coarse or fine-grained reset mux
            for port in ("\\A", "\\B"):
                for b, y in zip(bits(pc.get(port, ""), width), bits(pc.get("\\Y", ""), width)):
                    if b in qbit_index:
                        flops[qbit_index[b]]["obs"].add(y)

    def closure(b):
        seen, todo = {b}, [b]
        while todo:
            x = todo.pop()
            for y in alias.get(x, ()):
                if y not in seen:
                    seen.add(y)
                    todo.append(y)
        return seen

    for f in flops:
        names = set()
        for o in f["obs"]:
            names |= closure(o)
        f["names"] = sorted(x for x in names if x.startswith("\\"))
        del f["obs"]
    return flops, (lines, start, end, width)


def norm(n):
    # "\name [3]" and "\name[3]" (a 1-bit wire literally named with brackets) are the same RTL bit
    return n.replace(" [", "[")


if sys.argv[1] == "pair":
    gold, _ = scan(sys.argv[2])
    gate, _ = scan(sys.argv[3])
    idx = defaultdict(set)
    for j, f in enumerate(gate):
        for n in f["names"]:
            idx[norm(n)].add(j)
    manual = {norm(k): norm(v) for k, v in MANUAL_ALIASES.items()}
    pairs, amb, used = [], [], set()
    for i, f in enumerate(gold):
        cand = set()
        for n in f["names"]:
            cand |= idx.get(norm(n), set())
            if norm(n) in manual:
                cand |= idx.get(manual[norm(n)], set())
        if len(cand) == 1:
            j = cand.pop()
            if j in used:
                amb.append((i, "gate flop already paired"))
                continue
            used.add(j)
            pairs.append((i, j))
        elif len(cand) > 1:
            amb.append((i, "%d gate candidates" % len(cand)))
    gold_only = sorted(set(range(len(gold))) - {i for i, _ in pairs})
    gate_only = sorted(set(range(len(gate))) - used)
    json.dump({"gold": gold, "gate": gate, "pairs": pairs, "gold_only": gold_only, "gate_only": gate_only,
               "ambiguous": amb}, open(sys.argv[4], "w"))
    print("gold flop bits %d, gate flop bits %d, pairs %d, gold-only %d, gate-only %d, ambiguous %d"
          % (len(gold), len(gate), len(pairs), len(gold_only), len(gate_only), len(amb)))
    for i, why in amb[:20]:
        print("  ambiguous", gold[i]["names"][:3], why)
    for j in gate_only[:20]:
        print("  gate-only", gate[j]["names"][:3])
    sys.exit(0)

if sys.argv[1] == "cut":
    # optional: --spec spec.json   {"const": {gold_only_k: 0|1}, "dup": {gold_only_k: pair_k}}
    #   const: the gold-only flop is PROVED constant (const_check); its Q is tied to that value.
    #   dup:   the gold-only flop duplicates pair k (synthesis merged the two); its Q is tied to
    #          pair k's input and its D is compared (output lec_d_x<k>) with the gate flop of pair k
    #          - the induction that justifies the tie.
    #           --gold-only-d   also expose D of every gold-only flop (gold side, const analysis only)
    path, side, pj, dst = sys.argv[2:6]
    opts = sys.argv[6:]
    spec = json.load(open(opts[opts.index("--spec") + 1])) if "--spec" in opts else {"const": {}, "dup": {}}
    CONST = {int(k): int(v) for k, v in spec.get("const", {}).items()}
    DUP = {int(k): int(v) for k, v in spec.get("dup", {}).items()}
    GOD = "--gold-only-d" in opts
    # one-hot restriction of the FSM state registers synthesis re-encoded (Incident 89):
    #   spec "onehot": [{"name", "mode": "exact"|"atmost", "pairs": [pair_k per bit]}]  (LEC, both sides)
    #   --inv: gold only; spec "onehot_gold": [{"name", "gold": [gold flop index per bit]}] are decoded
    #          "exact" and their D bits are exposed as lec_inv_<name>_<b> (invariant check)
    INV = "--inv" in opts
    P = json.load(open(pj))
    OH = {}          # my flop index -> (group name, bit, mode, nbits)
    ohgroups = spec.get("onehot_gold", []) if INV else spec.get("onehot", [])
    for grp in ohgroups:
        idxs = grp["gold"] if INV else [P["pairs"][k][0 if side == "gold" else 1] for k in grp["pairs"]]
        for b, n_ in enumerate(idxs):
            OH[n_] = (grp["name"], b, "exact" if INV else grp["mode"], len(idxs))
    flops, (lines, start, end, width) = scan(path)
    ref = P[side]
    assert len(ref) == len(flops) and all(a["cell"] == b["cell"] and a["i"] == b["i"] for a, b in zip(ref, flops)), \
        "flop list differs from pairs.json"
    me, other = (0, 1) if side == "gold" else (1, 0)
    pid = {}                                   # my flop index -> (id, paired?)
    for k, pr in enumerate(P["pairs"]):
        pid[pr[me]] = ("p%05d" % k, True)
    for k, i in enumerate(P["gold_only"]):
        if side == "gold":
            pid[i] = ("g%05d" % k, False)
    for k, j in enumerate(P["gate_only"]):
        if side == "gate":
            pid[j] = ("t%05d" % k, False)
    all_in = ["\\lec_q_p%05d" % k for k in range(len(P["pairs"]))] + \
             ["\\lec_q_g%05d" % k for k in range(len(P["gold_only"]))] + \
             ["\\lec_q_t%05d" % k for k in range(len(P["gate_only"]))]
    all_out = ["\\lec_d_p%05d" % k for k in range(len(P["pairs"]))] + \
              ["\\lec_d_x%05d" % g for g in sorted(DUP)]
    if GOD and side == "gold":
        all_out += ["\\lec_d_g%05d" % k for k in range(len(P["gold_only"]))]
    gold_only_pos = {i: k for k, i in enumerate(P["gold_only"])}
    body = lines[start + 1:end]
    dff_cells = {f["cell"] for f in flops}
    new_body, conns, pend, i = [], [], [], 0
    ports = []                                  # (name, dir, width)
    while i < len(body):
        l = body[i]
        if l.startswith("  attribute "):
            pend.append(l)
            i += 1
            continue
        if (l.startswith("  cell $dff ") or l.startswith("  cell $_DFF_P_ ")) and l.split()[2] in dff_cells:
            while body[i] != "  end":
                i += 1
            i += 1
            pend = []
            continue
        if l.startswith("  wire ") and (" input " in l or " output " in l):
            p = l.split()
            d = "input" if " input " in l else "output"
            k = p.index(d)
            ports.append((p[-1], d, int(p[p.index("width") + 1]) if "width" in p else 1))
            l = " ".join(p[:k] + p[k + 2:])      # strip "input N"; re-added below in canonical order
            l = "  " + l
        new_body.extend(pend)
        pend = []
        new_body.append(l)
        i += 1
    new_body.extend(pend)
    oh_cells, oh_ports, oh_wires = [], [], []
    for gname in sorted({v[0] for v in OH.values()}):
        members = sorted((v[1], n_) for n_, v in OH.items() if v[0] == gname)
        nb_, mode = len(members), OH[members[0][1]][2]
        ncodes = nb_ if mode == "exact" else nb_ + 1          # atmost: one extra code = no bit set
        m = max(1, (ncodes - 1).bit_length())
        sel = ["\\lec_oh_%s_%d" % (gname, j) for j in range(m)]
        oh_ports += sel
        selsig = "{ " + " ".join(reversed(sel)) + " }" if m > 1 else sel[0]
        for b, n_ in members:
            codes = [b]
            if mode == "exact" and b == 0:
                codes += list(range(nb_, 1 << m))                 # unused codes map to bit 0
            eqs = []
            for v in codes:
                w = "$lecoh$%s$%d$%d" % (gname, b, v)
                oh_wires.append("  wire %s" % w)
                oh_cells += ["  cell $eq %s$eq" % w, "    parameter \\A_SIGNED 0", "    parameter \\A_WIDTH %d" % m,
                             "    parameter \\B_SIGNED 0", "    parameter \\B_WIDTH %d" % m, "    parameter \\Y_WIDTH 1",
                             "    connect \\A %s" % selsig, "    connect \\B %d'%s" % (m, format(v, "0%db" % m)),
                             "    connect \\Y %s" % w, "  end"]
                eqs.append(w)
            q = flops[n_]["q"]
            if len(eqs) == 1:
                oh_cells.append("  connect %s %s" % (q, eqs[0]))
            else:
                oh_cells += ["  cell $reduce_or $lecoh$%s$%d$or" % (gname, b), "    parameter \\A_SIGNED 0",
                             "    parameter \\A_WIDTH %d" % len(eqs), "    parameter \\Y_WIDTH 1",
                             "    connect \\A { %s }" % " ".join(eqs), "    connect \\Y %s" % q, "  end"]
            if INV:
                oh_ports.append(("\\lec_inv_%s_%d" % (gname, b), flops[n_]["d"]))
    for n, f in enumerate(flops):
        ident, paired = pid[n]
        g = gold_only_pos.get(n) if side == "gold" else None
        if n in OH:
            pass                                             # Q driven by the one-hot decoder
        elif g is not None and g in CONST:
            conns.append("  connect %s 1'%d" % (f["q"], CONST[g]))
        elif g is not None and g in DUP:
            conns.append("  connect %s \\lec_q_p%05d" % (f["q"], DUP[g]))
            conns.append("  connect \\lec_d_x%05d %s" % (g, f["d"]))
        else:
            conns.append("  connect %s \\lec_q_%s" % (f["q"], ident))
        if paired:
            conns.append("  connect \\lec_d_%s %s" % (ident, f["d"]))
        if g is not None and GOD:
            conns.append("  connect \\lec_d_g%05d %s" % (g, f["d"]))
    if side == "gate":
        for g, k in sorted(DUP.items()):
            conns.append("  connect \\lec_d_x%05d %s" % (g, flops[P["pairs"][k][1]]["d"]))
    new_wires = list(oh_wires)
    for e in oh_ports:
        if isinstance(e, tuple):
            ports.append((e[0], "output", 1))
            new_wires.append("  wire %s" % e[0])
            conns.append("  connect %s %s" % e)
        else:
            ports.append((e, "input", 1))
            new_wires.append("  wire %s" % e)
    conns = oh_cells + conns
    for nm in all_in:
        ports.append((nm, "input", 1))
        new_wires.append("  wire %s" % nm)
    for nm in all_out:
        ports.append((nm, "output", 1))
        new_wires.append("  wire %s" % nm)
    new_body = new_wires + new_body
    # canonical port numbering: by name
    order = {nm: k + 1 for k, nm in enumerate(sorted(p[0] for p in ports))}
    decl = {}
    for nm, d, w in ports:
        decl[nm] = "  wire %s%s %d %s" % ("width %d " % w if w != 1 else "", d, order[nm], nm)
    out_body = []
    for l in new_body:
        if l.startswith("  wire "):
            nm = l.split()[-1]
            if nm in decl:
                out_body.append(decl.pop(nm))
                continue
        out_body.append(l)
    assert not decl, list(decl)[:5]
    out = lines[:start + 1] + out_body + conns + lines[end:]
    open(dst, "w", newline="\n").write("\n".join(out))
    print("%s: %d flop bits cut, %d ports (%d lec_q, %d lec_d)" % (side, len(flops), len(ports), len(all_in), len(all_out)))
