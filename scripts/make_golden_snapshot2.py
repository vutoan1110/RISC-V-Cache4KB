#!/usr/bin/env python3
"""Golden Snapshot v2 of the workspace (FLOW_JOURNAL Incident 93: the final3 deliverable before the
experimental phase). Differences from make_golden_snapshot.py (Incident 88), which lost one file:
Questa rewrote the hard-linked `transcript` in place, so the snapshot's copy changed with it.

  * HARD-LINK only immutable artifacts: files inside a run's step directories
    (asic/*/runs/<run>/<NN-step>/...) and large binary intermediates by extension (.aig .il .saif .gds .odb
    .def .spef .gz .vcd .mag .lef .guide). Everything else, including logs, CSVs, text, `transcript`, the
    top-level files of a run (flow.log, resolved.json, error.log, which a resumed run rewrites) and every
    file under 1 MB, is COPIED.
  * The sha256 of EVERY file (copies and links) is recorded, so --verify also detects an in-place rewrite
    of a hard-linked file (Windows/NTFS links share content).
  * --restore puts the workspace back to the snapshot: every file whose content differs or which is missing
    is copied back from the snapshot (a copy, so the workspace no longer shares that inode); files created
    after the snapshot are LISTED (not deleted) in <snapshot>/RESTORE_EXTRA_FILES.txt.

    python scripts/make_golden_snapshot2.py <dst>              # create + verify
    python scripts/make_golden_snapshot2.py <dst> --verify     # re-verify the snapshot itself
    python scripts/make_golden_snapshot2.py <dst> --diff       # list workspace files that differ from it
    python scripts/make_golden_snapshot2.py <dst> --restore    # restore the workspace from it
"""
import hashlib
import os
import re
import shutil
import sys

SRC = r"E:\Projects\RISCV-research"
DST = sys.argv[1]
MODE = next((a for a in sys.argv[2:] if a.startswith("--")), "--create")
LIMIT = 1 << 20
IMMUTABLE_EXT = (".aig", ".il", ".saif", ".gds", ".odb", ".def", ".spef", ".gz", ".vcd", ".mag", ".lef", ".guide")
STEP_DIR = re.compile(r"(^|\\)runs\\[^\\]+\\\d+-[^\\]+\\", re.I)
MAN = os.path.join(DST, "GOLDEN_SNAPSHOT_MANIFEST.tsv")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def mode_for(rel, size):
    if size < LIMIT:
        return "copy"
    if STEP_DIR.search(rel) or rel.lower().endswith(IMMUTABLE_EXT):
        return "link"
    return "copy"


def walk(root):
    for d, dirs, files in os.walk(root):
        for fn in files:
            yield os.path.normpath(os.path.relpath(os.path.join(d, fn), root))


def manifest():
    rows = {}
    for line in open(MAN, encoding="utf-8"):
        if line.startswith("#"):
            continue
        m, size, h, rel = line.rstrip("\n").split("\t", 3)
        rows[rel] = (m, int(size), h)
    return rows


if MODE == "--create":
    if os.path.exists(DST):
        sys.exit("destination exists: %s" % DST)
    os.makedirs(DST)
    out = []
    for rel in walk(SRC):
        s, t = os.path.join(SRC, rel), os.path.join(DST, rel)
        os.makedirs(os.path.dirname(t), exist_ok=True)
        size = os.path.getsize(s)
        m = mode_for(rel, size)
        if m == "copy":
            shutil.copy2(s, t)
        else:
            os.link(s, t)
        out.append((m, size, sha(t), rel))
    with open(MAN, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Golden Snapshot v2 of %s (FLOW_JOURNAL Incident 93): mode\tbytes\tsha256\tpath\n" % SRC)
        for r in out:
            f.write("%s\t%d\t%s\t%s\n" % r)
    print("created %s: %d files (%d copied, %d hard-linked), %.2f GB referenced" % (
        DST, len(out), sum(r[0] == "copy" for r in out), sum(r[0] == "link" for r in out),
        sum(r[1] for r in out) / 2 ** 30))
    MODE = "--verify"

rows = manifest()
if MODE == "--verify":
    bad = 0
    for rel, (m, size, h) in rows.items():
        t = os.path.join(DST, rel)
        if not os.path.isfile(t) or os.path.getsize(t) != size or sha(t) != h:
            bad += 1
            print("CHANGED/MISSING", rel)
        elif m == "copy" and os.path.exists(os.path.join(SRC, rel)) and \
                os.stat(t).st_ino == os.stat(os.path.join(SRC, rel)).st_ino:
            bad += 1
            print("COPY SHARES INODE", rel)
    print("verified %d files, %d problems" % (len(rows), bad))
    sys.exit(1 if bad else 0)

if MODE in ("--diff", "--restore"):
    changed = []
    for rel, (m, size, h) in rows.items():
        w = os.path.join(SRC, rel)
        if not os.path.isfile(w) or os.path.getsize(w) != size or sha(w) != h:
            changed.append(rel)
    extra = sorted(set(walk(SRC)) - set(rows))
    print("workspace vs snapshot: %d changed/missing, %d files created after the snapshot" % (len(changed), len(extra)))
    for rel in changed[:50]:
        print("  CHANGED/MISSING", rel)
    if MODE == "--restore":
        for rel in changed:
            w, t = os.path.join(SRC, rel), os.path.join(DST, rel)
            os.makedirs(os.path.dirname(w), exist_ok=True)
            if os.path.exists(w):
                os.remove(w)
            shutil.copy2(t, w)
        with open(os.path.join(DST, "RESTORE_EXTRA_FILES.txt"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(extra) + "\n")
        print("restored %d files; %d extra files listed in RESTORE_EXTRA_FILES.txt (not deleted)" % (len(changed), len(extra)))
