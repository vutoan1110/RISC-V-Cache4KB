"""Local Boolean definedness of the actual pre-setundef UART baud mux.

All four configuration codes are free. Exact current/signed source cases,
raw unsigned selector widths and actual B-data bit ordering are checked.
No initialization, reset, invariant or source-X coercion is assumed.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
from review_bht_definedness import read_il, bits, decoder, sha
from review_lec_onehot_cnf import ROOT, memory_cap, peak_memory


CFG = r"\u_soc.u_uart.cfg_reg"
OUTPUT = r"\u_soc.u_uart.u_uart_core.baudrate_gen_block.count_max"
INPUT = r"\u_soc.u_uart.u_uart_core.baudrate_gen_block.set_baud"


def source_case(path):
    raw = path.read_text(encoding="ascii")
    text = re.sub(r"//[^\r\n]*|/\*.*?\*/", "", raw, flags=re.S)
    if re.search(r"^\s*`", text, re.M):
        raise ValueError("Unsupported macro/directive in exact baud source")
    width = re.findall(r"parameter\s+COUNT_BIT_WIDTH\s*=\s*(\d+)", text)
    if width != ["16"] or len(re.findall(r"input\s*\[1:0\]\s*set_baud\s*,", text)) != 1 \
            or len(re.findall(r"logic\s*\[COUNT_BIT_WIDTH-1:0\]\s*count_max\s*;", text)) != 1:
        raise ValueError("Exact source width/input/result contract missing")
    declared = re.findall(r"localparam\s+(BAUD\w+)\s*=\s*2'b([01]{2})\s*;", text)
    codes = {name: int(value, 2) for name, value in declared}
    if len(declared) != 4 or len(codes) != 4 or set(codes.values()) != set(range(4)):
        raise ValueError("Source baud codes do not cover all four Boolean inputs")
    blocks = list(re.finditer(r"always_comb\s+begin\s+case\s*\(set_baud\)(.*?)endcase\s+end", text, re.S))
    if len(blocks) != 1:
        raise ValueError("Unique unconditional source baud case missing")
    body = blocks[0][1]
    assignments = re.findall(r"(BAUD\w+|default)\s*:\s*count_max\s*=\s*16'd(\d+)\s*;", body)
    leftovers = re.sub(r"(BAUD\w+|default)\s*:\s*count_max\s*=\s*16'd\d+\s*;", "", body)
    if leftovers.strip() or len(assignments) != 5 or {name for name, _ in assignments} != set(codes) | {"default"}:
        raise ValueError("Unsupported alternative source case semantics")
    values = {name: int(value) for name, value in assignments}
    if any(value < 0 or value >= 65536 for value in values.values()):
        raise ValueError("Source divisor exceeds declared data width")
    cases = {codes[name]: values[name] for name in codes}
    return {"case_values_by_unsigned_code": cases, "source_default_value": values["default"],
            "code_parameters": codes, "input_bits": 2, "result_bits": 16,
            "case_start_line": text[:blocks[0].start()].count("\n") + 1,
            "case_end_line": text[:blocks[0].end()].count("\n") + 1}


def load_actual():
    widths, cells, connections, _ = read_il(ROOT / "asic/equiv/lec/gold_flat_r14.il")
    candidates = [cell for cell in cells if cell["type"] == "$pmux" and cell["c"].get("\\Y") == OUTPUT]
    if len(candidates) != 1:
        raise ValueError("Exactly one actual baud output mux required")
    mux = candidates[0]
    if mux["p"] != {"\\WIDTH": "16", "\\S_WIDTH": "4"} or set(mux["c"]) != {"\\A", "\\B", "\\S", "\\Y"} \
            or mux["c"]["\\A"] != "16'x" or widths[CFG] != 32 or widths[OUTPUT] != 16:
        raise ValueError("Actual baud mux/config/result contract differs")
    binding = [r for r in connections if r["lhs"] == INPUT]
    if len(binding) != 1 or binding[0]["rhs"] != CFG + " [1:0]":
        raise ValueError("Original source baud input does not bind to exact cfg_reg[1:0]")
    drivers = {}
    for cell in cells:
        if "\\Y" not in cell["c"]:
            continue
        outputs = bits(cell["c"]["\\Y"], widths)
        if len(outputs) == 1:
            if outputs[0] in drivers:
                raise ValueError("Ambiguous actual scalar selector driver")
            drivers[outputs[0]] = cell
    return widths, mux, drivers, binding[0]


def decode_actual(mux, widths, drivers):
    selections = bits(mux["c"]["\\S"], widths)
    data = bits(mux["c"]["\\B"], widths)
    if len(selections) != 4 or len(set(selections)) != 4 or len(data) != 64 \
            or any(type(bit) is not int for bit in data):
        raise ValueError("Actual selector/data size or constant ordering unsupported")
    rows = []
    for index, atom in enumerate(selections):
        if atom not in drivers:
            raise ValueError("Actual selector is not an original scalar decoder")
        driver = drivers[atom]
        code = decoder(driver, [(CFG, 0), (CFG, 1)], widths)
        word = data[16 * index:16 * (index + 1)]
        rows.append({"selector_LSB_bit": index, "original_selector_bit_atom": atom,
                     "decoded_unsigned_cfg_code": code, "original_driver": driver,
                     "actual_data_bits_LSB_first": word,
                     "actual_data_value": sum(bit << offset for offset, bit in enumerate(word))})
    if {r["decoded_unsigned_cfg_code"] for r in rows} != set(range(4)):
        raise ValueError("Actual UART selectors do not cover all free two-bit config codes")
    return rows


def pmux_evaluate(mux, code, arbitrary_default, widths, drivers):
    """Evaluate the actual raw S/B SigSpecs, including copied constant-zero faults."""
    flags = []
    for atom in bits(mux["c"]["\\S"], widths):
        if type(atom) is int:
            flags.append(atom)
        elif atom in drivers:
            flags.append(int(code == decoder(drivers[atom], [(CFG, 0), (CFG, 1)], widths)))
        else:
            raise ValueError("Unsupported copied PMUX selector atom")
    data = bits(mux["c"]["\\B"], widths)
    if len(flags) != 4 or len(data) != 64 or any(type(bit) is not int for bit in data):
        raise ValueError("Invalid actual/copied PMUX signal dimensions")
    chosen = [index for index, flag in enumerate(flags) if flag]
    if len(chosen) > 1:
        raise ValueError("Overlapping PMUX selectors; behavior cannot be assumed")
    if not chosen:
        return arbitrary_default, flags, True
    index = chosen[0]
    return sum(bit << offset for offset, bit in enumerate(data[16 * index:16 * (index + 1)])), flags, False


def literal(bit_vector):
    if any(type(bit) is not int or bit not in (0, 1) for bit in bit_vector):
        raise ValueError("Defined binary bit-vector required")
    return str(len(bit_vector)) + "'" + "".join(str(bit) for bit in reversed(bit_vector))


def negative_controls(mux, rows, widths, drivers, source):
    missing = copy.deepcopy(mux)
    terms = missing["c"]["\\S"][2:-2].split()
    if len(terms) != 4:
        raise ValueError("Original four-scalar selector concat required for exact missing-selector mutation")
    row = next(r for r in rows if r["decoded_unsigned_cfg_code"] == 3)
    position = 3 - row["selector_LSB_bit"]
    removed = terms[position]
    terms[position] = "1'0"
    missing["c"]["\\S"] = "{ " + " ".join(terms) + " }"
    missing_results = [pmux_evaluate(missing, 3, value, widths, drivers) for value in (0, 65535)]
    if any(not default for _, _, default in missing_results) or [value for value, _, _ in missing_results] != [0, 65535]:
        raise ValueError("Actual copied selector fault did not expose arbitrary default")
    reordered = copy.deepcopy(mux)
    data = bits(mux["c"]["\\B"], widths)
    begin = 16 * row["selector_LSB_bit"]
    data[begin:begin + 16] = reversed(data[begin:begin + 16])
    reordered["c"]["\\B"] = literal(data)
    wrong_value, _, default_selected = pmux_evaluate(reordered, 3, 0, widths, drivers)
    expected = source["case_values_by_unsigned_code"][3]
    if default_selected or wrong_value == expected:
        raise ValueError("Actual copied data-bit-order fault did not alter defined selected output")
    return {"missing_actual_code3_selector": {
                "status": "DISPROVED_DEFAULT_UNREACHABILITY_FOR_COPIED_RAW_PMUX",
                "original_selector_net": removed, "actual_mutated_S_SigSpec": missing["c"]["\\S"],
                "free_cfg_code_witness": 3, "arbitrary_default_values": [0, 65535],
                "observed_values": [value for value, _, _ in missing_results],
                "default_selected": True},
            "reversed_actual_selected_16bit_B_slice": {
                "status": "DISPROVED_SOURCE_DATA_EQUALITY_FOR_COPIED_RAW_PMUX",
                "actual_mutated_B_SigSpec": reordered["c"]["\\B"],
                "free_cfg_code_witness": 3, "original_expected_value": expected,
                "observed_mutated_value": wrong_value, "default_selected": False},
            "scope": "Local copied raw signal semantics only; no mutated source/frontend or full-chip reachable trace",
            "mutations_written_to_source_or_IR": False}


def prove():
    current, snapshot = [source_case(ROOT / path) for path in
                         ("hdl/baudrate_gen_block.sv", "asic/snapshots/rtl_r14/hdl/baudrate_gen_block.sv")]
    if current != snapshot:
        raise ValueError("Current and signed source baud cases differ")
    parent_sources = []
    for prefix in ("hdl/", "asic/snapshots/rtl_r14/hdl/"):
        for name, expression in (("uart_core.sv", r"baudrate_gen_block\s+baudrate_gen_block\s*\((.*?)\)\s*;"),
                                 ("uart_apb.v", r"uart_core\s+u_uart_core\s*\((.*?)\)\s*;")):
            path = prefix + name
            source = re.sub(r"//[^\r\n]*|/\*.*?\*/", "", (ROOT / path).read_text(encoding="ascii"), flags=re.S)
            instances = re.findall(expression, source, re.S)
            expected = "set_baud" if name == "uart_core.sv" else "cfg_reg[1:0]"
            if len(instances) != 1 or not re.search(r"\.set_baud\s*\(\s*" + re.escape(expected) + r"\s*\)", instances[0]):
                raise ValueError("Parent baud input source binding or default parameter instance differs")
            parent_sources.append({"path": path, "set_baud_connection": expected})
    widths, mux, drivers, binding = load_actual()
    rows = decode_actual(mux, widths, drivers)
    truth = []
    for code in range(4):
        expected = current["case_values_by_unsigned_code"][code]
        outcomes = [pmux_evaluate(mux, code, default, widths, drivers) for default in (0, 65535)]
        if any(value != expected or selected or sum(flags) != 1 for value, flags, selected in outcomes):
            raise ValueError("Actual original baud data/default behavior differs from source case")
        truth.append({"free_cfg_code": code, "active_selector_count": 1,
                      "source_case_value": expected, "actual_output_value": outcomes[0][0],
                      "actual_selector_bits_LSB_first": outcomes[0][1], "default_selected": False,
                      "output_expression_independent_of_all16_undefined_default_bits": True})
    negatives = negative_controls(mux, rows, widths, drivers, current)
    return {"current_and_signed_source_case_equal": True, "source_case_contract": current,
            "parent_source_bindings": parent_sources, "original_IR_input_binding": binding,
            "original_raw_pmux": mux, "actual_decoded_selector_and_data_rows": rows,
            "free_configuration_truth_cases": truth, "negative_controls": negatives}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if out.exists() or not out.is_relative_to(ROOT):
        raise ValueError("New research output required; no existing receipt may be replaced")
    enforced = memory_cap()
    paths = ["hdl/baudrate_gen_block.sv", "asic/snapshots/rtl_r14/hdl/baudrate_gen_block.sv",
             "hdl/uart_core.sv", "asic/snapshots/rtl_r14/hdl/uart_core.sv",
             "hdl/uart_apb.v", "asic/snapshots/rtl_r14/hdl/uart_apb.v",
             "asic/equiv/lec/gold_flat_r14.il", "asic/equiv/lec/gold_flat_r14.ys",
             "scripts/verification/check_uart_baud_default_definedness.py",
             "scripts/verification/review_bht_definedness.py", "scripts/verification/review_lec_onehot_cnf.py",
             "results/uart_baud_definedness_controls_20261010.json"]
    hashes = {path: sha(ROOT / path) for path in paths}
    control = json.loads((ROOT / paths[-1]).read_text(encoding="ascii"))
    if control["status"] != "PASS_LOCAL_UART_BAUD_ACTUAL_IR_CONTROLS" \
            or any(sha(ROOT / path) != expected for path, expected in control["input_sha256"].items()):
        raise ValueError("Frozen actual-IR controls not valid for current checker/source")
    result = prove()
    if any(sha(ROOT / path) != expected for path, expected in hashes.items()):
        raise ValueError("Input changed during local baud proof")
    receipt = {"status": "PROVED_LOCAL_UART_BAUD_BOOLEAN_DEFAULT_DEFINEDNESS_ONLY",
               "input_sha256": hashes, "memory_enforcement": enforced,
               "method": "Exact source case/default/parent bindings plus raw pre-setundef unsigned selector and B SigSpec interpretation; all four two-bit configuration codes free",
               "actual_cfg_support_bits": 2, "actual_mux_result_bits": 16,
               "all_boolean_cfg_codes_checked": 4,
               "IR_undefined_default_connect_lines_closed": 1,
               "all_undefined_default_data_bits_free": 16,
               "init_reset_legal_state_or_invariant_assumption_used": False,
               "GOLD_functional_XZ_connect_lines_classified": 358,
               "earlier_BHT_locally_closed_lines": 257,
               "BHT_and_UART_baud_locally_closed_lines_after_review": 258,
               "remaining_GOLD_functional_XZ_connect_lines_after_review": 100,
               "count_scope": "Connect lines, not bits or whole-chip defect/equivalence counts",
               "full_sequential_LEC": "OPEN", "whole_source_undefined_abstraction": "OPEN",
               "four_state_equivalence": "NOT_CLAIMED", "independent_method_review": "PENDING",
               "external_tool_or_frontend_started": False,
               **result}
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print(receipt["status"], "all4cfg/data codes;16 default bits free;peak", peak_memory(), flush=True)


if __name__ == "__main__":
    main()
