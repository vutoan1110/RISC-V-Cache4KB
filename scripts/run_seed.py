#!/usr/bin/env python3
"""Re-fit the three frozen cache configurations at one or more placement seeds.

Runs entirely inside research/, which mirrors the repository layout, so the
published output_files_de2_115_* directories are never touched. The RTL here is
a byte-identical copy of hdl/, so seed results are comparable to the paper.

    python scripts/run_seed.py --seeds 4
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = {
    "DM": "soc_top_de2_115_dm",
    "SA2": "soc_top_de2_115_sa2",
    "DM_VC4": "soc_top_de2_115_dm_vc4",
}
RETRIES = 3           # quartus_map/quartus_fit crash randomly at a few percent


def tool(name: str) -> str:
    root = Path(os.environ.get("QUARTUS_ROOTDIR", r"D:\altera\quartus")) / "bin64"
    found = shutil.which(name) or (root / (name + ".exe"))
    if not (found and Path(found).is_file()):
        sys.exit("[FAIL] %s not found; set QUARTUS_ROOTDIR" % name)
    return str(found)


def run(cmd: list[str], log: Path) -> None:
    """Run one Quartus stage, retrying the known random crashes."""
    for attempt in range(1, RETRIES + 1):
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True,
                              text=True, timeout=7200)
        log.write_bytes(((proc.stdout or "") + (proc.stderr or "")).encode(
            "utf-8", "replace"))
        if proc.returncode == 0:
            return
        print("      attempt %d failed (rc=%d)" % (attempt, proc.returncode))
        time.sleep(5)
    sys.exit("[FAIL] %s failed %d times; see %s" % (cmd[0], RETRIES, log))


def scrape(cfg: str, seed: int, dest: Path) -> dict:
    """Pull the headline numbers out of the fitter and timing reports."""
    project = PROJECTS[cfg]
    out = ROOT / ("output_files_" + project[len("soc_top_"):])
    row = {"config": cfg, "seed": seed}
    for suffix in ("fit.rpt", "sta.rpt", "map.rpt"):
        src = out / ("%s.%s" % (project, suffix))
        if src.exists():
            shutil.copy2(src, dest / src.name)

    fit = dest / ("%s.fit.rpt" % project)
    if fit.exists():
        txt = fit.read_bytes().decode("utf-8", "replace")
        for key, pat in (("le", r"Total logic elements\s*;\s*([\d,]+)"),
                         ("comb", r"Total combinational functions\s*;\s*([\d,]+)"),
                         ("regs", r"Dedicated logic registers\s*;\s*([\d,]+)"),
                         ("mem", r"Total memory bits\s*;\s*([\d,]+)")):
            m = re.search(pat, txt)
            row[key] = int(m.group(1).replace(",", "")) if m else None

    sta = dest / ("%s.sta.rpt" % project)
    if sta.exists():
        txt = sta.read_bytes().decode("utf-8", "replace")
        # Anchor on the table header itself; the same wording appears in the
        # report's table of contents, and the clock is named "clk", not "clk_50".
        m = re.search(r"^; Slow 1200mV 85C Model Setup Summary ;.*?"
                      r"^;\s*\S+\s*;\s*(-?[\d.]+)\s*;", txt, re.S | re.M)
        row["setup_slack"] = float(m.group(1)) if m else None
        m = re.search(r"^; Slow 1200mV 85C Model Fmax Summary.*?"
                      r"^;\s*[\d.]+ MHz\s*;\s*([\d.]+) MHz", txt, re.S | re.M)
        row["fmax"] = float(m.group(1)) if m else None
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="4")
    ap.add_argument("--configs", default=",".join(PROJECTS))
    ap.add_argument("--resume-sta", action="store_true",
                    help="a fit already completed; rerun timing analysis only")
    args = ap.parse_args()

    bins = {s: tool("quartus_" + s) for s in ("map", "fit", "sta")}
    rows = []
    for seed in [int(s) for s in args.seeds.split(",")]:
        for cfg in args.configs.split(","):
            project = PROJECTS[cfg]
            dest = ROOT / "results" / ("seed_%d" % seed) / cfg
            dest.mkdir(parents=True, exist_ok=True)
            print("[RUN] %s seed %d" % (cfg, seed))
            if not args.resume_sta:
                run([bins["map"], project, "--read_settings_files=on",
                     "--write_settings_files=off", "-c", project],
                    dest / "map.log")
                run([bins["fit"], project, "--read_settings_files=off",
                     "--write_settings_files=off", "--seed=%d" % seed,
                     "-c", project], dest / "fit.log")
            # quartus_sta rejects the settings-file switches the other tools take
            run([bins["sta"], project, "-c", project], dest / "sta.log")
            row = scrape(cfg, seed, dest)
            rows.append(row)
            print("      LE=%s  regs=%s  slack=%s ns" %
                  (row.get("le"), row.get("regs"), row.get("setup_slack")))

    csv = ROOT / "results" / "seed_sweep.csv"
    cols = ["config", "seed", "le", "comb", "regs", "mem", "setup_slack", "fmax"]
    lines = [",".join(cols)]
    lines += [",".join("" if r.get(c) is None else str(r.get(c)) for c in cols)
              for r in rows]
    csv.write_bytes("\n".join(lines).encode("utf-8"))
    print("[PASS] %d fit(s); summary in %s" % (len(rows), csv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
