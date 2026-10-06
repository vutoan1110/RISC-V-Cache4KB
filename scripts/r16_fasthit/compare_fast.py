"""R16 chain: a FAST_HIT=1 result CSV against the FAST_HIT=0 CSV of the same RTL (run_ablation.py / run_coremark.py
output, one row per kernel x config).

FAST_HIT only answers a main-array hit one cycle earlier; it decides nothing differently. So for every FAST row:
  - the base row (same kernel, same config) exists;
  - every field outside the cycle accounting is equal: cache counters (accesses, main / victim hits, misses, AXI
    beats), architectural counters (minstret, branches, predictions ...), result_pass / invariant_pass, mcause;
  - mcycle_fast <= mcycle_base.
--dm KERNELS-CSV: additionally report how many FAST DM_DSE rows equal the DM row of that CSV in mcycle (review M1:
the DSE core used as a direct-mapped cache, with FAST_HIT, against the five-state DM controller).

    python scripts/r16_fasthit/compare_fast.py base.csv fast.csv [--dm base.csv]
Exit 0 only when every FAST row passes.
"""
import argparse
import csv
import math
import sys

TIMING = {"mcycle", "cycle_retire", "load_use", "i_wait", "d_wait", "control", "trap", "mmio", "fill_drain",
          "other", "snap_seq"}
NAMES = {"kernel", "config", "config_id"}

ap = argparse.ArgumentParser()
ap.add_argument("base")
ap.add_argument("fast")
ap.add_argument("--dm", default="")
a = ap.parse_args()
B = {(r["kernel"], r["config"]): r for r in csv.DictReader(open(a.base, newline="", encoding="utf-8"))}
F = list(csv.DictReader(open(a.fast, newline="", encoding="utf-8")))
bad, gm = [], {}
for r in F:
    k = (r["kernel"], r["config"])
    b = B.get(k)
    if b is None:
        bad.append("%s/%s: no FAST_HIT=0 row" % k)
        continue
    diff = [f for f in r if f not in TIMING and f not in NAMES and r[f] != b.get(f)]
    if diff:
        bad.append("%s/%s: %s" % (k + (", ".join("%s %s->%s" % (f, b.get(f), r[f]) for f in diff[:6]),)))
    if int(r["mcycle"]) > int(b["mcycle"]):
        bad.append("%s/%s: mcycle grew %s -> %s" % (k + (b["mcycle"], r["mcycle"])))
    gm.setdefault(r["config"], []).append(math.log(int(r["mcycle"]) / int(b["mcycle"])))
print("%d FAST rows, %d problem(s)" % (len(F), len(bad)))
for c, xs in sorted(gm.items()):
    print("  %-7s %2d kernels  GM mcycle FAST/base %+.3f %%" % (c, len(xs), 100 * (math.exp(sum(xs) / len(xs)) - 1)))
if a.dm:
    D = {r["kernel"]: r for r in csv.DictReader(open(a.dm, newline="", encoding="utf-8")) if r["config"] == "DM"}
    rows = [r for r in F if r["config"] == "DM_DSE"]
    same = [r["kernel"] for r in rows if r["kernel"] in D and r["mcycle"] == D[r["kernel"]]["mcycle"]]
    print("  DM_DSE FAST mcycle == DM: %d/%d (%s)" % (len(same), len(rows),
                                                      ", ".join(r["kernel"] for r in rows if r["kernel"] not in same)
                                                      or "all"))
for x in bad:
    print("  " + x)
sys.exit(1 if bad else 0)
