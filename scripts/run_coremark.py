# -*- coding: utf-8 -*-
"""Run the frozen CoreMark firmware with counter and source-known CRC gates.

Default backing RAM is 4096 + 4096 words (32 KiB); the approximately 19.4 KiB
image does not fit the research chip's 16 KiB RAM. The measured window covers
the complete coremark_main call, including initialization, validation and UART
printing. This one-iteration simulation is not an official CoreMark score or
an iterate-only performance measurement.

The caller compiles the active RTL into --lib first. A passive APB TXDATA
observer is added to that same library. It captures accepted firmware writes;
physical UART serialization is outside this check. All existing CLI parameters
and the 43-column counter CSV contract are retained.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = {0: "DM", 1: "SA2", 2: "DM_VC4", 3: "DM_DSE", 4: "SA4", 5: "SA2N"}
VSIM = "C:/questasim64_2024.1/win64/vsim.exe"
OBSERVER = ROOT / "scripts/verification/coremark_uart_observer.sv"
CRC_SOURCE = ROOT / "sw/coremark/core_main.c"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/verification"))
from snapshot_fields import FIELDS, invariants, parse as parse_snapshot  # noqa: E402
from coremark_crc_gate import known_crcs, validate_case  # noqa: E402

SIM_ERROR = re.compile(r"^\s*#?\s*(?:\*\*\s+(?:Fatal|Error)(?::|\b)|\[FAIL\]|Errors:\s*[1-9]\d*)",
                       re.IGNORECASE | re.MULTILINE)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parser():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lines", type=int, default=64)
    ap.add_argument("--l0", type=int, default=8)
    ap.add_argument("--imem", type=int, default=4096)
    ap.add_argument("--dmem", type=int, default=4096)
    ap.add_argument("--max-cycles", type=int, default=200000000)
    ap.add_argument("--out", required=True)
    ap.add_argument("--configs", default="0,1,2,3")
    ap.add_argument("--lib", default="work")
    ap.add_argument("--fast", action="store_true")
    return ap


def main(argv=None):
    ap = parser()
    args = ap.parse_args(argv)
    try:
        configs = [int(c) for c in args.configs.split(",")]
    except ValueError:
        ap.error("--configs requires comma-separated configuration IDs")
    if not configs or len(set(configs)) != len(configs) or any(c not in CONFIGS for c in configs):
        ap.error("--configs must contain distinct configuration IDs 0 through 5")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", args.lib):
        ap.error("--lib must be a Questa library name")
    if any(value <= 0 for value in (args.lines, args.l0, args.imem, args.dmem, args.max_cycles)):
        ap.error("cache, RAM and simulation limits must be positive")

    parent = ROOT / "results/coremark_logs" / Path(args.out).stem
    parent.mkdir(parents=True, exist_ok=True)
    log_dir = Path(tempfile.mkdtemp(prefix=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_"), dir=parent))
    inputs = {p.relative_to(ROOT).as_posix(): sha(p) for p in
              (Path(__file__), OBSERVER, CRC_SOURCE, ROOT / "scripts/verification/coremark_crc_gate.py",
               ROOT / "scripts/snapshot_fields.py", ROOT / "fw/coremark.hex", ROOT / "results/rtl_manifest.json")}
    (log_dir / "inputs.json").write_text(json.dumps({
        "sources": inputs, "arguments": vars(args),
        "ram_bytes": 4 * (args.imem + args.dmem), "window": "complete_coremark_main",
        "method": "accepted_apb_txdata_bytes_to_source_reference_crcs", "official_score": False}, indent=2) + "\n", encoding="ascii")
    print("[INFO] CoreMark simulation RAM=%d bytes; complete coremark_main window; official_score=0"
          % (4 * (args.imem + args.dmem)))
    print("[INFO] raw evidence: %s" % log_dir.relative_to(ROOT))

    compile_log = log_dir / "compile_observer.log"
    compile_do = ("onerror {quit -code 1 -f}; vlog -work %s -sv {%s}; "
                  "echo {[PASS] Passive CoreMark UART observer compiled}; quit -f"
                  % (args.lib, OBSERVER.as_posix()))
    with compile_log.open("wb") as stream:
        rc = subprocess.run([VSIM, "-c", "-do", compile_do], cwd=str(ROOT),
                            stdout=stream, stderr=subprocess.STDOUT).returncode
    text = compile_log.read_text(encoding="utf-8", errors="replace")
    if rc or SIM_ERROR.search(text) or "[PASS] Passive CoreMark UART observer compiled" not in text:
        print("[FAIL] passive observer compilation rc=%d; see %s" % (rc, compile_log))
        return 1

    try:
        reference = known_crcs(CRC_SOURCE)
    except ValueError as exc:
        print("[FAIL] suite reference CRCs: %s" % exc)
        return 1
    rows, failures = [], []
    for cfg in configs:
        name = CONFIGS[cfg]
        suffix = "coremark_%s_lc%d%s" % (name, args.lines, "_fast" if args.fast else "")
        log, uart = log_dir / (suffix + ".log"), log_dir / (suffix + ".uart.txt")
        do = ("onerror {quit -code 1 -f}; vsim -onfinish stop "
              "-gCACHE_CONFIG=%d -gCACHE_FAST_HIT=%d "
              "-gICACHE_LINE_COUNT=%d -gDCACHE_LINE_COUNT=%d -gL0_ENTRIES=%d "
              "-gIMEM_DEPTH=%d -gDMEM_DEPTH=%d %s.tb_coremark_crc_audit "
              "+benchmark=coremark +max_cycles=%d {+coremark_uart=%s}; run -all; quit -f"
              % (cfg, int(args.fast), args.lines, args.lines, args.l0,
                 args.imem, args.dmem, args.lib, args.max_cycles, uart.as_posix()))
        t0 = time.time()
        try:
            with log.open("wb") as stream:
                rc = subprocess.run([VSIM, "-c", "-do", do], cwd=str(ROOT),
                                    stdout=stream, stderr=subprocess.STDOUT).returncode
            if rc:
                raise ValueError("rc=%d" % rc)
            text = log.read_text(encoding="utf-8", errors="replace")
            if SIM_ERROR.search(text):
                raise ValueError("simulator reported Error/Fatal/FAIL or nonzero Errors count")
            row, numeric = validate_case(log, uart, reference, cfg, parse_snapshot, invariants)
            proof = {"status": "VERIFIED", "configuration": cfg, "fast_hit": int(args.fast),
                     "crc": numeric, "log_sha256": sha(log), "uart_sha256": sha(uart),
                     "method": "accepted_apb_txdata_bytes_to_source_reference_crcs",
                     "ram_bytes": 4 * (args.imem + args.dmem), "window": "complete_coremark_main"}
            (log_dir / (suffix + ".crc.json")).write_text(json.dumps(proof, indent=2) + "\n", encoding="ascii")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            failures.append("%s: %s" % (name, exc))
            print("[FAIL] %-8s %s  see %s" % (name, exc, log))
            continue
        row["kernel"], row["config"], row["config_id"] = "coremark", name, cfg
        rows.append(row)
        print("[ok]   %-8s source CRCs valid; mcycle=%-12s minstret=%-10s %.0fs"
              % (name, row["mcycle"], row["minstret"], time.time() - t0))

    changed = [rel for rel, digest in inputs.items() if sha(ROOT / rel) != digest]
    if changed:
        failures.append("verification inputs changed: " + ", ".join(changed))
    if failures:
        print("[FAIL] %s" % "; ".join(failures))
        return 1
    if not rows or len(rows) != len(configs):
        print("[FAIL] incomplete CoreMark configuration matrix")
        return 1
    with open(args.out, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["kernel", "config", "config_id"] + list(FIELDS))
        writer.writeheader()
        writer.writerows(rows)
    print("[PASS] %d run(s), source-known CRCs validated -> %s" % (len(rows), args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
