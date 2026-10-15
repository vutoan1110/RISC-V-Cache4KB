"""Unused-A default proof for three actual Icache hot-array read muxes.

All three-bit indexes and original array data bits are free. This proves
only that the local A default is unused and the selected B slice matches
the source array access; no global Y-definedness or full LEC is inferred.
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


BASE = r"\u_soc.u_icache.g_dm_baseline.u_controller"
PC = r"\u_soc.u_core.u_pipeline.datapath.pc_f"
MISS = BASE + ".miss_index"
TARGETS = {"$procmux$22675": {"array": "hot_tag", "width": 25, "slice": [24, 0], "index": "request"},
           "$procmux$22684": {"array": "hot_line", "width": 128, "slice": [127, 0], "index": "request"},
           "$procmux$22693": {"array": "hot_tag", "width": 5, "slice": [4, 0], "index": "miss"}}


def require(pattern, text, label):
    found = list(re.finditer(pattern, text, re.S))
    if len(found) != 1:
        raise ValueError("Exactly one " + label + " required")
    return found[0]


def clean(path):
    return re.sub(r"//[^\r\n]*|/\*.*?\*/", "", path.read_text(encoding="ascii"), flags=re.S)


def source_chain(prefix, asic_top):
    controller = clean(ROOT / (prefix + "cache/icache_controller.v"))
    cache = clean(ROOT / (prefix + "cache/icache.v"))
    soc = clean(ROOT / (prefix + "soc_top.v"))
    wrapper = clean(ROOT / asic_top)
    chip = require(r"soc_top\s*#\s*\((.*?)\)\s*u_soc\s*\(", wrapper, "DM ASIC SoC instance")
    for parameter, value in (("ICACHE_LINE_COUNT", "256"), ("L0_ENTRIES", "8"), ("CACHE_CONFIG", "0")):
        require(r"\." + parameter + r"\s*\(\s*" + value + r"\s*\)", chip[1], "exact ASIC " + parameter)
    soc_cache = require(r"icache\s*#\s*\((.*?)\)\s*u_icache\s*\((.*?)\)\s*;", soc, "SoC Icache instance")
    for parameter, value in (("LINE_COUNT", "ICACHE_LINE_COUNT"), ("L0_ENTRIES", "L0_ENTRIES"), ("CACHE_CONFIG", "CACHE_CONFIG")):
        require(r"\." + parameter + r"\s*\(\s*" + value + r"\s*\)", soc_cache[1], "forwarded " + parameter)
    require(r"\.req_addr\s*\(\s*if_req_addr\s*\)", soc_cache[2], "SoC request address binding")
    require(r"if\s*\(CACHE_CONFIG\s*==\s*0\)\s*begin\s*:\s*g_dm_baseline", cache, "DM controller branch")
    require(r"localparam\s+INDEX_WIDTH\s*=\s*\(LINE_COUNT>1\)\?clog2\(LINE_COUNT\):1\s*;", cache, "derived index width")
    require(r"localparam\s+TAG_WIDTH\s*=\s*32-4-INDEX_WIDTH\s*;", cache, "derived main tag width")
    clog = require(r"function\s+integer\s+clog2\s*;(.*?)endfunction", cache, "parent clog2 function")
    require(r"tmp\s*=\s*value-1;\s*clog2\s*=\s*0;\s*while\(tmp>0\)\s*begin\s*clog2\s*=\s*clog2\+1;\s*tmp\s*=\s*tmp>>1;\s*end", clog[1], "exact parent width calculation")
    instance = require(r"icache_controller\s*#\s*\((.*?)\)\s*u_controller\s*\((.*?)\)\s*;", cache, "Icache controller instance")
    for parameter in ("INDEX_WIDTH", "TAG_WIDTH", "L0_ENTRIES"):
        require(r"\." + parameter + r"\s*\(\s*" + parameter + r"\s*\)", instance[1], "controller " + parameter)
    require(r"\.req_addr\s*\(req_addr\)", instance[2], "controller request binding")
    patterns = {
        "request_address_declaration": r"input\s+wire\s*\[31:0\]\s+req_addr\s*,",
        "miss_index_declaration": r"reg\s*\[INDEX_WIDTH-1:0\]\s*miss_index\s*;",
        "index_bit_calculation": r"localparam\s+L0_IDX_BITS\s*=\s*\(L0_ENTRIES\s*>\s*1\)\s*\?\s*\$clog2\(L0_ENTRIES\)\s*:\s*1\s*;",
        "hot_tag_declaration": r"reg\s*\[27-L0_IDX_BITS:0\]\s*hot_tag\s*\[0:L0_ENTRIES-1\]\s*;",
        "hot_line_declaration": r"reg\s*\[127:0\]\s*hot_line\s*\[0:L0_ENTRIES-1\]\s*;",
        "request_block": r"assign\s+request_block\s*=\s*req_addr\[31:4\]\s*;",
        "miss_block": r"assign\s+miss_block\s*=\s*\{miss_tag,\s*miss_index\}\s*;",
        "hot_index": r"assign\s+hot_index\s*=\s*request_block\[L0_IDX_BITS-1:0\]\s*;",
        "miss_hot_index": r"assign\s+miss_hot_index\s*=\s*miss_block\[L0_IDX_BITS-1:0\]\s*;",
        "hot_tag_read": r"hot_tag\[hot_index\]\s*==\s*request_block\[27:L0_IDX_BITS\]",
        "hot_line_read": r"assign\s+hot_hit_line\s*=\s*hot_line\[hot_index\]\s*;",
        "miss_tag_slice_width": r"localparam\s+HOT_LI_BITS\s*=\s*INDEX_WIDTH\s*-\s*L0_IDX_BITS\s*;",
        "miss_tag_read": r"hot_tag\[miss_hot_index\]\[HOT_LI_BITS-1:0\]\s*==\s*miss_index\[INDEX_WIDTH-1:L0_IDX_BITS\]",
    }
    facts = {key: " ".join(require(pattern, controller, key)[0].split()) for key, pattern in patterns.items()}
    return {"source_prefix": prefix, "ASIC_top": asic_top, "cache_lines": 256,
            "controller_index_bits": (256 - 1).bit_length(), "controller_tag_bits": 20,
            "L0_entries": 8, "L0_index_bits": 3, "hot_tag_bits": 25, "hot_line_bits": 128,
            "miss_hot_tag_read_bits": 5, "source_array_and_index_contract": facts}


def actual():
    widths, cells, connections, _ = read_il(ROOT / "asic/equiv/lec/gold_flat_r14.il")
    muxes = {cell["name"]: cell for cell in cells if cell["name"] in TARGETS}
    if set(muxes) != set(TARGETS) or widths[PC] != 32 or widths[MISS] != 8 or widths[BASE + ".miss_tag"] != 20:
        raise ValueError("Raw target population or main index/PC/tag widths differ")
    if widths[BASE + ".hot_index"] != 3 or widths[BASE + ".miss_hot_index"] != 3:
        raise ValueError("Original hot/miss index declarations are not exactly3bits")
    expected = {BASE + ".req_addr": PC, BASE + ".request_block": PC + " [31:4]",
                BASE + ".hot_index": PC + " [6:4]", BASE + ".miss_hot_index": MISS + " [2:0]",
                BASE + ".miss_block": "{ " + BASE + ".miss_tag " + MISS + " }"}
    bindings = [c for c in connections if c["lhs"] in expected]
    if len(bindings) != 5 or any(c["rhs"] != expected[c["lhs"]] for c in bindings):
        raise ValueError("Original source request/miss index bindings differ")
    drivers = {}
    for cell in cells:
        if "\\Y" in cell["c"]:
            atoms = bits(cell["c"]["\\Y"], widths)
            if len(atoms) == 1:
                if atoms[0] in drivers:
                    raise ValueError("Multiple raw scalar decoder drivers")
                drivers[atoms[0]] = cell
    return widths, muxes, drivers, bindings


def select(mux, descriptor, address, widths, drivers):
    width = descriptor["width"]
    if mux["type"] != "$pmux" or mux["p"] != {"\\WIDTH": str(width), "\\S_WIDTH": "8"} \
            or mux["c"]["\\A"] != str(width) + "'x":
        raise ValueError("Exact read mux and undefined-default width required")
    index = [(PC, bit) for bit in range(4, 7)] if descriptor["index"] == "request" else [(MISS, bit) for bit in range(3)]
    selectors, data = bits(mux["c"]["\\S"], widths), bits(mux["c"]["\\B"], widths)
    if len(selectors) != 8 or len(data) != 8 * width:
        raise ValueError("Actual selector/B vector size differs")
    flags = [atom if type(atom) is int else int(address == decoder(drivers[atom], index, widths)) for atom in selectors]
    selected = [position for position, flag in enumerate(flags) if flag]
    if len(selected) > 1:
        raise ValueError("Overlapping selector behavior cannot be assumed")
    if not selected:
        return [("DEFAULT_A", bit) for bit in range(width)], flags, True
    position = selected[0]
    return data[position * width:(position + 1) * width], flags, False


def words_msb(expression):
    if not expression.startswith("{ ") or not expression.endswith(" }"):
        raise ValueError("Exact B word concat required")
    words = re.findall(r"\S+(?:\s+\[\d+(?::\d+)?\])?", expression[2:-2])
    if len(words) != 8:
        raise ValueError("Exact eight source B words required")
    return words


def controls(mux, description, widths, drivers):
    missing = copy.deepcopy(mux)
    terms = missing["c"]["\\S"][2:-2].split()
    if len(terms) != 8:
        raise ValueError("Exact original scalar selector concat required")
    index = [(PC, b) for b in range(4, 7)] if description["index"] == "request" else [(MISS, b) for b in range(3)]
    codes_msb = [decoder(drivers[bits(term, widths)[0]], index, widths) for term in terms]
    position = codes_msb.index(7)
    removed = terms[position]
    terms[position] = "1'0"
    missing["c"]["\\S"] = "{ " + " ".join(terms) + " }"
    output, flags, is_default = select(missing, description, 7, widths, drivers)
    if not is_default or sum(flags) != 0 or output != [("DEFAULT_A", b) for b in range(description["width"])]:
        raise ValueError("Actual selector-zero fault did not expose default")
    swapped = copy.deepcopy(mux)
    words = words_msb(swapped["c"]["\\B"])
    other = codes_msb.index(6)
    words[position], words[other] = words[other], words[position]
    swapped["c"]["\\B"] = "{ " + " ".join(words) + " }"
    original, _, _ = select(mux, description, 7, widths, drivers)
    mutated, swap_flags, swap_default = select(swapped, description, 7, widths, drivers)
    if swap_default or sum(swap_flags) != 1 or original == mutated:
        raise ValueError("Actual B word swap did not alter selected symbolic source word")
    witness = {atom: (2 >> bit) & 1 for bit, atom in enumerate(original)}
    witness.update({atom: (1 >> bit) & 1 for bit, atom in enumerate(mutated)})
    old_value = sum(witness[atom] << bit for bit, atom in enumerate(original))
    new_value = sum(witness[atom] << bit for bit, atom in enumerate(mutated))
    if old_value != 2 or new_value != 1:
        raise ValueError("Actual B-swap free-data witness is not observable")
    return {"missing_code7_selector": {"status": "DISPROVED_UNUSED_A_IN_COPIED_MUX", "removed_selector": removed,
                                      "mutated_actual_S": missing["c"]["\\S"], "raw_index": 7,
                                      "default_data_witness_values": [0, (1 << description["width"]) - 1],
                                      "default_selected": True},
            "actual_B_words6_and7_swapped": {"status": "DISPROVED_SOURCE_ARRAY_IDENTITY_IN_COPIED_MUX",
                                             "mutated_actual_B": swapped["c"]["\\B"], "raw_index": 7,
                                             "original_free_data_witness_value": old_value,
                                             "mutated_free_data_witness_value": new_value,
                                             "data_binding_is_control_witness_not_initial_state_assumption": True},
            "source_or_IR_mutated_on_disk": False,
            "scope": "Local exact copied SigSpec faults only; no mutated frontend or whole-chip reachable trace"}


def prove():
    source = [source_chain("hdl/", "asic/soc_dm_4kb/soc_asic_top.v"),
              source_chain("asic/snapshots/rtl_r14/hdl/", "asic/snapshots/rtl_r14/asic/soc_dm_4kb/soc_asic_top.v")]
    ignored = {"source_prefix", "ASIC_top"}
    if any(source[0][key] != source[1][key] for key in set(source[0]) - ignored):
        raise ValueError("Current/signed DM source array/index/depth contracts differ")
    widths, muxes, drivers, bindings = actual()
    targets, free_bits = [], set()
    for name, description in TARGETS.items():
        mux = muxes[name]
        s = bits(mux["c"]["\\S"], widths)
        expected = [(PC, bit) for bit in range(4, 7)] if description["index"] == "request" else [(MISS, bit) for bit in range(3)]
        if len(set(s)) != 8 or any(atom not in drivers for atom in s):
            raise ValueError("Original read must use eight distinct scalar decoded selectors")
        decoded = [decoder(drivers[atom], expected, widths) for atom in s]
        if set(decoded) != set(range(8)):
            raise ValueError("Actual three-bit decoder is incomplete")
        rows = []
        for address in range(8):
            atoms, flags, default = select(mux, description, address, widths, drivers)
            word = BASE + "." + description["array"] + "[" + str(address) + "]"
            expected_atoms = [(word, bit) for bit in range(description["slice"][1], description["slice"][0] + 1)]
            if default or sum(flags) != 1 or atoms != expected_atoms or widths[word] != (25 if description["array"] == "hot_tag" else 128):
                raise ValueError("Actual selected B slice mismatches original source array word")
            free_bits.update(atoms)
            rows.append({"free_raw_index": address, "active_selector_count": 1, "A_default_selected": False,
                         "actual_selected_B_bit_atoms_LSB_first": atoms})
        targets.append({"descriptor": description, "actual_original_pmux": mux,
                        "actual_selector_codes_LSB_first": decoded, "all_eight_free_index_cases": rows,
                        "negative_controls": controls(mux, description, widths, drivers)})
    return {"current_and_signed_source_chain_contracts_equal": True, "source_chain_contracts": source,
            "original_IR_index_source_bindings": bindings, "targets": targets,
            "unique_original_array_bit_atoms_free": len(free_bits)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if out.exists() or not out.is_relative_to(ROOT):
        raise ValueError("New research receipt required")
    enforced = memory_cap()
    paths = ["hdl/cache/icache_controller.v", "hdl/cache/icache.v", "hdl/soc_top.v", "asic/soc_dm_4kb/soc_asic_top.v",
             "asic/snapshots/rtl_r14/hdl/cache/icache_controller.v", "asic/snapshots/rtl_r14/hdl/cache/icache.v",
             "asic/snapshots/rtl_r14/hdl/soc_top.v", "asic/snapshots/rtl_r14/asic/soc_dm_4kb/soc_asic_top.v",
             "asic/equiv/lec/gold_flat_r14.il", "asic/equiv/lec/gold_flat_r14.ys",
             "scripts/verification/check_icache_hot_default_definedness.py", "scripts/verification/review_bht_definedness.py",
             "scripts/verification/review_lec_onehot_cnf.py", "results/icache_hot_definedness_controls_20261010.json"]
    before = {p: sha(ROOT / p) for p in paths}
    control = json.loads((ROOT / paths[-1]).read_text(encoding="ascii"))
    if control["status"] != "PASS_LOCAL_ICACHE_HOT_ACTUAL_IR_CONTROLS" \
            or any(sha(ROOT / p) != h for p, h in control["input_sha256"].items()):
        raise ValueError("Exact source/checker control freeze is invalid")
    proof = prove()
    if any(sha(ROOT / p) != h for p, h in before.items()):
        raise ValueError("An input changed during local Icache proof")
    result = {"status": "PROVED_LOCAL_ICACHE_HOT_UNUSED_A_DEFAULT_ONLY", "input_sha256": before,
              "memory_enforcement": enforced, "three_read_muxes": 3, "free_three_bit_indexes_per_mux": 8,
              "all_free_index_cases_per_pass": 24, "all_data_and_index_bits_symbolic_free": True,
              "no_init_reset_invariant_or_reachability_assumption": True,
              "original_A_default_connect_lines_closed": 3,
              "whole_Y_definedness": "NOT_CLAIMED; selected B atoms may have other undefined origins",
              "full_sequential_LEC": "OPEN", "whole_source_undefined_abstraction": "OPEN",
              "four_state_equivalence": "NOT_CLAIMED", "independent_method_review": "PENDING",
              "local_closed_GOLD_lines_after_review": 261, "remaining_GOLD_XZ_connect_lines_after_review": 97,
              "count_unit": "Classified connect lines, not bits or full-chip equivalence obligations",
              "external_tool_started_or_source_IR_changed": False, **proof}
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(result["status"], "3mux/24indexcases;6negativecontrols;peak", peak_memory(), flush=True)


if __name__ == "__main__":
    main()
