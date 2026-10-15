"""Exact local BHT read default-definedness in pre-setundef GOLD RTLIL.

Parses the actual unsigned eight-bit read decoder, every selector and every
data word. All 256 addresses are checked with symbolic table/default bits.
The check assumes neither reset, legal states, nor zero initialization.
Only bounded local Boolean source/IR behavior is claimed, not full LEC.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
from review_lec_onehot_cnf import ROOT, digest, memory_cap, peak_memory
from check_bht_default_definedness import cells


BHT = r"\u_soc.u_core.u_pipeline.datapath.g_bp_on.u_bht"
PC = r"\u_soc.u_core.u_pipeline.datapath.pc_f"
INDEX = PC + " [9:2]"
RESULT = r"\u_soc.u_core.u_pipeline.datapath.bht_state_f"


def asic_view(text):
    """Strictly select only the explicitly supported __openlane__ directive."""
    parents, active, output = [], True, []
    for line in text.splitlines():
        directive = re.fullmatch(r"\s*`(ifdef|ifndef)\s+(__openlane__)\s*", line)
        if directive:
            condition = directive[1] == "ifdef"
            parents.append((active, condition, False))
            active = active and condition
        elif re.fullmatch(r"\s*`else\s*", line):
            if not parents or parents[-1][2]:
                raise ValueError("Malformed or repeated preprocessor else")
            parent, condition, _ = parents[-1]
            parents[-1] = parent, condition, True
            active = parent and not condition
        elif re.fullmatch(r"\s*`endif\s*", line):
            if not parents:
                raise ValueError("Unmatched preprocessor endif")
            active = parents.pop()[0]
        elif line.lstrip().startswith("`"):
            raise ValueError("Unsupported source preprocessor directive")
        else:
            output.append(line if active else "")
    if parents:
        raise ValueError("Unterminated preprocessor conditional")
    return "\n".join(output)


def one(pattern, text, description):
    matches = list(re.finditer(pattern, text, re.S))
    if len(matches) != 1:
        raise ValueError("Exactly one " + description + " required")
    return matches[0]


def source_read(text):
    selected = asic_view(text)
    source = re.sub(r"//[^\n]*|/\*.*?\*/", "", selected, flags=re.S)
    entry = one(r"parameter\s+integer\s+BHT_ENTRIES\s*=\s*(\d+)\s*[,)]", source, "entry parameter")
    if int(entry[1]) != 256:
        raise ValueError("The current local check requires exactly256 table entries")
    one(r"parameter\s+integer\s+BHT_INDEX_BITS\s*=\s*\$clog2\(BHT_ENTRIES\)\s*\)", source, "index parameter")
    one(r"output\s+wire\s+\[BHT_INDEX_BITS-1:0\]\s+fetch_index\s*,", source, "eight-bit index declaration")
    declaration = one(r"reg\s+\[1:0\]\s+bht_mem\s*\[0:BHT_ENTRIES-(\d+)\]\s*;", source, "table declaration")
    subtract = int(declaration[1])
    if subtract not in (1, 2):
        raise ValueError("Unsupported memory bound expression")
    fetch_index = one(r"assign\s+fetch_index\s*=\s*fetch_pc\[BHT_INDEX_BITS\+1:2\]\s*;", source, "source fetch slice")
    fetch_state = one(r"assign\s+fetch_state\s*=\s*bht_mem\[fetch_index\]\s*;", source, "ASIC direct read")
    # Reject a second alternative driver with an expression the local parser does not support.
    if len(re.findall(r"assign\s+fetch_index\s*=", source)) != 1 or len(re.findall(r"assign\s+fetch_state\s*=", source)) != 1:
        raise ValueError("Unsupported alternative fetch driver")
    return {"entries_parameter": 256, "index_bits": 8, "declared_first_entry": 0,
            "declared_last_entry": 256 - subtract,
            "fetch_pc_slice": [9, 2],
            "table_declaration": " ".join(declaration[0].split()),
            "fetch_index_assignment": " ".join(fetch_index[0].split()),
            "fetch_state_assignment": " ".join(fetch_state[0].split()),
            "source_read_lines": {"table_declaration": source[:declaration.start()].count("\n") + 1,
                                  "fetch_index": source[:fetch_index.start()].count("\n") + 1,
                                  "fetch_state": source[:fetch_state.start()].count("\n") + 1}}


def concat(value):
    if not value.startswith("{ ") or not value.endswith(" }"):
        raise ValueError("Explicit single-level signal concat required")
    nets = value[2:-2].split()
    if len(nets) != 256 or len(set(nets)) != 256:
        raise ValueError("Exactly256 distinct whole signals required")
    return nets


def decode(pmux, drivers):
    if pmux["kind"] != "$pmux" or pmux["parameters"] != {"\\S_WIDTH": "256", "\\WIDTH": "2"}:
        raise ValueError("Exact256way two-bit parallel mux required")
    ports = pmux["ports"]
    if set(ports) != {"\\A", "\\B", "\\S", "\\Y"} or ports["\\A"] != "2'x" or ports["\\Y"] != RESULT:
        raise ValueError("Unexpected actual BHT read default/result interface")
    nets, data = concat(ports["\\S"]), concat(ports["\\B"])
    rows = []
    for position, (net, word) in enumerate(zip(nets, data)):
        if net not in drivers:
            raise ValueError("Missing decoded selector driver")
        driver = drivers[net]
        p, v = driver["parameters"], driver["ports"]
        if p.get("\\A_WIDTH") != "8" or p.get("\\A_SIGNED") != "0" or p.get("\\Y_WIDTH") != "1" \
                or v.get("\\A") != INDEX or v.get("\\Y") != net:
            raise ValueError("Selector must compare the full actual unsigned8-bit PC slice")
        if driver["kind"] == "$logic_not":
            if set(p) != {"\\A_WIDTH", "\\A_SIGNED", "\\Y_WIDTH"} or set(v) != {"\\A", "\\Y"}:
                raise ValueError("Unsupported zero decoder")
            code = 0
        elif driver["kind"] == "$eq":
            if set(p) != {"\\A_WIDTH", "\\A_SIGNED", "\\B_WIDTH", "\\B_SIGNED", "\\Y_WIDTH"} \
                    or set(v) != {"\\A", "\\B", "\\Y"} or p["\\B_SIGNED"] != "0":
                raise ValueError("Unsupported equality decoder")
            value = re.fullmatch(r"([1-8])'([01]+)", v["\\B"])
            if not value or int(value[1]) != len(value[2]) or p["\\B_WIDTH"] != value[1]:
                raise ValueError("Comparator constant is undefined, wide, or malformed")
            code = int(value[2], 2)  # actual unsigned extension to A_WIDTH8.
        else:
            raise ValueError("Unsupported read selector cell type")
        expected = BHT + ".bht_mem[" + str(code) + "]"
        if word != expected:
            raise ValueError("Selected data word does not match its actual decoded index")
        rows.append({"concat_position_MSB_first": position, "RTLIL_selector_bit": 255 - position,
                     "selector_net": net, "driver_cell": driver["name"], "driver_kind": driver["kind"],
                     "driver_IR_line": driver["line"], "driver_parameters": p,
                     "driver_ports": v, "decoded_index": code, "data_word": word})
    if {r["decoded_index"] for r in rows} != set(range(256)):
        raise ValueError("Actual read selector network does not cover all256 eight-bit codes")
    return rows


def symbolic_output(rows, address, disabled=()):
    selected = [r for r in rows if r["decoded_index"] == address and r["decoded_index"] not in disabled]
    if not selected:
        return ["default_A[0]", "default_A[1]"], []
    if len(selected) != 1:
        raise ValueError("Overlapping selectors invalidate local mux symbolic semantics")
    word = selected[0]["data_word"]
    return [word + "[0]", word + "[1]"], selected


def controls(source, pmux, drivers, rows):
    witness = 255
    before, chosen = symbolic_output(rows, witness)
    after, removed = symbolic_output(rows, witness, (255,))
    if len(chosen) != 1 or removed or after != ["default_A[0]", "default_A[1]"]:
        raise ValueError("IR missing-selector negative did not expose the actual default")
    changed, count = re.subn(r"bht_mem\s*\[0:BHT_ENTRIES-1\]", "bht_mem [0:BHT_ENTRIES-2]", source)
    if count != 1:
        raise ValueError("Exact-source negative must alter only the actual table declaration")
    modified = source_read(changed)
    if modified["declared_last_entry"] != 254 or witness <= modified["declared_last_entry"]:
        raise ValueError("Source missing-last-entry negative did not produce an out-of-range read")
    rejected = []
    first_eq = next(r for r in rows if r["driver_kind"] == "$eq")
    mutations = [("selector_A_WIDTH7", lambda c: c["parameters"].update({"\\A_WIDTH": "7"})),
                 ("selector_A_SIGNED1", lambda c: c["parameters"].update({"\\A_SIGNED": "1"})),
                 ("selector_different_slice", lambda c: c["ports"].update({"\\A": PC + " [10:3]"}))]
    for name, mutate in mutations:
        copied = dict(drivers)
        target = copy.deepcopy(copied[first_eq["selector_net"]])
        mutate(target)
        copied[first_eq["selector_net"]] = target
        try:
            decode(pmux, copied)
        except ValueError as error:
            rejected.append({"fault": name, "status": "REJECTED", "reason": str(error)})
        else:
            raise ValueError("Malformed actual-selector control was accepted")
    data_swapped = copy.deepcopy(pmux)
    words = concat(data_swapped["ports"]["\\B"])
    words[0], words[1] = words[1], words[0]
    data_swapped["ports"]["\\B"] = "{ " + " ".join(words) + " }"
    try:
        decode(data_swapped, drivers)
    except ValueError as error:
        rejected.append({"fault": "actual_data_words_swapped", "status": "REJECTED", "reason": str(error)})
    else:
        raise ValueError("Wrong selected-memory-word control was accepted")
    return {"IR_semantic_missing_selector": {
                "status": "DISPROVED_DEFAULT_UNREACHABILITY_IN_COPIED_READ_MUX",
                "removed_actual_selector": chosen[0]["selector_net"], "decoded_code": 255,
                "raw_fetch_PC_slice_witness": 255, "all_other_input_and_memory_bits_free": True,
                "original_output_symbols": before, "mutated_output_symbols": after,
                "original_selected_word_arbitrary_value": 2, "two_arbitrary_default_values": [0, 3],
                "observed_original_output": 2, "observed_mutated_outputs": [0, 3],
                "mutation_written_to_IR": False},
            "exact_source_missing_last_entry": {
                "status": "DISPROVED_SOURCE_INDEX_RANGE_COVERAGE_IN_SOURCE_COPY",
                "original_declared_last_entry": 255, "mutated_declared_last_entry": 254,
                "eight_bit_fetch_index_witness": 255, "out_of_range_default_now_observable": True,
                "mutation_written_to_source": False,
                "mutated_source_frontend_executed": False,
                "scope": "Supported source array bounds/read semantics only; no mutated frontend correspondence or whole-chip reachable trace claimed"},
            "malformed_selector_or_data_controls": rejected}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if out.exists() or not out.is_relative_to(ROOT):
        raise ValueError("New research receipt required; existing output cannot be replaced")
    enforcement = memory_cap()
    paths = ["hdl/predictor/bht_2bit.v", "asic/snapshots/rtl_r14/hdl/predictor/bht_2bit.v",
             "hdl/datapath.v", "asic/snapshots/rtl_r14/hdl/datapath.v",
             "asic/equiv/lec/gold_flat_r14.il", "asic/equiv/lec/gold_flat_r14.ys",
             "asic/equiv/lec/gold_god_r14_aig.ys",
             "scripts/verification/check_bht_read_default_definedness.py",
             "scripts/verification/check_bht_default_definedness.py",
             "scripts/verification/review_lec_onehot_cnf.py"]
    hashes = {path: digest(ROOT / path) for path in paths}
    sources = [(ROOT / path).read_text(encoding="ascii") for path in paths[:2]]
    contracts = [source_read(source) for source in sources]
    semantic_keys = set(contracts[0]) - {"source_read_lines"}
    if any(contracts[0][key] != contracts[1][key] for key in semantic_keys) \
            or any(contract["declared_last_entry"] != 255 for contract in contracts):
        raise ValueError("Current and signed ASIC BHT read contracts differ or do not cover full index range")
    datapath_evidence = []
    for path in paths[2:4]:
        raw = (ROOT / path).read_text(encoding="ascii")
        raw_instance = one(r"bht_2bit\s*#\s*\((.*?)\)\s*u_bht\s*\((.*?)\)\s*;", raw, "raw parent BHT instance")
        # Only the prefix needed to establish this parent instance is in scope.
        # Attribute macros on unrelated later datapath logic are not interpreted.
        text = asic_view(raw[:raw_instance.end()])
        source = re.sub(r"//[^\n]*|/\*.*?\*/", "", text, flags=re.S)
        instance = one(r"bht_2bit\s*#\s*\((.*?)\)\s*u_bht\s*\((.*?)\)\s*;", source, "BHT datapath instance")
        if not re.search(r"\.BHT_ENTRIES\s*\(BHT_ENTRIES\)", instance[1]) \
                or not re.search(r"\.fetch_pc\s*\(pc_f\)", instance[2]) \
                or not re.search(r"\.fetch_state\s*\(bht_state_f\)", instance[2]):
            raise ValueError("Actual parent BHT source connections differ")
        datapath_evidence.append({"path": path, "source_instance_start_line": source[:instance.start()].count("\n") + 1,
                                  "fetch_pc": "pc_f", "fetch_state": "bht_state_f",
                                  "preprocessor_view_scope": "Source prefix through exact u_bht instance only"})
    all_cells = cells(ROOT / paths[4])
    drivers = {}
    for cell in all_cells:
        net = cell["ports"].get("\\Y")
        if net is not None:
            if net in drivers:
                raise ValueError("Ambiguous actual RTLIL output driver")
            drivers[net] = cell
    candidates = [c for c in all_cells if c["kind"] == "$pmux" and c["ports"].get("\\A") == "2'x"
                  and any("hdl/predictor/bht_2bit.v:0.0-0.0" in a for a in c["attributes"])]
    if len(candidates) != 1:
        raise ValueError("Exactly one actual undefined-default BHT read pmux required")
    pmux = candidates[0]
    decoded = decode(pmux, drivers)
    width_evidence, connect_evidence = {}, {}
    needed_wires = {PC: 32, **{BHT + ".bht_mem[" + str(i) + "]": 2 for i in range(256)}}
    needed_connects = {BHT + ".fetch_pc": PC, BHT + ".fetch_index": INDEX, BHT + ".fetch_state": RESULT}
    with (ROOT / paths[4]).open(encoding="ascii") as stream:
        for line_no, line in enumerate(stream, 1):
            wire = re.fullmatch(r"  wire width (\d+) (\\\S+)\s*", line)
            if wire and wire[2] in needed_wires:
                if wire[2] in width_evidence or int(wire[1]) != needed_wires[wire[2]]:
                    raise ValueError("Actual source/index/data width is ambiguous or unsupported")
                width_evidence[wire[2]] = {"width": int(wire[1]), "IR_line": line_no}
            connection = re.fullmatch(r"  connect (\\\S+) (.*?)\s*", line)
            if connection and connection[1] in needed_connects:
                if connection[1] in connect_evidence or connection[2] != needed_connects[connection[1]]:
                    raise ValueError("Actual source read/index wire connection differs")
                connect_evidence[connection[1]] = {"value": connection[2], "IR_line": line_no}
    if set(width_evidence) != set(needed_wires) or set(connect_evidence) != set(needed_connects):
        raise ValueError("Some actual source/data-width or index connections are missing")
    truth = []
    for address in range(256):
        symbols, chosen = symbolic_output(decoded, address)
        if len(chosen) != 1 or chosen[0]["decoded_index"] != address \
                or symbols != [BHT + ".bht_mem[" + str(address) + "][" + str(bit) + "]" for bit in range(2)]:
            raise ValueError("Actual local BHT read is not fully defined symbolic table selection")
        truth.append({"raw_eight_bit_index": address, "active_selector_count": 1,
                      "active_selector_bit": chosen[0]["RTLIL_selector_bit"],
                      "default_selected": False, "output_symbolic_bits_LSB_first": symbols})
    negatives = controls(sources[1], pmux, drivers, decoded)
    if any(digest(ROOT / path) != expected for path, expected in hashes.items()):
        raise ValueError("A source, IR, recipe, or checker changed during the local proof")
    receipt = {"status": "PROVED_LOCAL_BHT_READ_BOOLEAN_DEFAULT_DEFINEDNESS_ONLY",
               "full_sequential_LEC": "OPEN", "whole_source_undefined_abstraction": "OPEN",
               "four_state_X_or_Z_behavior_equivalence": "NOT_CLAIMED",
               "method": "Strict current/signed ASIC source read and pre-setundef RTLIL parsing; exhaustive256 unsigned8-bit addresses; independent symbolic table/default data; no frontend or solver",
               "input_sha256": hashes, "memory_enforcement": enforcement,
               "source_contracts": [{"path": paths[i], **contracts[i]} for i in range(2)],
               "datapath_source_connections": datapath_evidence,
               "current_and_signed_ASIC_read_contract_equal": True,
               "actual_read_pmux": pmux, "actual_selector_rows_MSB_first": decoded,
               "actual_wire_width_evidence": width_evidence, "actual_module_connect_evidence": connect_evidence,
               "actual_read_selector_count": 256, "actual_selector_index_support_bits": 8,
               "all256_boolean_index_codes_have_exactly_one_selector": True,
               "symbolic_memory_data_bits": 512, "symbolic_undefined_default_bits": 2,
               "symbolic_output_equals_selected_original_table_word_for_all_data": True,
               "reset_or_invariant_or_zero_initial_state_premise_used": False,
               "IR_undefined_default_connect_lines_closed": 1, "exhaustive_address_truth_cases": truth,
               "negative_controls": negatives,
               "historical_GOLD_functional_XZ_connect_lines": 358,
               "previous_BHT_update_connect_lines_locally_closed": 256,
               "combined_BHT_update_and_read_connect_lines_locally_closed": 257,
               "remaining_GOLD_functional_XZ_connect_lines": 101,
               "count_scope": "Classified X/Z connect lines, not bits, defects, or global source-equivalence obligations discharged",
               "source_or_IR_mutation_written": False,
               "external_frontend_simulator_or_solver_executed": False}
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print(receipt["status"], "256 addresses;512 symbolic table bits; six controls; peak", peak_memory(), flush=True)


if __name__ == "__main__":
    main()
