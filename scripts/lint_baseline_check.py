#!/usr/bin/env python3
"""Compare an OpenLane verilator-lint.log with the accepted warning baseline.

ERROR_ON_LINTER_WARNINGS stays False for soc_dm_4kb because 111 warnings are
by design (NHAT_KY.md, 2026-09-25). This keeps the gate honest instead:
any warning that is not in asic/soc_dm_4kb/lint_baseline.tsv fails the check.

usage: lint_baseline_check.py <verilator-lint.log> [baseline.tsv]
"""
import io, re, sys

log = sys.argv[1]
base = sys.argv[2] if len(sys.argv) > 2 else "asic/soc_dm_4kb/lint_baseline.tsv"
accepted = set()
for line in io.open(base, encoding="utf-8"):
    if line.startswith("#") or not line.strip():
        continue
    accepted.add(tuple(line.rstrip("\n").split("\t")))
found = set()
text = io.open(log, encoding="utf-8", errors="ignore").read()
for cls, path, _line, msg in re.findall(r"%Warning-([A-Z]+): (\S+?):(\d+):\d+: (.+)", text):
    m = re.search(r"'([^']+)'", msg)
    found.add((path.split("/")[-1], cls, m.group(1) if m else ""))
new = sorted(found - accepted)
gone = sorted(accepted - found)
print("lint baseline: %d accepted, %d found, %d new, %d no longer present"
      % (len(accepted), len(found), len(new), len(gone)))
for n in new:
    print("  NEW  %s %s %s" % n)
for g in gone:
    print("  GONE %s %s %s" % g)
sys.exit(1 if new else 0)
