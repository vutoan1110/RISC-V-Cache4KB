"""Review M1/M2 sweep: does the sweep runner reproduce the frozen R15 results at the published point?

    python scripts/m2/check_m2_vs_ref.py results/m2/sweep_p0.csv
Every 4 KiB / 16 B-line row of the sweep CSV (DM, DM_DSE, SA2, VC4, SA4) is compared field by field with
results/r15_4kb_p1.csv (Embench) or results/coremark_r15_4kb_p1.csv (CoreMark). Exit 0 only if every compared row
is identical in every snapshot field and at least one row was compared.

    python scripts/m2/check_m2_vs_ref.py results/m2/sweep_p1.csv results/m2/sweep_p2.csv
With two sweep CSVs: pass 1 = pass 2 on every row and field (double execution).
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from snapshot_fields import FIELDS  # noqa: E402

NAME = {"DM": "DM", "DM_DSE": "DM_DSE", "SA2": "SA2", "VC4": "DM_VC4", "SA4": "SA4"}


def load(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


if len(sys.argv) == 3:
    a = {(r["point"], r["workload"]): r for r in load(sys.argv[1])}
    b = {(r["point"], r["workload"]): r for r in load(sys.argv[2])}
    keys = sorted(set(a) | set(b))
    bad = [k for k in keys if k not in a or k not in b or any(a[k][f] != b[k][f] for f in FIELDS)]
    print("%d rows in pass 1, %d in pass 2, %d common; %d differ or are missing" % (len(a), len(b),
                                                                                   len(set(a) & set(b)), len(bad)))
    for k in bad[:20]:
        print("   ", k)
    sys.exit(0 if not bad and keys else 1)

ref = {}
for r in load(ROOT / "results" / "r15_4kb_p1.csv"):
    ref[(r["config"], r["kernel"])] = r
for r in load(ROOT / "results" / "coremark_r15_4kb_p1.csv"):
    ref[(r["config"], "coremark")] = r
n, bad = 0, []
for r in load(sys.argv[1]):
    if r["cap_bytes"] != "4096" or r["line_bytes"] != "16" or r["org"] not in NAME:
        continue
    k = (NAME[r["org"]], r["workload"])
    if k not in ref:
        bad.append("%s/%s: no reference row" % k)
        continue
    n += 1
    diff = [f for f in FIELDS if f in ref[k] and r[f] != ref[k][f]]
    missing = [f for f in FIELDS if f not in ref[k]]
    if diff:
        bad.append("%s/%s differs in %s" % (k[0], k[1], ", ".join("%s %s!=%s" % (f, r[f], ref[k][f]) for f in diff[:6])))
    print("%-7s %-16s %s%s" % (k[0], k[1], "IDENTICAL" if not diff else "DIFFERS",
                               "" if not missing else " (reference lacks %s)" % ",".join(missing)))
print("%d rows compared, %d problems" % (n, len(bad)))
for b in bad:
    print("   ", b)
sys.exit(0 if n and not bad else 1)
