"""Prepare or run paired CoreMark standard-size timed RTL simulations.

These are RAM32KiB simulations, not measurements of the 16KiB chip and not an
EEMBC certification. Existing algorithms, firmware, TBs and libraries are read
only. Only the final upstream iterate interval is used for throughput.
"""
from __future__ import annotations
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts/fpga"))
from coremark_crc_gate import known_crcs
from snapshot_fields import parse as parse_snapshot, invariants
from board_common import free_mb

VSIM = Path("C:/questasim64_2024.1/win64/vsim.exe")
SYSTEM_INI = VSIM.parent.parent / "modelsim.ini"
ERROR = re.compile(r"\*\*\s+(?:Error|Fatal)|\[FAIL\]|FAIL_TIMEOUT|FORMAT_ERROR|Errors:\s*[1-9]\d*", re.I)
MIN_FREE_MB = 6000

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def once(text, pattern, label):
    matches = re.findall(pattern, text, re.M)
    if len(matches) != 1: raise ValueError("Expected exactly one " + label)
    return matches[0]

def validate_case(log, uart, profile, cfg, build, max_cycles):
    text = Path(log).read_text(encoding="utf-8", errors="strict")
    data = Path(uart).read_bytes()
    serial = data.decode("ascii").replace("\r\n", "\n").replace("\r", "\n")
    if ERROR.search(text) or re.search(r"ERROR|Errors detected|Cannot validate|FORMAT_ERROR", serial):
        raise ValueError("Native/firmware error reported")
    actual = tuple(map(int, once(text,
        r"COREMARK_STANDARD_PROFILE cfg=(\d+) fast=(\d+) i_lines=(\d+) d_lines=(\d+) line_words=(\d+) l0=(\d+) predictor=(\d+) imem=(\d+) dmem=(\d+)\s*$", "elaborated profile")))
    if actual != (cfg, 0, 256, 256, 4, 8, 1, 4096, 4096): raise ValueError("Wrong actual RTL profile")
    finished, byte_count = map(int, once(text,
        r"COREMARK_STANDARD_FINISH cycles=(\d+) uart_bytes=(\d+)\s*$", "bounded simulation finish"))
    if not 0 < finished < max_cycles < 2**31 or byte_count != len(data):
        raise ValueError("Unbounded simulation, timeout, or incomplete UART bytes")
    if len(re.findall(r"BENCHMARK_SNAPSHOT ", text)) != 1: raise ValueError("Ambiguous snapshot")
    if int(once(text, r"BENCHMARK_SNAPSHOT benchmark=coremark config=(\d+) ", "snapshot context")) != cfg:
        raise ValueError("Wrong snapshot config")
    counters, err = parse_snapshot(Path(log))
    if err or not counters or invariants(counters) or counters["minstret"] <= 0:
        raise ValueError("Invalid complete-program counter frame: " + err)
    seed = int(once(serial, r"^seedcrc\s*:\s*0x([0-9a-fA-F]{4})\s*$", "seedcrc"), 16)
    expected_seed = 0xe9f5 if profile == "performance" else 0x18f2
    if seed != expected_seed: raise ValueError("Wrong standard seeds")
    reference = known_crcs(ROOT / "sw/coremark/core_main.c")[seed]
    crc_values = {}
    for key in ("crclist", "crcmatrix", "crcstate", "crcfinal"):
        crc_values[key] = int(once(serial, r"^\[0\]" + key + r"\s*:\s*0x([0-9a-fA-F]{4})\s*$", key), 16)
    if any(crc_values[k] != v for k, v in reference.items()): raise ValueError("Numeric suite CRC mismatch")
    if re.search(r"^\[[1-9]\d*\]crc", serial, re.M): raise ValueError("Unexpected extra context")
    if int(once(serial, r"^CoreMark Size\s*:\s*(\d+)\s*$", "algorithm size")) != 666:
        raise ValueError("Not standard 2000-byte total workload")
    ticks = int(once(serial, r"^Total ticks\s*:\s*(\d+)\s*$", "ticks"))
    iterations = int(once(serial, r"^Iterations\s*:\s*(\d+)\s*$", "iterations"))
    if ticks < 500000000 or ticks > finished or iterations <= 0:
        raise ValueError("Final main-loop interval is shorter than 10 seconds or impossible")
    if once(serial, r"^Compiler version\s*:\s*(.+?)\s*$", "compiler version") != "GCC" + build["compiler_macro_version"]:
        raise ValueError("Wrong compiler version metadata")
    if once(serial, r"^Compiler flags\s*:\s*(.+?)\s*$", "compiler flags") != " ".join(build["compiler_flags"]):
        raise ValueError("Wrong compile flag metadata")
    if once(serial, r"^Memory location\s*:\s*(.+?)\s*$", "memory method") != "STATIC":
        raise ValueError("Wrong memory method")
    count, error, opened = map(int, once(serial,
        r"^COREMARK_TIMER clock_hz=50000000 bits=32 samples=(\d+) error=(\d+) open=(\d+)\s*$", "CSR timer profile"))
    intervals = re.findall(r"^COREMARK_INTERVAL index=(\d+) start=0x([0-9a-fA-F]{8}) stop=0x([0-9a-fA-F]{8}) ticks=(\d+)\s*$", serial, re.M)
    if not 1 <= count <= 16 or error or opened or len(intervals) != count: raise ValueError("Invalid timer sequence")
    parsed = []
    for i, (index, start, stop, elapsed) in enumerate(intervals):
        a, b, dt = int(start, 16), int(stop, 16), int(elapsed)
        if int(index) != i or ((b - a) & 0xffffffff) != dt or not 0 < dt <= finished:
            raise ValueError("Invalid CSR interval/wrap handling")
        parsed.append({"index": i, "start": a, "stop": b, "ticks": dt})
    if parsed[-1]["ticks"] != ticks: raise ValueError("Final iterate interval differs from reported ticks")
    if serial.count("Correct operation validated. See README.md for run and reporting rules.") != 1:
        raise ValueError("No unambiguous upstream validation success")
    if serial.count("COREMARK_STANDARD_BEGIN") != 1 or serial.count("BENCH=coremark") != 1 or serial.count("RESULT=PASS") != 1:
        raise ValueError("No complete firmware envelope")
    seconds = Decimal(ticks) / Decimal(50000000)
    shown = Decimal(once(serial, r"^Total time \(secs\)\s*:\s*(\d+(?:\.\d+)?)\s*$", "seconds"))
    score = Decimal(iterations) * Decimal(50000000) / Decimal(ticks)
    rate = Decimal(once(serial, r"^Iterations/Sec\s*:\s*(\d+(?:\.\d+)?)\s*$", "throughput"))
    if build["has_float"]:
        if abs(shown - seconds) > Decimal("0.000002") or abs(rate - score) > Decimal("0.000002"):
            raise ValueError("Printed floating timing/rate disagrees with exact integer ticks")
    elif shown != int(ticks / 50000000) or rate != iterations // int(shown):
        raise ValueError("Integer port's printed seconds/rate disagree with upstream rounding")
    score_lines = re.findall(r"^CoreMark 1\.0 : (\d+\.\d+) / (.+)\s*$", serial, re.M)
    if profile == "performance" and build["has_float"]:
        if len(score_lines) != 1 or abs(Decimal(score_lines[0][0]) - score) > Decimal("0.000002"):
            raise ValueError("Missing/wrong upstream performance result")
    elif score_lines: raise ValueError("No upstream performance line expected with integer time or validation profile")
    return {"profile": profile, "configuration": cfg, "timer_ticks": ticks, "iterations": iterations,
            "seconds_exact": str(seconds), "iterations_per_second_exact": str(score),
            "coremark_per_mhz_exact": str(score / Decimal(50)) if profile == "performance" else None,
            "seedcrc": seed, "crcs": crc_values, "timer_intervals": parsed,
            "whole_program_snapshot": counters, "completion_cycles": finished,
            "ram_bytes": 32768, "minimum_duration_pass": True, "numeric_crc_pass": True,
            "timing_window": "upstream_final_iterate_only", "certified": False}

def wrapper():
    source = (HERE / "coremark_uart_observer.sv").read_text()
    source = source.replace("module tb_coremark_crc_audit #(", "module tb_coremark_standard #(")
    source = source.replace("    parameter integer DMEM_DEPTH = 4096\n", "    parameter integer DMEM_DEPTH = 4096,\n    parameter MEMFILE = \"unused.hex\"\n")
    source = source.replace('.MEMFILE("fw/coremark.hex")', ".MEMFILE(MEMFILE)")
    source = source.replace('    integer uart_fd = 0;',
        '    initial $display("COREMARK_STANDARD_PROFILE cfg=%0d fast=%0d i_lines=%0d d_lines=%0d line_words=%0d l0=%0d predictor=%0d imem=%0d dmem=%0d",\n'
        '        bench.CACHE_CONFIG, bench.CACHE_FAST_HIT, bench.ICACHE_LINE_COUNT, bench.DCACHE_LINE_COUNT,\n'
        '        bench.CACHE_LINE_WORDS, bench.L0_ENTRIES, bench.BRANCH_PREDICT_ENABLE, bench.IMEM_DEPTH, bench.DMEM_DEPTH);\n'
        '    integer uart_fd = 0;')
    source = source.replace('COREMARK_UART_CAPTURE bytes=%0d method=accepted_apb_txdata_writes", uart_bytes',
        'COREMARK_STANDARD_FINISH cycles=%0d uart_bytes=%0d", bench.cycles, uart_bytes')
    if any(x in source for x in ("tb_coremark_crc_audit", 'fw/coremark.hex', 'COREMARK_UART_CAPTURE')):
        raise ValueError("Wrapper substitution failed")
    return source

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--build", required=True, help="Isolated build.json")
    ap.add_argument("--output", required=True)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--configs", default="0,1,2,3")
    ap.add_argument("--max-cycles", type=int, default=2000000000)
    args = ap.parse_args()
    build_path = Path(args.build).resolve(); out = Path(args.output).resolve()
    if not build_path.is_relative_to(ROOT / "results") or not out.is_relative_to(ROOT / "results"):
        ap.error("Build/output must be inside research results")
    cfgs = [int(x) for x in args.configs.split(",")]
    if set(cfgs) != {0, 1, 2, 3} or len(cfgs) != 4: ap.error("Four canonical cache configurations required")
    if not 500000000 < args.max_cycles < 2**31: ap.error("Bound must permit >=10sec and fit frozen TB signed int")
    build = json.loads(build_path.read_text())
    if build["status"] != "BUILT_NOT_RUN_NOT_A_SCORE" or set(build["profiles"]) != {"performance", "validation"}:
        raise RuntimeError("Incomplete firmware build")
    manifest = json.loads((ROOT / "results/rtl_manifest.json").read_text())
    frozen = dict(manifest["files"])
    if manifest["count"] != len(frozen): raise RuntimeError("Manifest membership mismatch")
    frozen.update(build["inputs"])
    for p in build["profiles"].values(): frozen.update(p["artifacts"])
    for p in (build_path, Path(__file__), HERE / "coremark_uart_observer.sv", HERE / "coremark_crc_gate.py",
              ROOT / "tb/compile_active_design.do", ROOT / "tb/benchmark_snapshot_tb.sv", ROOT / "scripts/snapshot_fields.py",
              ROOT / "scripts/fpga/board_common.py", ROOT / "results/rtl_manifest.json"):
        frozen[p.relative_to(ROOT).as_posix()] = sha(p)
    def check():
        changed = [p for p, h in frozen.items() if sha(ROOT / p) != h]
        if changed: raise RuntimeError("Frozen input changed: " + ", ".join(changed))
    check(); out.mkdir(parents=True, exist_ok=False)
    receipt = out / "receipt.json"
    record = {"status": "PREPARED_NOT_EXECUTED", "inputs": frozen, "build": str(build_path),
              "rtl_manifest": manifest["aggregate"], "profiles": ["performance", "validation"],
              "configurations": cfgs, "passes": 2, "cases_per_pass": 8, "ram_bytes": 32768,
              "max_cycles": args.max_cycles, "minimum_final_iterate_ticks": 500000000,
              "clock_hz": 50000000, "minimum_free_windows_mb": MIN_FREE_MB,
              "physical_chip_execution": False, "EEMBC_certification": False,
              "measurement": False, "commands": [], "cases": []}
    def save(): receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="ascii")
    (out / "observer.sv").write_text(wrapper(), encoding="ascii")
    save()
    if not args.run: print(receipt); return 0
    record["status"] = "IN_PROGRESS_NOT_A_RESULT"; save()
    try:
        def native(command, name):
            check()
            if (out / "abort_before_next_native").exists(): raise RuntimeError("Cooperative stop before next tool")
            if free_mb() < MIN_FREE_MB: raise RuntimeError("Insufficient RAM; no next native tool started")
            log = out / (name + ".stdout.log")
            record["commands"].append({"command": command, "output": str(log), "returncode": None}); save()
            with log.open("xb") as f: rc = subprocess.run(command, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT).returncode
            record["commands"][-1]["returncode"] = rc; record["commands"][-1]["sha256"] = sha(log); save()
            if rc or ERROR.search(log.read_text(encoding="utf-8", errors="strict")):
                raise RuntimeError("Native tool failed: " + name)
            check(); return log
        results = {}
        for number in (1, 2):
            library = "coremark_standard_p" + str(number); libdir = out / library
            ini = out / f"modelsim_p{number}.ini"
            ini.write_text(f"[Library]\n{library} = {libdir.as_posix()}\nothers = {SYSTEM_INI.as_posix()}\n", encoding="ascii")
            old = (ROOT / "tb/compile_active_design.do").read_text()
            block = "if {[file exists work]} {\n    vdel -lib work -all\n}\nvlib work"
            if old.count(block) != 1: raise RuntimeError("Unexpected compile library block")
            script = out / f"compile_p{number}.do"
            text = old.replace(block, f"vlib {{{libdir.as_posix()}}}").replace("vlog -sv", f"vlog -work {library} -sv")
            text += f"\nvlog -work {library} -sv {{{(out / 'observer.sv').as_posix()}}}\necho {{COREMARK_STANDARD_COMPILED}}\n"
            if "vdel" in text or re.search(r"^vlog(?! -work " + library + r"\b)", text, re.M):
                raise RuntimeError("Private compile script touches another library")
            script.write_text(text, encoding="ascii")
            common = [str(VSIM), "-c", "-modelsimini", str(ini)]
            compiled = native([*common, "-l", str(out / f"compile_p{number}.transcript.log"), "-wlf", str(out / f"compile_p{number}.wlf"),
                               "-do", f"do {{{script.as_posix()}}}; quit -f"], f"compile_p{number}")
            if "COREMARK_STANDARD_COMPILED" not in compiled.read_text(): raise RuntimeError("Incomplete compilation")
            for profile in ("performance", "validation"):
                fw = build_path.parent / profile / "coremark.hex"
                for cfg in cfgs:
                    suffix = f"p{number}_{profile}_c{cfg}"; uart = out / (suffix + ".uart.txt")
                    do = ("onerror {quit -code 1 -f}; vsim -onfinish stop "
                          f"-gCACHE_CONFIG={cfg} -gCACHE_FAST_HIT=0 -gICACHE_LINE_COUNT=256 -gDCACHE_LINE_COUNT=256 "
                          f"-gL0_ENTRIES=8 -gIMEM_DEPTH=4096 -gDMEM_DEPTH=4096 -gMEMFILE={{{fw.as_posix()}}} "
                          f"{library}.tb_coremark_standard +benchmark=coremark +max_cycles={args.max_cycles} "
                          f"{{+coremark_uart={uart.as_posix()}}}; run -all; quit -f")
                    log = native([*common, "-l", str(out / (suffix + ".transcript.log")), "-wlf", str(out / (suffix + ".wlf")), "-do", do], suffix)
                    value = validate_case(log, uart, profile, cfg, build, args.max_cycles)
                    record["cases"].append({"pass": number, **value, "log": str(log), "uart": str(uart),
                                            "log_sha256": sha(log), "uart_sha256": sha(uart)})
                    key = profile, cfg
                    if number == 1: results[key] = value
                    elif results.get(key) != value: raise RuntimeError("Independent passes differ field by field")
                    save()
        check()
        if len(record["cases"]) != 16: raise RuntimeError("Incomplete paired matrix")
        record["status"] = "VERIFIED_PAIRED_TIMED_COREMARK_RAM32K_SIMULATION_NOT_CERTIFICATION"
        record["measurement"] = True; save(); return 0
    except BaseException as exc:
        record["status"] = "FAILED_NOT_A_PAIRED_RESULT"; record["error"] = str(exc); save(); raise

if __name__ == "__main__": raise SystemExit(main())
