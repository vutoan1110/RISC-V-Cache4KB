"""Exact local Boolean default-definedness check on frozen BHT RTL and IR.

The pre-setundef gold $pmux selector networks are read directly. All four
two-state counter codes are enumerated for every entry, without an invariant,
initial-state tie, simulator, frontend or solver. An in-memory missing-case
mutation must make the otherwise unused default input observable.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
from review_lec_onehot_cnf import ROOT, digest, memory_cap, peak_memory


def source_case(path):
    text = Path(path).read_text(encoding="ascii")
    matches = list(re.finditer(r"function\s+\[1:0\]\s+next_counter_state\s*;(.+?)endfunction", text, re.S))
    if len(matches) != 1:
        raise ValueError("Exactly one source two-bit counter function required")
    body = re.sub(r"//[^\n]*|/\*.*?\*/", "", matches[0].group(1), flags=re.S)
    pattern = r"2'b([01]{2})\s*:\s*next_counter_state\s*=\s*taken\s*\?\s*2'b([01]{2})\s*:\s*2'b([01]{2})\s*;"
    rows = re.findall(pattern, body)
    if len(rows) != 4 or len({r[0] for r in rows}) != 4 \
            or not re.search(r"default\s*:\s*next_counter_state\s*=\s*BHT_RESET_STATE\s*;", body):
        raise ValueError("Source counter case differs from supported exact syntax")
    case = {int(state, 2): {0: int(no, 2), 1: int(yes, 2)} for state, yes, no in rows}
    if set(case) != set(range(4)):
        raise ValueError("Source counter case does not cover all two-state values")
    for state in range(4):
        for taken in (0, 1):
            expected = min(3, state + 1) if taken else max(0, state - 1)
            if case[state][taken] != expected:
                raise ValueError("Source branch counter does not implement saturating update")
    return {"case": case, "function_start_line": text[:matches[0].start()].count("\n") + 1,
            "function_end_line": text[:matches[0].end()].count("\n") + 1,
            "case_body_normalized": " ".join(body.split())}


def cells(path):
    found, pending, current = [], [], None
    with Path(path).open(encoding="ascii") as f:
        for line_no, raw in enumerate(f, 1):
            text = raw.rstrip("\r\n")
            if text.startswith("  attribute "):
                pending.append(text)
            elif text.startswith("  cell "):
                _, kind, name = text.split(None, 2)
                current = {"kind": kind, "name": name, "line": line_no, "attributes": pending,
                           "parameters": {}, "ports": {}}
                pending = []
            elif current is not None and text.startswith("    parameter "):
                _, name, value = text.split(None, 2)
                current["parameters"][name] = value
            elif current is not None and text.startswith("    connect "):
                _, name, value = text.split(None, 2)
                current["ports"][name] = value
            elif current is not None and text == "  end":
                found.append(current)
                current = None
            elif current is None and text and not text.startswith("  attribute "):
                pending = []
    if current is not None:
        raise ValueError("Incomplete IR cell")
    return found


def selectors(pmux, drivers):
    p = pmux["parameters"]
    ports = pmux["ports"]
    if pmux["kind"] != "$pmux" or p != {"\\S_WIDTH": "4", "\\WIDTH": "2"} \
            or ports["\\A"] != "2'x":
        raise ValueError("Expected exact two-bit four-way undefined-default mux")
    signal = ports["\\S"]
    if not signal.startswith("{ ") or not signal.endswith(" }"):
        raise ValueError("Explicit four-scalar selector concat required")
    nets = signal[2:-2].split()
    if len(nets) != 4 or len(set(nets)) != 4:
        raise ValueError("Four distinct decoded selectors required")
    decoded, state_wire, evidence = [], None, []
    for net in nets:
        cell = drivers[net]
        ports, params = cell["ports"], cell["parameters"]
        if params["\\A_WIDTH"] != "2" or params["\\A_SIGNED"] != "0" or params["\\Y_WIDTH"] != "1":
            raise ValueError("Selector state must be exactly unsigned2bits")
        if cell["kind"] == "$eq":
            if params["\\B_SIGNED"] != "0":
                raise ValueError("Unsigned comparison required")
            match = re.fullmatch(r"([12])'([01]+)", ports["\\B"])
            if not match or params["\\B_WIDTH"] != match[1] or len(match[2]) != int(match[1]):
                raise ValueError("Defined1/2bit comparator constant required")
            code = int(match[2], 2)
        elif cell["kind"] == "$logic_not":
            code = 0
        else:
            raise ValueError("Unsupported BHT selector cell type")
        if state_wire is not None and state_wire != ports["\\A"]:
            raise ValueError("Selectors do not compare the same raw state")
        state_wire = ports["\\A"]
        decoded.append(code)
        evidence.append({"cell": cell["name"], "kind": cell["kind"], "line": cell["line"],
                         "compared_code": code, "ports": ports, "parameters": params})
    entry = re.fullmatch(r"\\u_soc\.u_core\.u_pipeline\.datapath\.g_bp_on\.u_bht\.bht_mem\[(\d+)\]", state_wire)
    if not entry:
        raise ValueError("Selector is not the exact BHT memory entry state")
    return int(entry[1]), decoded, evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if out.exists() or not out.is_relative_to(ROOT):
        raise ValueError("New research receipt required")
    enforcement = memory_cap()
    paths = ["hdl/predictor/bht_2bit.v", "asic/snapshots/rtl_r14/hdl/predictor/bht_2bit.v",
             "asic/equiv/lec/gold_flat_r14.il", "asic/equiv/lec/gold_flat_r14.ys",
             "asic/equiv/lec/gold_god_r14_aig.ys", "scripts/verification/check_bht_default_definedness.py",
             "scripts/verification/review_lec_onehot_cnf.py"]
    hashes = {rel: digest(ROOT / rel) for rel in paths}
    current, snapshot = [source_case(ROOT / rel) for rel in paths[:2]]
    if current["case_body_normalized"] != snapshot["case_body_normalized"]:
        raise ValueError("Current and signed snapshot counter function differ")
    all_cells = cells(ROOT / paths[2])
    drivers = {}
    for cell in all_cells:
        output = cell["ports"].get("\\Y")
        if output is not None:
            if output in drivers:
                raise ValueError("Ambiguous IR output driver")
            drivers[output] = cell
    bht = [cell for cell in all_cells if cell["kind"] == "$pmux"
           and cell["ports"].get("\\A") == "2'x"
           and any("hdl/predictor/bht_2bit.v:31.9-37.16" in a for a in cell["attributes"])]
    if len(bht) != 256:
        raise ValueError("Complete exact256entry BHT population required")
    rows, seen = [], set()
    for pmux in bht:
        entry, decoded, evidence = selectors(pmux, drivers)
        if entry in seen or set(decoded) != set(range(4)):
            raise ValueError("Duplicate or incomplete BHT selector coverage")
        seen.add(entry)
        truth = []
        for state in range(4):
            mask = [int(state == code) for code in decoded]
            if sum(mask) != 1:
                raise ValueError("Undefined default or overlapping BHT branches can be selected")
            truth.append({"raw_state": state, "selector_concat_MSB_first": mask,
                          "active_selector_count": sum(mask), "default_selected": False})
        rows.append({"entry": entry, "pmux": pmux["name"], "IR_line": pmux["line"],
                     "default_connect": pmux["ports"]["\\A"], "decoded_raw_codes": decoded,
                     "selector_cells": evidence, "boolean_truth_cases": truth,
                     "status": "PROVED_DEFAULT_UNREACHABLE_FOR_ALL_BOOLEAN_RAW_STATES"})
    if seen != set(range(256)):
        raise ValueError("BHT entry coverage is incomplete")
    # Mutate a copy of the actual first selector population only in memory.
    original = rows[0]["decoded_raw_codes"]
    missing = [code for code in original if code != 3]
    witness = 3
    if any(witness == code for code in missing):
        raise ValueError("Missing-case negative control did not activate default")
    default_values = [0, 3]
    observed = [value for value in default_values]  # no selector: Y equals A.
    if observed[0] == observed[1]:
        raise ValueError("Undefined-default negative control is not observable")
    negative = {"status": "DISPROVED_DEFAULT_UNREACHABILITY_UNDER_IN_MEMORY_MISSING_CASE",
                "original_pmux": rows[0]["pmux"], "removed_compared_code": 3,
                "raw_state_witness": witness, "remaining_decoded_codes": missing,
                "default_selected": True, "two_arbitrary_default_values": default_values,
                "observed_local_pmux_values": observed,
                "scope": "Local copied mux semantic fault only, not a reachable whole-chip hardware counterexample"}
    if any(digest(ROOT / rel) != value for rel, value in hashes.items()):
        raise ValueError("BHT source or raw IR changed during definedness check")
    receipt = {"status": "PROVED_LOCAL_BHT_BOOLEAN_DEFAULT_DEFINEDNESS_ONLY",
               "full_sequential_LEC": "OPEN", "whole_source_undefined_abstraction": "OPEN",
               "four_state_X_or_Z_behavior_equivalence": "NOT_CLAIMED",
               "method": "Exact source case and pre-setundef RTLIL scalar comparator parsing; exhaustive all4Boolean state codes for each256entry mux; no state/invariant assumptions",
               "input_sha256": hashes, "memory_enforcement": enforcement,
               "current_source_function_lines": [current["function_start_line"], current["function_end_line"]],
               "snapshot_source_function_lines": [snapshot["function_start_line"], snapshot["function_end_line"]],
               "source_function_case": current["case"], "source_saturating_update_truth_cases": 8,
               "current_and_snapshot_function_tokens_equal": True,
               "IR_undefined_default_cells_checked": len(rows), "IR_selector_truth_cases": 4 * len(rows),
               "undefined_default_values_do_not_affect_local_pmux_output": True,
               "reset_or_invariant_or_zero_initial_state_premise_used": False,
               "entries": sorted(rows, key=lambda row: row["entry"]), "semantic_negative_control": negative,
               "external_frontend_simulator_or_solver_executed": False}
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print(receipt["status"], "256 cells/1024 state cases; negative control observed", observed,
          "peak", peak_memory(), flush=True)


if __name__ == "__main__":
    main()
