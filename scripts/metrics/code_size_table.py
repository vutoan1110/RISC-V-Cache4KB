"""Code-size table from the linker maps written by scripts/metrics/code_size_r14.sh.

Every input section in the map's memory-map part is charged to the object it came from:
  kernel   the benchmark's own sources (embench_<k>.c, the upstream kernel files, embench_ramsweep.c)
  harness  startup.S and main_*.c: boot, measurement window and the UART report
  support  embench_beebs.c and libc_shim.c: heap, rand and the small libc the kernels call
  libgcc   the compiler runtime (rv32i_zmmul has no divide instruction, so division comes from here)
  fill     alignment padding
The per-output-section sums are checked against the section sizes the map itself reports.

    python scripts/metrics/code_size_table.py   -> results/code_size_r14.csv
"""
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "results" / "code_size_r14"
SECTIONS = (".text", ".rodata", ".data", ".bss")
HARNESS = re.compile(r"-(startup|main_[\w-]+|main_upstream)\.o$")
SUPPORT = re.compile(r"-(embench_beebs|libc_shim)\.o$")

out_re = re.compile(r"^(\.[\w.]+)\s+0x([0-9a-f]+)\s+0x([0-9a-f]+)")
in_full = re.compile(r"^ (\S+)\s+0x([0-9a-f]+)\s+0x([0-9a-f]+)\s*(.*)$")
in_name = re.compile(r"^ (\.\S+|COMMON)\s*$")
in_rest = re.compile(r"^\s+0x([0-9a-f]+)\s+0x([0-9a-f]+)\s+(\S.*)$")


def category(obj):
    if not obj:
        return "fill"
    if "libgcc.a(" in obj or "libc.a(" in obj:
        return "libgcc"
    if HARNESS.search(obj):
        return "harness"
    if SUPPORT.search(obj):
        return "support"
    return "kernel"


def parse(path):
    sizes = defaultdict(int)         # (output section, category) -> bytes
    totals = {}
    lines = path.read_text(errors="replace").splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.startswith("Linker script and memory map"))
    except StopIteration:
        raise SystemExit("[FAIL] %s: no memory map" % path)
    cur, pending = None, None
    for line in lines[start:]:
        m = out_re.match(line)
        if m and not line.startswith(" "):
            cur = m.group(1) if m.group(1) in SECTIONS else None
            if cur:
                totals[cur] = int(m.group(3), 16)
            pending = None
            continue
        if line and not line.startswith(" "):
            cur = line.split()[0] if line.split()[0] in SECTIONS else None
            pending = None
            continue
        if cur is None:
            continue
        if pending is not None:
            m = in_rest.match(line)
            if m:
                sizes[(cur, category(m.group(3).strip()))] += int(m.group(2), 16)
            pending = None
            continue
        m = in_full.match(line)
        if m and (m.group(1).startswith(".") or m.group(1) in ("*fill*", "COMMON")):
            obj = m.group(4).strip() if m.group(1) != "*fill*" else ""
            sizes[(cur, category(obj))] += int(m.group(3), 16)
            continue
        if in_name.match(line):
            pending = line.strip()
    return sizes, totals


def main():
    status = dict(l.split() for l in (SRC / "status.txt").read_text().splitlines() if l.strip())
    cats = ("kernel", "harness", "support", "libgcc", "fill")
    cols = ["image", "hex_check"] + [s.lstrip(".") for s in SECTIONS] + ["rom_bytes"] + \
           ["%s_%s" % (s.lstrip("."), c) for s in (".text", ".rodata") for c in cats] + \
           ["data_kernel", "bss_kernel", "text_kernel_share_pct", "check"]
    rows = []
    for name, st in status.items():
        if st != "HEX_IDENTICAL":
            rows.append({"image": name, "hex_check": st})
            continue
        sizes, totals = parse(SRC / (name + ".map"))
        r = {"image": name, "hex_check": st}
        for s in SECTIONS:
            r[s.lstrip(".")] = totals.get(s, 0)
        r["rom_bytes"] = r["text"] + r["rodata"] + r["data"]
        for s in (".text", ".rodata"):
            for c in cats:
                r["%s_%s" % (s.lstrip("."), c)] = sizes.get((s, c), 0)
        r["data_kernel"] = sizes.get((".data", "kernel"), 0)
        r["bss_kernel"] = sizes.get((".bss", "kernel"), 0)
        r["text_kernel_share_pct"] = round(100.0 * r["text_kernel"] / r["text"], 1) if r["text"] else ""
        bad = [s for s in SECTIONS if sum(sizes.get((s, c), 0) for c in cats) != totals.get(s, 0)]
        r["check"] = "OK" if not bad else "SUM_MISMATCH:" + ",".join(bad)
        rows.append(r)
    with open(ROOT / "results" / "code_size_r14.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print("%-18s %-14s text %6s (kernel %6s, harness %5s, support %5s, libgcc %5s)  rodata %6s  data %4s  %s"
              % (r["image"], r["hex_check"], r.get("text", ""), r.get("text_kernel", ""), r.get("text_harness", ""),
                 r.get("text_support", ""), r.get("text_libgcc", ""), r.get("rodata", ""), r.get("data", ""),
                 r.get("check", "")))
    return 0 if all(r.get("check") == "OK" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
