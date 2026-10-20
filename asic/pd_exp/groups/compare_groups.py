"""FLOW_JOURNAL Incident 93: per register group (Q net name without the bit index) worst setup slack and
violating-endpoint count, side by side for several runs.  python compare_groups.py <corner> run1 run2 ...
Env ALIAS=run:a=b,... renames a group of one run (e.g. final3's pc_f Q net is called u_soc.if_req_addr)."""
import collections
import csv
import os
import re
import sys

corner = sys.argv[1]
runs = sys.argv[2:]
here = os.path.dirname(os.path.abspath(__file__))
alias = {}
for pair in filter(None, os.environ.get("ALIAS", "").split(",")):
    run_key, _, to = pair.partition("=")
    alias[run_key] = to
data = {}
for r in runs:
    g = collections.defaultdict(list)
    for row in csv.DictReader(open(os.path.join(here, r, "endgroups_%s.tsv" % corner)), delimiter="\t"):
        q = row["qnet"] or ("macro:" + row["endpoint"].split("/")[-1])
        q = re.sub(r"\\?\[\d+\\?\]$", "", q)
        q = re.sub(r"u_soc\.u_(icache|dcache)\.g_dm_baseline\.u_data_ram\.u_ram\.g_bank\\?\[\d\\?\]\.u_bank", r"\1_bank", q)
        q = alias.get(r + ":" + q, q)
        g[q].append(float(row["slack"]))
    data[r] = g
keys = sorted(set().union(*[d.keys() for d in data.values()]),
              key=lambda k: min(min(d[k]) if k in d else 0 for d in data.values()))
print("%-64s" % "group" + "".join("%20s" % r for r in runs))
for k in keys[:int(os.environ.get("TOP", "40"))]:
    cells = []
    for r in runs:
        v = data[r].get(k)
        cells.append("%8.3f (%5d)" % (min(v), len(v)) if v else "%15s" % "-")
    print("%-64s" % k[-64:] + "".join("%20s" % c for c in cells))
for r in runs:
    print(r, "endpoints", sum(len(v) for v in data[r].values()), "groups", len(data[r]),
          "sum of slack %.0f" % sum(sum(v) for v in data[r].values()))
