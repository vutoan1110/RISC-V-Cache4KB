"""Complete the inspected common-seed FPGA matrix and prepare board images.

The stopped 51-fit experiment and its receipts remain immutable. Only its five
unfinished measurements are run, serially, under a new descriptive tag. Existing
fit functions and the board builder remain unchanged. No board is programmed and
maintained project documents are not edited.

    python scripts/fpga/continue_common_seed_preparation.py --prepare
    python scripts/fpga/continue_common_seed_preparation.py --run

Default mode performs read-only validation. A prepared plan pins the original
evidence, current helper sources, RTL and canonical MIFs. Resuming this new driver
requires --resume; orphaned locks or unrecorded measurements require inspection.
"""
from __future__ import annotations

import argparse
import copy
import csv
import importlib.util
import json
import os
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

from board_common import ROOT, POINTS, MIFS, sha, stamp, manifest, validate_pair, check_idle, free_mb, checked_tool
from run_paired_seed_matrix import load_csv, write_csv, write_json, check_seed_report
import build_board_matrix as builder
import complete_board_preparation as completion

SOURCE_TAG = "paired10_6c4ccffd_20261009"
REFERENCE_TAG = "board_reference_6c4ccffd_20261009"
DEFAULT_TAG = "fpga_common_seeds_continued_20261009"
DEFAULT_OUT = "output_files_board_matrix_6c4ccffd_seed2"
RTL_ID = "6c4ccffd4257c224a537bd8d8e7b724ac8505bb19eb4d9e1361019af77341291"
MIN_FREE_MB = 6000
REPORT_SUFFIXES = ("map.rpt", "fit.rpt", "sta.rpt", "pow.rpt", "fit.summary", "map.summary", "sta.summary", "qsf")


def relative(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def inside(rel):
    path = (ROOT / str(rel).replace("\\", "/")).resolve()
    if not path.is_relative_to(ROOT) or path == ROOT:
        raise RuntimeError(f"Evidence path leaves the research repository: {rel}")
    return path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def verify_hashes(files):
    for rel, digest in files.items():
        if sha(inside(rel)) != digest:
            raise RuntimeError(f"Frozen evidence changed: {rel}")


def jobs():
    return [f"p{n}/{p}/s{s}" for n in (1, 2) for s in (*range(5, 11), 2) for p in POINTS]


def parse_job(key):
    n, p, s = key.split("/")
    return int(n[1:]), p, int(s[1:])


def fitter():
    spec = importlib.util.spec_from_file_location("common_seed_fitter", ROOT / "scripts/run_fpga_points.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.run = checked_tool
    return module


def check_row(row, point, seed, cols):
    if set(row) != set(cols) or any(row[c] in ("", None) for c in cols if c != "seconds"):
        raise RuntimeError(f"Incomplete measurement schema: {point}/s{seed}")
    expected = point if seed == 2 else f"{point}@s{seed}"
    if row["point"] != expected or int(row["seed"]) != seed:
        raise RuntimeError(f"Incorrect measurement identity: {point}/s{seed}")
    if int(row["cache_config"]) != list(POINTS).index(point) or int(row["capacity_bytes"]) != 4096:
        raise RuntimeError(f"Incorrect cache configuration: {point}/s{seed}")
    if int(row["line_bytes"]) != 16 or int(row["lines"]) != 256 or int(row["l0"]) != 8:
        raise RuntimeError(f"Incorrect cache geometry: {point}/s{seed}")


def same_row(a, b, label, ignore=()):
    if a.keys() != b.keys():
        raise RuntimeError(f"Different field sets: {label}")
    diff = [c for c in a if c not in ignore and str(a[c]) != str(b[c])]
    if diff:
        raise RuntimeError(f"Measurement differs: {label}: {diff}")


def check_reports(point, seed, dest):
    check_seed_report(point, seed, dest)
    rev = "point_" + point
    if any(not (dest / f"{rev}.{suffix}").is_file() for suffix in REPORT_SUFFIXES):
        raise RuntimeError(f"Incomplete archived report set: {dest}")
    qsf = (dest / f"{rev}.qsf").read_text(encoding="utf-8")
    for parameter, value in (("CACHE_CONFIG", list(POINTS).index(point)),
                             ("ICACHE_LINE_COUNT", 256), ("DCACHE_LINE_COUNT", 256),
                             ("CACHE_LINE_WORDS", 4), ("BHT_ENTRIES", 256), ("L0_ENTRIES", 8)):
        if not re.search(rf"^set_parameter -name {parameter} {value}\s*$", qsf, re.M):
            raise RuntimeError(f"Archived settings differ: {point}/s{seed}: {parameter}")


def validate_progress(progress, tables, baseline, cols):
    order = jobs()
    done = progress["done"]
    if set(done) != set(order[:len(done)]):
        raise RuntimeError("Recorded fits are not the ordered prefix of the approved 56-fit schedule")
    origins = progress["row_origins"]
    evidence = {}
    for n, table in enumerate(tables, 1):
        expected = set(baseline[n - 1]) | {(p, s) for key in done for pn, p, s in [parse_job(key)] if pn == n}
        if set(table) != expected:
            raise RuntimeError(f"Aggregate CSV contains missing or unrecorded measurements: pass {n}")
        for (point, seed), row in table.items():
            key = f"p{n}/{point}/s{seed}"
            check_row(row, point, seed, cols)
            origin = origins.get(key, {})
            csv_path = inside(origin["source_csv"])
            source_rows = load_csv(csv_path)
            source_row = source_rows[point, seed]
            same_row(row, source_row, key)
            dest = inside(origin["reports"])
            check_reports(point, seed, dest)
            if key in done:
                if origin["kind"] != "new_independent_measurement" or len(source_rows) != 1:
                    raise RuntimeError(f"Incorrect completed-fit provenance: {key}")
                if sha(csv_path) != done[key]["measurement_sha256"]:
                    raise RuntimeError(f"Completed measurement hash differs: {key}")
                reports = done[key]["reports"]
                required = {relative(dest / f"point_{point}.{s}") for s in REPORT_SUFFIXES}
                if not required.issubset({r.replace("\\", "/") for r in reports}):
                    raise RuntimeError(f"Recorded report hashes are incomplete: {key}")
                if any(inside(r).parent != dest for r in reports):
                    raise RuntimeError(f"Recorded reports belong to another fit: {key}")
                verify_hashes(reports)
            else:
                if origin["kind"] != "existing_independent_measurement":
                    raise RuntimeError(f"Incorrect reused-fit provenance: {key}")
                same_row(row, baseline[n - 1][point, seed], key)
                reports = {relative(p): sha(p) for p in dest.iterdir() if p.is_file()}
            evidence.update({relative(csv_path): sha(csv_path), **reports})
    if set(origins) != {f"p{n}/{p}/s{s}" for n, table in enumerate(tables, 1) for p, s in table}:
        raise RuntimeError("Row provenance does not exactly cover the retained aggregate tables")
    return evidence


def verify_reference():
    path = ROOT / f"results/{REFERENCE_TAG}_inputs.json"
    meta = read_json(path)
    if meta["rtl_id"] != RTL_ID or meta["status"] != "VERIFIED_100_PAIRED_ROWS_EQUAL_R14":
        raise RuntimeError("The current-RTL board reference is not independently verified")
    evidence = {relative(path): sha(path)}
    for group in ("inputs", "outputs", "firmware"):
        verify_hashes(meta[group])
        evidence.update(meta[group])
    reference = validate_pair(ROOT / f"results/{REFERENCE_TAG}_p1.csv",
                              ROOT / f"results/{REFERENCE_TAG}_p2.csv", ["kernel", "config"], ignore=())
    if len(reference) != 100:
        raise RuntimeError("Require exactly 100 verified paired board reference cases")
    return meta, reference, evidence


def inspect_source(driver):
    res = ROOT / "results"
    plan_path = res / f"{SOURCE_TAG}_plan.json"
    progress_path = res / f"{SOURCE_TAG}_progress.json"
    old_plan, old = read_json(plan_path), read_json(progress_path)
    if old_plan["rtl_id"] != RTL_ID or old_plan["seeds"] != list(range(1, 11)) or old_plan["board_seed"] != 2:
        raise RuntimeError("The original plan has another revision or seed policy")
    if old_plan["points"] != POINTS or len(old_plan["inputs"]) != 32:
        raise RuntimeError("The original 32-input plan differs from the inspected experiment")
    if old["status"] != "STOPPED_REQUIRES_INSPECTION" or len(old["done"]) != 51:
        raise RuntimeError("Require the preserved stopped 51-fit experiment")
    if old["error"] != "Only 5384 MB free; owner scheduling decision required":
        raise RuntimeError("The original stop reason differs from the inspected memory guard")
    verify_hashes(old_plan["inputs"])
    if manifest()["aggregate"] != RTL_ID:
        raise RuntimeError("Current RTL differs from the approved frozen revision")
    bases = [res / f"fpga_points_rfbht_p{n}.csv" for n in (1, 2)]
    if len(validate_pair(*bases, ["point", "seed"])) != 16:
        raise RuntimeError("The independently measured four-seed baseline is incomplete")
    baseline = [load_csv(p) for p in bases]
    if any(set(t) != {(p, s) for p in POINTS for s in range(1, 5)} for t in baseline):
        raise RuntimeError("Incorrect four-seed baseline configuration/seed set")
    outputs = [res / f"fpga_points_{SOURCE_TAG}_p{n}.csv" for n in (1, 2)]
    tables = [load_csv(p) for p in outputs]
    evidence = validate_progress(old, tables, baseline, driver.COLS)
    for p in (plan_path, progress_path, *outputs, res / "board_preparation_6c4ccffd_seed2_20261009.json"):
        evidence[relative(p)] = sha(p)
    meta, reference, ref_hashes = verify_reference()
    evidence.update(ref_hashes)
    return old_plan, old, baseline, tables, evidence, meta, reference


def snapshot(driver, tag, out):
    original, old, baseline, tables, evidence, meta, reference = inspect_source(driver)
    pins = [Path(__file__), ROOT / "scripts/fpga/run_paired_seed_matrix.py",
            ROOT / "scripts/run_fpga_points.py", ROOT / "scripts/fpga/board_common.py",
            ROOT / "scripts/fpga/build_board_matrix.py", ROOT / "scripts/fpga/complete_board_preparation.py",
            ROOT / "scripts/fpga_seed_summary.py", ROOT / "scripts/rtl_manifest.py"]
    plan = {"rtl_id": RTL_ID, "common_seed": 2, "seeds": list(range(1, 11)), "tag": tag,
        "source_tag": SOURCE_TAG, "reference_tag": REFERENCE_TAG, "board_output": relative(out),
        "completed_preserved": 51, "remaining": jobs()[51:], "memory_guard_mb": MIN_FREE_MB,
        "comparison": "all hardware fields; wall-clock seconds excluded; configurations paired within common seed",
        "original_inputs": original["inputs"], "preserved_evidence": evidence,
        "continuation_sources": {relative(p): sha(p) for p in pins},
        "canonical_mifs": {relative(p): sha(p) for p in MIFS}}
    return plan, old, baseline, tables, meta, reference


def verify_plan(plan, check_mifs=True):
    for group in ("original_inputs", "preserved_evidence", "continuation_sources"):
        verify_hashes(plan[group])
    if check_mifs:
        verify_hashes(plan["canonical_mifs"])
    if manifest()["aggregate"] != plan["rtl_id"] or plan["memory_guard_mb"] != MIN_FREE_MB:
        raise RuntimeError("RTL or the mandatory 6000-MB resource guard changed")


def wait_for_memory(progress, path, interval=30):
    while True:
        if (ROOT / "results/.abort_fpga_sweep").exists() or (ROOT / "results/.abort_board_completion").exists():
            raise RuntimeError("Cooperative abort requested between measurements; running tools are not killed")
        check_idle()
        available = free_mb()
        if available >= MIN_FREE_MB:
            return available
        progress["status"] = "WAITING_FOR_MEMORY"
        progress["available_mb"] = available
        write_json(path, progress)
        print(f"[WAIT] Windows free {available} MB < {MIN_FREE_MB} MB; no tool started", flush=True)
        time.sleep(interval)


def publish_artifacts(tag, plan, tables, outputs, progress, progress_path, meta, reference):
    verify_plan(plan)
    pair = validate_pair(*outputs, ["point", "seed"])
    if len(pair) != 40:
        raise RuntimeError("Require exactly 40 independently measured paired rows")
    board_reports = {}
    for point in POINTS:
        rev = "point_" + point
        current = ROOT / f"output_files_{point}"
        check_seed_report(point, 2, current)
        for ext in ("map.rpt", "fit.rpt", "sta.rpt", "fit.summary"):
            p = current / f"{rev}.{ext}"
            board_reports[relative(p)] = sha(p)
        board_reports[f"{rev}.qsf"] = sha(ROOT / f"{rev}.qsf")
    receipt = {"created": stamp(), "rtl_id": RTL_ID, "common_seed": 2,
        "fit_p1": relative(outputs[0]), "fit_p2": relative(outputs[1]), "reports": board_reports,
        "settings": {**plan["original_inputs"], **plan["continuation_sources"], **plan["canonical_mifs"]},
        "continuation_plan": f"results/{tag}_plan.json", "row_provenance": f"results/{tag}_progress.json",
        "points": {p: {"config": POINTS[p], "seed": 2, "reference": tables[1][p, 2]} for p in POINTS}}
    builder.validate_matrix(receipt, meta, pair, reference)
    receipt_path = ROOT / f"results/{tag}_board_fit_receipt.json"
    write_json(receipt_path, receipt)
    for n, out in enumerate(outputs, 1):
        subprocess.run([sys.executable, "scripts/fpga_seed_summary.py", relative(out),
            "--seeds", ",".join(map(str, range(1, 11))), "--points", ",".join(POINTS),
            "--out", f"results/fpga_seed_summary_{tag}_p{n}.md"], cwd=ROOT, check=True)
    stats = {}
    for p, cfg in POINTS.items():
        rows = [tables[0][p, s] for s in range(1, 11)]
        stats[p] = {"config": cfg, "seed2": tables[1][p, 2], "metrics": {}}
        for field in ("le", "fmax_s85", "fmax_restricted_s85", "pow_total_mw", "pow_core_dyn_mw", "pow_core_static_mw"):
            values = [float(r[field]) for r in rows]
            stats[p]["metrics"][field] = {"min": min(values), "max": max(values),
                "mean": statistics.mean(values), "sample_sd": statistics.stdev(values)}
    ppa = {"rtl_id": RTL_ID, "seeds": list(range(1, 11)), "paired_rows": 40,
        "passes": 2, "board_common_seed": 2, "statistics": stats,
        "power_method": "Quartus default toggle-rate estimate", "timing_corner": "Slow 1200 mV 85 C",
        "physical_status": "NOT_RUN", "sources": {relative(p): sha(p) for p in outputs}}
    write_json(ROOT / f"results/{tag}_ppa.json", ppa)
    lines = ["# FPGA: ten common seeds, independently measured twice", "",
        "RTL function: RAM 16 KiB, FPGA register file/BHT in M9K, unchanged benchmark cycles.", "",
        "Gate: 40/40 paired point/seed rows match every hardware field (runtime excluded).",
        "All configurations use seeds 1..10. Board seed 2 was fixed before the expanded results.",
        "Seeds 1, 3 and 4 reuse the independent rfbht passes; seeds 5..10 and seed 2 were refitted twice.", "",
        "Timing corner: Slow 1200 mV 85 C. Power: Quartus default toggle-rate estimate.",
        "Power is an estimate, not a board measurement. Physical board status: NOT_RUN.", "",
        "| configuration | LE mean [min, max], SD | Fmax mean [min, max], SD (MHz) | total power mean [min, max], SD (mW) |",
        "|---|---|---|---|"]
    for p, cfg in POINTS.items():
        cells = []
        for field in ("le", "fmax_s85", "pow_total_mw"):
            d = stats[p]["metrics"][field]
            cells.append(f"{d['mean']:.2f} [{d['min']:g}, {d['max']:g}], {d['sample_sd']:.2f}")
        lines.append(f"| {cfg} | " + " | ".join(cells) + " |")
    lines += ["", f"Full fields and within-seed differences: `fpga_seed_summary_{tag}_p1.md` and `_p2.md`.",
        f"Measurement origins: `{tag}_progress.json`. Frozen evidence and sources: `{tag}_plan.json`.", ""]
    (ROOT / f"results/{tag}_ppa.md").write_text("\n".join(lines), encoding="ascii")
    progress["status"] = "VERIFIED_40_PAIRED_ROWS"
    progress["fits_completed"] = stamp()
    write_json(progress_path, progress)
    return receipt_path


def run(args, driver, plan, old, baseline, tables, meta, reference):
    res = ROOT / "results"
    path = res / f"{args.tag}_progress.json"
    outputs = [res / f"fpga_points_{args.tag}_p{n}.csv" for n in (1, 2)]
    lock = res / ".lock_paired_seed_matrix"
    check_idle()
    if lock.exists():
        raise RuntimeError("Existing Quartus sweep lock retained; inspect its process and archive before removal")
    if path.exists():
        if not args.resume:
            raise RuntimeError("Continuation progress exists; inspect it before explicitly using --resume")
        progress = read_json(path)
        tables = [load_csv(p) for p in outputs]
        if progress.get("plan_sha256") != sha(res / f"{args.tag}_plan.json"):
            raise RuntimeError("Continuation progress refers to another prepared plan")
        validate_progress(progress, tables, baseline, driver.COLS)
    else:
        if args.resume or any(p.exists() for p in outputs):
            raise RuntimeError("Inconsistent continuation starting state; preserve and inspect artifacts")
        progress = copy.deepcopy(old)
        progress.update({"status": "CONTINUING_INSPECTED_MEMORY_STOP", "started": stamp(),
            "original_source_tag": SOURCE_TAG, "source_completed_preserved": 51,
            "plan_sha256": sha(res / f"{args.tag}_plan.json"), "physical_status": "NOT_RUN"})
        progress.pop("error", None)
        for output, table in zip(outputs, tables):
            write_csv(output, table, driver.COLS)
        write_json(path, progress)
    with lock.open("x", encoding="ascii") as stream:
        stream.write(f"pid={os.getpid()} tag={args.tag}\n")
    try:
        for key in jobs():
            if key in progress["done"]:
                continue
            verify_plan(plan)
            available = wait_for_memory(progress, path)
            verify_plan(plan)
            n, point, seed = parse_job(key)
            one_csv = res / f"{args.tag}_measurements/{key.replace('/', '_')}.csv"
            dest = res / f"fpga_points/{args.tag}_p{n}/{point}/s{seed}"
            if one_csv.exists() or dest.exists():
                raise RuntimeError(f"Unrecorded fit evidence exists: {key}; preserve and inspect before retry")
            one_csv.parent.mkdir(parents=True, exist_ok=True)
            progress["status"] = "FITTING"
            progress["current_job"] = key
            progress["available_mb"] = available
            write_json(path, progress)
            print(f"[START] {key}; Windows free {available} MB; serial fit", flush=True)
            original_argv = sys.argv
            try:
                sys.argv = ["run_fpga_points.py", "--points", point, "--seed", str(seed),
                    "--tag", f"{args.tag}_p{n}", "--out", relative(one_csv)]
                if driver.main() != 0:
                    raise RuntimeError(f"Fit failed: {key}; no automatic deterministic retry")
            finally:
                sys.argv = original_argv
            check_reports(point, seed, dest)
            rows = load_csv(one_csv)
            if set(rows) != {(point, seed)}:
                raise RuntimeError(f"One-fit CSV contains the wrong measurement: {key}")
            row = rows[point, seed]
            check_row(row, point, seed, driver.COLS)
            if seed == 2:
                same_row(row, baseline[n - 1][point, seed], key, ignore=("seconds",))
            verify_plan(plan)
            tables[n - 1][point, seed] = row
            write_csv(outputs[n - 1], tables[n - 1], driver.COLS)
            progress["done"][key] = {"completed": stamp(), "measurement_sha256": sha(one_csv),
                "reports": {relative(p): sha(p) for p in dest.iterdir() if p.is_file()}}
            progress["row_origins"][key] = {"kind": "new_independent_measurement",
                "source_csv": relative(one_csv), "reports": relative(dest)}
            progress["status"] = "FIT_RECORDED"
            write_json(path, progress)
            print(f"[DONE] {key}; {len(progress['done'])}/56, including 51 preserved fits", flush=True)
        validate_progress(progress, tables, baseline, driver.COLS)
        verify_reference()
        receipt = publish_artifacts(args.tag, plan, tables, outputs, progress, path, meta, reference)
        if args.fits_only:
            return 0
        wait_for_memory(progress, path)
        verify_plan(plan)
        if inside(args.out).exists():
            raise RuntimeError("Board output already exists; preserve and audit it rather than rebuilding")
        progress["status"] = "BUILDING_BOARD_IMAGES"
        write_json(path, progress)
        checked_tool([sys.executable, "-u", "scripts/fpga/build_board_matrix.py", "--build",
            "--fit-receipt", relative(receipt), "--reference-tag", REFERENCE_TAG,
            "--out", args.out], res / f"{args.tag}_board_build.log", retries=1)
        completion.OUT = inside(args.out)
        completion.REF_TAG = REFERENCE_TAG
        audit = completion.audit_sofs()
        verify_plan(plan)
        write_json(res / f"{args.tag}_board_audit.json", {"created": stamp(), **audit})
        progress.update({"status": "READY_FOR_PHYSICAL_SESSION", "completed": stamp(),
            "board_output": args.out, "board_audit": audit, "physical_status": "NOT_RUN"})
        write_json(path, progress)
        print("[READY] 40 paired fits, 100 seed-2 SOFs, 200-row checklist; physical board NOT_RUN", flush=True)
        return 0
    except BaseException as exc:
        progress["status"] = "STOPPED_REQUIRES_INSPECTION"
        progress["error"] = str(exc)
        progress["stopped"] = stamp()
        write_json(path, progress)
        raise
    finally:
        lock.unlink()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    modes = ap.add_mutually_exclusive_group()
    modes.add_argument("--prepare", action="store_true", help="Freeze a new immutable continuation plan; run no tools")
    modes.add_argument("--run", action="store_true", help="Run only unfinished fits, then prepare and audit SOFs")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--fits-only", action="store_true", help="Finish verified PPA artifacts and defer SOF assembly")
    ap.add_argument("--tag", default=DEFAULT_TAG)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()
    if not re.fullmatch(r"[a-z0-9_]+", args.tag) or args.tag == SOURCE_TAG:
        ap.error("a new descriptive lower-case ASCII tag is required")
    if args.resume and not args.run:
        ap.error("--resume requires --run")
    os.chdir(ROOT)
    driver = fitter()
    plan, old, baseline, tables, meta, reference = snapshot(driver, args.tag, inside(args.out))
    plan_path = ROOT / f"results/{args.tag}_plan.json"
    if plan_path.exists():
        if read_json(plan_path) != plan:
            raise RuntimeError("Prepared continuation inputs or sources changed; preserve the plan and inspect")
    elif args.prepare:
        write_json(plan_path, plan)
    elif args.run:
        raise RuntimeError("An independently inspected --prepare plan is required before --run")
    print(f"[VALIDATED] 32 original inputs unchanged; 51 completed fit CSV/report sets verified; {len(reference)} paired reference cases", flush=True)
    print("[REMAINING] " + ", ".join(plan["remaining"]), flush=True)
    print(f"[MEMORY] Windows free {free_mb()} MB; mandatory guard {MIN_FREE_MB} MB retained", flush=True)
    if not args.run:
        return 0
    verify_plan(plan)
    subprocess.run([sys.executable, "scripts/rtl_manifest.py", "--check"], cwd=ROOT, check=True)
    return run(args, driver, plan, old, baseline, tables, meta, reference)


if __name__ == "__main__":
    raise SystemExit(main())
