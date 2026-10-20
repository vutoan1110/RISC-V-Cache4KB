#!/usr/bin/env python3
"""Quartus Power Analyzer per design point (review item A9).

The fitter alone is not enough: quartus_pow refuses to run until the assembler
has produced a programming image, so each point is assembled first. Estimation
is vectorless, which is a default-toggle-rate model rather than a measurement;
the numbers are comparable to each other but are not silicon power.

    python scripts/run_power.py --points dm,sa2,dm_vc4,dm_dse
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_fpga_points import POINTS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

FIELDS = [
    ("total_mw", r"Total Thermal Power Dissipation\s*;\s*([\d.]+)\s*mW"),
    ("core_dynamic_mw", r"Core Dynamic Thermal Power Dissipation\s*;\s*([\d.]+)\s*mW"),
    ("core_static_mw", r"Core Static Thermal Power Dissipation\s*;\s*([\d.]+)\s*mW"),
    ("io_mw", r"I/O Thermal Power Dissipation\s*;\s*([\d.]+)\s*mW"),
]


def tool(name: str) -> str:
    root = Path(os.environ.get("QUARTUS_ROOTDIR", r"D:\altera\quartus")) / "bin64"
    found = shutil.which(name) or (root / (name + ".exe"))
    if not (found and Path(found).is_file()):
        sys.exit("[FAIL] %s not found" % name)
    return str(found)


def run(cmd: list[str], log: Path) -> int:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=7200)
    log.write_bytes(((p.stdout or "") + (p.stderr or "")).encode("utf-8", "replace"))
    return p.returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", default="dm,sa2,dm_vc4,dm_dse")
    ap.add_argument("--out", default="results/power.csv")
    # The L0 variants fit into the same Quartus revision as their base
    # point, so the row has to be labelled or it overwrites the base row.
    # Run this immediately after the matching fit.
    ap.add_argument("--l0", type=int, default=8)
    args = ap.parse_args()

    # Same cooperative abort as run_fpga_points.py.
    if (ROOT / "results" / ".abort_fpga_sweep").exists():
        print("[ABORT] results/.abort_fpga_sweep present; nothing run")
        return 3

    asm, pow_ = tool("quartus_asm"), tool("quartus_pow")
    rows, failed = [], []
    for name in args.points.split(","):
        if name not in POINTS:
            sys.exit("[FAIL] unknown point '%s'" % name)
        rev = "point_" + name
        dest = ROOT / "results" / "power" / name
        dest.mkdir(parents=True, exist_ok=True)
        print("[RUN] %s" % name)
        t0 = time.time()
        if run([asm, rev, "-c", rev], dest / "asm.log"):
            print("      [FAIL] assembler; see %s" % (dest / "asm.log"))
            failed.append(name)
            continue
        if run([pow_, rev, "-c", rev], dest / "pow.log"):
            print("      [FAIL] power analyzer; see %s" % (dest / "pow.log"))
            failed.append(name)
            continue

        out_dir = ROOT / ("output_files_" + name)
        rpt = out_dir / (rev + ".pow.rpt")
        label = name if args.l0 == 8 else "%s@l0-%d" % (name, args.l0)
        row = {"point": label, "cache_config": POINTS[name][0]}
        if rpt.exists():
            shutil.copy2(rpt, dest / rpt.name)
            txt = rpt.read_bytes().decode("utf-8", "replace")
            for key, pat in FIELDS:
                m = re.search(pat, txt)
                row[key] = float(m.group(1)) if m else None
        rows.append(row)
        print("      %s: total=%s mW  core_dyn=%s  core_static=%s  io=%s  [%.0fs]"
              % (label, row.get("total_mw"), row.get("core_dynamic_mw"),
                 row.get("core_static_mw"), row.get("io_mw"), time.time() - t0))

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = ["point", "cache_config"] + [f[0] for f in FIELDS]
    # Merge, do not overwrite: this script is run one point at a time, right
    # after that point's fit, so overwriting throws away every earlier result.
    existing = []
    if out.is_file():
        existing = [r for r in csv.DictReader(out.open(encoding="utf-8"))
                    if r["point"] not in {r2["point"] for r2 in rows}]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(existing)
        w.writerows(rows)
    print("")
    print("[%s] %d point(s) -> %s"
          % ("PASS" if not failed else "PARTIAL", len(rows), out))
    for n in failed:
        print("   failed: %s" % n)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
