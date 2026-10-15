"""Plan or execute two independent, sequential CRC-gated CoreMark simulations.

Only new evidence under results/<content_date_tag>/ is written. The original
firmware, frozen testbench, RTL, default work libraries, and existing result
CSVs remain unchanged. This is a 32 KiB simulation, not a chip/board score.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/fpga"))
from snapshot_fields import FIELDS, invariants, parse as parse_snapshot
from board_common import free_mb
from coremark_crc_gate import known_crcs, validate_case

VSIM = Path("C:/questasim64_2024.1/win64/vsim.exe")
SYSTEM_INI = VSIM.parent.parent / "modelsim.ini"
CONFIGS = {0: "DM", 1: "SA2", 2: "DM_VC4", 3: "DM_DSE", 4: "SA4", 5: "SA2N"}
CASES = [(False, cfg) for cfg in CONFIGS] + [(True, cfg) for cfg in range(1, 6)]
MIN_FREE_MB = 3000
MEMORY_GUARD = {
    "windows_free_mb_minimum": MIN_FREE_MB,
    "method": "single_process_rtl_simulation_with_measured_margin",
    "supporting_live_sample": {
        "date": "2026-10-09", "model": "current_RTL_UVM_ACT4_SoC",
        "vsimk_working_set_bytes": 100761600, "vsimk_private_bytes": 297000000,
        "launcher_working_set_bytes_approx": 10000000,
        "windows_free_kib_at_sample": 4381256,
    },
    "reason": "CoreMark uses the same RTL SoC without UVM packages; RAM grows by16KiB. A3GB free guard leaves a margin over observed~0.3GB private use. The6GB Quartus-fit guard does not apply to this new small RTL simulation runner.",
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def stamp():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def baselines():
    expected = {}
    paths = []
    for fast in (False, True):
        pairs = []
        for pass_no in (1, 2):
            path = ROOT / f"results/coremark_rfbht{'f' if fast else ''}_4kb_p{pass_no}.csv"
            paths.append(path)
            with path.open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            ids = range(1, 6) if fast else range(6)
            if len(rows) != len(ids) or {int(row["config_id"]) for row in rows} != set(ids):
                raise RuntimeError(f"Incomplete/duplicate reference: {path}")
            parsed = {}
            for row in rows:
                cfg = int(row["config_id"])
                if row["kernel"] != "coremark" or row["config"] != CONFIGS[cfg]:
                    raise RuntimeError(f"Wrong reference context: {path}")
                one = {field: int(row[field]) for field in FIELDS}
                if invariants(one) or one["result_pass"] != 1 or one["invariant_pass"] != 1:
                    raise RuntimeError(f"Invalid reference counters: {path}/{cfg}")
                parsed[cfg] = one
            pairs.append(parsed)
        if pairs[0] != pairs[1]:
            raise RuntimeError("Existing independently measured CoreMark references differ")
        expected.update({(fast, cfg): row for cfg, row in pairs[0].items()})
    return expected, paths


def frozen_inputs(extra_paths):
    manifest_path = ROOT / "results/rtl_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    inputs = dict(manifest["files"])
    for rel, digest in inputs.items():
        if sha(ROOT / rel) != digest:
            raise RuntimeError(f"Frozen RTL/firmware input differs: {rel}")
    if len(inputs) != manifest["count"]:
        raise RuntimeError("Manifest count differs")
    for path in [manifest_path, ROOT / "tb/compile_active_design.do", ROOT / "scripts/snapshot_fields.py",
                 ROOT / "scripts/fpga/board_common.py", ROOT / "sw/coremark/core_main.c",
                 ROOT / "sw/coremark/coremark.h", ROOT / "sw/coremark/core_portme.h",
                 ROOT / "sw/coremark/core_portme.c", ROOT / "sw/coremark/build_hex.sh",
                 HERE / "coremark_uart_observer.sv", HERE / "coremark_crc_gate.py", Path(__file__),
                 *extra_paths]:
        inputs[path.relative_to(ROOT).as_posix()] = sha(path)
    return manifest, inputs


def check_inputs(inputs):
    bad = [rel for rel, digest in inputs.items() if sha(ROOT / rel) != digest]
    if bad:
        raise RuntimeError("Frozen inputs changed: " + ", ".join(bad))


def write_json(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="ascii")
    tmp.replace(path)


def validate_compile_script(text, library, libdir):
    """Check actual Tcl library commands; the '-work' option is legitimate."""
    commands = [line.strip() for line in text.splitlines()
                if line.strip() and not line.lstrip().startswith("#")]
    library_commands = [line for line in commands if re.match(r"(?:vlog|vcom|vlib|vdel|vmap)\b", line)]
    expected_vlib = f"vlib {{{libdir.as_posix()}}}"
    if library_commands.count(expected_vlib) != 1:
        raise RuntimeError("Generated compilation must create exactly its own private library")
    vlog_count = 0
    for line in library_commands:
        if line == expected_vlib:
            continue
        if re.match(r"vlog\s+-work\s+" + re.escape(library) + r"(?:\s|$)", line):
            vlog_count += 1
            continue
        raise RuntimeError("Unexpected/default library command in generated compilation: " + line)
    if vlog_count < 2:
        raise RuntimeError("Generated compilation lacks explicit private-library vlog commands")


def compile_library(output, pass_no):
    library = f"coremark_crc_p{pass_no}"
    libdir = output / library
    ini = output / f"modelsim_p{pass_no}.ini"
    script = output / f"compile_p{pass_no}.do"
    log = output / f"compile_p{pass_no}.log"
    if any(path.exists() for path in (libdir, ini, script, log)):
        raise RuntimeError("Private library/artifact already exists; preserve and inspect")
    ini.write_text(f"[Library]\n{library} = {libdir.as_posix()}\nothers = {SYSTEM_INI.as_posix()}\n", encoding="ascii")
    original = (ROOT / "tb/compile_active_design.do").read_text(encoding="utf-8")
    block = "if {[file exists work]} {\n    vdel -lib work -all\n}\nvlib work"
    if original.count(block) != 1:
        raise RuntimeError("Unexpected active compile library block")
    generated = original.replace(block, f"vlib {{{libdir.as_posix()}}}")
    generated = generated.replace("vlog -sv", f"vlog -work {library} -sv")
    generated += (f"\nvlog -work {library} -sv {{{(HERE / 'coremark_uart_observer.sv').as_posix()}}}\n"
                  "echo {[PASS] Passive CoreMark UART observer compiled}\n")
    validate_compile_script(generated, library, libdir)
    script.write_text(generated, encoding="ascii")
    with log.open("wb") as f:
        proc = subprocess.run([str(VSIM), "-c", "-modelsimini", str(ini), "-do",
                               f"do {{{script.as_posix()}}}; quit -f"], cwd=ROOT,
                              stdout=f, stderr=subprocess.STDOUT, timeout=1800)
    text = log.read_text(encoding="utf-8", errors="replace")
    if proc.returncode or "[PASS] Passive CoreMark UART observer compiled" not in text or re.search(r"\*\*\s+(Fatal|Error)", text):
        raise RuntimeError(f"Private compilation failed rc={proc.returncode}: {log}")
    return library, ini, (ini, script, log)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--tag", default="coremark_crc_20261009")
    parser.add_argument("--max-cycles", type=int, default=200000000)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z][a-z0-9_]+", args.tag):
        parser.error("Use an ASCII content/date tag")
    expected, ref_paths = baselines()
    manifest, inputs = frozen_inputs(ref_paths)
    reference = known_crcs(ROOT / "sw/coremark/core_main.c")
    print("[PLAN] 11 cases x 2 fresh independent simulations; one process at a time", flush=True)
    print("[PLAN] 4 KiB caches, RAM32 KiB simulation, current frozen firmware, numeric suite CRCs", flush=True)
    print("[PLAN] final gate: all CRCs + all snapshot fields = independent pass = existing reference", flush=True)
    if not args.run:
        return 0
    if not VSIM.is_file() or not SYSTEM_INI.is_file():
        raise RuntimeError("Questa executable/installation modelsim.ini missing")
    if free_mb() < MIN_FREE_MB:
        raise RuntimeError(f"Less than {MIN_FREE_MB} MB Windows memory free; no new simulation started")
    output = ROOT / "results" / args.tag
    output.mkdir(exist_ok=False)
    receipt = output / "verification.json"
    metadata = {"status": "IN_PROGRESS", "started": stamp(), "rtl_id": manifest["aggregate"],
                "inputs": inputs, "method": "accepted_apb_txdata_bytes_to_source_reference_crcs",
                "ram_bytes": 32768, "cache_bytes_each": 4096, "official_score": False,
                "cases_per_pass": len(CASES), "memory_guard": MEMORY_GUARD,
                "libraries": [], "artifacts": {}, "cases": []}
    write_json(receipt, metadata)
    results = []
    try:
        for pass_no in (1, 2):
            check_inputs(inputs)
            if free_mb() < MIN_FREE_MB:
                raise RuntimeError(f"Less than {MIN_FREE_MB} MB free before private compilation")
            library, ini, artifacts = compile_library(output, pass_no)
            metadata["libraries"].append(library)
            metadata["artifacts"].update({p.relative_to(ROOT).as_posix(): sha(p) for p in artifacts})
            rows = []
            for fast, cfg in CASES:
                if (ROOT / "results/.abort_coremark_crc").exists():
                    raise RuntimeError("Cooperative stop requested between cases")
                check_inputs(inputs)
                if free_mb() < MIN_FREE_MB:
                    raise RuntimeError(f"Less than {MIN_FREE_MB} MB free before the next case")
                suffix = f"p{pass_no}_c{cfg}{'_fast' if fast else ''}"
                log, uart = output / f"{suffix}.log", output / f"{suffix}.uart.txt"
                if log.exists() or uart.exists():
                    raise RuntimeError("Case output already exists; no overwrite")
                command = (f"onerror {{quit -code1 -f}}; vsim -onfinish stop -gCACHE_CONFIG={cfg} "
                           f"-gCACHE_FAST_HIT={int(fast)} {library}.tb_coremark_crc_audit "
                           f"+benchmark=coremark +max_cycles={args.max_cycles} "
                           f"+coremark_uart={uart.as_posix()}; run -all; quit -f")
                # Keep the Questa option and its value as separate Tcl tokens.
                command = command.replace("-code1", "-code 1")
                with log.open("wb") as f:
                    proc = subprocess.run([str(VSIM), "-c", "-modelsimini", str(ini), "-do", command],
                                          cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, timeout=1800)
                if proc.returncode:
                    raise RuntimeError(f"Simulation failed rc={proc.returncode}: {log}")
                counters, numeric = validate_case(log, uart, reference, cfg, parse_snapshot, invariants)
                if counters != expected[(fast, cfg)]:
                    raise RuntimeError(f"Measured counter frame differs from current reference: {suffix}")
                row = {"kernel": "coremark", "config": CONFIGS[cfg], "config_id": cfg,
                       "fast_hit": int(fast), **counters, **numeric}
                rows.append(row)
                metadata["cases"].append({"pass": pass_no, "config": CONFIGS[cfg], "fast_hit": int(fast),
                                         "crc_pass": True, "counters_equal_current_reference": True})
                metadata["artifacts"].update({p.relative_to(ROOT).as_posix(): sha(p) for p in (log, uart)})
                write_json(receipt, metadata)
                print(f"[PASS] {suffix} CRCs source-known; all{len(FIELDS)} counters match; mcycle={counters['mcycle']}", flush=True)
            csv_path = output / f"results_p{pass_no}.csv"
            with csv_path.open("w", newline="", encoding="ascii") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            metadata["artifacts"][csv_path.relative_to(ROOT).as_posix()] = sha(csv_path)
            results.append(rows)
            write_json(receipt, metadata)
        check_inputs(inputs)
        if results[0] != results[1]:
            raise RuntimeError("Independent CRC/counter passes differ")
        for rel, digest in metadata["artifacts"].items():
            if sha(ROOT / rel) != digest:
                raise RuntimeError("Recorded result artifact changed: " + rel)
        metadata["status"] = "VERIFIED_11_PAIRED_CASES_CRC_AND_ALL_COUNTERS_EQUAL_REFERENCE"
        metadata["completed"] = stamp()
        print("[VERIFIED] 22 fresh simulations; suite numeric CRCs, all counters, input hashes agree", flush=True)
    except BaseException as exc:
        metadata["status"] = "STOPPED_REQUIRES_INSPECTION"
        metadata["error"] = str(exc)
        raise
    finally:
        write_json(receipt, metadata)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
