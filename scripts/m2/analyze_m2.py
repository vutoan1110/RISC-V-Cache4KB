"""Review M1 + M2: analysis of the cache design-space sweep (results/m2/sweep_p1.csv, optional sweep_fast_p1.csv).

    python scripts/m2/analyze_m2.py [--fast results/m2/sweep_fast_p1.csv] [--out results/m2/M1_M2_analysis.md]

Per point and workload: mcycle (all cycles), CPI = mcycle / minstret, I$ miss rate = i_miss / i_access, D$ miss rate =
d_miss / (d_read + d_write), AXI read beats. Aggregates use the geometric mean over the 12 upstream Embench-IoT
kernels (GM of mcycle ratios); CoreMark is reported on its own.

M1 decomposition at every capacity (16 B lines), all ratios against the DM point (five-state controller):
  controller cost   = GM(DM_DSE / DM)       (same direct-mapped organisation, ten-state DSE core)
  organisation      = GM(X / DM_DSE)        X = SA2, SA4, VC4 (same DSE / N-way controller timing)
  total             = GM(X / DM)            (what the published comparison measured)
With the R16 FAST_HIT data (--fast): GM(X_fast / DM) is the organisation effect on a controller whose hit latency
equals DM's; DM_DSE_fast / DM must be exactly 1 on every kernel (checked and reported).
"""
import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EMB = ("up_aha-mont64", "up_crc32", "up_depthconv", "up_edn", "up_huffbench", "up_matmult-int", "up_md5sum",
       "up_nettle-sha256", "up_slre", "up_statemate", "up_tarfind", "up_ud")


def load(p):
    d = {}
    for r in csv.DictReader(open(p, encoding="utf-8")):
        d[(r["point"], r["workload"])] = r
    return d


def gm(xs):
    xs = [x for x in xs if x is not None]
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else None


def ratio(d, a, b, w, field="mcycle"):
    ra, rb = d.get((a, w)), d.get((b, w))
    if not ra or not rb:
        return None
    return int(ra[field]) / int(rb[field])


def pct(x):
    return "n/a" if x is None else "%+.2f %%" % (100 * (x - 1))


ap = argparse.ArgumentParser()
ap.add_argument("--base", default=str(ROOT / "results" / "m2" / "sweep_p1.csv"))
ap.add_argument("--fast", default="")
ap.add_argument("--out", default=str(ROOT / "results" / "m2" / "M1_M2_analysis.md"))
a = ap.parse_args()
a.base = str(Path(a.base).resolve())
a.fast = str(Path(a.fast).resolve()) if a.fast else ""
a.out = str(Path(a.out).resolve())
d = load(a.base)
f = load(a.fast) if a.fast else {}
caps = (256, 512, 1024, 2048, 4096, 8192)
L = []
L.append("# Review M1 + M2: cache design-space sweep (R15 RTL%s)\n" % (" + R16 FAST_HIT" if f else ""))
L.append("Source: `%s`%s. Every ratio is mcycle against the DM point of the same capacity, geometric mean over the "
         "12 upstream Embench-IoT kernels; CoreMark separately. Negative = faster than DM.\n" %
         (Path(a.base).relative_to(ROOT).as_posix(), (", `%s`" % Path(a.fast).relative_to(ROOT).as_posix()) if f else ""))
L.append("CoreMark rows are repeatable full-program simulation counters (RAM 32 KiB), including initialization/reporting; "
         "CRC is not part of the wrapper PASS gate. Functional validation remains pending; these are not official scores.\n")

# ---------------------------------------------------------------- M1 decomposition (16 B lines)
L.append("## M1: controller cost vs organisation (16 B lines)\n")
L.append("| capacity | controller GM(DM_DSE/DM) | org SA2/DM_DSE | org SA4/DM_DSE | org VC4/DM_DSE | total SA2/DM | total SA4/DM | total VC4/DM | CoreMark SA2/DM |")
L.append("|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for c in caps:
    P = lambda o: "%s_%dB_L16" % (o, c)
    ctl = gm([ratio(d, P("DM_DSE"), P("DM"), w) for w in EMB])
    org = {o: gm([ratio(d, P(o), P("DM_DSE"), w) for w in EMB]) for o in ("SA2", "SA4", "VC4")}
    tot = {o: gm([ratio(d, P(o), P("DM"), w) for w in EMB]) for o in ("SA2", "SA4", "VC4")}
    L.append("| %d B | %s | %s | %s | %s | %s | %s | %s | %s |" % (
        c, pct(ctl), pct(org["SA2"]), pct(org["SA4"]), pct(org["VC4"]), pct(tot["SA2"]), pct(tot["SA4"]),
        pct(tot["VC4"]), pct(ratio(d, P("SA2"), P("DM"), "coremark"))))
L.append("")

if f:
    L.append("## M1 with R16 FAST_HIT: organisation on a controller with DM's hit latency (16 B lines)\n")
    L.append("DM_DSE_fast/DM is what remains of the controller difference once the hit latency is equal: the two "
             "D-cache controllers still differ in the D$ L0 and in how store misses are classified (d_main / d_miss "
             "differ, the I$ counters do not), which matters only while the cache is small.\n")
    L.append("| capacity | DM_DSE_fast/DM (residual) | SA2_fast/DM | SA4_fast/DM | VC4_fast/DM | CoreMark SA2_fast/DM | CoreMark SA4_fast/DM | CoreMark VC4_fast/DM |")
    L.append("|---:|---:|---:|---:|---:|---:|---:|---:|")
    exact = []
    for c in caps:
        P = lambda o: "%s_%dB_L16" % (o, c)

        def fr(o, w):
            rf, rd = f.get((P(o), w)), d.get((P("DM"), w))
            return None if not rf or not rd else int(rf["mcycle"]) / int(rd["mcycle"])
        dd = [fr("DM_DSE", w) for w in EMB + ("coremark",)]
        exact.append((c, sum(1 for x in dd if x == 1.0), sum(1 for x in dd if x is not None)))
        L.append("| %d B | %s | %s | %s | %s | %s | %s | %s |" % (
            c, pct(gm([fr("DM_DSE", w) for w in EMB])), pct(gm([fr("SA2", w) for w in EMB])),
            pct(gm([fr("SA4", w) for w in EMB])), pct(gm([fr("VC4", w) for w in EMB])),
            pct(fr("SA2", "coremark")), pct(fr("SA4", "coremark")), pct(fr("VC4", "coremark"))))
    L.append("")
    L.append("DM_DSE_fast cycle-identical to DM (12 kernels + CoreMark): " +
             ", ".join("%d B %d/%d" % e for e in exact) + "\n")
    L.append("## M1: organisation on ONE controller with DM's hit latency, GM(X_fast / DM_DSE_fast) (16 B lines)\n")
    L.append("| capacity | SA2 | SA4 | VC4 | CoreMark SA2 | CoreMark SA4 | CoreMark VC4 |")
    L.append("|---:|---:|---:|---:|---:|---:|---:|")
    for c in caps:
        P = lambda o: "%s_%dB_L16" % (o, c)

        def ff(o, w):
            rx, rd = f.get((P(o), w)), f.get((P("DM_DSE"), w))
            return None if not rx or not rd else int(rx["mcycle"]) / int(rd["mcycle"])
        L.append("| %d B | %s | %s | %s | %s | %s | %s |" % (
            c, pct(gm([ff("SA2", w) for w in EMB])), pct(gm([ff("SA4", w) for w in EMB])),
            pct(gm([ff("VC4", w) for w in EMB])), pct(ff("SA2", "coremark")), pct(ff("SA4", "coremark")),
            pct(ff("VC4", "coremark"))))
    L.append("")

# ---------------------------------------------------------------- miss rates and traffic
L.append("## Miss rates and AXI traffic (16 B lines, GM-free sums over the 12 kernels)\n")
L.append("| capacity | org | I$ miss % | D$ miss % | AXI read beats | CPI (sum mcycle / sum minstret) |")
L.append("|---:|---|---:|---:|---:|---:|")
for c in caps:
    for o in ("DM", "DM_DSE", "SA2", "SA4", "VC4"):
        rows = [d.get(("%s_%dB_L16" % (o, c), w)) for w in EMB]
        if not all(rows):
            L.append("| %d B | %s | n/a | n/a | n/a | n/a |" % (c, o))
            continue
        s = lambda k: sum(int(r[k]) for r in rows)
        L.append("| %d B | %s | %.3f | %.3f | %d | %.4f |" % (
            c, o, 100.0 * s("i_miss") / s("i_access"), 100.0 * s("d_miss") / (s("d_read") + s("d_write")),
            s("axi_read"), s("mcycle") / s("minstret")))
L.append("")

# ---------------------------------------------------------------- line size and victim depth
# on the R15 controller and, with --fast, on the R16 FAST_HIT controller (same tables, second dataset)
for lab, ds in [("R15 controller", d)] + ([("R16 FAST_HIT", f)] if f else []):
    L.append("## M2: line size, %s (DSE family; DM's controller supports 16 B only)\n" % lab)
    L.append("| capacity | org | 8 B vs 16 B | 32 B vs 16 B | CoreMark 8 B | CoreMark 32 B | I$ miss % 8/16/32 | D$ miss % 8/16/32 |")
    L.append("|---:|---|---:|---:|---:|---:|---|---|")
    for c in (1024, 4096):
        for o in ("DM_DSE", "SA2", "SA4", "VC4"):
            def mr(line, kind):
                rows = [ds.get(("%s_%dB_L%d" % (o, c, line), w)) for w in EMB]
                if not all(rows):
                    return "n/a"
                s = lambda k: sum(int(r[k]) for r in rows)
                return "%.2f" % (100.0 * s("i_miss") / s("i_access") if kind == "i" else
                                 100.0 * s("d_miss") / (s("d_read") + s("d_write")))
            P = lambda line: "%s_%dB_L%d" % (o, c, line)
            L.append("| %d B | %s | %s | %s | %s | %s | %s | %s |" % (
                c, o, pct(gm([ratio(ds, P(8), P(16), w) for w in EMB])), pct(gm([ratio(ds, P(32), P(16), w) for w in EMB])),
                pct(ratio(ds, P(8), P(16), "coremark")), pct(ratio(ds, P(32), P(16), "coremark")),
                "/".join(mr(x, "i") for x in (8, 16, 32)), "/".join(mr(x, "d") for x in (8, 16, 32))))
    L.append("")
    L.append("## M2: victim-buffer depth, %s (16 B lines), vs VC4\n" % lab)
    L.append("| capacity | VC2/VC4 | VC8/VC4 | CoreMark VC2/VC4 | CoreMark VC8/VC4 |")
    L.append("|---:|---:|---:|---:|---:|")
    for c in (1024, 4096):
        V = lambda n: "VC%d_%dB_L16" % (n, c)
        L.append("| %d B | %s | %s | %s | %s |" % (
            c, pct(gm([ratio(ds, V(2), V(4), w) for w in EMB])), pct(gm([ratio(ds, V(8), V(4), w) for w in EMB])),
            pct(ratio(ds, V(2), V(4), "coremark")), pct(ratio(ds, V(8), V(4), "coremark"))))
    L.append("")
missing = sorted({k[0] for k in d} ^ {k[0] for k in d})
L.append("Points without data (e.g. SA4 at 256 B: 4 sets < the L0's 3 index bits, rejected at elaboration): " +
         ", ".join(sorted({"%s_%dB_L16" % (o, c) for c in caps for o in ("DM", "DM_DSE", "SA2", "SA4", "VC4")}
                          - {k[0] for k in d})) + "\n")
Path(a.out).write_text("\n".join(L), encoding="utf-8")
print("\n".join(L[:30]))
print("... -> %s" % a.out)
