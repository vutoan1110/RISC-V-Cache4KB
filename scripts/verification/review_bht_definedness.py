"""Independent bounded replay of frozen local BHT definedness proofs.

Uses a separate streaming RTLIL parser, bit-vector SigSpec interpreter and
source reader. It does not import the BHT proof checkers or their parsers.
Every read/update selector and actual data slice is reconstructed from IR.
This is an audit of saved proofs, not a new synthesis or full-chip LEC run.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
from review_lec_onehot_cnf import ROOT, memory_cap, peak_memory


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def strip_comments(text):
    return re.sub(r"/\*.*?\*/|//[^\r\n]*", "", text, flags=re.S)


def source_view(text):
    stack, live, result = [], True, []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("`ifdef ") or line.startswith("`ifndef "):
            tokens = line.split()
            if len(tokens) != 2 or tokens[1] != "__openlane__":
                raise ValueError("Unsupported conditional in inspected BHT source")
            cond = tokens[0] == "`ifdef"
            stack.append([live, cond, False])
            live = live and cond
            result.append("")
        elif line == "`else":
            if not stack or stack[-1][2]:
                raise ValueError("Invalid BHT conditional else")
            stack[-1][2] = True
            live = stack[-1][0] and not stack[-1][1]
            result.append("")
        elif line == "`endif":
            if not stack:
                raise ValueError("Unmatched BHT conditional end")
            live = stack.pop()[0]
            result.append("")
        elif line.startswith("`"):
            raise ValueError("Unsupported BHT source directive")
        else:
            result.append(raw if live else "")
    if stack:
        raise ValueError("Unclosed BHT conditional")
    return strip_comments("\n".join(result))


def source_contract(path):
    text = source_view(path.read_text(encoding="ascii"))
    function = re.findall(r"function\s+\[1:0\]\s+next_counter_state\s*;(.*?)endfunction", text, re.S)
    if len(function) != 1:
        raise ValueError("Unique exact source function missing")
    branches = re.findall(r"2'b([01]{2})\s*:\s*next_counter_state\s*=\s*taken\s*\?\s*2'b([01]{2})\s*:\s*2'b([01]{2})\s*;", function[0])
    cases = {}
    for state, yes, no in branches:
        code = int(state, 2)
        if code in cases:
            raise ValueError("Duplicate counter source case")
        cases[code] = (int(no, 2), int(yes, 2))
    if set(cases) != set(range(4)) or not re.search(r"default\s*:\s*next_counter_state\s*=\s*BHT_RESET_STATE\s*;", function[0]):
        raise ValueError("Source saturation function is incomplete")
    for code in range(4):
        if cases[code] != (max(0, code - 1), min(3, code + 1)):
            raise ValueError("Source function differs from saturated two-bit update")
    entry = re.findall(r"parameter\s+integer\s+BHT_ENTRIES\s*=\s*(\d+)", text)
    reset = re.findall(r"parameter\s+\[1:0\]\s+BHT_RESET_STATE\s*=\s*2'b([01]{2})", text)
    if entry != ["256"] or not re.search(r"parameter\s+integer\s+BHT_INDEX_BITS\s*=\s*\$clog2\(BHT_ENTRIES\)", text):
        raise ValueError("Source address domain is not the exact256-entry eight-bit table")
    if len(reset) != 1:
        raise ValueError("Explicit source default parameter missing")
    requirements = [r"reg\s*\[1:0\]\s*bht_mem\s*\[0:BHT_ENTRIES-1\]\s*;",
                    r"assign\s+fetch_index\s*=\s*fetch_pc\[BHT_INDEX_BITS\+1:2\]\s*;",
                    r"assign\s+fetch_state\s*=\s*bht_mem\[fetch_index\]\s*;",
                    r"output\s+wire\s*\[BHT_INDEX_BITS-1:0\]\s*fetch_index\s*,"]
    for expression in requirements:
        if len(re.findall(expression, text)) != 1:
            raise ValueError("Exact source table/read/index contract missing")
    return {"saturating_function_cases": cases, "table_entries": 256,
            "index_width": (256 - 1).bit_length(), "source_slice": [9, 2],
            "explicit_source_default_reset_state": int(reset[0], 2)}


def read_il(path):
    widths, cells, module_connects, unknown_lines = {}, [], [], []
    cell, attributes = None, []
    inside, selected_modules, closed = False, 0, False
    with path.open(encoding="ascii") as stream:
        for number, raw in enumerate(stream, 1):
            text = raw.rstrip()
            if text.startswith("module "):
                inside = text == r"module \soc_asic_top"
                if inside:
                    selected_modules += 1
                attributes = []
                continue
            if text == "end":
                if inside:
                    closed = True
                inside = False
                attributes = []
                continue
            if not inside:
                continue
            if text.startswith("  attribute "):
                attributes.append(text)
                continue
            match = re.fullmatch(r"  cell (\S+) (.+)", text)
            if match:
                if cell is not None:
                    raise ValueError("Nested RTLIL cell")
                cell = {"type": match[1], "name": match[2], "line": number,
                        "attributes": attributes, "p": {}, "c": {}}
                attributes = []
                continue
            if cell is not None:
                if text == "  end":
                    cells.append(cell)
                    cell = None
                    continue
                match = re.fullmatch(r"    (parameter|connect) (\\\S+) (.*)", text)
                if match:
                    target = cell["p" if match[1] == "parameter" else "c"]
                    if match[2] in target:
                        raise ValueError("Duplicate RTLIL cell field")
                    target[match[2]] = match[3]
                    if match[1] == "connect" and re.search(r"\d+'[01xz]*[xz][01xz]*", match[3]):
                        unknown_lines.append({"line": number, "cell_line": cell["line"],
                                              "cell": cell["name"], "type": cell["type"],
                                              "port": match[2], "value": match[3],
                                              "attributes": cell["attributes"]})
                elif text.strip():
                    raise ValueError("Unsupported statement in RTLIL cell")
                continue
            attributes = []
            match = re.fullmatch(r"  wire(?: (?:width|offset|upto|signed|input|output)(?: \d+)?)* (\S+)", text)
            if match:
                parts = text.split()
                width = int(parts[parts.index("width") + 1]) if "width" in parts else 1
                if match[1] in widths:
                    raise ValueError("Duplicate RTLIL wire")
                widths[match[1]] = width
            match = re.fullmatch(r"  connect (\S+(?: \[[^]]+\])?) (.*)", text)
            if match:
                record = {"line": number, "lhs": match[1], "rhs": match[2]}
                module_connects.append(record)
                if re.search(r"\d+'[01xz]*[xz][01xz]*", match[2]):
                    unknown_lines.append({"line": number, "type": "module_connect", **record})
    if cell is not None or selected_modules != 1 or not closed:
        raise ValueError("Unterminated cell or missing/duplicate top module")
    return widths, cells, module_connects, unknown_lines


def bits(expression, widths):
    """Interpret RTLIL SigSpec as LSB-first constants or original wire-bit atoms."""
    tokens = re.findall(r"[{}]|\[[^]]+\]|[^\s{}]+", expression)
    pos = 0
    def item():
        nonlocal pos
        if pos >= len(tokens):
            raise ValueError("Incomplete RTLIL SigSpec")
        token = tokens[pos]
        pos += 1
        if token == "{":
            words = []
            while pos < len(tokens) and tokens[pos] != "}":
                words.append(item())
            if pos == len(tokens):
                raise ValueError("Unclosed RTLIL concat")
            pos += 1
            return [bit for word in reversed(words) for bit in word]
        if token == "}" or token.startswith("["):
            raise ValueError("Malformed RTLIL leaf")
        literal = re.fullmatch(r"(\d+)'([01xz]+)", token)
        if literal:
            width, payload = int(literal[1]), literal[2]
            if len(payload) == 1 and payload in "xz":
                payload *= width
            if len(payload) != width:
                raise ValueError("Unsupported RTLIL constant extension")
            return [int(value) if value in "01" else ("UNDEFINED", value, index)
                    for index, value in enumerate(reversed(payload))]
        if token not in widths:
            raise ValueError("Unknown original RTLIL wire: " + token)
        indices = list(range(widths[token]))
        if pos < len(tokens) and tokens[pos].startswith("["):
            selection = re.fullmatch(r"\[(\d+)(?::(\d+))?\]", tokens[pos])
            if not selection:
                raise ValueError("Unsupported RTLIL slice")
            high, low = int(selection[1]), int(selection[2] or selection[1])
            if high < low or high >= widths[token]:
                raise ValueError("Slice exceeds the actual wire width")
            indices = list(range(low, high + 1))
            pos += 1
        return [(token, index) for index in indices]
    result = item()
    if pos != len(tokens):
        raise ValueError("Unexpected extra RTLIL SigSpec tokens")
    return result


def decoder(cell, expected_atoms, widths):
    p, c = cell["p"], cell["c"]
    n = len(expected_atoms)
    if int(p["\\A_WIDTH"]) != n or p["\\A_SIGNED"] != "0" or p["\\Y_WIDTH"] != "1" \
            or bits(c["\\A"], widths) != expected_atoms:
        raise ValueError("Raw selector support/unsigned width differs")
    if cell["type"] == "$logic_not":
        if set(c) != {"\\A", "\\Y"} or set(p) != {"\\A_WIDTH", "\\A_SIGNED", "\\Y_WIDTH"}:
            raise ValueError("Unsupported actual zero selector")
        return 0
    if cell["type"] != "$eq" or p["\\B_SIGNED"] != "0":
        raise ValueError("Unsupported actual selector primitive")
    operand = bits(c["\\B"], widths)
    if len(operand) != int(p["\\B_WIDTH"]) or len(operand) > n or any(type(bit) is not int for bit in operand):
        raise ValueError("Undefined, symbolic, or excessively wide decoder comparison")
    return sum(bit << index for index, bit in enumerate(operand))


def sources_and_pairs():
    input_paths = ["hdl/predictor/bht_2bit.v", "asic/snapshots/rtl_r14/hdl/predictor/bht_2bit.v",
                   "asic/equiv/lec/gold_flat_r14.il", "scripts/verification/review_bht_definedness.py"]
    source = [source_contract(ROOT / path) for path in input_paths[:2]]
    if source[0] != source[1]:
        raise ValueError("Current and signed ASIC local BHT contracts differ")
    paired = {}
    for tag in ("bht_default_definedness", "bht_read_default_definedness"):
        paths = ["results/" + tag + "_20261010_p" + str(n) + ".json" for n in (1, 2)]
        decoded = [json.loads((ROOT / path).read_text(encoding="ascii")) for path in paths]
        if decoded[0] != decoded[1] or sha(ROOT / paths[0]) != sha(ROOT / paths[1]):
            raise ValueError("Frozen local proof pair is not byte/all-field identical")
        for path, expected in decoded[0]["input_sha256"].items():
            if sha(ROOT / path) != expected:
                raise ValueError("Frozen proof source changed: " + path)
            input_paths.append(path)
        input_paths.extend(paths)
        paired[tag] = decoded[0]
    return source[0], paired, sorted(set(input_paths))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if out.exists() or not out.is_relative_to(ROOT):
        raise ValueError("A new review output inside research is required")
    bound = memory_cap()
    source, paired, input_paths = sources_and_pairs()
    before = {path: sha(ROOT / path) for path in input_paths}
    widths, cells, connections, unknown = read_il(ROOT / "asic/equiv/lec/gold_flat_r14.il")
    bit_drivers, selector_drivers = {}, {}
    for cell in cells:
        output = cell["c"].get("\\Y")
        if output is None:
            continue
        atoms = bits(output, widths)
        for offset, atom in enumerate(atoms):
            if atom in bit_drivers:
                raise ValueError("Multiple original IR bit drivers")
            bit_drivers[atom] = (cell, offset)
        if len(atoms) == 1:
            selector_drivers[atoms[0]] = cell
    bht_name = r"\u_soc.u_core.u_pipeline.datapath.g_bp_on.u_bht.bht_mem"
    taken_name = r"\u_soc.u_core.u_pipeline.datapath.branch_taken_e"
    pc_name = r"\u_soc.u_core.u_pipeline.datapath.pc_f"
    read_targets = [cell for cell in cells if cell["type"] == "$pmux"
                    and cell["c"].get("\\Y") == r"\u_soc.u_core.u_pipeline.datapath.bht_state_f"]
    updates = [cell for cell in cells if cell["type"] == "$pmux" and cell["c"].get("\\A") == "2'x"
               and any("hdl/predictor/bht_2bit.v:31.9-37.16" in attribute for attribute in cell["attributes"])]
    if len(read_targets) != 1 or len(updates) != 256:
        raise ValueError("Actual BHT read/update population differs")
    read = read_targets[0]
    if read["p"] != {"\\WIDTH": "2", "\\S_WIDTH": "256"} or read["c"]["\\A"] != "2'x" \
            or widths[pc_name] != 32:
        raise ValueError("Actual read mux or raw PC width differs")
    s_atoms, b_atoms = bits(read["c"]["\\S"], widths), bits(read["c"]["\\B"], widths)
    if len(s_atoms) != 256 or len(b_atoms) != 512:
        raise ValueError("Actual read selector/data vector size differs")
    read_codes = [decoder(selector_drivers[atom], [(pc_name, bit) for bit in range(2, 10)], widths)
                  for atom in s_atoms]
    if set(read_codes) != set(range(256)) or len(set(s_atoms)) != 256:
        raise ValueError("Actual read decoder does not cover all free eight-bit codes uniquely")
    read_rows = []
    for address in range(256):
        selected = [i for i, code in enumerate(read_codes) if address == code]
        if len(selected) != 1:
            raise ValueError("Read undefined default or overlap remains")
        index = selected[0]
        actual = b_atoms[2 * index:2 * index + 2]
        expected = [(bht_name + "[" + str(address) + "]", bit) for bit in range(2)]
        if actual != expected or widths[expected[0][0]] != 2:
            raise ValueError("Actual read data slice/order mismatches address")
        read_rows.append({"address": address, "selector_LSB_bit": index, "selected_original_bit_atoms": actual})

    def evaluate(atom, environment, depth=0):
        if type(atom) is int:
            return atom
        if atom in environment:
            return environment[atom]
        if depth >= 12 or atom not in bit_drivers:
            raise ValueError("Unsupported symbolic leaf/depth in exact update data cone")
        cell, offset = bit_drivers[atom]
        if cell["type"] != "$mux" or set(cell["p"]) != {"\\WIDTH"}:
            raise ValueError("Unsupported actual update data primitive")
        control = bits(cell["c"]["\\S"], widths)
        if len(control) != 1:
            raise ValueError("Actual update data select is not scalar")
        port = "\\B" if evaluate(control[0], environment, depth + 1) else "\\A"
        operand = bits(cell["c"][port], widths)
        if len(operand) != int(cell["p"]["\\WIDTH"]) or offset >= len(operand):
            raise ValueError("Actual update data mux width differs")
        return evaluate(operand[offset], environment, depth + 1)

    update_rows, covered = [], set()
    for mux in updates:
        if mux["p"] != {"\\WIDTH": "2", "\\S_WIDTH": "4"}:
            raise ValueError("Actual update mux width differs")
        sels, data = bits(mux["c"]["\\S"], widths), bits(mux["c"]["\\B"], widths)
        if len(sels) != 4 or len(data) != 8 or len(set(sels)) != 4:
            raise ValueError("Actual update selector/data size differs")
        first_driver = selector_drivers[sels[0]]
        state_atoms = bits(first_driver["c"]["\\A"], widths)
        if len(state_atoms) != 2 or state_atoms[0][1] != 0 or state_atoms[1][1] != 1 \
                or state_atoms[0][0] != state_atoms[1][0]:
            raise ValueError("Actual update state is not the original two-bit table entry")
        matched = re.fullmatch(re.escape(bht_name) + r"\[(\d+)\]", state_atoms[0][0])
        if not matched or int(matched[1]) in covered:
            raise ValueError("Actual update table entry is missing or repeated")
        entry = int(matched[1])
        covered.add(entry)
        codes = [decoder(selector_drivers[atom], state_atoms, widths) for atom in sels]
        if set(codes) != set(range(4)):
            raise ValueError("Actual update decoder is incomplete")
        cases = []
        for state in range(4):
            selected = [i for i, code in enumerate(codes) if state == code]
            if len(selected) != 1:
                raise ValueError("Actual update default or overlapping selector remains")
            for taken in (0, 1):
                observed = sum(evaluate(atom, {(taken_name, 0): taken}) << bit
                               for bit, atom in enumerate(data[2 * selected[0]:2 * selected[0] + 2]))
                expected = source["saturating_function_cases"][state][taken]
                if observed != expected:
                    raise ValueError("Actual update B slice does not match source saturating semantics")
                cases.append({"raw_state": state, "taken": taken, "actual_value": observed})
        update_rows.append({"entry": entry, "pmux": mux["name"], "line": mux["line"],
                            "codes_LSB_first": codes, "actual_update_truth_cases": cases})
    if covered != set(range(256)):
        raise ValueError("Actual BHT update table population incomplete")

    # Independently activate copied missing-branch/default behavior; these local
    # controls do not assert a reachable full-chip counterexample.
    copied_read_codes = [code for code in read_codes if code != 255]
    copied_update_codes = [code for code in update_rows[0]["codes_LSB_first"] if code != 3]
    read_missing = [i for i, code in enumerate(copied_read_codes) if code == 255]
    update_missing = [code for code in copied_update_codes if code == 3]
    if read_missing or update_missing:
        raise ValueError("Copied missing-branch control did not activate default")
    if len(copied_read_codes) != 255 or set(copied_update_codes) != {0, 1, 2}:
        raise ValueError("Copied missing-branch mutation did not remove exactly its actual selector")
    source_default = source["explicit_source_default_reset_state"]
    if source["saturating_function_cases"][3][1] != 3 or source_default == 3:
        raise ValueError("Exact-source missing11 branch did not alter saturation output")
    saved_read = paired["bht_read_default_definedness"]["negative_controls"]
    if saved_read["IR_semantic_missing_selector"]["observed_mutated_outputs"] != [0, 3] \
            or saved_read["exact_source_missing_last_entry"]["mutated_declared_last_entry"] != 254:
        raise ValueError("Saved read negatives have different restricted local semantics")
    saved_update = paired["bht_default_definedness"]["semantic_negative_control"]
    if saved_update["raw_state_witness"] != 3 or saved_update["observed_local_pmux_values"] != [0, 3]:
        raise ValueError("Saved update negative has different restricted local semantics")
    # Cross-check every saved proof row against independent reconstruction.
    stored_read = paired["bht_read_default_definedness"]["actual_selector_rows_MSB_first"]
    if len(stored_read) != 256:
        raise ValueError("Saved read selector population missing")
    for row in stored_read:
        bit = row["RTLIL_selector_bit"]
        if read_codes[bit] != row["decoded_index"]:
            raise ValueError("Saved actual read selector order differs")
    stored_update = paired["bht_default_definedness"]["entries"]
    actual_updates = {r["entry"]: r for r in update_rows}
    if len(stored_update) != 256:
        raise ValueError("Saved update entry population missing")
    for row in stored_update:
        actual = actual_updates[row["entry"]]
        if actual["pmux"] != row["pmux"] or list(reversed(actual["codes_LSB_first"])) != row["decoded_raw_codes"]:
            raise ValueError("Saved actual update selector order differs")

    remaining = [line for line in unknown if not (line.get("type") == "$pmux"
                 and line.get("cell") in {read["name"], *(c["name"] for c in updates)})]
    if len(unknown) != 358 or len(remaining) != 101:
        raise ValueError("Raw GOLD X/Z connect-line classification differs")
    groups = Counter()
    for line in remaining:
        if line["type"] == "module_connect":
            origin = "module_connect"
        else:
            origin = next((a.split('"')[1] for a in line["attributes"] if a.startswith("  attribute \\src ")), "NO_SRC")
        groups[(line["type"], origin)] += 1
    classification = [{"cell_type": kind, "original_source_origin": origin, "connect_line_count": count}
                      for (kind, origin), count in sorted(groups.items())]
    hashes = {path: sha(ROOT / path) for path in input_paths}
    if hashes != before:
        raise ValueError("A proof input changed during independent review")
    result = {"status": "PASS_INDEPENDENT_LOCAL_BHT_READ_AND_UPDATE_REVIEW",
              "input_sha256": hashes, "memory_enforcement": bound,
              "original_BHT_update_cells": 256, "original_BHT_read_cells": 1,
              "all_free_read_addresses_checked": 256, "free_read_table_data_bits": 512,
              "update_selector_state_cases": 1024, "exact_update_data_state_taken_cases": 2048,
              "source_saturation_cases": 8,
              "raw_data_concat_order_and_actual_output_slice_verified": True,
              "whole_source_undefined_abstraction": "OPEN", "full_sequential_LEC": "OPEN",
              "four_state_equivalence": "NOT_CLAIMED", "zero_init_or_invariant_premise_used": False,
              "independent_parser_or_evaluator_imported_from_BHT_checker": False,
              "independent_control_scope": "Local missing selectors and supported source bounds/function semantics only; no mutated frontend or full-chip reachable trace",
              "independent_controls": {"missing_read_code255_default_observable": True,
                                       "missing_update_state3_default_observable": True,
                                       "source_missing_state11_taken1_value_changes3_to1": True,
                                       "source_missing_last_table_entry_address255_out_of_range": True},
              "reconstructed_read_rows": read_rows,
              "reconstructed_update_rows": sorted(update_rows, key=lambda r: r["entry"]),
              "raw_GOLD_XZ_connect_line_count": 358, "BHT_local_connect_lines_closed": 257,
              "remaining_raw_GOLD_XZ_connect_line_count": 101,
              "remaining_XZ_connect_line_classification": classification,
              "remaining_XZ_connect_lines": remaining,
              "counts_are_connect_lines_not_bits": True,
              "external_tool_or_frontend_started": False}
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(result["status"], "read256/update2048cases;remaining101lines;peak", peak_memory(), flush=True)


if __name__ == "__main__":
    main()
