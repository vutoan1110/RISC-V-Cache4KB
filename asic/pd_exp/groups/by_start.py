"""FLOW_JOURNAL Incident 93: violating setup endpoints grouped by the START of their worst path (register
group from the Q net name, or SRAM macro + pin bus for macro launches).  python by_start.py <corner> run..."""
import collections
import csv
import os
import re
import sys

corner = sys.argv[1]
here = os.path.dirname(os.path.abspath(__file__))
for r in sys.argv[2:]:
    rows = list(csv.DictReader(open(os.path.join(here, r, "endgroups_%s.tsv" % corner)), delimiter="\t"))
    count = collections.Counter()
    worst = {}
    for x in rows:
        sp, sn = x["startpoint"], x["startnet"].replace("\\", "")
        if "u_bank" in sp:
            mem = "icache" if "icache" in sp else "dcache" if "dcache" in sp else "axi_ram"
            k = "SRAM %s %s" % (mem, re.sub(r"\[\d+\]$", "", sp.split("/")[-1].replace("\\", "")))
        else:
            k = re.sub(r"\[\d+\]$", "", sn) or sp
        count[k] += 1
        worst[k] = min(worst.get(k, 0.0), float(x["slack"]))
    sram = sum(v for k, v in count.items() if k.startswith("SRAM"))
    print("== %s: %d violating endpoints, %d of them from SRAM launches" % (r, len(rows), sram))
    for k, v in count.most_common(int(os.environ.get("TOP", "25"))):
        print("  %5d  worst %8.3f  %s" % (v, worst[k], k[-90:]))
