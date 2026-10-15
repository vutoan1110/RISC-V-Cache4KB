"""2026-10-14: compare the two independent executions of the DM_VC4 LEC part that depends only on the synthesis
(results/lec_vc4_20261014/p1, p2: front end GoldN1, steps A, Mul, Inv, NegFSM, xsens) object by object, as
compare_lec_passes.py does for the full SA2 LEC: SHA-256 of every proof input / mapping / named LEC network / residual
list, and the verdict lines of every step. The constant-fixpoint rounds (specA_c<r>.json) are taken from the folders and
must be the same set in both. Solver-reduced AIGs are compared by their verdicts only (ABC writes a timestamp into
the AIGER comment). Writes a JSON receipt and exits 1 on any difference.
usage: python compare_lec_vc4_goldn1.py <pass1 folder> <pass2 folder> <out.json>"""
import hashlib
import json
import os
import re
import sys

p1, p2, out = sys.argv[1:4]
# 2026-10-15: DM / SA2 on 6c4ccffd have no SRAM removed by synthesis, hence no NegAlign control (--no-negalign)
NO_NEGALIGN = "--no-negalign" in sys.argv[4:]
rounds = [sorted(f for f in os.listdir(p) if re.fullmatch(r"specA_c\d+\.json", f)) for p in (p1, p2)]
EXACT = ["enc.txt", "replay/n1_pre_abc_fast.il", "replay/soc_asic_top.nl.v", "gold_pre.il", "gold_flat.il", "n1_flat.il",
         "gold_flat_al.il", "n1_flat_al.il",
         "pairs_a.json", "specA_0.json"] + sorted(set(rounds[0]) | set(rounds[1])) + [
         "A_spec.json", "A_gold.aig", "A_gate.aig", "A_open.txt", "t1/t1_iter1.il", "AX_gold.aig", "AX_gate.aig",
         "mul_pure_gold.aig", "mul_pure_gate.aig", "mulproof/t1_pure.aig", "mulproof/rtl_t2_pure.aig", "A_mul_outs.txt",
         "AXs_gold.aig", "AXs_gate.aig", "gold_inv.aig", "inv_proof.aig", "xsens_main/A_gold_xf.aig",
         "xsens_main/A_gold_xz.aig"]
VERDICTS = {  # file -> regex whose matches must be identical in both passes
    "stepA.out": r"(Unsat calls|Sat   calls|Undef calls)\s+\d+|outputs \d+, open \(not proved\) \d+|NOT proved \d+|const \d+, dup \d+, free \d+",
    "stepMul.out": r"RESULT: \S+( \S+)?|Networks are \w+|targets: \d+",
    "stepInv.out": r"ALL_PROVED \d+|NOT_PROVED \d+|-> one-hot|-> NOT one-hot",
    "stepNegFSM.out": r"prove_fsm_neg rc=\d+|Found \d+ unproven|successfully proven",
    "stepNegAlign.out": r"(Unsat calls|Sat   calls|Undef calls)\s+\d+|lec_d_p00001 (DETECTED \(open\)|NOT DETECTED)",
    "align.log": r"gold-only SRAM instances \d+|ALIGNED: both sides now have \d+ ports",
    "prove_fsm.log": r"Equivalence successfully proven!|Found \d+ unproven",
    "xsens_main/xzero.log": r"ALL_PROVED \d+|NOT_PROVED \d+ of \d+",
    "xsens_main/xtie.log": r"tied \d+ of \d+ inputs",
}


if NO_NEGALIGN:
    VERDICTS.pop("stepNegAlign.out")
def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


rows, diffs = [], 0
if rounds[0] != rounds[1]:
    rows.append({"object": "constant fixpoint rounds", "status": "DIFFERS", "p1": rounds[0], "p2": rounds[1]})
    diffs += 1
for f in EXACT:
    a, b = os.path.join(p1, f), os.path.join(p2, f)
    if not (os.path.exists(a) and os.path.exists(b)):
        rows.append({"object": f, "status": "MISSING", "p1": os.path.exists(a), "p2": os.path.exists(b)})
        diffs += 1
        continue
    ha, hb = sha(a), sha(b)
    diffs += ha != hb
    rows.append({"object": f, "status": "SAME" if ha == hb else "DIFFERS", "sha256_p1": ha, "sha256_p2": hb})
for f, rx in VERDICTS.items():
    a, b = os.path.join(p1, f), os.path.join(p2, f)
    if not (os.path.exists(a) and os.path.exists(b)):
        rows.append({"verdicts": f, "status": "MISSING"})
        diffs += 1
        continue
    va = [m.group(0) for m in re.finditer(rx, open(a, errors="replace").read())]
    vb = [m.group(0) for m in re.finditer(rx, open(b, errors="replace").read())]
    same = va == vb and len(va) > 0
    diffs += not same
    rows.append({"verdicts": f, "status": "SAME" if same else ("DIFFERS" if va != vb else "NO_VERDICT_LINES"),
                 "p1": va, "p2": vb if va != vb else "same"})
rec = {"pass1": p1, "pass2": p2, "constant_rounds": rounds[0], "differences": diffs, "rows": rows,
       "status": "PASS1_EQUALS_PASS2" if diffs == 0 else "DIFFERENCES_FOUND"}
json.dump(rec, open(out, "w"), indent=1)
for r in rows:
    print("%-16s %s" % (r["status"], r.get("object") or ("verdicts of " + r["verdicts"])))
print(rec["status"], diffs)
sys.exit(0 if diffs == 0 else 1)
