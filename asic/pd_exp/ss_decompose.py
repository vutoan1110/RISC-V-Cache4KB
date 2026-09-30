"""FLOW_JOURNAL Incident 91: decompose the worst setup path per violating endpoint (report_checks
-format full -fields {input_pin net}) into launch/capture clock latency, setup, and data-path delay
split into repeater cells (buffers/inverter pairs inserted by the resizer: buf*, clkbuf*, dlygate*,
dlymetal*, and the resizer's named repeaters), logic cells, and net (wire) delay.  Endpoint and
startpoint registers are named by their Q net (from the final netlist).
usage: python ss_decompose.py paths.rpt netlist.v [top_k_groups]"""
import collections
import re
import sys

rpt, nlv = sys.argv[1], sys.argv[2]
K = int(sys.argv[3]) if len(sys.argv) > 3 else 25

# instance -> Q net (flops) from the netlist
qnet = {}
cur = None
txt = open(nlv, encoding="latin1").read()
for m in re.finditer(r"\n\s*(sky130_fd_sc_hd__(?:df|ed|sdf)\w+)\s+(\S+)\s*\((.*?)\);", txt, re.S):
    inst = m.group(2).lstrip("\\")
    q = re.search(r"\.Q\s*\(\s*(\\?\S+?)\s*\)", m.group(3))
    if q:
        qnet[inst] = q.group(1).lstrip("\\")
print("flops with Q net:", len(qnet))

REP = re.compile(r"^(buf|clkbuf|dlygate|dlymetal|clkdlybuf)")
paths = []
blk = []
for line in open(rpt, encoding="utf-8", errors="replace"):
    if line.startswith("Startpoint:") and blk:
        paths.append(blk)
        blk = []
    blk.append(line.rstrip("\n"))
if blk:
    paths.append(blk)


def parse(b):
    d = {"start": b[0].split()[1], "end": b[1].split()[1]}
    lines = b
    # split arrival and required sections at the first "data arrival time"
    ia = next(i for i, l in enumerate(lines) if "data arrival time" in l)
    arr, req = lines[:ia], lines[ia + 1:]
    cell = rep = net = 0.0
    nrep = nlog = 0
    chain = []
    launch = None
    prev_inst = None
    for l in arr:
        m = re.match(r"\s*(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(.*)$", l)
        if not m:
            continue
        dl, desc = float(m.group(1)), m.group(3)
        if "clock network delay" in desc:
            launch = dl
            continue
        pm = re.match(r"[\^v]\s+(\S+)/(\S+)\s+\((\S+)\)", desc)
        if not pm:
            continue
        inst, pin, ref = pm.group(1), pm.group(2), pm.group(3).replace("sky130_fd_sc_hd__", "")
        if inst == prev_inst:          # output pin of the same instance: cell arc
            cell += dl
            if REP.match(ref) or re.match(r"(fanout|load_slew|wire|max_length|rebuffer|split)\d+$", inst):
                rep += dl; nrep += 1
            else:
                nlog += 1
            chain.append(ref)
        else:
            net += dl
        prev_inst = inst
    cap = setup = unc = None
    for l in req:
        m = re.match(r"\s*(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(.*)$", l)
        if not m:
            continue
        dl, desc = float(m.group(1)), m.group(3)
        if "clock network delay" in desc:
            cap = dl
        elif "library setup time" in desc:
            setup = -dl
        elif "clock uncertainty" in desc:
            unc = -dl
    sl = next(float(l.split()[0]) for l in lines if "slack" in l)
    d.update(slack=sl, launch=launch or 0.0, capture=cap or 0.0, setup=setup or 0.0, unc=unc or 0.0,
             cell=cell, rep=rep, net=net, nrep=nrep, nlog=nlog, chain=chain)
    return d


P = [parse(b) for b in paths if any("data arrival time" in l for l in b)]
n = len(P)
print("violating endpoints analysed: %d (worst slack %.3f, median %.3f)" % (n, P[0]["slack"], sorted(p["slack"] for p in P)[n // 2]))


def avg(k, S=None):
    S = S or P
    return sum(p[k] for p in S) / len(S)


for tag, S in (("all", P), ("worst 100", P[:100])):
    print("[%s] mean: slack %.2f | launch clk %.2f capture clk %.2f (skew %.2f) setup %.2f unc %.2f | data: logic %.2f ns in %.1f cells, repeaters %.2f ns in %.1f cells, nets %.2f"
          % (tag, avg("slack", S), avg("launch", S), avg("capture", S), avg("capture", S) - avg("launch", S),
             avg("setup", S), avg("unc", S), avg("cell", S) - avg("rep", S), avg("nlog", S), avg("rep", S),
             avg("nrep", S), avg("net", S)))


def reg(inst):
    q = qnet.get(inst, inst)
    return re.sub(r"\[\d+\]", "", q)


g = collections.defaultdict(list)
for p in P:
    g[(reg(p["start"]), reg(p["end"]))].append(p)
print("\nstart register group -> end register group (count, worst slack, mean repeater ns / logic ns / net ns):")
for (s, e), S in sorted(g.items(), key=lambda kv: -len(kv[1]))[:K]:
    print("  %4d  %7.3f  %5.2f/%5.2f/%5.2f  %s -> %s" % (len(S), min(p["slack"] for p in S), avg("rep", S),
          avg("cell", S) - avg("rep", S), avg("net", S), s, e))
eg = collections.Counter(reg(p["end"]) for p in P)
print("\nend register groups:", eg.most_common(K))
sg = collections.Counter(reg(p["start"]) for p in P)
print("\nstart register groups:", sg.most_common(K))
# if every repeater delay could be removed, how many endpoints would pass?
fix = sum(p["slack"] + p["rep"] >= 0 for p in P)
fixn = sum(p["slack"] + p["rep"] + p["net"] >= 0 for p in P)
print("\nendpoints that would pass with zero repeater delay: %d / %d; with zero repeater AND zero net delay: %d / %d"
      % (fix, n, fixn, n))
print("\ngroups by worst slack:")
for (s, e), S in sorted(g.items(), key=lambda kv: min(p["slack"] for p in kv[1]))[:K]:
    w = min(S, key=lambda p: p["slack"])
    print("  %7.3f  n=%4d  launch %.2f capture %.2f  rep %5.2f (%d) logic %5.2f (%d) net %.2f  %s -> %s"
          % (w["slack"], len(S), w["launch"], w["capture"], w["rep"], w["nrep"], w["cell"] - w["rep"], w["nlog"], w["net"], s, e))
