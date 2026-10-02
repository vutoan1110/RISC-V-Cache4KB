"""Field-by-field identity of configuration rows between two result CSVs (R15 chain).

    python scripts/metrics/compare_cfg.py A.csv B.csv --map DM=DM,SA2=SA2      # same configs, two runs
    python scripts/metrics/compare_cfg.py A.csv A.csv --map SA2N=SA2            # SA2N rows of A vs SA2 rows

Every row of each mapped configuration in A must have a partner (same kernel) in B with every field equal,
except config / config_id (which name the configuration). Exit 0 only when all pairs are identical.
"""
import argparse
import csv
import sys

ap = argparse.ArgumentParser()
ap.add_argument("a")
ap.add_argument("b")
ap.add_argument("--map", required=True, help="configA=configB,...")
args = ap.parse_args()

A = list(csv.DictReader(open(args.a, newline="")))
B = list(csv.DictReader(open(args.b, newline="")))
pairs = [m.split("=") for m in args.map.split(",")]
bad, n = [], 0
for ca, cb in pairs:
    ra = {r["kernel"]: r for r in A if r["config"] == ca}
    rb = {r["kernel"]: r for r in B if r["config"] == cb}
    if not ra or set(ra) != set(rb):
        bad.append("%s->%s: kernel sets differ (%d vs %d)" % (ca, cb, len(ra), len(rb)))
        continue
    for k in sorted(ra):
        fields = [f for f in ra[k] if f not in ("config", "config_id") and f in rb[k]]
        d = [f for f in fields if ra[k][f] != rb[k][f]]
        n += 1
        if d:
            bad.append("%s/%s->%s: %s" % (k, ca, cb, [(f, ra[k][f], rb[k][f]) for f in d[:4]]))
print("[%s] %d row pair(s) compared%s" % ("IDENTICAL" if not bad else "DIFF", n,
      "" if not bad else ": " + "; ".join(bad[:6])))
sys.exit(1 if bad else 0)
