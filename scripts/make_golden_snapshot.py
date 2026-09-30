#!/usr/bin/env python3
"""Golden Snapshot of the signed-off 4 KiB workspace (user directive 2026-09-27, before any
Option-B PD rerun). FLOW_JOURNAL Incident 88.

    python scripts/make_golden_snapshot.py <dst>            # create
    python scripts/make_golden_snapshot.py <dst> --verify   # re-verify an existing snapshot

Files that can still be edited in place (text/scripts/tables anywhere, and everything under
1 MB) are COPIED, so later edits in the workspace cannot reach the snapshot through a shared
inode. Large immutable artifacts (run outputs: odb/def/gds/spef/netlists/logs under runs/,
AIG/RTLIL intermediates) are HARD-LINKED: same volume, no extra space, and deleting them in the
workspace does not delete them from the snapshot. A manifest records every file with its mode
(copy/link), size and, for copies, SHA-256; --verify re-checks all of it.
"""
import hashlib
import os
import shutil
import sys

SRC = r"E:\Projects\RISCV-research"
DST = sys.argv[1]
VERIFY = "--verify" in sys.argv
EDITABLE = (".md", ".txt", ".py", ".sh", ".ps1", ".ys", ".v", ".sv", ".vh", ".json", ".csv", ".tcl",
            ".eqy", ".sdc", ".qsf", ".qpf", ".cfg", ".yaml", ".yml", ".mk", ".c", ".h", ".S", ".ld")
LIMIT = 1 << 20


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def mode_for(rel, size):
    parts = rel.lower().split(os.sep)
    in_runs = "runs" in parts
    if size < LIMIT:
        return "copy"
    if rel.lower().endswith(EDITABLE) and not in_runs:
        return "copy"
    return "link"


man_path = os.path.join(DST, "GOLDEN_SNAPSHOT_MANIFEST.tsv")
if not VERIFY:
    if os.path.exists(DST):
        sys.exit("destination exists: %s" % DST)
    os.makedirs(DST)
    rows = []
    for d, dirs, files in os.walk(SRC):
        rd = os.path.relpath(d, SRC)
        os.makedirs(os.path.join(DST, rd), exist_ok=True)
        for fn in files:
            s = os.path.join(d, fn)
            rel = os.path.normpath(os.path.join(rd, fn))
            t = os.path.join(DST, rel)
            size = os.path.getsize(s)
            m = mode_for(rel, size)
            if m == "copy":
                shutil.copy2(s, t)
                rows.append((m, size, sha(s), rel))
            else:
                os.link(s, t)
                rows.append((m, size, "-", rel))
    with open(man_path, "w", newline="\n") as f:
        f.write("# Golden Snapshot of %s (FLOW_JOURNAL Incident 88): mode\tbytes\tsha256(copies)\tpath\n" % SRC)
        for r in rows:
            f.write("%s\t%d\t%s\t%s\n" % r)
    print("created %s: %d files (%d copied, %d hard-linked), %.2f GB referenced"
          % (DST, len(rows), sum(r[0] == "copy" for r in rows), sum(r[0] == "link" for r in rows),
             sum(r[1] for r in rows) / 2**30))

# verification (always)
bad = 0
n = 0
for line in open(man_path):
    if line.startswith("#"):
        continue
    m, size, h, rel = line.rstrip("\n").split("\t", 3)
    t = os.path.join(DST, rel)
    n += 1
    if not os.path.isfile(t) or os.path.getsize(t) != int(size):
        bad += 1
        print("MISSING/SIZE", rel)
        continue
    if m == "copy":
        if sha(t) != h:
            bad += 1
            print("HASH", rel)
        st, ss = os.stat(t), os.stat(os.path.join(SRC, rel)) if os.path.exists(os.path.join(SRC, rel)) else None
        if ss is not None and st.st_ino == ss.st_ino:
            bad += 1
            print("COPY SHARES INODE", rel)
    else:
        if os.stat(t).st_nlink < 1:
            bad += 1
            print("LINK", rel)
print("verified %d files, %d problems" % (n, bad))
sys.exit(1 if bad else 0)
