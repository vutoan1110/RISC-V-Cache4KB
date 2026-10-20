"""Independently reread a completed 92-point, two-pass CoreMark CRC sweep.

No simulator or runner is imported or invoked. The point set, raw counter
parser, invariants, UART CRC parser and CSV rows are derived here. A receipt is
written only after all checks pass; existing evidence is never rewritten.
CoreMark uses 32 KiB simulation RAM and one iteration, not an official score.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
STATUS = "VERIFIED_92_PAIRED_SWEEP_POINTS_CRC_AND_ALL_COUNTERS_EQUAL_REFERENCE"
FIELDS = (
    "mcycle", "minstret", "cycle_retire", "load_use", "i_wait", "d_wait",
    "control", "trap", "mmio", "fill_drain", "other", "i_access", "i_main",
    "i_victim", "i_miss", "d_read", "d_write", "d_main", "d_victim", "d_miss",
    "branches", "taken", "not_taken", "predictions", "correct", "mispredict",
    "axi_read", "axi_write", "i_hit_ev", "i_miss_ev", "d_rd_hit", "d_rd_miss",
    "d_wr_hit", "d_wr_miss", "control_ev", "trap_ev", "mcause", "snap_seq",
    "result_pass", "invariant_pass",
)
PARAMETERS = ("cfg", "lines", "line_words", "victim_entries", "fast_hit")
PROFILE = (*PARAMETERS, "d_lines", "imem_words", "dmem_words", "l0_entries", "predictor")
CRC_FIELDS = ("seedcrc", "crclist", "crcmatrix", "crcstate", "crcfinal",
              "size_per_algorithm", "iterations", "duration_seconds", "crc_pass",
              "official_score", "validation")
RESULT_HEADER = ("point", *PARAMETERS, "cap_bytes", *FIELDS, *CRC_FIELDS)
REF_HEADER = ("point", "org", "cfg", "cap_bytes", "line_bytes", "lines", "vc", "workload", *FIELDS)
REFERENCE_PATHS = tuple(f"results/m2/sweep_{fast}p{n}.csv" for fast in ("", "fast_") for n in (1, 2))
EXTRAS = ("results/rtl_manifest.json", "tb/compile_active_design.do", "scripts/snapshot_fields.py",
    "scripts/fpga/board_common.py", "sw/coremark/core_main.c", "sw/coremark/coremark.h",
    "sw/coremark/core_portme.h", "sw/coremark/core_portme.c", "sw/coremark/build_hex.sh",
    "scripts/verification/coremark_uart_observer.sv", "scripts/verification/coremark_crc_gate.py",
    "scripts/verification/run_coremark_crc.py", "scripts/verification/run_coremark_sweep_crc.py",
    "scripts/m2/run_m2_sweep.py", *REFERENCE_PATHS)
VSIM = Path("C:/questasim64_2024.1/win64/vsim.exe")
SYSTEM_INI = Path("C:/questasim64_2024.1/modelsim.ini")
ERROR = re.compile(r"^\s*#?\s*(?:\*\*\s+(?:Fatal|Error)(?::|\b)|\[FAIL\]|Errors:\s*[1-9]\d*)", re.M | re.I)
MAX_TEXT_BYTES = 16 * 1024 * 1024


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def text(path, encoding="utf-8"):
    require(0 < path.stat().st_size <= MAX_TEXT_BYTES, "Empty/oversized evidence: " + str(path))
    return path.read_text(encoding=encoding, errors="strict")


def safe_path(root, relative):
    require(isinstance(relative, str) and relative and "\\" not in relative,
            "Invalid relative evidence path")
    p = Path(relative)
    require(not p.is_absolute() and ".." not in p.parts and p.as_posix() == relative,
            "Evidence path escapes/cannot be canonical: " + relative)
    resolved = (root / p).resolve()
    require(resolved.is_relative_to(root.resolve()) and resolved.is_file(), "Missing/outside evidence: " + relative)
    return resolved


def read_csv(path, header):
    require(path.stat().st_size <= MAX_TEXT_BYTES, "Oversized CSV")
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        require(tuple(reader.fieldnames or ()) == tuple(header), "Wrong/incomplete/duplicate CSV header: " + str(path))
        rows = list(reader)
    require(rows and all(None not in r and all(isinstance(v, str) and v.strip() for v in r.values()) for r in rows),
            "Incomplete/blank CSV row: " + str(path))
    return rows


def grid():
    points = {}
    def add(org, cfg, cap, line, vc=0):
        name = f"{org}_{cap}B_L{line}"
        require(name not in points, "Duplicate independent grid point")
        points[name] = dict(point=name, org=org, cfg=cfg, cap_bytes=cap,
                            line_bytes=line, lines=cap // line, line_words=line // 4,
                            vc=vc, victim_entries=vc or 4)
    orgs = (("DM", 0), ("DM_DSE", 3), ("SA2", 1), ("VC4", 2), ("SA4", 4))
    for cap in (256, 512, 1024, 2048, 4096, 8192):
        for org, cfg in orgs:
            add(org, cfg, cap, 16, 4 if cfg == 2 else 0)
    for cap in (1024, 4096):
        for line in (8, 32):
            for org, cfg in orgs[1:]:
                add(org, cfg, cap, line, 4 if cfg == 2 else 0)
        for vc in (2, 8):
            add(f"VC{vc}", 2, cap, 16, vc)
    require(len(points) == 50, "Independent grid cardinality")
    del points["SA4_256B_L16"]
    return {(name, fast): {**p, "fast_hit": fast}
            for fast in (0, 1) for name, p in sorted(points.items()) if not fast or p["cfg"] != 0}


def counters_valid(r):
    require(set(r) == set(FIELDS) and all(type(v) is int and v >= 0 for v in r.values()), "Invalid complete counter schema")
    equations = (
        (r["mcycle"], sum(r[k] for k in FIELDS[2:11])),
        (r["i_access"], r["i_main"] + r["i_victim"] + r["i_miss"]),
        (r["d_read"] + r["d_write"], r["d_main"] + r["d_victim"] + r["d_miss"]),
        (r["i_access"], r["i_hit_ev"] + r["i_miss_ev"]),
        (r["d_read"], r["d_rd_hit"] + r["d_rd_miss"]),
        (r["d_write"], r["d_wr_hit"] + r["d_wr_miss"]),
        (r["branches"], r["taken"] + r["not_taken"]),
        (r["predictions"], r["correct"] + r["mispredict"]),
    )
    require(all(a == b for a, b in equations), "Counter invariant fails")
    require(r["result_pass"] == r["invariant_pass"] == 1 and r["minstret"] > 0, "Counter result/invariant/minstret gate fails")


def parse_counters(values):
    require(all(re.fullmatch(r"\d+", values[k]) for k in FIELDS), "Non-numeric/negative counter")
    result = {k: int(values[k]) for k in FIELDS}
    counters_valid(result)
    return result


def baseline(root, points):
    result = {}
    for fast in (0, 1):
        pair = []
        for n in (1, 2):
            path = root / f"results/m2/sweep_{'fast_' if fast else ''}p{n}.csv"
            index = {}
            for row in read_csv(path, REF_HEADER):
                if row["workload"] != "coremark":
                    continue
                key = (row["point"], fast)
                require(key in points and key not in index, "Unknown/duplicate historical CoreMark point")
                p = points[key]
                require(all(row[k] == str(p[k]) for k in REF_HEADER[:7]), "Historical metadata differs from independent grid")
                index[key] = parse_counters(row)
            require(set(index) == {k for k in points if k[1] == fast}, "Historical sweep CoreMark set incomplete")
            pair.append(index)
        require(pair[0] == pair[1], "Historical independent counter passes differ")
        result.update(pair[0])
    return result


def source_crcs(source):
    arrays = {}
    for name in ("list", "matrix", "state"):
        matches = re.findall(r"\b" + name + r"_known_crc\s*\[\s*\]\s*=\s*\{([^}]+)\}", source)
        require(len(matches) == 1, "Ambiguous/missing source-known CRC array")
        arrays[name] = [int(x, 16) for x in re.findall(r"0x([\da-fA-F]+)", matches[0])]
        require(len(arrays[name]) == 5, "Source CRC table must have five profiles")
    mappings = re.findall(r"case\s+(0x[\da-fA-F]+)\s*:\s*(?:/\*.*?\*/\s*)?known_id\s*=\s*(\d+)\s*;", source, re.S)
    require(len(mappings) == 5 and len({int(s, 16) for s, _ in mappings}) == 5, "Source seed mapping incomplete/ambiguous")
    selected = [int(i) for s, i in mappings if int(s, 16) == 0xe9f5]
    require(len(selected) == 1 and 0 <= selected[0] < 5, "Canonical seed missing from source")
    return {"crc" + k: v[selected[0]] for k, v in arrays.items()}


def once(txt, pattern, label):
    matches = re.findall(pattern, txt, re.M)
    require(len(matches) == 1, "Missing/duplicate " + label)
    return matches[0]


def parse_uart(data, expected):
    uart = data.decode("ascii").replace("\r\n", "\n").replace("\r", "\n")
    result = {"seedcrc": int(once(uart, r"^seedcrc\s*:\s*0x([\da-fA-F]{4})\s*$", "seedcrc"), 16)}
    for key in ("crclist", "crcmatrix", "crcstate", "crcfinal"):
        result[key] = int(once(uart, r"^\[0\]" + key + r"\s*:\s*0x([\da-fA-F]{4})\s*$", key), 16)
    result.update(size_per_algorithm=int(once(uart, r"^CoreMark Size\s*:\s*(\d+)\s*$", "size")),
                  iterations=int(once(uart, r"^Iterations\s*:\s*(\d+)\s*$", "iterations")),
                  duration_seconds=int(once(uart, r"^Total time \(secs\)\s*:\s*(\d+)\s*$", "duration")))
    require(result["seedcrc"] == 0xe9f5 and (result["size_per_algorithm"], result["iterations"], result["duration_seconds"]) == (666, 1, 0), "Wrong canonical short-run UART profile")
    require(all(result[k] == v for k, v in expected.items()) and result["crcfinal"] == result["crclist"], "UART numeric CRC differs from source")
    require(not re.search(r"^\[[1-9]\d*\]crc", uart, re.M), "Unexpected UART context")
    errors = [line.strip() for line in uart.splitlines() if "ERROR" in line.upper()]
    require(errors == ["ERROR! Must execute for at least 10 secs for a valid result!", "Errors detected"], "Unexpected/missing UART errors")
    require("2K performance run parameters for coremark." in uart and "Cannot validate operation" not in uart and "Correct operation validated" not in uart, "Unexpected suite validation profile")
    require(once(uart, r"^RESULT=(\w+)\s*$", "firmware RESULT") == "PASS"
            and once(uart, r"^VERIFY_CODE=(0x[\da-fA-F]+)\s*$", "VERIFY_CODE") == "0x00000000"
            and len(re.findall(r"^DONE\s*$", uart, re.M)) == 1, "Firmware snapshot report incomplete/failed")
    return {**result, "crc_pass": 1, "official_score": 0, "validation": "suite_numeric_crc_short_simulation"}


def check_log(log):
    require(log.startswith("Reading pref.tcl\n") or log.startswith("Reading pref.tcl\r\n"), "Unexpected simulator init header")
    require(not ERROR.search(log), "Simulator reported Fatal/Error/FAIL")
    require(re.search(r"^#\s+2024\.1\s*$", log, re.M), "Missing simulator version")
    require(re.search(r"^#\s+onerror \{quit -code 1 -f\}\s*$", log, re.M), "Missing fail-closed Tcl header")
    require(re.search(r"^#\s+Start time:", log, re.M) and re.search(r"^#\s+End time:", log, re.M), "Incomplete simulator lifetime log")
    require(re.search(r"^#\s+Errors: 0, Warnings: \d+\s*$", log, re.M), "Missing clean simulator completion")
    require(re.search(r"^#\s+quit -f\s*$", log, re.M), "Missing simulator quit")


def compile_commands(script):
    # Tcl continuation folding is restricted to the frozen explicit file-list
    # recipe. Braces only quote paths, so remove them for Questa's command echo.
    logical = script.replace("\\\n", " ")
    return [" ".join(line.replace("{", "").replace("}", "").split())
            for line in logical.splitlines() if re.match(r"\s*vlog\b", line)]


def parse_case(log, data, p, expected_crc):
    check_log(log)
    profile = once(log, r"^#\s+COREMARK_SWEEP_PROFILE ([^\r\n]+)$", "elaborated profile")
    expect_profile = dict((k, p[k]) for k in PARAMETERS)
    expect_profile.update(d_lines=p["lines"], imem_words=4096, dmem_words=4096, l0_entries=8, predictor=1)
    require(profile.strip() == " ".join(f"{k}={expect_profile[k]}" for k in PROFILE), "Actual elaborated parameters differ")
    frame = once(log, r"^#\s+BENCHMARK_SNAPSHOT ([^\r\n]+)$", "atomic snapshot")
    tokens = frame.split()
    require(all(t.count("=") == 1 for t in tokens), "Malformed snapshot token")
    pairs = [t.split("=") for t in tokens]
    require(len({k for k, _ in pairs}) == len(pairs), "Duplicate snapshot field")
    values = dict(pairs)
    require(set(values) == {"benchmark", "config", *FIELDS} and values["benchmark"] == "coremark" and values["config"] == str(p["cfg"]), "Wrong/incomplete snapshot context")
    require(len(re.findall(r"^#\s+\[PASS\] Atomic benchmark snapshot\s*$", log, re.M)) == 1, "Missing/duplicate snapshot PASS")
    counters = parse_counters(values)
    count = int(once(log, r"^#\s+COREMARK_UART_CAPTURE bytes=(\d+) method=accepted_apb_txdata_writes\s*$", "UART capture"))
    require(count == len(data) and 0 < count < MAX_TEXT_BYTES, "UART byte count incomplete")
    crc = parse_uart(data, expected_crc)
    # UART contains a firmware copy of the same latched snapshot, independently
    # checked against the testbench frame as well as both historical CSVs.
    uart = data.decode("ascii").replace("\r", "")
    uart_map = dict(MCYCLE="mcycle", MINSTRET="minstret", I_ACCESS="i_access", I_MAIN_HIT="i_main",
        I_VICTIM_HIT="i_victim", I_TRUE_MISS="i_miss", D_MAIN_HIT="d_main", D_VICTIM_HIT="d_victim",
        D_TRUE_MISS="d_miss", I_WAIT="i_wait", D_WAIT="d_wait", LOAD_USE="load_use", CONTROL_REDIRECT="control",
        TRAP_REDIRECT="trap", MMIO_WAIT="mmio", PIPE_FILL_DRAIN="fill_drain", OTHER="other", BRANCH="branches",
        BRANCH_TAKEN="taken", BRANCH_NOT_TAKEN="not_taken", PRED="predictions", CORRECT="correct",
        MISPRED="mispredict", AXI_READ="axi_read", AXI_WRITE="axi_write")
    for key, counter in uart_map.items():
        require(int(once(uart, r"^" + key + r"=0x([\da-fA-F]{8})\s*$", key), 16) == counters[counter], "UART/snapshot counter differs: " + key)
    require(int(once(uart, r"^D_ACCESS=0x([\da-fA-F]{8})\s*$", "D_ACCESS"), 16) == counters["d_read"] + counters["d_write"], "UART D_ACCESS differs")
    return {k: p[k] for k in RESULT_HEADER[:7]} | counters | crc


def expected_wrapper(original):
    # Exact expected transformation from the frozen passive observer. This
    # module never imports the live sweep runner or its validation functions.
    a = "    parameter integer L0_ENTRIES = 8,"
    b = "        .L0_ENTRIES(L0_ENTRIES), .IMEM_DEPTH(IMEM_DEPTH), .DMEM_DEPTH(DMEM_DEPTH),"
    require(original.count("module tb_coremark_crc_audit #(") == original.count(a) == original.count(b) == original.count("    integer uart_fd = 0;") == 1, "Original observer anchors ambiguous")
    return original.replace("module tb_coremark_crc_audit #(", "module tb_coremark_sweep_crc_audit #(").replace(a,
        "    parameter integer CACHE_LINE_WORDS = 4,\n    parameter integer VICTIM_ENTRIES = 4,\n" + a).replace(b,
        "        .CACHE_LINE_WORDS(CACHE_LINE_WORDS), .VICTIM_ENTRIES(VICTIM_ENTRIES),\n" + b).replace("    integer uart_fd = 0;",
        '    initial $display("COREMARK_SWEEP_PROFILE cfg=%0d lines=%0d line_words=%0d victim_entries=%0d fast_hit=%0d d_lines=%0d imem_words=%0d dmem_words=%0d l0_entries=%0d predictor=%0d",\n'
        "        bench.CACHE_CONFIG, bench.ICACHE_LINE_COUNT, bench.CACHE_LINE_WORDS,\n"
        "        bench.VICTIM_ENTRIES, bench.CACHE_FAST_HIT, bench.DCACHE_LINE_COUNT,\n"
        "        bench.IMEM_DEPTH, bench.DMEM_DEPTH, bench.L0_ENTRIES, bench.BRANCH_PREDICT_ENABLE);\n\n    integer uart_fd = 0;")


def verify(root, output):
    receipt_path = output / "verification.json"
    receipt_sha = sha(receipt_path)
    state = json.loads(text(receipt_path))
    require(state.get("status") == STATUS, "Sweep is not complete: " + str(state.get("status")))
    require(state.get("cases_per_pass") == 92 and state.get("ram_bytes") == 32768
            and state.get("window") == "complete_coremark_main" and state.get("official_score") is False
            and state.get("method") == "fresh_single_lane_simulations_passive_apb_uart_source_numeric_crc", "Wrong measurement scope")
    require(datetime.fromisoformat(state["completed"]) >= datetime.fromisoformat(state["started"]), "Invalid execution time interval")
    require(state.get("excluded_point", {}).get("point") == "SA4_256B_L16", "Wrong excluded unsupported point")
    manifest = json.loads(text(root / "results/rtl_manifest.json"))
    files = manifest["files"]
    require(len(files) == manifest["count"] == 227 and state["rtl_id"] == manifest["aggregate"], "Wrong current RTL manifest")
    require(hashlib.sha256("".join(p + files[p] for p in sorted(files)).encode()).hexdigest() == manifest["aggregate"], "Manifest aggregate invalid")
    inputs = state["inputs"]
    require(set(inputs) == set(files) | set(EXTRAS), "Frozen input hash inventory incomplete/unexpected")
    require(all(inputs[k] == v for k, v in files.items()), "Input manifest hashes differ")
    for rel, digest in inputs.items():
        require(re.fullmatch(r"[0-9a-f]{64}", digest) and sha(safe_path(root, rel)) == digest, "Frozen source SHA differs: " + rel)
    points = grid()
    require(len(points) == 92, "Independent paired point count")
    expected = baseline(root, points)
    crcs = source_crcs(text(root / "sw/coremark/core_main.c"))
    generated = output / "coremark_sweep_observer.sv"
    require(text(generated) == expected_wrapper(text(root / "scripts/verification/coremark_uart_observer.sv")), "Generated observer source/forwarding differs")
    require(sha(generated) == state["generated_observer_sha256"], "Generated observer SHA differs")
    artifacts = {generated.relative_to(root).as_posix()}
    require(len(state.get("compilations", [])) == 2, "Two independent compilations missing")
    library_locations = [(output / f"coremark_crc_p{n}").resolve() for n in (1, 2)]
    require(library_locations[0] != library_locations[1]
            and all(p.parent == output.resolve() for p in library_locations), "Private libraries alias/reuse another directory")
    for number, compilation in enumerate(state["compilations"], 1):
        lib = f"coremark_crc_p{number}"
        libdir = output / lib
        ini = output / f"modelsim_p{number}.ini"
        script = output / f"compile_p{number}.do"
        log = output / f"compile_p{number}.log"
        sweep_log = output / f"compile_sweep_p{number}.log"
        require(libdir.is_dir() and any(libdir.iterdir()), "Missing private compiled library: " + lib)
        require(compilation["pass"] == number and compilation["library"] == lib and compilation["modelsim_ini"] == str(ini), "Private pass library mapping differs")
        require(text(ini) == f"[Library]\n{lib} = {libdir.as_posix()}\nothers = {SYSTEM_INI.as_posix()}\n", "Private INI mapping differs")
        original = text(root / "tb/compile_active_design.do")
        block = "if {[file exists work]} {\n    vdel -lib work -all\n}\nvlib work"
        require(original.count(block) == 1, "Active compilation block ambiguous")
        expected_do = original.replace(block, f"vlib {{{libdir.as_posix()}}}").replace("vlog -sv", f"vlog -work {lib} -sv")
        expected_do += f"\nvlog -work {lib} -sv {{{(root / 'scripts/verification/coremark_uart_observer.sv').as_posix()}}}\necho {{[PASS] Passive CoreMark UART observer compiled}}\n"
        require(text(script) == expected_do, "Private compilation recipe differs")
        compile_text = text(log)
        check_log(compile_text)
        require(f"# do {{{script.as_posix()}}}" in compile_text and f"# vlib {{{libdir.as_posix()}}}" in compile_text and "# [PASS] Passive CoreMark UART observer compiled" in compile_text, "Private base compilation evidence missing")
        require(all(m == lib for m in re.findall(r"^#\s+vlog -work (\S+)", compile_text, re.M)), "Base compile used another library")
        compiler_invocations = compile_commands(expected_do)
        require(len(compiler_invocations) >= 2, "Private compilation lacks actual source invocations")
        for invocation in compiler_invocations:
            require(len(re.findall(r"^#\s+" + re.escape(invocation) + r"\s*$", compile_text, re.M)) >= 1,
                    "Compiler raw log lacks source invocation: " + invocation)
        require(len(re.findall(r"^#\s+Errors: 0, Warnings: \d+\s*$", compile_text, re.M)) >= len(compiler_invocations),
                "Compiler raw log lacks completion for every source invocation")
        wrapper_command = f"onerror {{quit -code 1 -f}}; vlog -work {lib} -sv {{{generated.as_posix()}}}; echo {{[PASS] Sweep passive observer compiled}}; quit -f"
        require(compilation["generated_wrapper_command"] == [str(VSIM), "-c", "-modelsimini", str(ini), "-do", wrapper_command]
                and type(compilation["generated_wrapper_returncode"]) is int and compilation["generated_wrapper_returncode"] == 0, "Wrapper compilation command/process failed")
        wrapper_log = text(sweep_log)
        check_log(wrapper_log)
        require(f"#  vlog -work {lib} -sv {{{generated.as_posix()}}}" in wrapper_log and "# [PASS] Sweep passive observer compiled" in wrapper_log and "# -- Compiling module tb_coremark_sweep_crc_audit" in wrapper_log, "Wrapper compile evidence missing")
        artifacts.update(p.relative_to(root).as_posix() for p in (ini, script, log, sweep_log))
    cases = state.get("cases", [])
    require(len(cases) == 184, "Expected 184 actual case records")
    observed = {}
    limits = set()
    for case in cases:
        number, name, fast = case["pass"], case["point"], case["fast_hit"]
        key = (number, name, fast)
        require(type(number) is int and number in (1, 2) and type(fast) is int and (name, fast) in points and key not in observed, "Unknown/duplicate sweep case membership")
        p = points[(name, fast)]
        require(case.get("crc_pass") is True and case.get("all_counters_equal_reference") is True
                and type(case.get("returncode")) is int and case["returncode"] == 0, "Case returncode or recorded gates fail")
        suffix = f"p{number}_{name.lower()}_fast{fast}"
        log, uart = output / f"{suffix}.log", output / f"{suffix}.uart.txt"
        require(case["log"] == log.relative_to(root).as_posix() and case["uart"] == uart.relative_to(root).as_posix(), "Case suffix/raw path differs")
        command = case["command"]
        require(len(command) == 6 and command[:5] == [str(VSIM), "-c", "-modelsimini", str(output / f"modelsim_p{number}.ini"), "-do"], "Simulator command/init mapping differs")
        limit = re.findall(r"\+max_cycles=(\d+)", command[5])
        require(len(limit) == 1 and int(limit[0]) > 0, "Missing/ambiguous simulation limit")
        limits.add(int(limit[0]))
        invocation = (f"vsim -onfinish stop -gCACHE_CONFIG={p['cfg']} -gCACHE_FAST_HIT={fast} -gICACHE_LINE_COUNT={p['lines']} "
            f"-gDCACHE_LINE_COUNT={p['lines']} -gCACHE_LINE_WORDS={p['line_words']} -gVICTIM_ENTRIES={p['victim_entries']} "
            f"coremark_crc_p{number}.tb_coremark_sweep_crc_audit +benchmark=coremark +max_cycles={limit[0]} +coremark_uart={uart.as_posix()}")
        require(command[5] == f"onerror {{quit -code 1 -f}}; {invocation}; run -all; quit -f", "Simulator parameters/command recipe differs")
        raw = text(log)
        require(len(re.findall(r"^#\s+" + re.escape(invocation) + r"\s*$", raw, re.M)) == 1, "Raw invocation differs from receipt")
        require(uart.stat().st_size <= MAX_TEXT_BYTES, "Oversized UART")
        row = parse_case(raw, uart.read_bytes(), p, crcs)
        require({k: row[k] for k in FIELDS} == expected[(name, fast)], "Fresh counters differ from both historical sweeps")
        observed[key] = row
        artifacts.update((case["log"], case["uart"]))
    require(set(observed) == {(n, *k) for n in (1, 2) for k in points} and len(limits) == 1, "Missing independent pair/inconsistent simulation limits")
    for number in (1, 2):
        result = output / f"results_p{number}.csv"
        rows = read_csv(result, RESULT_HEADER)
        index = {}
        for row in rows:
            require(re.fullmatch(r"[01]", row["fast_hit"]), "Invalid CSV fast flag")
            key = (number, row["point"], int(row["fast_hit"]))
            require(key in observed and key not in index, "Duplicate/unknown CSV result row")
            require(row == {k: str(v) for k, v in observed[key].items()}, "CSV field differs from independent raw parse")
            index[key] = row
        require(set(index) == {k for k in observed if k[0] == number}, "CSV complete point set differs")
        artifacts.add(result.relative_to(root).as_posix())
    require(all(observed[(1, *k)] == observed[(2, *k)] for k in points), "Fresh independent raw passes differ")
    require(set(state["artifacts"]) == artifacts, "Artifact SHA inventory incomplete/unexpected")
    for rel, digest in state["artifacts"].items():
        require(re.fullmatch(r"[0-9a-f]{64}", digest) and sha(safe_path(root, rel)) == digest, "Output artifact SHA differs: " + rel)
    for rel, digest in inputs.items():
        require(sha(safe_path(root, rel)) == digest, "Source changed during independent audit: " + rel)
    require(sha(receipt_path) == receipt_sha, "Receipt changed during audit")
    return {"status": "VERIFIED_BY_INDEPENDENT_RAW_SWEEP_AUDIT", "audited_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_receipt": receipt_path.relative_to(root).as_posix(), "source_receipt_sha256": receipt_sha,
        "rtl_id": manifest["aggregate"], "cases_per_pass": 92, "raw_cases_reread": 184,
        "private_compilations": 2, "historical_csvs_checked": 4, "counter_fields_per_case": len(FIELDS),
        "source_inputs_checked": len(inputs), "output_artifacts_checked": len(artifacts),
        "max_cycles": next(iter(limits)), "ram_bytes": 32768, "window": "complete_coremark_main",
        "official_score": False, "uart_method": "accepted_apb_txdata_writes",
        "fresh_measurements_performed_by_audit": 0, "inputs": inputs, "artifacts": state["artifacts"],
        "evidence_limitations": ["The base compile helper checks native returncode but does not persist it; its private recipe and successful compiler raw logs are audited. Wrapper compilation and all184 case native returncodes are persisted and checked.",
            "Private compiled library bytes are not frozen in the runner receipt; independent creation recipes, mappings and compilation logs are checked."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", default="coremark_sweep_crc_20261010")
    parser.add_argument("--out", type=Path, required=True, help="New audit receipt; never overwritten")
    args = parser.parse_args()
    require(re.fullmatch(r"[a-z][a-z0-9_]+", args.tag), "Use an ASCII content/date tag")
    destination = args.out if args.out.is_absolute() else ROOT / args.out
    require(destination.resolve().is_relative_to((ROOT / "results").resolve()) and not destination.exists(), "Audit output must be a new file under results")
    result = verify(ROOT, ROOT / "results" / args.tag)
    result["checker_sha256"] = sha(Path(__file__))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="ascii") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print("[VERIFIED] 184 fresh raw cases,92 independent pairs,source CRCs,40counters,exact CSVs and hashes; no simulation")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, TypeError, OSError, UnicodeError) as exc:
        print("[REJECT] " + str(exc), file=sys.stderr)
        raise SystemExit(1)
