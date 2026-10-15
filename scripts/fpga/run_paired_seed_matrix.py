"""Extend the verified four-seed FPGA matrix to ten COMMON seeds, twice.

Existing seeds 1..4 retain the provenance of the independent rfbht passes.
Seeds 5..10 are fitted sequentially in each new pass. Common board seed 2 is
refitted last in each pass, reproducing its existing evidence and leaving all
four shared databases at seed 2. No per-configuration best seed is selected.

    python scripts/fpga/run_paired_seed_matrix.py          # plan only
    python scripts/fpga/run_paired_seed_matrix.py --run    # start measurements
    python scripts/fpga/run_paired_seed_matrix.py --run --resume

Resume is an explicit action after inspecting the interrupted run; it never
overwrites an already recorded measurement or resumes with changed inputs.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from board_common import ROOT, POINTS, sha, stamp, manifest, validate_pair, check_idle, free_mb, checked_tool

SEEDS = tuple(range(1, 11))
BOARD_SEED = 2


def write_json(path, value):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n", encoding="ascii")
    temp.replace(path)


def load_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    result = {(r["point"].split("@")[0], int(r["seed"])): r for r in rows}
    if not rows or len(rows) != len(result):
        raise RuntimeError(f"Empty or duplicate point/seed rows: {path}")
    return result


def write_csv(path, rows, cols):
    temp = path.with_suffix(".tmp")
    with temp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows[k] for k in sorted(rows))
    temp.replace(path)


def check_seed_report(point, seed, dest):
    rev = "point_" + point
    text = (dest / f"{rev}.fit.rpt").read_text(encoding="utf-8", errors="replace")
    match = re.search(r"Fitter Initial Placement Seed\s*;\s*(\d+)", text)
    if not match or int(match[1]) != seed:
        raise RuntimeError(f"Fitter report has wrong seed: {point}, expected {seed}")
    if "EP4CE115F29C7" not in text:
        raise RuntimeError(f"Wrong FPGA device: {point}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--tag", default="paired10_6c4ccffd_20261009")
    args = ap.parse_args()
    if not re.fullmatch(r"[a-z0-9_]+", args.tag):
        ap.error("tag must contain only lower-case ASCII letters, digits and underscores")
    res = ROOT / "results"
    m = manifest()
    if m["aggregate"][:8] != "6c4ccffd":
        raise RuntimeError("This extension is for frozen RTL 6c4ccffd")
    source = [res / f"fpga_points_rfbht_p{n}.csv" for n in (1, 2)]
    verified = validate_pair(*source, ["point", "seed"])
    expected_keys = {(p, s) for p in POINTS for s in range(1, 5)}
    baseline = [load_csv(p) for p in source]
    if any(set(rows) != expected_keys for rows in baseline) or len(verified) != 16:
        raise RuntimeError("Existing four-point, four-seed matrix is incomplete")
    spec = importlib.util.spec_from_file_location("paired_fit_driver", ROOT / "scripts/run_fpga_points.py")
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)
    driver.run = checked_tool
    for rows in baseline:
        for row in rows.values():
            if set(row) != set(driver.COLS) or any(row[c] == "" for c in driver.COLS if c != "seconds"):
                raise RuntimeError("Incomplete existing measurement schema")
    inputs = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p)
              for p in (ROOT / "quartus").rglob("*") if p.is_file()}
    inputs.update({str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in
                   source + [ROOT / "scripts/run_fpga_points.py", Path(__file__),
                             ROOT / "scripts/fpga/board_common.py", res / "rtl_manifest.json"]})
    plan = {"rtl_id": m["aggregate"], "seeds": list(SEEDS), "board_seed": BOARD_SEED,
            "points": POINTS, "comparison": "paired_by_common_seed; no per-point best-seed selection",
            "reused_independent_passes": [str(p.relative_to(ROOT)) for p in source],
            "additional_fits": 56, "inputs": inputs}
    plan_path = res / f"{args.tag}_plan.json"
    if plan_path.exists():
        if json.loads(plan_path.read_text()) != plan:
            raise RuntimeError("Recorded plan differs; inspect before continuing")
    else:
        write_json(plan_path, plan)
    print("[PLAN] 4 configurations x SAME seeds 1..10 x 2 independent passes", flush=True)
    print("[PLAN] preserve 1..4 provenance; fit 5..10 and common seed 2 last: 56 additional fits", flush=True)
    if not args.run:
        return 0
    check_idle()
    outputs = [res / f"fpga_points_{args.tag}_p{n}.csv" for n in (1, 2)]
    progress_path = res / f"{args.tag}_progress.json"
    if progress_path.exists():
        if not args.resume:
            raise RuntimeError("Progress exists; inspect before explicitly using --resume")
        progress = json.loads(progress_path.read_text())
        tables = [load_csv(p) for p in outputs]
    else:
        if args.resume or any(p.exists() for p in outputs):
            raise RuntimeError("Inconsistent starting state; inspect outputs")
        tables = baseline
        for out, table in zip(outputs, tables):
            write_csv(out, table, driver.COLS)
        progress = {"status": "IN_PROGRESS", "started": stamp(), "done": {}, "row_origins": {}}
        for n, rows in enumerate(tables, 1):
            for point, seed in rows:
                progress["row_origins"][f"p{n}/{point}/s{seed}"] = {
                    "kind": "existing_independent_measurement", "source_csv": str(source[n-1].relative_to(ROOT)),
                    "reports": f"results/fpga_points/rfbht_p{n}/{point}/s{seed}"}
        write_json(progress_path, progress)
    lock = res / ".lock_paired_seed_matrix"
    with lock.open("x", encoding="ascii") as f:
        f.write(f"pid={os.getpid()} tag={args.tag}\n")
    try:
        for pass_no, out in enumerate(outputs, 1):
            for seed in (*range(5, 11), BOARD_SEED):
                for point in POINTS:
                    job_key = f"p{pass_no}/{point}/s{seed}"
                    dest = res / f"fpga_points/{args.tag}_p{pass_no}/{point}/s{seed}"
                    if job_key in progress["done"]:
                        for rel, digest in progress["done"][job_key]["reports"].items():
                            if sha(ROOT / rel) != digest:
                                raise RuntimeError(f"Recorded report changed: {rel}")
                        continue
                    if (res / ".abort_fpga_sweep").exists():
                        progress["status"] = "ABORTED_BETWEEN_FITS"
                        write_json(progress_path, progress)
                        return 3
                    if any(sha(ROOT / p) != digest for p, digest in inputs.items()):
                        raise RuntimeError("Frozen inputs changed since the plan")
                    if manifest()["aggregate"] != m["aggregate"]:
                        raise RuntimeError("RTL manifest changed")
                    check_idle()
                    available = free_mb()
                    if available < 6000:
                        raise RuntimeError(f"Only {available} MB free; owner scheduling decision required")
                    print(f"[START] {job_key}; Windows free {available} MB", flush=True)
                    one_csv = res / f"{args.tag}_measurements/{job_key.replace('/', '_')}.csv"
                    one_csv.parent.mkdir(parents=True, exist_ok=True)
                    if one_csv.exists():
                        raise RuntimeError(f"Unrecorded measurement exists: {one_csv}; inspect before retry")
                    sys.argv = ["run_fpga_points.py", "--points", point, "--seed", str(seed),
                                "--tag", f"{args.tag}_p{pass_no}", "--out", str(one_csv.relative_to(ROOT))]
                    if driver.main() != 0:
                        raise RuntimeError(f"Fit failed: {job_key}")
                    check_seed_report(point, seed, dest)
                    row = load_csv(one_csv)[point, seed]
                    if seed == BOARD_SEED:
                        reference = baseline[pass_no - 1][point, seed]
                        diff = [c for c in driver.COLS if c != "seconds" and row[c] != reference[c]]
                        if diff:
                            raise RuntimeError(f"Board seed refit differs from verified evidence: {job_key}: {diff}")
                    if any(sha(ROOT / p) != digest for p, digest in inputs.items()):
                        raise RuntimeError("Frozen inputs changed during the measurement")
                    reports = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p)
                               for p in dest.iterdir() if p.is_file()}
                    tables[pass_no - 1][point, seed] = row
                    write_csv(out, tables[pass_no - 1], driver.COLS)
                    progress["done"][job_key] = {"completed": stamp(), "reports": reports,
                                                 "measurement_sha256": sha(one_csv)}
                    progress["row_origins"][job_key] = {"kind": "new_independent_measurement",
                        "source_csv": str(one_csv.relative_to(ROOT)), "reports": str(dest.relative_to(ROOT))}
                    write_json(progress_path, progress)
                    print(f"[DONE] {job_key}; {len(progress['done'])}/56 new fits", flush=True)
        pair = validate_pair(*outputs, ["point", "seed"])
        if len(pair) != 40:
            raise RuntimeError("Ten-seed matrix must contain 40 paired rows")
        for pass_no, out in enumerate(outputs, 1):
            subprocess.run([sys.executable, "scripts/fpga_seed_summary.py", str(out.relative_to(ROOT)),
                            "--seeds", ",".join(map(str, SEEDS)), "--points", ",".join(POINTS),
                            "--out", f"results/fpga_seed_summary_{args.tag}_p{pass_no}.md"], cwd=ROOT, check=True)
        board_reports = {}
        for point in POINTS:
            rev = "point_" + point
            current = ROOT / f"output_files_{point}"
            check_seed_report(point, BOARD_SEED, current)
            for ext in ("map.rpt", "fit.rpt", "sta.rpt", "fit.summary"):
                p = current / f"{rev}.{ext}"
                board_reports[str(p.relative_to(ROOT))] = sha(p)
            board_reports[f"{rev}.qsf"] = sha(ROOT / f"{rev}.qsf")
        write_json(res / f"{args.tag}_board_fit_receipt.json", {
            "created": stamp(), "rtl_id": m["aggregate"], "common_seed": BOARD_SEED,
            "fit_p1": str(outputs[0].relative_to(ROOT)), "fit_p2": str(outputs[1].relative_to(ROOT)),
            "reports": board_reports, "settings": inputs,
            "points": {p: {"config": POINTS[p], "seed": BOARD_SEED,
                            "reference": tables[1][p, BOARD_SEED]} for p in POINTS}})
        progress["status"] = "VERIFIED_40_PAIRED_ROWS"
        progress["completed"] = stamp()
        write_json(progress_path, progress)
        print("[VERIFIED] 40/40 rows identical; four board databases hold common seed 2", flush=True)
        return 0
    except BaseException as exc:
        progress["status"] = "STOPPED_REQUIRES_INSPECTION"
        progress["error"] = str(exc)
        write_json(progress_path, progress)
        raise
    finally:
        lock.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
