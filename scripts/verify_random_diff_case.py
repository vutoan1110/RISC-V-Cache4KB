#!/usr/bin/env python3
"""Require completed BP OFF/ON simulations and complete matching retirement traces.

The completion counts come from tb/random_trace_tb.sv after HALT, register and
memory checks. A matching partial trace, including a header-only trace, fails.
This checks predictor equivalence; it is not an independent ISA oracle.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path

HEADER = ("order", "pc", "instr", "rd", "we", "rd_data", "mem_we",
          "mem_addr", "mem_wdata", "mem_wstrb")
ERROR = re.compile(r"^\s*#?\s*(?:\*\*\s+(?:Fatal|Error)(?::|\b)|\[FAIL\]|Errors:\s*[1-9]\d*)",
                   re.IGNORECASE | re.MULTILINE)


def trace(path: Path, expected_count: int) -> bytes:
    data = path.read_bytes()
    if not data or not data.endswith(b"\n"):
        raise ValueError(f"Empty or unterminated trace: {path}")
    rows = list(csv.reader(io.StringIO(data.decode("ascii")), strict=True))
    if not rows or tuple(rows[0]) != HEADER:
        raise ValueError(f"Incorrect trace header: {path}")
    if expected_count <= 0 or len(rows) - 1 != expected_count:
        raise ValueError(f"Incomplete trace: {path}, {len(rows)-1} records, completion requires {expected_count}")
    for order, row in enumerate(rows[1:]):
        if len(row) != len(HEADER):
            raise ValueError(f"Incorrect field count: {path}, record {order}")
        for field in ("order", "rd", "we", "mem_we"):
            if not re.fullmatch(r"\d+", row[HEADER.index(field)]):
                raise ValueError(f"Invalid decimal {field}: {path}, record {order}")
        values = dict(zip(HEADER, row))
        if int(values["order"]) != order or not 0 <= int(values["rd"]) <= 31:
            raise ValueError(f"Invalid retirement order/register: {path}, record {order}")
        if any(values[f] not in ("0", "1") for f in ("we", "mem_we")):
            raise ValueError(f"Invalid write flag: {path}, record {order}")
        for field in ("pc", "instr", "rd_data", "mem_addr", "mem_wdata"):
            if not re.fullmatch(r"[0-9a-fA-F]{8}", values[field]):
                raise ValueError(f"Invalid 32-bit {field}: {path}, record {order}")
        if not re.fullmatch(r"[0-9a-fA-F]", values["mem_wstrb"]):
            raise ValueError(f"Invalid memory strobe: {path}, record {order}")
        if int(values["pc"], 16) & 3 or values["instr"].lower() == "0000006f":
            raise ValueError(f"Unaligned PC or unexpected HALT record: {path}, record {order}")
    return data


def verify(seed: int, rc: int, log: Path, off: Path, on: Path,
           hexfile: Path | None = None, manifest: Path | None = None) -> dict:
    report = {"seed": seed, "simulator_returncode": rc, "status": "FAIL"}
    try:
        if rc != 0:
            raise ValueError(f"Simulator returned {rc}")
        text = log.read_text(encoding="utf-8", errors="replace")
        if ERROR.search(text):
            raise ValueError("Simulator log contains Error, Fatal, FAIL or nonzero error count")
        completed = re.findall(r"^\s*#?\s*\[PASS\] Random retirement traces generated seed=(\d+) OFF=(\d+) ON=(\d+)\s*$",
                               text, re.MULTILINE)
        state = re.findall(r"^\s*#?\s*\[PASS\] BP OFF/ON architectural state equivalent seed=(\d+)\s*$",
                           text, re.MULTILINE)
        if len(completed) != 1 or len(state) != 1:
            raise ValueError("Missing or duplicate simulation/state completion markers")
        actual_seed, n_off, n_on = map(int, completed[0])
        if actual_seed != seed or int(state[0]) != seed or n_off != n_on:
            raise ValueError("Completion seed or OFF/ON record counts differ")
        a, b = trace(off, n_off), trace(on, n_on)
        if a != b:
            raise ValueError("BP OFF/ON retirement traces differ")
        if (hexfile is None) != (manifest is None):
            raise ValueError("Provide both firmware and generator manifest")
        if hexfile is not None:
            image = hexfile.read_bytes()
            meta = json.loads(manifest.read_text())
            # gen_rv32 hashes its LF text before write_text; Windows writes
            # CRLF. Check that exact generator convention and also retain the
            # raw on-disk hash, without treating other edits as equivalent.
            normalized = image.decode("ascii").replace("\r\n", "\n")
            words = normalized.splitlines()
            if ("\r" in normalized or meta["seed"] != seed
                    or meta["sha256"] != hashlib.sha256(normalized.encode("ascii")).hexdigest()
                    or meta["static_instruction_words"] != len(words)
                    or meta["requested_length_before_halt"] + 1 != len(words)
                    or not words or words[-1].lower() != "0000006f"
                    or any(not re.fullmatch(r"[0-9a-fA-F]{8}", w) for w in words)):
                raise ValueError("Generated firmware or its manifest differs")
            report["firmware_sha256"] = hashlib.sha256(image).hexdigest()
            report["generator_lf_text_sha256"] = meta["sha256"]
            report["generator_manifest_sha256"] = hashlib.sha256(manifest.read_bytes()).hexdigest()
        report.update(status="VERIFIED", retirements=n_off,
                      off_sha256=hashlib.sha256(a).hexdigest(), on_sha256=hashlib.sha256(b).hexdigest(),
                      log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    except (OSError, ValueError, KeyError, TypeError, csv.Error) as exc:
        report["error"] = str(exc)
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--rc", type=int, required=True)
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--off", type=Path, required=True)
    ap.add_argument("--on", type=Path, required=True)
    ap.add_argument("--hex", dest="hexfile", type=Path)
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    report = verify(args.seed, args.rc, args.log, args.off, args.on, args.hexfile, args.manifest)
    rendered = json.dumps(report, indent=2) + "\n"
    if args.out:
        # A receipt belongs to one fresh run directory; never replace evidence.
        with args.out.open("x", encoding="utf-8") as f:
            f.write(rendered)
    print(rendered, end="")
    return 0 if report["status"] == "VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
