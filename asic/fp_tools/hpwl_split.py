# NHAT_KY.md section 8: split the placed HPWL of a design into nets touching a macro (grouped by macro kind
# and pin group) and nets between std cells only (grouped by HPWL length class), to see where SA2 / DM_VC4 put
# their extra wire compared with DM.
# Run: openroad -python -exit hpwl_split.py <odb> <label>
import collections
import re
import sys

import odb

path, label = sys.argv[1], sys.argv[2]
db = odb.dbDatabase.create()
odb.read_db(db, path)
block = db.getChip().getBlock()
dbu = block.getDefUnits()
mac = collections.Counter()
macn = collections.Counter()
std = collections.Counter()
stdn = collections.Counter()
tot = 0.0
for net in block.getNets():
    if net.getSigType() in ("POWER", "GROUND", "CLOCK"):
        continue
    xs, ys, mk = [], [], None
    for it in net.getITerms():
        ok, x, y = it.getAvgXY()
        if not ok:
            continue
        xs.append(x / dbu)
        ys.append(y / dbu)
        inst = it.getInst()
        if inst.getMaster().getType() == "BLOCK":
            n = inst.getName()
            kind = "RAM" if "axi_ram" in n else ("I$" if "icache" in n else "D$")
            pin = re.sub(r"\[\d+\]", "", it.getMTerm().getName())
            mk = "%s.%s" % (kind, pin)
    if len(xs) < 2:
        continue
    h = (max(xs) - min(xs)) + (max(ys) - min(ys))
    tot += h
    if mk:
        mac[mk] += h
        macn[mk] += 1
    else:
        c = "<100" if h < 100 else "100-500" if h < 500 else "500-1000" if h < 1000 else ">=1000"
        std[c] += h
        stdn[c] += 1
print("%s: total HPWL %.3f m (signal nets, clock excluded)" % (label, tot / 1e6))
print("  macro nets  %.3f m:" % (sum(mac.values()) / 1e6), ", ".join(
    "%s %.0f mm/%d" % (k, v / 1e3, macn[k]) for k, v in sorted(mac.items(), key=lambda kv: -kv[1])[:14]))
for c in ("<100", "100-500", "500-1000", ">=1000"):
    print("  std-only %-9s %.3f m in %6d nets" % (c, std[c] / 1e6, stdn[c]))
