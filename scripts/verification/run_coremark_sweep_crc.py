"""Close numerical CRC evidence for the preserved M1/M2 CoreMark sweep.

Two fresh private compilations, 92 parameter points in each pass, one simulator
at a time. Original sweeps, firmware, RTL and the original observer are kept.
This is a 32 KiB simulation and full-program window, never an official score.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts"))
from run_coremark_crc import (VSIM, SYSTEM_INI, MIN_FREE_MB, MEMORY_GUARD,
    compile_library, frozen_inputs, check_inputs, write_json, sha, stamp, free_mb)
from coremark_crc_gate import known_crcs, validate_case
from snapshot_fields import FIELDS, parse as parse_snapshot, invariants

ERROR = re.compile(r"^\s*#?\s*(?:\*\*\s+(?:Fatal|Error)(?::|\b)|\[FAIL\]|Errors:\s*[1-9]\d*)", re.M | re.I)
PARAMETERS = ("cfg", "lines", "line_words", "victim_entries", "fast_hit")
PROFILE = (*PARAMETERS, "d_lines", "imem_words", "dmem_words", "l0_entries", "predictor")
EXCLUDED = "SA4_256B_L16"  # Four sets cannot support the fixed eight-entry L0 index.


def read_reference(path, grid, fast):
    """Accept the exact supported sweep set, with unambiguous complete frames."""
    required = {"point", "org", "cfg", "cap_bytes", "line_bytes", "lines", "vc", "workload", *FIELDS}
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if (not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames)
                or set(reader.fieldnames) != required):
            raise ValueError("Incomplete/duplicate/unexpected sweep header")
        selected = [r for r in reader if r["workload"] == "coremark"]
    index = {}
    for row in selected:
        if None in row or any(v is None or not v.strip() for v in row.values()):
            raise ValueError("Incomplete reference row")
        name = row["point"]
        if name in index or name not in grid or name == EXCLUDED:
            raise ValueError("Duplicate/unknown/unsupported sweep point: " + name)
        p = grid[name]
        for field in ("org", "cfg", "cap_bytes", "line_bytes", "lines", "vc"):
            if str(p[field]) != row[field]:
                raise ValueError("Point parameters differ from source grid: " + name + "/" + field)
        if fast and p["cfg"] == 0:
            raise ValueError("DM is not a FAST_HIT experiment")
        if any(not re.fullmatch(r"\d+", row[k]) for k in FIELDS):
            raise ValueError("Non-integer or negative snapshot field")
        counters = {k: int(row[k]) for k in FIELDS}
        if (invariants(counters) or counters["result_pass"] != 1
                or counters["invariant_pass"] != 1 or counters["minstret"] <= 0):
            raise ValueError("Invalid baseline counter frame: " + name)
        index[name] = counters
    supported = {name for name, p in grid.items() if name != EXCLUDED and (not fast or p["cfg"] != 0)}
    if set(index) != supported:
        raise ValueError("Unexpected CoreMark sweep completeness")
    return index


def baselines():
    spec = importlib.util.spec_from_file_location("sweep_grid", ROOT / "scripts/m2/run_m2_sweep.py")
    sweep = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sweep)
    grid = {p["point"]: p for p in sweep.grid()}
    cases, paths = [], []
    for fast, expected_count in ((0, 49), (1, 43)):
        passes = []
        for number in (1, 2):
            path = ROOT / f"results/m2/sweep_{'fast_' if fast else ''}p{number}.csv"
            paths.append(path)
            index = read_reference(path, grid, fast)
            if len(index) != expected_count:
                raise ValueError("Unexpected CoreMark sweep completeness")
            passes.append(index)
        if passes[0] != passes[1]:
            raise ValueError("Preserved independent sweep passes differ")
        for name, expected in sorted(passes[0].items()):
            p = grid[name]
            cases.append({"point": name, "cfg": p["cfg"], "lines": p["lines"],
                "line_words": p["line_words"], "victim_entries": p["vc"] or 4,
                "fast_hit": fast, "cap_bytes": p["cap_bytes"], "expected": expected})
    return cases, paths


def wrapper_text(source):
    old = "module tb_coremark_crc_audit #("
    if source.count(old) != 1 or source.count("    parameter integer L0_ENTRIES = 8,") != 1:
        raise ValueError("Unexpected passive observer parameter block")
    anchor = "        .L0_ENTRIES(L0_ENTRIES), .IMEM_DEPTH(IMEM_DEPTH), .DMEM_DEPTH(DMEM_DEPTH),"
    if source.count(anchor) != 1 or source.count("    integer uart_fd = 0;") != 1:
        raise ValueError("Unexpected passive observer forwarding/observation block")
    text = source.replace(old, "module tb_coremark_sweep_crc_audit #(")
    text = text.replace("    parameter integer L0_ENTRIES = 8,",
        "    parameter integer CACHE_LINE_WORDS = 4,\n"
        "    parameter integer VICTIM_ENTRIES = 4,\n"
        "    parameter integer L0_ENTRIES = 8,")
    text = text.replace(anchor,
        "        .CACHE_LINE_WORDS(CACHE_LINE_WORDS), .VICTIM_ENTRIES(VICTIM_ENTRIES),\n" + anchor)
    text = text.replace("    integer uart_fd = 0;",
        '    initial $display("COREMARK_SWEEP_PROFILE cfg=%0d lines=%0d line_words=%0d victim_entries=%0d fast_hit=%0d d_lines=%0d imem_words=%0d dmem_words=%0d l0_entries=%0d predictor=%0d",\n'
        "        bench.CACHE_CONFIG, bench.ICACHE_LINE_COUNT, bench.CACHE_LINE_WORDS,\n"
        "        bench.VICTIM_ENTRIES, bench.CACHE_FAST_HIT, bench.DCACHE_LINE_COUNT,\n"
        "        bench.IMEM_DEPTH, bench.DMEM_DEPTH, bench.L0_ENTRIES, bench.BRANCH_PREDICT_ENABLE);\n\n    integer uart_fd = 0;")
    return text


def validate_profile(text, case):
    pattern = "COREMARK_SWEEP_PROFILE " + " ".join(k + r"=(\d+)" for k in PROFILE) + r"\s*$"
    matches = re.findall(pattern, text, re.M)
    expected = (*[case[k] for k in PARAMETERS], case["lines"], 4096, 4096, 8, 1)
    if len(matches) != 1 or tuple(map(int, matches[0])) != expected:
        raise ValueError("Missing/wrong actual elaborated sweep parameters")
    if ERROR.search(text):
        raise ValueError("Simulator error/failure in sweep case")


def guard(output):
    if (output / ".abort").exists():
        raise RuntimeError("Cooperative stop requested between cases")
    if free_mb() < MIN_FREE_MB:
        raise RuntimeError(f"Less than {MIN_FREE_MB} MB Windows memory free; no new case started")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--tag", default="coremark_sweep_crc_20261010")
    ap.add_argument("--max-cycles", type=int, default=40000000)
    args = ap.parse_args()
    if not re.fullmatch(r"[a-z][a-z0-9_]+", args.tag) or args.max_cycles <= 0:
        ap.error("Use a content/date tag and positive simulation limit")
    cases, refs = baselines()
    extra = [Path(__file__), HERE / "run_coremark_crc.py", ROOT / "scripts/m2/run_m2_sweep.py", *refs]
    manifest, inputs = frozen_inputs(extra)
    numeric_reference = known_crcs(ROOT / "sw/coremark/core_main.c")
    wrapper = wrapper_text((HERE / "coremark_uart_observer.sv").read_text())
    print(f"[PLAN] {len(cases)} points x2, fresh private compilations, one simulator at a time", flush=True)
    print("[PLAN] source-known CRCs + every counter equal to paired historical sweep; RAM32KiB/full program", flush=True)
    if not args.run:
        return 0
    if not VSIM.is_file() or not SYSTEM_INI.is_file():
        raise RuntimeError("Missing Questa installation")
    output = ROOT / "results" / args.tag
    guard(output)
    output.mkdir(exist_ok=False)
    generated = output / "coremark_sweep_observer.sv"
    generated.write_text(wrapper, encoding="ascii")
    artifacts = {generated.relative_to(ROOT).as_posix(): sha(generated)}
    receipt = output / "verification.json"
    state = {"status": "IN_PROGRESS", "started": stamp(), "rtl_id": manifest["aggregate"],
        "inputs": inputs, "artifacts": artifacts, "cases_per_pass": len(cases), "cases": [],
        "ram_bytes": 32768, "window": "complete_coremark_main", "official_score": False,
        "memory_guard": MEMORY_GUARD, "generated_observer_sha256": sha(generated),
        "method": "fresh_single_lane_simulations_passive_apb_uart_source_numeric_crc",
        "excluded_point": {"point": EXCLUDED, "reason": "Four sets cannot support the fixed eight-entry L0 index"},
        "compilations": []}
    write_json(receipt, state)
    measurements = []
    try:
        for number in (1, 2):
            check_inputs(inputs)
            guard(output)
            library, ini, compilation = compile_library(output, number)
            artifacts.update({p.relative_to(ROOT).as_posix(): sha(p) for p in compilation})
            compile_log = output / f"compile_sweep_p{number}.log"
            command = (f"onerror {{quit -code 1 -f}}; vlog -work {library} -sv {{{generated.as_posix()}}}; "
                "echo {[PASS] Sweep passive observer compiled}; quit -f")
            with compile_log.open("wb") as stream:
                process = subprocess.run([str(VSIM), "-c", "-modelsimini", str(ini), "-do", command],
                    cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=1800)
            txt = compile_log.read_text(errors="replace")
            if process.returncode or ERROR.search(txt) or "[PASS] Sweep passive observer compiled" not in txt:
                raise RuntimeError("Sweep observer compilation failed")
            artifacts[compile_log.relative_to(ROOT).as_posix()] = sha(compile_log)
            state["compilations"].append({"pass": number, "library": library, "modelsim_ini": str(ini),
                "generated_wrapper_command": [str(VSIM), "-c", "-modelsimini", str(ini), "-do", command],
                "generated_wrapper_returncode": process.returncode})
            rows = []
            for case in cases:
                guard(output)
                check_inputs(inputs)
                if sha(generated) != state["generated_observer_sha256"]:
                    raise RuntimeError("Generated observer changed during execution")
                suffix = f"p{number}_{case['point'].lower()}_fast{case['fast_hit']}"
                log, uart = output / f"{suffix}.log", output / f"{suffix}.uart.txt"
                if log.exists() or uart.exists():
                    raise RuntimeError("Refusing to overwrite case evidence")
                command = (f"onerror {{quit -code 1 -f}}; vsim -onfinish stop -gCACHE_CONFIG={case['cfg']} "
                    f"-gCACHE_FAST_HIT={case['fast_hit']} -gICACHE_LINE_COUNT={case['lines']} "
                    f"-gDCACHE_LINE_COUNT={case['lines']} -gCACHE_LINE_WORDS={case['line_words']} "
                    f"-gVICTIM_ENTRIES={case['victim_entries']} {library}.tb_coremark_sweep_crc_audit "
                    f"+benchmark=coremark +max_cycles={args.max_cycles} +coremark_uart={uart.as_posix()}; run -all; quit -f")
                started = time.monotonic()
                with log.open("wb") as stream:
                    process = subprocess.run([str(VSIM), "-c", "-modelsimini", str(ini), "-do", command],
                        cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=1800)
                if process.returncode:
                    raise RuntimeError(f"Sweep simulator failed rc={process.returncode}: {suffix}")
                validate_profile(log.read_text(errors="replace"), case)
                counters, crc = validate_case(log, uart, numeric_reference, case["cfg"], parse_snapshot, invariants)
                if counters != case["expected"]:
                    changed = {k: [case["expected"][k], counters[k]] for k in FIELDS if counters[k] != case["expected"][k]}
                    raise RuntimeError("Current counter frame differs from sweep: " + suffix + " " + json.dumps(changed))
                row = {k: case[k] for k in ("point", *PARAMETERS, "cap_bytes")}
                row.update(counters)
                row.update(crc)
                rows.append(row)
                artifacts.update({p.relative_to(ROOT).as_posix(): sha(p) for p in (log, uart)})
                state["cases"].append({"pass": number, "point": case["point"], "fast_hit": case["fast_hit"],
                    "crc_pass": True, "all_counters_equal_reference": True, "elapsed_seconds": time.monotonic() - started,
                    "command": [str(VSIM), "-c", "-modelsimini", str(ini), "-do", command], "returncode": process.returncode,
                    "log": log.relative_to(ROOT).as_posix(), "uart": uart.relative_to(ROOT).as_posix()})
                write_json(receipt, state)
                print(f"[PASS] {suffix} numeric CRCs and all{len(FIELDS)} counters equal reference", flush=True)
            result = output / f"results_p{number}.csv"
            with result.open("w", newline="", encoding="ascii") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            artifacts[result.relative_to(ROOT).as_posix()] = sha(result)
            measurements.append(rows)
        check_inputs(inputs)
        if measurements[0] != measurements[1]:
            raise RuntimeError("Independent sweep CRC/counter passes differ")
        for rel, digest in artifacts.items():
            if sha(ROOT / rel) != digest:
                raise RuntimeError("Evidence artifact changed: " + rel)
        state["status"] = "VERIFIED_92_PAIRED_SWEEP_POINTS_CRC_AND_ALL_COUNTERS_EQUAL_REFERENCE"
        state["completed"] = stamp()
        print("[VERIFIED] 184 actual simulations; source CRCs, all counters and inputs identical", flush=True)
    except BaseException as exc:
        state["status"] = "STOPPED_REQUIRES_INSPECTION"
        state["error"] = str(exc)
        raise
    finally:
        write_json(receipt, state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
