#!/usr/bin/env python3
"""Workspace cleanup after the Option-A equivalence proof (user rule 4, PD_metrics.pdf;
FLOW_JOURNAL Incidents 89-90).

    python scripts/cleanup_20260927b.py            # dry run: list + sizes
    python scripts/cleanup_20260927b.py --do       # gzip the evidence, hash, delete, write manifest

Kept as gzip evidence first (the two inputs of the algebraic multiplier proof, macc_alg.py):
  asic/equiv/lec/synth_replay_t1/t1_iter1.il, asic/equiv/lec/mulproof/rtl_t2.il
Deleted (regenerable intermediates; the sha256 of every file goes to the manifest, and the
scripts rebuild them: the synthesis replays are byte-identical, the proof steps were double-run):
  * every RTLIL file larger than 1 MB under asic/equiv (sec, lec, synth_replay*, mulproof);
  * the bulky replay by-products: soc_asic_top.nl.v(.json), primitive_techmap.dot, hierarchy.dot
    (the replayed netlist is byte-identical to runs/final_B/06-yosys-synthesis);
  * asic/equiv/sec/miter_sym.vmap (symbol map of the SEC miter);
  * superseded LEC experiments: lec/gate_lec*.aig, lec/gold_lec*.aig, lec/cof/*.aig (alu_ctrl
    cofactor runs), lec/mul_gate.aig, lec/mul_gold.aig, lec/fraig1_out.aig.
KEEP: every log and markdown file, all scripts, the proof objects (*_proof*.aig, miter*.aig,
inv_*.aig, the A/AX/B pair AIGs, AXs_*/AXn_* substitution miters, every pure multiplier AIG),
the specs/pair JSONs, and everything outside asic/equiv.
"""
import glob
import gzip
import hashlib
import os
import shutil
import sys

DO = "--do" in sys.argv
R = r"E:\Projects\RISCV-research"
EQ = os.path.join(R, r"asic\equiv")
MANIFEST = os.path.join(R, r"results\cleanup_20260927b_deleted.txt")
MB = 1 << 20
GZ = [os.path.join(EQ, r"lec\synth_replay_t1\t1_iter1.il"), os.path.join(EQ, r"lec\mulproof\rtl_t2.il")]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 22), b""):
            h.update(blk)
    return h.hexdigest()


targets = []
for p in glob.glob(os.path.join(EQ, "**", "*.il"), recursive=True):
    if os.path.getsize(p) > MB:
        targets.append(p)
for d in glob.glob(os.path.join(EQ, r"lec\synth_replay*")):
    for n in ("soc_asic_top.nl.v", "soc_asic_top.nl.v.json", "primitive_techmap.dot", "hierarchy.dot"):
        p = os.path.join(d, n)
        if os.path.isfile(p):
            targets.append(p)
targets.append(os.path.join(EQ, r"sec\miter_sym.vmap"))
for pat in (r"lec\gate_lec*.aig", r"lec\gold_lec*.aig", r"lec\cof\*.aig", r"lec\mul_gate.aig",
            r"lec\mul_gold.aig", r"lec\fraig1_out.aig"):
    targets += glob.glob(os.path.join(EQ, pat))
targets = sorted({p for p in targets if os.path.isfile(p)})
total = sum(os.path.getsize(p) for p in targets)
for p in targets:
    print("%9.1f MB  %s" % (os.path.getsize(p) / MB, os.path.relpath(p, R)))
print("%d files, %.1f MB%s" % (len(targets), total / MB, "" if DO else "  (dry run)"))
if not DO:
    sys.exit(0)

lines = ["# cleanup_20260927b (FLOW_JOURNAL Incident 90): sha256  bytes  path (deleted, regenerable)"]
for p in GZ:
    h = sha(p)
    with open(p, "rb") as fi, gzip.open(p + ".gz", "wb", compresslevel=9) as fo:
        shutil.copyfileobj(fi, fo, 1 << 22)
    g = hashlib.sha256()
    with gzip.open(p + ".gz", "rb") as fi:
        for blk in iter(lambda: fi.read(1 << 22), b""):
            g.update(blk)
    assert g.hexdigest() == h, "gzip round trip mismatch: " + p
    lines.append("# kept as gzip (round trip verified): %s  %s.gz" % (h, os.path.relpath(p, R)))
    print("gzip ok:", os.path.relpath(p, R) + ".gz")
for p in targets:
    lines.append("%s  %d  %s" % (sha(p), os.path.getsize(p), os.path.relpath(p, R)))
open(MANIFEST, "w", newline="\n").write("\n".join(lines) + "\n")
for p in targets:
    os.remove(p)
print("deleted %d files, %.1f MB; manifest %s" % (len(targets), total / MB, os.path.relpath(MANIFEST, R)))
