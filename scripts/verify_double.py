#!/usr/bin/env python3
"""Compare two independent runs of the same measurement, field by field.

Independent executions establish reproducibility; they do not replace a
functional oracle or sign-off checks. The complete CSV schema and each row's
field count must agree before any values are compared.

    python scripts/verify_double.py pass_a.csv pass_b.csv --key point

Exit code 0 only when every row present in both passes matches on every
compared field. Rows present in one pass only are reported and fail the check --
a measurement that appeared once is not verified.
"""
from __future__ import annotations

import argparse
import csv
import sys

# Fields that legitimately differ between two runs of the same point, and so
# are not compared: wall-clock timings and anything naming a path.
IGNORE = {"runtime", "seconds", "elapsed", "path", "log"}


def load(path: str, key: str, also: str | None) -> dict:
    """Index rows by their identity.

    The composite key has to be built HERE. Indexing by `key` first and
    re-keying afterwards silently drops every row but one per kernel: the first
    version of this compared 12 rows of a 48-row matrix and printed VERIFIED.
    """
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f, strict=True)
        header = next(reader, None)
        if not header or any(not c.strip() for c in header):
            sys.exit("[FAIL] %s has a missing or blank CSV column" % path)
        if len(set(header)) != len(header):
            sys.exit("[FAIL] %s has duplicate CSV columns" % path)
        rows = []
        for number, values in enumerate(reader, 2):
            if len(values) != len(header):
                sys.exit("[FAIL] %s row %d has %d fields, expected %d"
                         % (path, number, len(values), len(header)))
            missing = [column for column, value in zip(header, values)
                       if column not in IGNORE and not value.strip()]
            if missing:
                sys.exit("[FAIL] %s row %d has missing compared values: %s"
                         % (path, number, ", ".join(missing)))
            rows.append(dict(zip(header, values)))
    if not rows:
        sys.exit("[FAIL] %s has no data rows" % path)
    for col in (c for c in (key, also) if c):
        if col not in rows[0]:
            sys.exit("[FAIL] %s has no column %r (has: %s)"
                     % (path, col, ", ".join(rows[0])))
    out = {}
    for r in rows:
        if any(not r[c].strip() for c in (key, also) if c):
            sys.exit("[FAIL] %s has an empty row identity" % path)
        k = (r[key], r[also]) if also else r[key]
        if k in out:
            sys.exit("[FAIL] %s has duplicate rows for %s -- the key is not "
                     "unique, add --also" % (path, k))
        out[k] = r
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pass_a")
    ap.add_argument("pass_b")
    ap.add_argument("--key", default="point",
                    help="column identifying a row; 'point' for fits, and for "
                         "simulation matrices use --key kernel with --also config")
    ap.add_argument("--also", default=None,
                    help="second column to include in the row identity")
    args = ap.parse_args()

    a = load(args.pass_a, args.key, args.also)
    b = load(args.pass_b, args.key, args.also)
    columns_a = set(next(iter(a.values())))
    columns_b = set(next(iter(b.values())))
    if columns_a != columns_b:
        print("[FAIL] CSV schema differs: only A=%s, only B=%s"
              % (sorted(columns_a - columns_b), sorted(columns_b - columns_a)))
        return 1

    only_a, only_b = sorted(set(a) - set(b)), sorted(set(b) - set(a))
    shared = sorted(set(a) & set(b))

    mismatched = 0
    for k in shared:
        diff = [f for f in a[k]
                if f not in IGNORE and a[k][f] != b[k][f]]
        if diff:
            mismatched += 1
            print("MISMATCH %s" % (k,))
            for f in diff:
                print("    %-16s A=%-14s B=%s" % (f, a[k][f], b[k][f]))

    for k in only_a:
        print("ONLY IN PASS A: %s" % (k,))
    for k in only_b:
        print("ONLY IN PASS B: %s" % (k,))

    ok = not mismatched and not only_a and not only_b
    print()
    print("%s  %d row(s) compared, %d identical, %d mismatched, %d unpaired"
          % ("[VERIFIED]" if ok else "[FAIL]", len(shared),
             len(shared) - mismatched, mismatched, len(only_a) + len(only_b)))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
