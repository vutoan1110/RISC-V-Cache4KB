# -*- coding: utf-8 -*-
"""Hash every RTL and testbench source, so "nothing changed" can be proved.

The project rule is that an RTL change carries the whole chain -- TB, UVM,
Embench, PD. The converse needs proof too: before reusing a verification result
we should be able to show the sources are bit-identical to the ones that
produced it, not merely believe so.

Writes results/rtl_manifest.json. Run with --check to compare against it.
"""
import hashlib
import json
import os
import sys

# verification/ holds the UVM environment and fw/ the benchmark images; both
# decide verification results, and the first version of this manifest left
# them out along with every ASIC design file.
ROOTS = ("hdl", "sim", "tb", "sw_baremetal", "uvm", "rtl", "verification", "fw", "sw")
# R14 (2026-09-29, RAM16K_CHANGES.md): "sw" added. The firmware sources (link.ld, platform.h, the
# benchmark ports) decide the memory layout and every benchmark result, and the tree is called sw/,
# not sw_baremetal/, so the manifest had silently not covered them. Build products are excluded.
SKIP_FILES = ("benchmark.hex", "benchmark_rv32.hex")
EXTS = (".v", ".sv", ".svh", ".vh", ".c", ".h", ".S", ".ld", ".hex")
# ASIC design sources, top level of each design directory only (runs/ holds
# generated netlists and is not a source).
ASIC_DESIGNS = ("asic/soc_dm_4kb",)
ASIC_EXTS = (".v", ".sv")   # RTL only; config.json, soc.sdc, *.cfg, *.eqy are PD files
SKIP_DIRS = ("results", "out", "work")
OUT = os.path.join("results", "rtl_manifest.json")


def collect():
    files = []
    for root in ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, dirs, names in os.walk(root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in sorted(names):
                if not name.endswith(EXTS) or name in SKIP_FILES:
                    continue
                path = os.path.join(dirpath, name).replace(os.sep, "/")
                with open(path, "rb") as fh:
                    files.append((path, hashlib.sha256(fh.read()).hexdigest()))
    for d in ASIC_DESIGNS:
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            path = d + "/" + name
            if os.path.isfile(path) and name.endswith(ASIC_EXTS) and "baseline_run1" not in name:
                with open(path, "rb") as fh:
                    files.append((path, hashlib.sha256(fh.read()).hexdigest()))
    files.sort()
    agg = hashlib.sha256("".join(p + h for p, h in files).encode()).hexdigest()
    return files, agg


files, agg = collect()

if "--check" in sys.argv:
    old = json.load(open(OUT))
    new = dict(files)
    added = sorted(set(new) - set(old["files"]))
    removed = sorted(set(old["files"]) - set(new))
    changed = sorted(p for p in set(new) & set(old["files"])
                     if new[p] != old["files"][p])
    print("manifest of %s, %d files, aggregate %s"
          % (old["generated"], old["count"], old["aggregate"][:16]))
    print("now              %d files, aggregate %s" % (len(files), agg[:16]))
    for tag, lst in (("added", added), ("removed", removed),
                     ("changed", changed)):
        for p in lst:
            print("  %-8s %s" % (tag, p))
    if not (added or removed or changed):
        print("  IDENTICAL -- verification results for this tree stay valid")
    sys.exit(0 if not (added or removed or changed) else 1)

json.dump({"generated": sys.argv[1] if len(sys.argv) > 1 else "",
           "count": len(files), "aggregate": agg,
           "files": dict(files)}, open(OUT, "w"), indent=1)
print("wrote %s: %d files, aggregate %s" % (OUT, len(files), agg[:32]))
