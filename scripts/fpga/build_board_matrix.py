"""Assemble current-RTL board SOFs from four verified fits at COMMON seed 2.

No synthesis or fit is run. Both the ten-seed fit matrix and the 100-row
simulation reference must be verified first. Canonical MIFs are restored and
all four canonical SOFs reassembled in finally. Default mode checks readiness.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

from board_common import ROOT, POINTS, UP, MIFS, sha, stamp, manifest, validate_pair, check_idle, checked_tool


def validate_matrix(receipt, meta, fit_pair, reference):
    expected_fit = {(p if s == 2 else f"{p}@s{s}", str(s))
                    for p in POINTS for s in range(1, 11)}
    if set(fit_pair) != expected_fit:
        raise RuntimeError("Require all four configurations at exactly the common seeds 1..10")
    kernels = {"ramsweep"} | {prefix + k for prefix in ("up_", "upfull_") for k in UP}
    if set(reference) != {(k, cfg) for k in kernels for cfg in POINTS.values()}:
        raise RuntimeError("Require exactly the 25 board firmware images at all four configurations")
    expected_fw = {"fw/ramsweep.hex"} | {f"{folder}/{prefix}{k}.hex"
        for folder, prefix in (("fw", "up_"), ("fw_board", "upfull_")) for k in UP}
    if set(meta["firmware"]) != expected_fw:
        raise RuntimeError("Board firmware set differs from the verified 25-image matrix")
    for point, cfg in POINTS.items():
        fact = receipt["points"][point]
        row = fit_pair[point, "2"]
        # Runtime is not a hardware metric and can differ between passes.
        a = {k: v for k, v in fact["reference"].items() if k != "seconds"}
        b = {k: v for k, v in row.items() if k != "seconds"}
        if fact["config"] != cfg or a != b:
            raise RuntimeError(f"Board fit facts do not match verified common seed 2: {point}")
        if int(row["cache_config"]) != list(POINTS).index(point) or int(row["capacity_bytes"]) != 4096:
            raise RuntimeError(f"Wrong 4 KiB cache configuration: {point}")
        for corner in ("s85", "s0", "f0"):
            for check in ("setup", "hold"):
                if float(row[f"{check}_{corner}_slack"]) < 0:
                    raise RuntimeError(f"Common seed 2 fails {check} at FPGA corner {corner}: {point}")


def write_checklist(out, rtl_id):
    text = f"""# DE2-115 board session checklist

RTL: `{rtl_id}`. Common placement seed: **2 for all four configurations**.
Clock: 50 MHz. Cache capacity: 4 KiB each. Main RAM: 16 KiB.

The physical session is scheduled separately. This directory contains prepared
SOFs and simulation expectations; it does not contain measured board results.
`BUILD_STATE.json` must say `READY_FOR_PHYSICAL_SESSION` before using the images.

## Session preparation

1. Copy `BOARD_RESULTS_TEMPLATE.csv` to `results/board_<session-date>/results.csv`.
   Record the session date, board identity, Quartus version and JTAG cable there.
2. Check all 100 SOF SHA-256 values against `INDEX.csv`. Preserve the index and
   build state with the session evidence. Each row must have `fit_seed=2`.
3. Connect the DE2-115 and USB-Blaster for the agreed session. If UART is used,
   capture the board RS-232 output at 115200 baud, 8 data bits, no parity, 1 stop
   bit. Firmware reports `CONFIG=HOST_ASSOCIATED_SOF`; associate each capture with
   the exact kernel, configuration, pass and SOF SHA-256 from the index.

## Each matrix pass

Run all rows of `INDEX.csv` in order: one firmware image, then DM, SA2, DM_VC4,
DM_DSE. Finish the complete first pass before repeating the complete second pass.
Program the listed SOF afresh for each measurement, including the second pass.
Programming initializes the RAM image; a reset alone is not a second programming.

The programming command, run only during the agreed physical session, is:

```powershell
& 'D:\\altera\\quartus\\bin64\\quartus_pgm.exe' -c USB-Blaster -m JTAG -o 'p;<absolute-sof-path>'
```

Wait until the firmware finishes. Initial/progress display values are not results.
For a passing row, LEDR[7:0] must be `A5` and HEX7..HEX0 (left to right, eight hex
digits) must equal `expected_mcycle_hex`. `EE` means self-check failure. Save a
photo showing both LEDR and HEX, named `p<pass>_<kernel>_<config>.jpg`, under the
session directory. Record the observed value rather than copying the expectation.

With UART, additionally require `RESULT=PASS`, `MCYCLE` and `MINSTRET` exactly equal
the corresponding index values. Save the full log as
`p<pass>_<kernel>_<config>.uart.log`. The final HEX display contains MCYCLE only;
MINSTRET is available in UART. When only a photo is available, leave observed
MINSTRET empty and identify the evidence as LEDR/HEX rather than a full counter
capture. CPI uses the measured MCYCLE / MINSTRET when both have been captured.

## Completion and discrepancies

The result template has 200 rows (100 cases, twice). Keep unexecuted rows as
`NOT_RUN`. Record failed checks and their evidence without replacing them with
successful retries. Compare the two independent passes by kernel/configuration
before any board values enter `RESULTS.md` or review item A7 changes status.
No power measurement is implied by this board session; Quartus power is a
separate activity-estimate result. Keep every photo, UART log and programming log.
"""
    (out / "SESSION_CHECKLIST.md").write_text(text, encoding="ascii")


def tool(name):
    p = Path(os.environ.get("QUARTUS_ROOTDIR", r"D:\altera\quartus")) / "bin64" / f"quartus_{name}.exe"
    if not p.is_file():
        raise RuntimeError(f"Missing tool: {p}")
    return str(p)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--fit-receipt", default="results/paired10_6c4ccffd_20261009_board_fit_receipt.json")
    ap.add_argument("--reference-tag", default="board_reference_6c4ccffd_20261009")
    ap.add_argument("--out", default="output_files_board_matrix_6c4ccffd_seed2")
    args = ap.parse_args()
    receipt_path = ROOT / args.fit_receipt
    meta_path = ROOT / f"results/{args.reference_tag}_inputs.json"
    if not receipt_path.is_file() or not meta_path.is_file():
        print("[WAIT] Verified common-seed fit receipt and current-RTL reference are required; no MIF or tool operation")
        return 2
    frozen = manifest()
    receipt = json.loads(receipt_path.read_text())
    meta = json.loads(meta_path.read_text())
    if receipt["rtl_id"] != frozen["aggregate"] or meta["rtl_id"] != frozen["aggregate"]:
        raise RuntimeError("Fit/reference revision differs from current frozen RTL")
    if receipt["common_seed"] != 2 or set(receipt["points"]) != set(POINTS):
        raise RuntimeError("Require common board seed 2 for exactly four points")
    if any(r["seed"] != 2 for r in receipt["points"].values()):
        raise RuntimeError("Per-configuration board seeds are forbidden")
    if meta["status"] != "VERIFIED_100_PAIRED_ROWS_EQUAL_R14":
        raise RuntimeError("Current-RTL reference is not yet verified")
    for rel, digest in {**receipt["reports"], **receipt["settings"], **meta["firmware"],
                        **meta["inputs"], **meta["outputs"]}.items():
        if sha(ROOT / rel) != digest:
            raise RuntimeError(f"Verified input changed: {rel}")
    fit_pair = validate_pair(ROOT / receipt["fit_p1"], ROOT / receipt["fit_p2"], ["point", "seed"])
    if len(fit_pair) != 40:
        raise RuntimeError("Require complete ten-seed comparison, 40 paired point/seed rows")
    reference = validate_pair(ROOT / f"results/{args.reference_tag}_p1.csv",
                              ROOT / f"results/{args.reference_tag}_p2.csv", ["kernel", "config"], ignore=())
    if len(reference) != 100:
        raise RuntimeError("Require exactly 100 independently simulated board reference rows")
    validate_matrix(receipt, meta, fit_pair, reference)
    print(f"[READY] RTL {frozen['aggregate'][:8]}, common seed 2, 100 SOFs", flush=True)
    if not args.build:
        return 0
    check_idle()
    out = (ROOT / args.out).resolve()
    if not out.is_relative_to(ROOT) or out == ROOT:
        raise RuntimeError("Output must be a new directory inside the research repository")
    out.mkdir(exist_ok=False)
    backup = out / "canonical_mif"
    backup.mkdir()
    logs = out / "logs"
    logs.mkdir()
    originals = {p.name: sha(p) for p in MIFS}
    for p in MIFS:
        shutil.copy2(p, backup / p.name)
    bins = {name: tool(name) for name in ("cdb", "asm")}
    status = {"state": "BUILDING", "started": stamp(), "rtl_id": frozen["aggregate"],
              "common_seed": 2, "canonical_mif_sha256": originals, "count": 0}
    rows = []

    def assemble(point, label):
        rev = "point_" + point
        checked_tool([bins["cdb"], rev, "-c", rev, "--update_mif"], logs / f"{label}_{point}_update_mif.log")
        checked_tool([bins["asm"], rev, "-c", rev], logs / f"{label}_{point}_asm.log")
        return ROOT / f"output_files_{point}/{rev}.sof"

    try:
        for kernel in sorted({k for k, cfg in reference}):
            image = next((rel for rel in meta["firmware"] if Path(rel).stem == kernel), None)
            if image is None:
                raise RuntimeError(f"No verified firmware: {kernel}")
            subprocess_args = [sys.executable, "scripts/fpga/hex_to_mif.py", "--input", image,
                               "--output-dir", "hdl", "--depth", "4096"]
            checked_tool(subprocess_args, logs / f"{kernel}_mif.log", retries=1)
            for point, cfg in POINTS.items():
                if (ROOT / "results/.abort_board_build").exists():
                    raise RuntimeError("Board build aborted between SOFs; canonical restoration follows")
                sof = assemble(point, kernel)
                name = f"{kernel}_{cfg}.sof"
                dst = out / name
                shutil.copy2(sof, dst)
                if sha(dst) != sha(sof):
                    raise RuntimeError(f"SOF copy differs: {dst}")
                exp = reference[kernel, cfg]
                facts = receipt["points"][point]["reference"]
                mc, mi = int(exp["mcycle"]), int(exp["minstret"])
                rows.append({"kernel": kernel, "config": cfg, "sof": name, "fw": image,
                    "sha256": sha(dst), "md5": hashlib.md5(dst.read_bytes()).hexdigest(),
                    "fw_sha256": meta["firmware"][image], "rtl_id": frozen["aggregate"][:8],
                    "rtl_aggregate": frozen["aggregate"], "fit_seed": 2, "le": facts["le"],
                    "setup_slack_slow85c_ns": facts["setup_s85_slack"],
                    "expected_mcycle": mc, "expected_mcycle_hex": f"{mc:08X}",
                    "expected_minstret": mi, "expected_minstret_hex": f"{mi:08X}", "built": stamp()})
                with (out / "INDEX.csv").open("w", newline="", encoding="ascii") as f:
                    w = csv.DictWriter(f, fieldnames=list(rows[0]))
                    w.writeheader()
                    w.writerows(rows)
                status["count"] = len(rows)
                print(f"[SOF] {name} ({len(rows)}/100); expected MCYCLE={mc:08X}", flush=True)
    except BaseException as exc:
        status["state"] = "BUILD_FAILED"
        status["error"] = str(exc)
        raise
    finally:
        errors = []
        for p in MIFS:
            shutil.copy2(backup / p.name, p)
            if sha(p) != originals[p.name]:
                errors.append(f"Canonical MIF differs: {p.name}")
        for point in POINTS:
            try:
                assemble(point, "restore_canonical")
            except Exception as exc:
                errors.append(str(exc))
        try:
            manifest()
        except Exception as exc:
            errors.append(str(exc))
        status["canonical_restoration"] = "PASS" if not errors else "FAIL"
        status["restoration_errors"] = errors
        if errors:
            status["state"] = "RESTORATION_FAILED"
        elif len(rows) == 100 and len({r["sha256"] for r in rows}) != 100:
            status["state"] = "DUPLICATE_SOF_HASHES_REQUIRES_INSPECTION"
        elif len(rows) == 100 and status["state"] == "BUILDING":
            status["state"] = "READY_FOR_PHYSICAL_SESSION"
        (out / "BUILD_STATE.json").write_text(json.dumps(status, indent=2) + "\n", encoding="ascii")
        if errors:
            raise RuntimeError("Canonical restoration failed; inspect BUILD_STATE.json")
    if len({r["sha256"] for r in rows}) != 100:
        raise RuntimeError("Unexpected duplicate SOF hashes; inspect firmware/configuration binding")
    with (out / "BOARD_RESULTS_TEMPLATE.csv").open("w", newline="", encoding="ascii") as f:
        columns = ["pass", "kernel", "config", "fit_seed", "sof_sha256", "expected_mcycle_hex", "expected_minstret_hex",
                   "observed_ledr_hex", "observed_mcycle_hex", "observed_minstret_hex", "uart_log", "photo", "status"]
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        for pass_no in (1, 2):
            for r in rows:
                w.writerow({"pass": pass_no, "kernel": r["kernel"], "config": r["config"], "fit_seed": 2,
                    "sof_sha256": r["sha256"], "expected_mcycle_hex": r["expected_mcycle_hex"],
                    "expected_minstret_hex": r["expected_minstret_hex"], "status": "NOT_RUN"})
    write_checklist(out, frozen["aggregate"])
    print(f"[READY] 100 SOFs; canonical MIFs restored; physical measurements NOT RUN: {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
