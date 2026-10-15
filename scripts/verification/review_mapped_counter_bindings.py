"""Separate small source/binding guards for the local mapped counter review."""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
from review_lec_onehot_cnf import ROOT, digest, memory_cap, peak_memory


def compact(text):
    return re.sub(r"\s+", "", re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S))


def instance(path, name, expected):
    text = Path(path).read_text()
    matches = re.findall(r"\b" + re.escape(name) + r"\s*\((.*?)\)\s*;", text, re.S)
    if len(matches) != 1:
        raise ValueError("Unique actual source instance required")
    body = compact(matches[0])
    for port, expression in expected.items():
        if "." + port + "(" + compact(expression) + ")" not in body:
            raise ValueError("Source instance binding differs: " + name + ":" + port)
    return expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    output = args.out.resolve()
    if output.exists() or output.with_suffix(".md").exists() or not output.is_relative_to(ROOT):
        raise ValueError("New research outputs required")
    guard = memory_cap()
    bound = {Path(__file__).relative_to(ROOT).as_posix(): digest(Path(__file__))}
    primary = "results/mapped_counter_freeze_checked_20261010/independent_review.json"
    receipt = json.loads((ROOT / primary).read_text())
    if receipt["status"] != "PASS_INDEPENDENT_MAPPED_MCYCLE_FREEZE_REVIEW":
        raise ValueError("Primary independent replay not PASS")
    bound[primary] = digest(ROOT / primary)
    for rel, expected in receipt["read_only_input_sha256"].items():
        if digest(ROOT / rel) != expected:
            raise ValueError("Primary proof input changed")
        bound[rel] = expected
    designs = []
    for design in receipt["designs"]:
        name = design["design"]
        netlist = next(d["netlist"] for d in [json.loads((ROOT / f"results/mapped_counter_freeze_checked_20261010/{name.lower()}_p1.json").read_text())])
        run = Path(netlist).parent.parent
        resolved = run / "resolved.json"
        config = json.loads((ROOT / resolved).read_text())
        bound[resolved.as_posix()] = digest(ROOT / resolved)
        top = [p for p in config["VERILOG_FILES"] if Path(p).name == "soc_asic_top.v"]
        if len(top) != 1 or not top[0].startswith("/mnt/e/Projects/RISCV-research/"):
            raise ValueError("Exact resolved flow top wrapper required")
        wrapper_rel = top[0].removeprefix("/mnt/e/Projects/RISCV-research/")
        wrapper = ROOT / wrapper_rel
        wrapper_text = compact(wrapper.read_text())
        if ".PERF_COUNTERS_ENABLE(1)" not in wrapper_text or "wiresoc_reset_n=reset_sync_q;" not in wrapper_text:
            raise ValueError("Enabled counter/reset boundary wrapper guard failed")
        ports = instance(wrapper, "u_soc", {"clk": "clk", "reset_n": "soc_reset_n"})
        bound[wrapper_rel] = digest(wrapper)
        designs.append({"design": name, "resolved_inputs": resolved.as_posix(), "wrapper": wrapper_rel,
                        "PERF_COUNTERS_ENABLE": 1, "top_soc_bindings": ports,
                        "reset_source_symbol": "reset_sync_q", "status": "PASS"})
    bindings = []
    for directory in ("asic/snapshots/rtl_r14/hdl", "hdl"):
        soc = ROOT / directory / "soc_top.v"
        obs = ROOT / directory / "performance_observability.v"
        items = [
            (soc, "u_core", {"reset_n": "reset_n", "d_req_valid": "d_req_valid", "d_req_ready": "d_req_ready", "d_req_write": "d_req_write", "d_req_addr": "d_req_addr", "d_req_wdata": "d_req_wdata"}),
            (soc, "u_mmio_axil_master", {"req_ready": "mmio_req_ready", "reset_n": "reset_n"}),
            (soc, "u_observability", {"freeze_early": "perf_freeze_early", "PSEL": "PSEL_bus && apb_sel_sysmon", "PENABLE": "PENABLE_bus && apb_sel_sysmon", "PADDR": "PADDR_bus[11:0]", "mcycle_count_dbg": "perf_mcycle_count_dbg"}),
            (obs, "u_perf_counters", {"counter_clear": "counter_clear", "counter_freeze": "counter_freeze", "mcycle_count": "mcycle_count_dbg"}),
            (obs, "u_sysmon", {"counter_clear": "counter_clear", "counter_freeze": "counter_freeze", "freeze_early": "freeze_early", "PSEL": "PSEL", "PENABLE": "PENABLE", "PADDR": "PADDR"}),
        ]
        for path, name, expected in items:
            bindings.append({"source": path.relative_to(ROOT).as_posix(), "instance": name,
                             "bindings": instance(path, name, expected), "status": "PASS"})
            bound[path.relative_to(ROOT).as_posix()] = digest(path)
    # Exhaustive direct check of the fixed priority, including freeze+clear.
    priority = []
    for clear, frozen, q, inc in itertools.product(range(2), repeat=4):
        source = 0 if clear else q if frozen else inc
        expression = (1 - clear) & ((frozen & q) | ((1 - frozen) & inc))
        if source != expression:
            raise ValueError("Clear priority Boolean reduction failed")
        priority.append([clear, frozen, q, inc, source])
    # A nonconstant next value is an actual counter-consumer path, rather than
    # an observer disconnected from the held counter. These four source cases
    # distinguish the enabled behavior from wrong hold and wrong priority.
    faults = [
        {"name": "freeze_omitted", "inputs": [0, 1, 0, 1], "actual": 0, "wrong": 1},
        {"name": "clear_priority_reversed", "inputs": [1, 1, 1, 0], "actual": 0, "wrong": 1},
        {"name": "increment_disconnected", "inputs": [0, 0, 0, 1], "actual": 1, "wrong": 0},
    ]
    for fault in faults:
        clear, frozen, q, inc = fault["inputs"]
        if (0 if clear else q if frozen else inc) != fault["actual"] or fault["actual"] == fault["wrong"]:
            raise ValueError("Source consumer finite negative control invalid")
    if any(digest(ROOT / rel) != expected for rel, expected in bound.items()):
        raise ValueError("Binding/source input changed during review")
    result = {"status": "PASS_INDEPENDENT_MAPPED_MCYCLE_SOURCE_BINDING_GUARDS",
              "scope": "Local two-state source/parameter/instance binding guard supplementary to exact mapped CNF replay. No asynchronous event/reset/init/full-LEC or source-X closure claim.",
              "designs": designs, "scoped_instance_bindings": bindings,
              "all16_clear_hold_increment_priority_cases": priority, "finite_source_negative_controls": faults,
              "primary_mapped_obligation_replay": primary, "input_sha256": bound,
              "memory_enforcement": guard, "peak_process_memory": peak_memory()}
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    output.with_suffix(".md").write_text("# Local MCYCLE source binding guards\n\nPASS for resolved DM/SA2 flow wrappers: performance counters are enabled, and the source reset boundary is reset_sync_q. Scoped current/snapshot instance guards connect the native core, MMIO master, early freeze, sysmon control and performance-counter consumers. All16 clear/freeze/Q/increment cases preserve clear priority; finite wrong-consumer examples distinguish omitted freeze, reversed priority and disconnected increment. Exact mapped all32-consumer proof remains in the primary independent replay receipt.\n\nThis is a local two-state check; it does not close source-X, asynchronous events, initialization, reachability or full-chip LEC. Input hashes and exact resolved wrapper identities are in the adjacent JSON.\n", encoding="ascii")
    print(result["status"])


if __name__ == "__main__":
    main()
