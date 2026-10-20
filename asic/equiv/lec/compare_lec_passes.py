"""2026-10-13: compare two independent executions of the SA2 LEC (two work folders, each with its own front end and
replay) object by object: SHA-256 of every proof input / mapping / named LEC network / residual list, and the verdict
lines of every step. Solver-reduced AIGs (msat*_a/b, xsens_*) are compared by their verdicts only, since ABC may
order their nodes differently. Writes a JSON receipt and exits 1 on any difference in an exact object or verdict.
usage: python compare_lec_passes.py <pass1 folder> <pass2 folder> <out.json>"""
import hashlib
import json
import os
import re
import sys

p1, p2, out = sys.argv[1:4]
EXACT = ["enc.txt", "replay/n1_pre_abc_fast.il", "replay/soc_asic_top.nl.v", "gold_pre.il", "gold_flat.il", "n1_flat.il",
         "gate1_flat.il", "gate2_flat.il", "pairs_a.json", "pairs_b1.json", "pairs_b2.json", "specA_0.json",
         "specA_c1.json", "specA_c2.json", "A_spec.json", "A_gold.aig", "A_gate.aig", "A_open.txt", "t1/t1_iter1.il",
         "AX_gold.aig", "AX_gate.aig", "mul_pure_gold.aig", "mul_pure_gate.aig", "mulproof/t1_pure.aig",
         "mulproof/rtl_t2_pure.aig", "A_mul_outs.txt", "AXs_gold.aig", "AXs_gate.aig", "gold_inv.aig", "inv_proof.aig",
         "B1_spec.json", "B1_gold.aig", "B1_gate.aig", "B1_open.txt", "B2_spec.json", "B2_gold.aig", "B2_gate.aig",
         "B2_open.txt", "xsens_main/A_gold_xf.aig"]
VERDICTS = {  # file -> regex whose matches must be identical in both passes
    "stepA.out": r"(Unsat calls|Sat   calls|Undef calls)\s+\d+|outputs \d+, open \(not proved\) \d+|NOT proved \d+|const \d+, dup \d+, free \d+",
    "stepMul.out": r"RESULT: \S+( \S+)?|Networks are \w+|targets: \d+",
    "stepInv.out": r"ALL_PROVED \d+|NOT_PROVED \d+|-> one-hot|-> NOT one-hot",
    "stepB.out": r"(Unsat calls|Sat   calls|Undef calls)\s+\d+|outputs \d+, open \(not proved\) \d+|Networks are \w+",
    "prove_fsm.log": r"Equivalence successfully proven!|Found \d+ unproven",
    "xsens_main/xzero.log": r"ALL_PROVED \d+|NOT_PROVED \d+ of \d+",
}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


rows, diffs = [], 0
for f in EXACT:
    a, b = os.path.join(p1, f), os.path.join(p2, f)
    if not (os.path.exists(a) and os.path.exists(b)):
        rows.append({"object": f, "status": "MISSING", "p1": os.path.exists(a), "p2": os.path.exists(b)})
        diffs += 1
        continue
    ha, hb = sha(a), sha(b)
    same = ha == hb
    diffs += not same
    rows.append({"object": f, "status": "SAME" if same else "DIFFERS", "sha256_p1": ha, "sha256_p2": hb})
for f, rx in VERDICTS.items():
    a, b = os.path.join(p1, f), os.path.join(p2, f)
    if not (os.path.exists(a) and os.path.exists(b)):
        rows.append({"verdicts": f, "status": "MISSING"})
        diffs += 1
        continue
    va = [m.group(0) for m in re.finditer(rx, open(a, errors="replace").read())]
    vb = [m.group(0) for m in re.finditer(rx, open(b, errors="replace").read())]
    same = va == vb
    diffs += not same
    rows.append({"verdicts": f, "status": "SAME" if same else "DIFFERS", "p1": va, "p2": vb if not same else "same"})
rec = {"pass1": p1, "pass2": p2, "differences": diffs, "rows": rows,
       "status": "PASS1_EQUALS_PASS2" if diffs == 0 else "DIFFERENCES_FOUND"}
json.dump(rec, open(out, "w"), indent=1)
for r in rows:
    print("%-8s %s" % (r["status"], r.get("object") or ("verdicts of " + r["verdicts"])))
print(rec["status"], diffs)
sys.exit(0 if diffs == 0 else 1)
