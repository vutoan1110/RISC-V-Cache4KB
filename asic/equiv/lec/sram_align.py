"""2026-10-14 (DM_VC4 LEC): align the SRAM cut ports of gold_flat.il (RTL + fsm) and n1_flat.il (synthesis) when the
RTL instantiates SRAM macros that synthesis removed. DM_VC4: the DSE cache core always instantiates way 1 of each
cache (4 + 4 banks of sky130_sram_1kbyte_1rw1r_32x256_8) and the direct-mapped configuration never reads it, so Yosys
deletes those black-box cells (outputs unused) and N1 / the routed netlist have 16 macros where gold has 24.

Gold-only SRAM instance = an instance whose cut ports (sram_cut.py names them <instance>__<pin>) exist in the gold
model only. Requirements, else exit 1: every gold-only port is an SRAM cut port of such an instance, every port of
that instance is gold-only, nothing is N1-only, and every common port has the same direction and width.
Transformation (written to new files, inputs untouched):
  - the instance's data outputs (dout0 / dout1: INPUTS of the cut model) stay inputs on the gold side and are added as
    unused inputs on the N1 side. The LEC then proves every compared output for ANY read data of these macros, i.e.
    the RTL behaviour does not depend on their contents (negative control: run_lec_vc4.ps1 -Step NegAlign);
  - the instance's input pins (clk, csb, web, wmask, addr, din: OUTPUTS of the cut model) become internal wires on the
    gold side: the macros do not exist in the synthesised or routed netlist, so what the RTL writes into them is
    unobservable once their read data is proved irrelevant.
Ports are renumbered 1..n in their original order (added N1 inputs last).
usage: python sram_align.py gold_flat.il n1_flat.il gold_out.il n1_out.il
"""
import re
import sys

PINS = ("clk0", "clk1", "csb0", "csb1", "web0", "wmask0", "addr0", "addr1", "din0", "dout0", "dout1")
SRAM_PORT = re.compile(r"^\\(.+)__(%s)$" % "|".join(PINS))


def load(path):
    lines = open(path).read().split("\n")
    start = next(i for i, l in enumerate(lines) if l == "module \\soc_asic_top")
    end = next(i for i in range(start + 1, len(lines)) if lines[i] == "end")
    ports = {}
    for k in range(start + 1, end):
        l = lines[k]
        if l.startswith("  wire "):
            p = l.split()
            for d in ("input", "output", "inout"):
                if d in p:
                    width = int(p[p.index("width") + 1]) if "width" in p else 1
                    ports[p[-1]] = {"dir": d, "width": width, "id": int(p[p.index(d) + 1]), "line": k}
    return lines, start, end, ports


def write(path, lines, start, end, ports, drop_dir, add, after=None):
    """drop_dir: port names whose direction is removed; add: [(name, width)] new unused inputs; after: for each added
    name, the existing port whose declaration it must follow (None = before the first port declaration).
    Yosys write_aiger orders the AIGER inputs / outputs by WIRE DECLARATION ORDER (not by port number), and ABC pairs
    the two LEC sides by position, so an added input must be declared exactly where the gold side declares it."""
    keep = sorted((v["id"], n) for n, v in ports.items() if n not in drop_dir)
    newid = {n: k + 1 for k, (_, n) in enumerate(keep)}
    out = list(lines)
    for n, v in ports.items():
        p = out[v["line"]].split()                 # every other keyword (width, signed, upto, offset) is kept
        k = p.index(v["dir"])
        p = p[:k] + p[k + 2:] if n in drop_dir else p[:k + 1] + [str(newid[n])] + p[k + 2:]
        out[v["line"]] = "  " + " ".join(p)
    first = min(v["line"] for v in ports.values())
    ins = {}                                       # line index -> declarations to insert AFTER that line
    for k, (n, w) in enumerate(add):
        decl = "  wire %sinput %d %s" % ("width %d " % w if w != 1 else "", len(keep) + k + 1, n)
        at = ports[after[n]]["line"] if after and after.get(n) else first - 1
        ins.setdefault(at, []).append(decl)
    res = []
    for i, l in enumerate(out):
        res.append(l)
        res.extend(ins.get(i, []))
    open(path, "w", newline="\n").write("\n".join(res))


def main():
    gpath, npath, gout, nout = sys.argv[1:5]
    gl, gs, ge, gp = load(gpath)
    nl, ns, ne, np_ = load(npath)
    gold_only = sorted(set(gp) - set(np_))
    n1_only = sorted(set(np_) - set(gp))
    bad = [n for n in set(gp) & set(np_) if (gp[n]["dir"], gp[n]["width"]) != (np_[n]["dir"], np_[n]["width"])]
    if n1_only or bad:
        print("FAIL: N1-only ports %d %s; common ports with a different direction/width %d %s"
              % (len(n1_only), n1_only[:3], len(bad), bad[:3]))
        return 1
    inst = {}
    for n in gold_only:
        m = SRAM_PORT.match(n)
        if not m:
            print("FAIL: gold-only port %s is not an SRAM cut port" % n)
            return 1
        inst.setdefault(m.group(1), []).append(n)
    for base in inst:
        common = [n for n in gp if SRAM_PORT.match(n) and SRAM_PORT.match(n).group(1) == base and n in np_]
        if common:
            print("FAIL: instance %s has ports on both sides: %s" % (base, common[:3]))
            return 1
    drop = {n for n in gold_only if gp[n]["dir"] == "output"}
    add = [(n, gp[n]["width"]) for n in gold_only if gp[n]["dir"] == "input"]
    if any(gp[n]["dir"] == "inout" for n in gold_only):
        print("FAIL: inout SRAM cut port")
        return 1
    gold_order = sorted(gp, key=lambda n: gp[n]["line"])
    after, prev = {}, None
    for n in gold_order:
        if n in np_:
            prev = n
        elif gp[n]["dir"] == "input":
            after[n] = prev                          # nearest preceding port that N1 also declares
    write(gout, gl, gs, ge, gp, drop, [])
    write(nout, nl, ns, ne, np_, set(), add, after)
    # self-check: both outputs declare the same ports with the same direction / width in the same ORDER
    g2, n2 = load(gout)[3], load(nout)[3]
    og = [(n, g2[n]["dir"], g2[n]["width"]) for n in sorted(g2, key=lambda n: g2[n]["line"])]
    on = [(n, n2[n]["dir"], n2[n]["width"]) for n in sorted(n2, key=lambda n: n2[n]["line"])]
    if og != on:
        k = next((i for i, (a, b) in enumerate(zip(og, on)) if a != b), min(len(og), len(on)))
        print("FAIL: port declaration order differs at position %d: %s | %s" % (k, og[k:k + 1], on[k:k + 1]))
        return 1
    print("gold-only SRAM instances %d: %s" % (len(inst), ", ".join(sorted(inst))))
    print("gold: %d ports, %d cut-model outputs made internal (%d bits); N1: %d ports, %d unused inputs added (%d bits)"
          % (len(gp), len(drop), sum(gp[n]["width"] for n in drop), len(np_), len(add), sum(w for _, w in add)))
    print("ALIGNED: both sides now have %d ports" % (len(gp) - len(drop)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
