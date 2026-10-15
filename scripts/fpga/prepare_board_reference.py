"""Regenerate the 100 current-RTL board reference rows twice, with private Questa libraries.

Two configurations run concurrently; fits remain sequential in their separate
driver. Firmware and RTL are unchanged. No FAST_HIT or FAST_UART build is used.
The complete counter frame must match both its independent pass and R14.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from board_common import ROOT, UP, sha, stamp, manifest, free_mb, validate_pair

CONFIGS = {0: "DM", 1: "SA2", 2: "DM_VC4", 3: "DM_DSE"}
V = r"C:\questasim64_2024.1\win64\vsim.exe"


def load(path):
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    data = {(r["kernel"], r["config"]): r for r in rows}
    if not rows or len(data) != len(rows):
        raise RuntimeError(f"Empty or duplicate benchmark rows: {path}")
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--resume", action="store_true", help="Continue after read-only inspection of an interrupted job")
    ap.add_argument("--tag", default="board_reference_6c4ccffd_20261009")
    args = ap.parse_args()
    if not re.fullmatch(r"[a-z0-9_]+", args.tag):
        ap.error("Use a lower-case ASCII content/date tag")
    m = manifest()
    kernels = [("ramsweep", "fw")] + [("up_" + k, "fw") for k in UP] + [("upfull_" + k, "fw_board") for k in UP]
    baseline = {}
    old_paths = [ROOT / f"results/{name}" for name in
                 ("upstream_r14_4kb_p1.csv", "ramsweep_r14_p1.csv", "upfull_r14_4kb_p1.csv")]
    for p in old_paths:
        for key, row in load(p).items():
            if key in baseline:
                raise RuntimeError(f"Duplicate R14 reference: {key}")
            baseline[key] = row
    expected = {(k, cfg) for k, _ in kernels for cfg in CONFIGS.values()}
    if set(baseline) != expected:
        raise RuntimeError("R14 reference must contain exactly 100 board kernel/configuration rows")
    firmware = {f"{d}/{k}.hex": sha(ROOT / f"{d}/{k}.hex") for k, d in kernels}
    inputs = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in
              old_paths + [ROOT / "tb/compile_active_design.do", ROOT / "scripts/run_ablation.py",
                           ROOT / "scripts/snapshot_fields.py", ROOT / "results/rtl_manifest.json"]}
    print("[PLAN] current RTL: 25 firmware images x 4 configurations x 2 independent simulations", flush=True)
    if not args.run:
        return 0
    if free_mb() < 6000:
        raise RuntimeError("Less than 6 GB Windows memory free; owner scheduling decision required")
    outdir = ROOT / f"results/{args.tag}"
    outputs = [ROOT / f"results/{args.tag}_p{p}.csv" for p in (1, 2)]
    meta_path = ROOT / f"results/{args.tag}_inputs.json"
    continuation = ""
    if args.resume:
        if not outdir.is_dir() or not meta_path.is_file():
            raise RuntimeError("No interrupted reference metadata; inspect before continuing")
        metadata = json.loads(meta_path.read_text())
        if metadata["status"].startswith("VERIFIED_") or metadata["rtl_id"] != m["aggregate"]:
            raise RuntimeError("Reference already verified or RTL differs; no re-execution")
        if metadata["firmware"] != firmware or metadata["inputs"] != inputs:
            raise RuntimeError("Interrupted reference inputs differ; preserve evidence and inspect")
        continuation = "_continued_" + re.sub(r"[^0-9]", "", stamp())[:14]
        metadata.setdefault("continuations", []).append({"started": stamp(),
            "driver_sha256": sha(Path(__file__)), "suffix": continuation,
            "method": "keep verified complete cases; fresh compile and full simulation for unfinished cases"})
        metadata["status"] = "IN_PROGRESS"
        metadata.pop("error", None)
    else:
        outdir.mkdir(exist_ok=False)
        if any(p.exists() for p in outputs):
            raise RuntimeError("Reference CSV already exists; inspect it; no overwrite")
        metadata = {"status": "IN_PROGRESS", "started": stamp(), "rtl_id": m["aggregate"],
                    "firmware": firmware, "inputs": inputs, "libraries": [], "expected_rows_per_pass": 100,
                    "driver_sha256": sha(Path(__file__))}

    def write_metadata():
        temp = meta_path.with_suffix(".tmp")
        temp.write_text(json.dumps(metadata, indent=2) + "\n", encoding="ascii")
        temp.replace(meta_path)

    write_metadata()
    failed = threading.Event()
    lock = threading.Lock()

    def check_inputs():
        if manifest()["aggregate"] != m["aggregate"]:
            raise RuntimeError("RTL revision changed")
        if any(sha(ROOT / p) != h for p, h in {**inputs, **firmware}.items()):
            raise RuntimeError("Frozen reference inputs changed")

    def lane(cfg, pass_no):
        if failed.is_set():
            raise RuntimeError("Reference stopped before the next lane")
        results = {}
        case_records = {}
        if args.resume:
            for one in sorted(outdir.glob(f"p{pass_no}_c{cfg}_*.csv")):
                actual = load(one)
                if len(actual) != 1:
                    raise RuntimeError(f"Interrupted case CSV has multiple rows: {one}")
                key, row = next(iter(actual.items()))
                if key not in expected or key[1] != CONFIGS[cfg] or row != baseline[key] or key in results:
                    raise RuntimeError(f"Invalid, changed or duplicate completed reference: {one}")
                rel = one.relative_to(ROOT).as_posix()
                digest = sha(one)
                if rel in metadata.get("case_artifacts", {}) and metadata["case_artifacts"][rel] != digest:
                    raise RuntimeError(f"Recorded completed reference changed: {one}")
                results.update(actual)
                case_records[rel] = digest
            with lock:
                metadata.setdefault("case_artifacts", {}).update(case_records)
                write_metadata()
                print(f"[KEEP] p{pass_no} {CONFIGS[cfg]}: {len(results)} complete cases verified", flush=True)
            if len(results) == len(kernels):
                return results, None
        library = f"work_{args.tag}_p{pass_no}_c{cfg}{continuation}"
        if (ROOT / library).exists():
            failed.set()
            raise RuntimeError(f"Private library already exists; preserve it and inspect: {library}")
        if free_mb() < 6000:
            failed.set()
            raise RuntimeError("Less than 6 GB free before the next simulation lane; owner scheduling required")
        check_inputs()
        script = outdir / f"compile_p{pass_no}_c{cfg}{continuation}.do"
        text = (ROOT / "tb/compile_active_design.do").read_text()
        text = re.sub(r"\bwork\b", library, text).replace("vlog -sv", f"vlog -work {library} -sv")
        script.write_text(text, encoding="ascii")
        compile_log = outdir / f"compile_p{pass_no}_c{cfg}{continuation}.log"
        with compile_log.open("wb") as f:
            p = subprocess.run([V, "-c", "-do", f"do {script.relative_to(ROOT).as_posix()}; quit -f"],
                               cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, timeout=7200)
        compiled = compile_log.read_text(encoding="utf-8", errors="replace")
        if p.returncode or "[PASS]" not in compiled or re.search(r"\*\*\s+(Fatal|Error):", compiled):
            failed.set()
            raise RuntimeError(f"Private library compilation failed: {compile_log}")
        with lock:
            metadata.setdefault("compile_artifacts", {}).update({p.relative_to(ROOT).as_posix(): sha(p)
                                                                 for p in (script, compile_log)})
            write_metadata()
        for kernel, fw_dir in kernels:
            key = kernel, CONFIGS[cfg]
            if key in results:
                continue
            if failed.is_set() or (ROOT / "results/.abort_board_reference").exists():
                raise RuntimeError("Reference stopped between simulations")
            check_inputs()
            one = outdir / f"p{pass_no}_c{cfg}_{kernel}{continuation}.csv"
            log = outdir / f"p{pass_no}_c{cfg}_{kernel}{continuation}.stdout"
            if one.exists() or log.exists():
                raise RuntimeError(f"Case artifacts already exist; no overwrite: {one}")
            cmd = [sys.executable, "scripts/run_ablation.py", "--lib", library, "--configs", str(cfg),
                   "--lines", "256", "--kernels", kernel, "--fw-dir", fw_dir, "--max-cycles", "60000000",
                   "--out", str(one.relative_to(ROOT))]
            with log.open("wb") as f:
                p = subprocess.run(cmd, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
            if p.returncode:
                failed.set()
                raise RuntimeError(f"Reference simulation failed: {log}")
            actual = load(one)
            if set(actual) != {key} or actual[key] != baseline[key]:
                failed.set()
                raise RuntimeError(f"Current RTL differs from R14 reference: {key}; {one}")
            results.update(actual)
            with lock:
                metadata.setdefault("case_artifacts", {}).update({one.relative_to(ROOT).as_posix(): sha(one)})
                write_metadata()
                print(f"[MATCH] p{pass_no} {kernel}/{CONFIGS[cfg]}: full counter frame = R14", flush=True)
        return results, library

    def guarded_lane(cfg, pass_no):
        try:
            return lane(cfg, pass_no)
        except BaseException:
            failed.set()
            raise

    try:
        for pass_no, out in enumerate(outputs, 1):
            check_inputs()
            all_rows = {}
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(guarded_lane, cfg, pass_no) for cfg in CONFIGS]
                for future in futures:
                    rows, library = future.result()
                    all_rows.update(rows)
                    if library is not None:
                        with lock:
                            metadata["libraries"].append(library)
                            write_metadata()
            check_inputs()
            if set(all_rows) != expected:
                raise RuntimeError("Incomplete reference pass")
            if out.exists():
                if not args.resume or load(out) != all_rows:
                    raise RuntimeError(f"Existing aggregate reference differs: {out}")
            else:
                with out.open("w", newline="", encoding="ascii") as f:
                    writer = csv.DictWriter(f, fieldnames=list(next(iter(all_rows.values()))))
                    writer.writeheader()
                    writer.writerows(all_rows[k] for k in sorted(all_rows))
            print(f"[PASS] reference pass {pass_no}: 100 rows", flush=True)
        validate_pair(*outputs, ["kernel", "config"], ignore=())
        metadata["status"] = "VERIFIED_100_PAIRED_ROWS_EQUAL_R14"
        metadata["completed"] = stamp()
        metadata["outputs"] = {str(p.relative_to(ROOT)): sha(p) for p in outputs}
        print("[VERIFIED] 100 reference rows, independently simulated twice, identical to R14", flush=True)
    except BaseException as exc:
        failed.set()
        metadata["status"] = "STOPPED_REQUIRES_INSPECTION"
        metadata["error"] = str(exc)
        raise
    finally:
        write_metadata()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
