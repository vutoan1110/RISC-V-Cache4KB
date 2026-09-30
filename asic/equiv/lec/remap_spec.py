"""FLOW_JOURNAL Incident 89: carry a spec (const/dup/free) from one pairs json to another built from
a re-written RTLIL of the same sides (only the flop ORDER changes). Flops are identified by
(cell name, bit); every const/dup entry must map, or the script fails.
usage: python remap_spec.py pairs_old.json spec_old.json pairs_new.json spec_new.json"""
import json
import sys

po, so, pn, sn = sys.argv[1:5]
PO, SO, PN = json.load(open(po)), json.load(open(so)), json.load(open(pn))


def ident(side, P, i):
    f = P[side][i]
    return (f["cell"], f["i"])


go_new = {ident("gold", PN, i): k for k, i in enumerate(PN["gold_only"])}
pair_new = {(ident("gold", PN, i), ident("gate", PN, j)): k for k, (i, j) in enumerate(PN["pairs"])}
assert len(PN["gold_only"]) == len(PO["gold_only"]) and len(PN["pairs"]) == len(PO["pairs"])
out = {"const": {}, "dup": {}, "free": []}
for k, v in SO["const"].items():
    out["const"][str(go_new[ident("gold", PO, PO["gold_only"][int(k)])])] = v
for k, p in SO["dup"].items():
    i, j = PO["pairs"][p]
    out["dup"][str(go_new[ident("gold", PO, PO["gold_only"][int(k)])])] = pair_new[(ident("gold", PO, i), ident("gate", PO, j))]
out["free"] = sorted(go_new[ident("gold", PO, PO["gold_only"][k])] for k in SO["free"])
json.dump(out, open(sn, "w"), indent=1)
print("remapped const %d, dup %d, free %d" % (len(out["const"]), len(out["dup"]), len(out["free"])))
