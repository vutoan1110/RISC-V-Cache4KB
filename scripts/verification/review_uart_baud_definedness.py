"""Independent UART baud local-proof method review with MSB-first parsing.

No import of the UART proof checker or the BHT RTLIL parser/evaluator.
Reads only the exact top module and four scalar decoder cells, then splits
the original binary B constant into four MSB-first sixteen-bit words.
This replays saved local evidence; it does not run another hardware flow.
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
from review_lec_onehot_cnf import ROOT, memory_cap, peak_memory


CFG = r"\u_soc.u_uart.cfg_reg"
RESULT = r"\u_soc.u_uart.u_uart_core.baudrate_gen_block.count_max"
INPUT = r"\u_soc.u_uart.u_uart_core.baudrate_gen_block.set_baud"


def hash_file(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1048576):
            value.update(block)
    return value.hexdigest()


def unique(pattern, text, label, flags=0):
    found = list(re.finditer(pattern, text, flags))
    if len(found) != 1:
        raise ValueError("Exactly one " + label + " required")
    return found[0]


def source_contract(text):
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
    if re.search(r"^\s*`", code, re.M):
        raise ValueError("Unsupported baud source directive")
    width = unique(r"\bparameter\s+COUNT_BIT_WIDTH\s*=\s*(\d+)", code, "source result width")
    if width[1] != "16":
        raise ValueError("Source result width must be exactly16")
    unique(r"\binput\s+\[1:0\]\s+set_baud\s*,", code, "source two-bit baud input")
    unique(r"\blogic\s+\[COUNT_BIT_WIDTH-1:0\]\s+count_max\s*;", code, "source result declaration")
    declarations = re.findall(r"\blocalparam\s+(BAUD\w+)\s*=\s*2'b([01]{2})\s*;", code)
    labels = {}
    for label, value in declarations:
        if label in labels:
            raise ValueError("Repeated source baud label")
        labels[label] = int(value, 2)
    if len(labels) != 4 or set(labels.values()) != {0, 1, 2, 3}:
        raise ValueError("Source labels do not uniquely cover all two-bit codes")
    block = unique(r"\balways_comb\s+begin\s+case\s*\(set_baud\)(.*?)\bendcase\s+end", code,
                   "source combinational case", re.S)
    clauses = block[1].split(";")
    rows, default = {}, None
    for clause in clauses:
        if not clause.strip():
            continue
        match = re.fullmatch(r"\s*(\w+)\s*:\s*count_max\s*=\s*16'd(\d+)\s*", clause)
        if not match:
            raise ValueError("Unsupported statement in source baud case")
        label, value = match[1], int(match[2])
        if value >= 65536:
            raise ValueError("Source divisor truncates declared width")
        if label == "default":
            if default is not None:
                raise ValueError("Repeated source default")
            default = value
        else:
            if label not in labels or labels[label] in rows:
                raise ValueError("Unknown or duplicate source baud branch")
            rows[labels[label]] = value
    if set(rows) != {0, 1, 2, 3} or default is None:
        raise ValueError("Source case has missing branches or default")
    return {"case_values": rows, "default": default, "input_bits": 2, "output_bits": 16}


def top_module(raw):
    match = unique(r"^module \\soc_asic_top\n(.*?)^end\s*$", raw, "original GOLD top module", re.M | re.S)
    return match[1], raw[:match.start(1)].count("\n") + 1


def parse_cells(top, first_line):
    result = {}
    for match in re.finditer(r"^  cell (\S+) ([^\n]+)\n(.*?)^  end\s*$", top, re.M | re.S):
        name = match[2]
        if name in result:
            raise ValueError("Duplicate top-module cell name")
        parameters, ports = {}, {}
        for line in match[3].splitlines():
            record = re.fullmatch(r"    (parameter|connect) (\\\S+) (.+)", line)
            if not record:
                if line.strip():
                    raise ValueError("Unsupported cell record in independent parser")
                continue
            target = parameters if record[1] == "parameter" else ports
            if record[2] in target:
                raise ValueError("Duplicate cell record")
            target[record[2]] = record[3]
        result[name] = {"type": match[1], "name": name, "parameters": parameters,
                        "ports": ports, "original_IR_line": first_line + top[:match.start()].count("\n")}
    return result


def vectors(mux):
    if mux["type"] != "$pmux" or mux["parameters"] != {"\\WIDTH": "16", "\\S_WIDTH": "4"}:
        raise ValueError("Exact original baud parallel mux widths required")
    ports = mux["ports"]
    if set(ports) != {"\\A", "\\B", "\\S", "\\Y"} or ports["\\A"] != "16'x" or ports["\\Y"] != RESULT:
        raise ValueError("Original UART default/result interface differs")
    selectors = re.fullmatch(r"\{ (.+) \}", ports["\\S"])
    if not selectors:
        raise ValueError("Exact scalar four-way selector concat required")
    names = selectors[1].split()
    data = re.fullmatch(r"64'([01]{64})", ports["\\B"])
    if len(names) != 4 or not data:
        raise ValueError("Exact original S/B vector lengths required")
    words = [int(data[1][start:start + 16], 2) for start in range(0, 64, 16)]
    return names, words


def selector_code(cell):
    p, c = cell["parameters"], cell["ports"]
    if p.get("\\A_WIDTH") != "2" or p.get("\\A_SIGNED") != "0" or p.get("\\Y_WIDTH") != "1" \
            or c.get("\\A") != CFG + " [1:0]":
        raise ValueError("Actual selector must use full unsigned two-bit cfg_reg[1:0]")
    if cell["type"] == "$logic_not":
        if set(p) != {"\\A_WIDTH", "\\A_SIGNED", "\\Y_WIDTH"} or set(c) != {"\\A", "\\Y"}:
            raise ValueError("Unsupported actual zero selector")
        return 0
    if cell["type"] != "$eq" or p.get("\\B_SIGNED") != "0" \
            or set(p) != {"\\A_WIDTH", "\\A_SIGNED", "\\B_WIDTH", "\\B_SIGNED", "\\Y_WIDTH"} \
            or set(c) != {"\\A", "\\B", "\\Y"}:
        raise ValueError("Unsupported equality selector")
    constant = re.fullmatch(r"([12])'([01]+)", c["\\B"])
    if not constant or len(constant[2]) != int(constant[1]) or p["\\B_WIDTH"] != constant[1]:
        raise ValueError("Malformed/undefined selector constant")
    return int(constant[2], 2)  # unsigned zero-extension to the actual two-bit A.


def evaluate(mux, cells, code, default):
    names, words = vectors(mux)
    flags = []
    for name in names:
        if name == "1'0":
            flags.append(0)
        else:
            if name not in cells or cells[name]["ports"].get("\\Y") != name:
                # Actual selector net names and decoder cell names differ.
                matches = [c for c in cells.values() if c["ports"].get("\\Y") == name]
                if len(matches) != 1:
                    raise ValueError("Missing or multiple original selector drivers")
                driver = matches[0]
            else:
                driver = cells[name]
            flags.append(int(code == selector_code(driver)))
    active = [index for index, flag in enumerate(flags) if flag]
    if len(active) > 1:
        raise ValueError("Overlapping PMUX selectors have no defined assumed behavior")
    return (words[active[0]] if active else default), flags, not bool(active)


def review(top, first_line, cells, source):
    muxes = [c for c in cells.values() if c["type"] == "$pmux" and c["ports"].get("\\Y") == RESULT]
    if len(muxes) != 1:
        raise ValueError("Exactly one raw UART baud output mux required")
    mux = muxes[0]
    cfg = unique(r"^  wire width (\d+) " + re.escape(CFG) + r"\s*$", top, "original config register width", re.M)
    output = unique(r"^  wire width (\d+) " + re.escape(RESULT) + r"\s*$", top, "original result width", re.M)
    port = unique(r"^  wire width (\d+) " + re.escape(INPUT) + r"\s*$", top, "original source input width", re.M)
    if (cfg[1], output[1], port[1]) != ("32", "16", "2"):
        raise ValueError("Original config/result/source input widths differ")
    unique(r"^  connect " + re.escape(INPUT) + " " + re.escape(CFG) + r" \[1:0\]\s*$", top,
           "original source input binding", re.M)
    selectors, data = vectors(mux)
    drivers = []
    for name in selectors:
        matches = [c for c in cells.values() if c["ports"].get("\\Y") == name]
        if len(matches) != 1:
            raise ValueError("Actual scalar selector driver not unique")
        drivers.append(matches[0])
    codes = [selector_code(c) for c in drivers]
    if len(set(selectors)) != 4 or set(codes) != {0, 1, 2, 3}:
        raise ValueError("Actual selectors do not cover every free code exactly once")
    rows = []
    for code in range(4):
        expected = source["case_values"][code]
        outputs = [evaluate(mux, cells, code, default) for default in (0, 65535)]
        if any(value != expected or default or sum(flags) != 1 for value, flags, default in outputs):
            raise ValueError("Original actual B word/default behavior differs from source")
        rows.append({"free_cfg_code": code, "source_value": expected, "actual_value": outputs[0][0],
                     "selector_flags_MSB_first": outputs[0][1], "default_selected": False})
    missing = copy.deepcopy(mux)
    fault_terms = list(selectors)
    position = codes.index(3)
    fault_terms[position] = "1'0"
    missing["ports"]["\\S"] = "{ " + " ".join(fault_terms) + " }"
    fault_outcomes = [evaluate(missing, cells, 3, default) for default in (0, 65535)]
    if any(not default for _, _, default in fault_outcomes) or [value for value, _, _ in fault_outcomes] != [0, 65535]:
        raise ValueError("Independent raw missing-selector control did not expose default")
    reversed_data = copy.deepcopy(mux)
    actual_bitstring = mux["ports"]["\\B"][3:]
    begin = position * 16
    bitstring = actual_bitstring[:begin] + actual_bitstring[begin:begin + 16][::-1] + actual_bitstring[begin + 16:]
    reversed_data["ports"]["\\B"] = "64'" + bitstring
    wrong, flags, default = evaluate(reversed_data, cells, 3, 0)
    if default or sum(flags) != 1 or wrong == source["case_values"][3]:
        raise ValueError("Independent raw B bit-order control did not alter selected output")
    malformed = []
    for label, mutate in (
        ("A_width1", lambda c: c["parameters"].update({"\\A_WIDTH": "1"})),
        ("A_signed1", lambda c: c["parameters"].update({"\\A_SIGNED": "1"})),
        ("cfg_slice2to1", lambda c: c["ports"].update({"\\A": CFG + " [2:1]"})),
        ("B_unknown_constant", lambda c: c["ports"].update({"\\B": "2'x"})),
    ):
        driver = copy.deepcopy(next(c for c in drivers if c["type"] == "$eq"))
        mutate(driver)
        try:
            selector_code(driver)
        except ValueError as error:
            malformed.append({"fault": label, "status": "REJECTED", "reason": str(error)})
        else:
            raise ValueError("Malformed original selector contract was accepted")
    bad_top = re.sub(r"(^  wire width )32( " + re.escape(CFG) + r"\s*$)", r"\g<1>1\2", top, flags=re.M)
    if bad_top == top:
        raise ValueError("Actual original port-width control did not modify its declaration")
    original_source = (ROOT / "hdl/baudrate_gen_block.sv").read_text(encoding="ascii")
    bad_source = original_source.replace("input  [1:0] set_baud", "input  [0:0] set_baud")
    if bad_source == original_source:
        raise ValueError("Source width control did not modify exact actual input declaration")
    try:
        source_contract(bad_source)
    except ValueError as error:
        malformed.append({"fault": "source_input_width1", "status": "REJECTED", "reason": str(error)})
    else:
        raise ValueError("Malformed source input width accepted")
    # Original top-width guard is checked directly to avoid recursive review.
    wrong_cfg = unique(r"^  wire width (\d+) " + re.escape(CFG) + r"\s*$", bad_top, "copied config width", re.M)
    if wrong_cfg[1] == "32":
        raise ValueError("Copied original config width fault did not differ")
    malformed.append({"fault": "original_cfg_wire_width1", "status": "REJECTED", "reason": "Copied raw config width1 differs from required32"})
    return {"raw_pmux": mux, "actual_selector_codes_MSB_first": codes,
            "actual_B_words_MSB_first": data, "four_free_cfg_cases": rows,
            "independent_negative_controls": {
                "missing_selector": {"actual_mutated_S": missing["ports"]["\\S"], "cfg_code": 3,
                                     "arbitrary_default_values": [0, 65535], "observed_values": [v for v, _, _ in fault_outcomes]},
                "bit_order": {"actual_mutated_B": reversed_data["ports"]["\\B"], "cfg_code": 3,
                              "original_value": source["case_values"][3], "mutated_value": wrong},
                "malformed_source_port_or_selector_guards": malformed}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if out.exists() or not out.is_relative_to(ROOT):
        raise ValueError("New independent review receipt required")
    enforced = memory_cap()
    paths = ["results/uart_baud_default_definedness_20261010_p1.json",
             "results/uart_baud_default_definedness_20261010_p2.json",
             "scripts/verification/review_uart_baud_definedness.py"]
    proofs = [json.loads((ROOT / p).read_text(encoding="ascii")) for p in paths[:2]]
    if proofs[0] != proofs[1] or hash_file(ROOT / paths[0]) != hash_file(ROOT / paths[1]):
        raise ValueError("Saved UART pair differs in bytes or fields")
    proof = proofs[0]
    for path, expected in proof["input_sha256"].items():
        if hash_file(ROOT / path) != expected:
            raise ValueError("Saved UART proof input changed")
        paths.append(path)
    paths = sorted(set(paths))
    hashes = {path: hash_file(ROOT / path) for path in paths}
    sources = [source_contract((ROOT / path).read_text(encoding="ascii")) for path in
               ("hdl/baudrate_gen_block.sv", "asic/snapshots/rtl_r14/hdl/baudrate_gen_block.sv")]
    if sources[0] != sources[1]:
        raise ValueError("Independent current/signed source contracts differ")
    parent_bindings = []
    for prefix in ("hdl/", "asic/snapshots/rtl_r14/hdl/"):
        for filename, instance, expected in (("uart_core.sv", "baudrate_gen_block", "set_baud"),
                                              ("uart_apb.v", "u_uart_core", "cfg_reg[1:0]")):
            path = prefix + filename
            text = re.sub(r"//[^\n]*|/\*.*?\*/", "", (ROOT / path).read_text(encoding="ascii"), flags=re.S)
            typename = "baudrate_gen_block" if filename == "uart_core.sv" else "uart_core"
            block = unique(r"\b" + typename + r"\s+" + instance + r"\s*\((.*?)\)\s*;", text,
                           "default-parameter parent source instance", re.S)
            unique(r"\.set_baud\s*\(\s*" + re.escape(expected) + r"\s*\)", block[1], "source port binding")
            parent_bindings.append({"path": path, "set_baud": expected})
    raw = (ROOT / "asic/equiv/lec/gold_flat_r14.il").read_text(encoding="ascii")
    top, first_line = top_module(raw)
    cells = parse_cells(top, first_line)
    reviewed = review(top, first_line, cells, sources[0])
    if proof["status"] != "PROVED_LOCAL_UART_BAUD_BOOLEAN_DEFAULT_DEFINEDNESS_ONLY" \
            or proof["init_reset_legal_state_or_invariant_assumption_used"] \
            or proof["actual_cfg_support_bits"] != 2 or proof["actual_mux_result_bits"] != 16:
        raise ValueError("Saved proof premise or count scope differs")
    reconstructed = {r["free_cfg_code"]: r["actual_value"] for r in reviewed["four_free_cfg_cases"]}
    stored = {r["free_cfg_code"]: r["actual_output_value"] for r in proof["free_configuration_truth_cases"]}
    if reconstructed != stored or len(proof["free_configuration_truth_cases"]) != 4:
        raise ValueError("Saved truth rows differ from independent original-IR reconstruction")
    for row in proof["actual_decoded_selector_and_data_rows"]:
        position = 3 - row["selector_LSB_bit"]
        if reviewed["actual_selector_codes_MSB_first"][position] != row["decoded_unsigned_cfg_code"] \
                or reviewed["actual_B_words_MSB_first"][position] != row["actual_data_value"]:
            raise ValueError("Saved selector/B bit order differs from independent reconstruction")
    if len(proof["actual_decoded_selector_and_data_rows"]) != 4:
        raise ValueError("Saved decoder population incomplete")
    own_negative = reviewed["independent_negative_controls"]
    if own_negative["missing_selector"]["observed_values"] != proof["negative_controls"]["missing_actual_code3_selector"]["observed_values"] \
            or own_negative["bit_order"]["mutated_value"] != proof["negative_controls"]["reversed_actual_selected_16bit_B_slice"]["observed_mutated_value"]:
        raise ValueError("Saved semantic negatives differ from independent actual-SigSpec evaluation")
    if any(hash_file(ROOT / path) != expected for path, expected in hashes.items()):
        raise ValueError("An independent review input changed")
    result = {"status": "PASS_INDEPENDENT_LOCAL_UART_BAUD_DEFINEDNESS_METHOD_REVIEW",
              "input_sha256": hashes, "memory_enforcement": enforced,
              "saved_pair_byte_and_all_field_equal": True, "ignored_pair_fields": [],
              "independent_implementation": "Separate exact top-body/cell regex parser, MSB-first64bit B split and actual scalar decoder interpreter; no UART/BHT proof parser or evaluator imported",
              "source_contract": sources[0], "parent_source_bindings": parent_bindings,
              "all_free_two_bit_cfg_codes_checked": 4, "all16_default_data_bits_free": True,
              "reset_init_invariant_premises_used": False, "local_GOLD_connect_line_closed": 1,
              "total_BHT_and_UART_baud_local_GOLD_lines_closed": 258,
              "remaining_GOLD_functional_XZ_connect_lines": 100,
              "count_unit": "Classified connect lines, not bits, defects or full-chip equivalence obligations",
              "full_sequential_LEC": "OPEN", "whole_source_undefined_abstraction": "OPEN",
              "four_state_equivalence": "NOT_CLAIMED", "external_tools_started": False,
              "negative_control_scope": "Local in-memory original SigSpec and source/port guard faults only; no whole-chip reachable trace or mutated frontend claim",
              **reviewed}
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(result["status"], "4codes;2semantic+6guardcontrols;peak", peak_memory(), flush=True)


if __name__ == "__main__":
    main()
