#!/usr/bin/env python3
"""Stream flattened RTLIL to audit the DM mapped-cut clock/edge prerequisite.

This proves only the structural clock obligation of the preserved flat models:
every supported flop clock must already be the scalar top input clk, and every
flop must be positive edge. An unresolved alias, buffered/inverted/gated clock,
unknown sequential primitive or absent clock is OPEN/FAIL, never assumed equal.
No Yosys, WSL, SAT or simulation is run. This is not complete sequential LEC.
"""
from __future__ import annotations

import argparse
from collections import Counter
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
INPUTS = (
    "asic/equiv/lec/gold_flat_r14.il",
    "asic/equiv/lec/n1_flat_r14.il",
    "asic/equiv/lec/gate_flat_R14FA.il",
    "asic/equiv/lec/gate_flat_R14FB.il",
)
MAX_LINE = 1024 * 1024
MEMORY_CAP_BYTES = 512 * 1024 * 1024
CLOCK = "\\clk"
POS_TYPES = ("$dff", "$_DFF_P_")
KNOWN_OUTPUTS = {"\\Y", "\\Q", "\\X", "\\CO", "\\SUM", "\\RD_DATA"}


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(MAX_LINE), b""):
            h.update(block)
    return h.hexdigest()


def peak_memory_bytes():
    if os.name != "nt":
        return None
    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong)] + [
            (name, ctypes.c_size_t) for name in ("PeakWorkingSetSize", "WorkingSetSize",
                "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
    state = Counters()
    state.cb = ctypes.sizeof(state)
    kernel = ctypes.windll.kernel32
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    probe = ctypes.windll.psapi.GetProcessMemoryInfo
    probe.argtypes = (ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong)
    probe.restype = ctypes.c_int
    if not probe(kernel.GetCurrentProcess(), ctypes.byref(state), state.cb):
        raise RuntimeError("process memory probe failed")
    if state.PeakWorkingSetSize > MEMORY_CAP_BYTES:
        raise RuntimeError("clock audit exceeded the 512 MiB process memory cap")
    return state.PeakWorkingSetSize


def integer(text):
    if re.fullmatch(r"[0-9]+", text):
        return int(text)
    m = re.fullmatch(r"([0-9]+)'([01]+)", text)
    if m and int(m.group(1)) == len(m.group(2)):
        return int(m.group(2), 2)
    raise ValueError("not a defined integer parameter: " + text)


def has_clock(sig):
    # Preserve token boundaries: clk_extra must not be mistaken for clk.
    return CLOCK in re.findall(r"[\\$][^\s{}]+", sig)


def sequential(cell_type):
    text = cell_type.lower()
    return "dff" in text or "latch" in text or cell_type in ("$ff", "$_FF_")


def audit(path):
    initial_hash = digest(path)
    top = False
    top_count = 0
    top_closed = False
    input_clock_declarations = 0
    cell = None
    counts = Counter()
    polarity_counts = Counter()
    cells_total = 0
    flop_cells = 0
    flop_bits = 0
    missing = []
    failures = []
    clock_roots = Counter()
    facts_hash = hashlib.sha256()
    max_line_bytes = 0
    # At most one cell's parameters/ports are retained; no full-file split/list.
    with path.open(encoding="utf-8") as fh:
        while True:
            line = fh.readline(MAX_LINE + 1)
            if not line:
                break
            if len(line) > MAX_LINE:
                raise RuntimeError("RTLIL line exceeds bounded parser limit")
            max_line_bytes = max(max_line_bytes, len(line))
            if line.startswith("module "):
                top = line.strip() == "module \\soc_asic_top"
                if top:
                    top_count += 1
                continue
            if not top:
                continue
            if line == "end\n" or line == "end":
                top_closed = True
                top = False
                continue
            if line.startswith("  wire "):
                words = line.split()
                if words[-1] == CLOCK:
                    width = int(words[words.index("width") + 1]) if "width" in words else 1
                    if "input" not in words or "output" in words or "inout" in words or width != 1:
                        failures.append("clk is not a scalar primary input")
                    else:
                        input_clock_declarations += 1
                continue
            if line.startswith("  cell "):
                words = line.split()
                cell = {"type": words[1], "name": words[2], "parameters": {}, "ports": {}}
                cells_total += 1
                continue
            if cell is not None:
                if line.startswith("    parameter "):
                    _, name, value = line.split(None, 2)
                    cell["parameters"][name] = value.strip()
                elif line.startswith("    connect "):
                    _, name, value = line.split(None, 2)
                    if name in cell["ports"]:
                        failures.append("duplicate cell port: " + cell["name"] + " " + name)
                    cell["ports"][name] = value.strip()
                elif line.startswith("  end"):
                    typ, params, ports = cell["type"], cell["parameters"], cell["ports"]
                    for name, sig in ports.items():
                        if name in KNOWN_OUTPUTS and has_clock(sig):
                            failures.append("internal cell drives primary clock: " + cell["name"] + " " + name)
                    if not typ.startswith("$") and any(has_clock(sig) for sig in ports.values()):
                        missing.append("unknown clock-connected cell primitive: " + typ + " " + cell["name"])
                    if sequential(typ):
                        flop_cells += 1
                        counts[typ] += 1
                        if typ not in POS_TYPES:
                            failures.append("unsupported/nonpositive sequential primitive: " + typ + " " + cell["name"])
                        clock_name = "\\C" if typ == "$_DFF_P_" else "\\CLK"
                        clock_sig = ports.get(clock_name)
                        if clock_sig is None:
                            failures.append("missing flop clock: " + cell["name"])
                        elif clock_sig != CLOCK:
                            missing.append("unresolved clock domain/cone: " + cell["name"] + " " + clock_sig)
                        clock_roots[str(clock_sig)] += 1
                        for required in ("\\D", "\\Q"):
                            if required not in ports:
                                failures.append("missing flop " + required + ": " + cell["name"])
                        try:
                            if typ == "$_DFF_P_":
                                width, polarity = 1, 1
                            else:
                                width = integer(params["\\WIDTH"])
                                polarity = integer(params["\\CLK_POLARITY"])
                            if width <= 0 or width > 1000000:
                                raise ValueError("invalid sequential width")
                            if polarity != 1:
                                failures.append("nonpositive clock polarity: " + cell["name"])
                            flop_bits += width
                            polarity_counts[str(polarity)] += 1
                        except (KeyError, ValueError) as exc:
                            failures.append("missing/invalid flop parameters: " + cell["name"] + " " + str(exc))
                            width, polarity = None, None
                        facts_hash.update((json.dumps({"type": typ, "cell": cell["name"],
                            "width": width, "polarity": polarity, "clock": clock_sig,
                            "q": ports.get("\\Q"), "d": ports.get("\\D")}, sort_keys=True) + "\n").encode())
                    cell = None
                continue
            if line.startswith("  connect "):
                # A module assignment to input clk would invalidate the external
                # clock premise; no alias of the input is presumed harmless.
                rest = line[len("  connect "):].strip()
                if rest.startswith("{"):
                    end = rest.find("}")
                    lhs = rest[:end + 1] if end >= 0 else rest
                else:
                    lhs = rest.split(None, 1)[0]
                if has_clock(lhs):
                    failures.append("module connection drives primary clock: " + rest)
    if top_count != 1 or not top_closed or cell is not None:
        failures.append("missing/duplicate/truncated top-module boundary")
    if input_clock_declarations != 1:
        failures.append("expected exactly one scalar clk input declaration")
    if not flop_cells or not flop_bits:
        failures.append("empty sequential audit is not a proof")
    final_hash = digest(path)
    if initial_hash != final_hash:
        failures.append("input bytes changed during audit")
    memory = peak_memory_bytes()
    return {"status": "FAIL" if failures else "MISSING_CLOCK_PROOF" if missing else "VERIFIED_CLOCK_EDGE_DOMAIN_AUDIT",
        "sha256_before": initial_hash, "sha256_after": final_hash, "file_bytes": path.stat().st_size,
        "top_modules": top_count, "scalar_clk_input_declarations": input_clock_declarations,
        "cell_count": cells_total, "flop_cells": flop_cells, "flop_bits": flop_bits,
        "sequential_types": dict(counts), "clock_polarities": dict(polarity_counts),
        "clock_roots": dict(clock_roots), "flop_clock_facts_sha256": facts_hash.hexdigest(),
        "failures": failures, "missing_obligations": missing, "maximum_line_characters": max_line_bytes,
        "peak_working_set_bytes": memory,
        "clock_semantics": "All flop clocks are literally scalar input clk in the preserved flattened functional models; no unresolved alias/buffer/inverter/gated clock is assumed equal."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    out = (ROOT / args.out).resolve()
    if not out.is_relative_to(ROOT) or out.exists():
        raise RuntimeError("output must be new and inside the research workspace")
    records = {}
    for name in INPUTS:
        print("STREAM " + name, flush=True)
        records[name] = audit(ROOT / name)
        print(json.dumps({"file": name, "status": records[name]["status"],
            "flop_cells": records[name]["flop_cells"], "flop_bits": records[name]["flop_bits"]}), flush=True)
    verdict = all(row["status"] == "VERIFIED_CLOCK_EDGE_DOMAIN_AUDIT" for row in records.values())
    output = {"created": datetime.now().astimezone().isoformat(timespec="seconds"),
        "label": args.label, "status": "VERIFIED_CLOCK_EDGE_DOMAIN_AUDIT" if verdict else "OPEN_CLOCK_OBLIGATIONS",
        "not_a_new_hardware_measurement": True, "tools_launched": 0, "wsl_started": False,
        "streaming_memory_cap_bytes": MEMORY_CAP_BYTES, "sources": {"scripts/verification/lec_clock_audit.py": digest(Path(__file__))},
        "inputs": records, "scope": "Clock/positive-edge obligation only. Reset-base, invariant bridge, all data/output closure and complete LEC remain independent obligations."}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
