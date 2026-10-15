"""Separate MSB-first method review of three local Icache unused-A proofs.

Uses the independent exact-top regex reader, not the Icache checker or its
BHT parser/SigSpec evaluator. Data words/slices are parsed independently.
Only local unused A defaults are closed; global Y-definedness is not claimed.
"""
from __future__ import annotations
import argparse
import copy
import json
import hashlib
from pathlib import Path
import re
import sys
sys.dont_write_bytecode = True
from review_lec_onehot_cnf import ROOT, memory_cap, peak_memory

BASE = r"\u_soc.u_icache.g_dm_baseline.u_controller"
PC = r"\u_soc.u_core.u_pipeline.datapath.pc_f"
MISS = BASE + ".miss_index"
CASES = [("$procmux$22675", "hot_tag", 25, 24, PC + " [6:4]"),
         ("$procmux$22684", "hot_line", 128, 127, PC + " [6:4]"),
         ("$procmux$22693", "hot_tag", 5, 4, MISS + " [2:0]")]


def hash_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def unique(pattern, text, label, flags=0):
    matches = list(re.finditer(pattern, text, flags))
    if len(matches) != 1:
        raise ValueError("Exactly one " + label + " required")
    return matches[0]


def top_module(raw):
    header = unique(r"^module \\soc_asic_top$", raw, "original top-module header", re.M)
    begin = raw.find("\n", header.end()) + 1
    ending = re.search(r"^end$", raw[begin:], re.M)
    if begin <= 0 or ending is None:
        raise ValueError("Missing exact top-module end")
    return raw[begin:begin + ending.start()], raw[:begin].count("\n") + 1


def parse_cells(top, first_line):
    """Read only three target blocks and their actual selector-driver blocks."""
    records = {}
    def read_block(start):
        finish = top.find("\n  end", start)
        line_end = top.find("\n", start)
        header = re.fullmatch(r"  cell (\S+) ([^\n]+)", top[start:line_end])
        if finish < 0 or line_end < 0 or not header:
            raise ValueError("Malformed exact target/decoder block")
        parameters, ports = {}, {}
        for text in top[line_end + 1:finish].splitlines():
            field = re.fullmatch(r"    (parameter|connect) (\\\S+) (.+)", text)
            if not field:
                raise ValueError("Unsupported target/decoder cell record")
            target = parameters if field[1] == "parameter" else ports
            if field[2] in target:
                raise ValueError("Duplicate exact cell field")
            target[field[2]] = field[3]
        record = {"type": header[1], "name": header[2], "parameters": parameters,
                  "ports": ports, "original_IR_line": first_line + top[:start].count("\n")}
        if record["name"] in records and records[record["name"]] != record:
            raise ValueError("Conflicting target/decoder record")
        records[record["name"]] = record
        return record
    selectors = set()
    for name, *_ in CASES:
        header = unique(r"^  cell \$pmux " + re.escape(name) + "$", top, "original target mux", re.M)
        record = read_block(header.start())
        concat = re.fullmatch(r"\{ (.+) \}", record["ports"]["\\S"])
        if not concat:
            raise ValueError("Original selector concat missing")
        selectors.update(concat[1].split())
    for selector in selectors:
        output = unique(r"^    connect \\Y " + re.escape(selector) + "$", top, "original scalar selector output", re.M)
        start = top.rfind("\n  cell ", 0, output.start()) + 1
        if start <= 0:
            raise ValueError("Selector output has no exact enclosing cell")
        record = read_block(start)
        if record["ports"].get("\\Y") != selector:
            raise ValueError("Selector output escaped its actual enclosing cell")
    return records


def source_facts(controller, cache, soc, wrapper):
    clean = lambda s: re.sub(r"/\*.*?\*/|//[^\n]*", "", s, flags=re.S)
    controller, cache, soc, wrapper = map(clean, (controller, cache, soc, wrapper))
    top_instance = unique(r"\bsoc_top\s*#\s*\((.*?)\)\s*u_soc\s*\(", wrapper, "source ASIC instance", re.S)
    values = {}
    for name in ("ICACHE_LINE_COUNT", "L0_ENTRIES", "CACHE_CONFIG"):
        match = unique(r"\." + name + r"\s*\(\s*(\d+)\s*\)", top_instance[1], "source literal " + name)
        values[name] = int(match[1])
    if values != {"ICACHE_LINE_COUNT": 256, "L0_ENTRIES": 8, "CACHE_CONFIG": 0}:
        raise ValueError("Exact DM/L0/capacity source parameters differ")
    soc_instance = unique(r"\bicache\s*#\s*\((.*?)\)\s*u_icache\s*\((.*?)\)\s*;", soc, "source Icache instance", re.S)
    for name, value in (("LINE_COUNT", "ICACHE_LINE_COUNT"), ("L0_ENTRIES", "L0_ENTRIES"), ("CACHE_CONFIG", "CACHE_CONFIG")):
        unique(r"\." + name + r"\s*\(\s*" + value + r"\s*\)", soc_instance[1], "source forwarded " + name)
    unique(r"\.req_addr\s*\(\s*if_req_addr\s*\)", soc_instance[2], "source SoC request binding")
    parent = unique(r"\bicache_controller\s*#\s*\((.*?)\)\s*u_controller\s*\((.*?)\)\s*;", cache, "source DM controller instance", re.S)
    for name in ("INDEX_WIDTH", "TAG_WIDTH", "L0_ENTRIES"):
        unique(r"\." + name + r"\s*\(\s*" + name + r"\s*\)", parent[1], "source controller parameter " + name)
    unique(r"\.req_addr\s*\(\s*req_addr\s*\)", parent[2], "source controller request binding")
    compact_cache, compact = re.sub(r"\s+", "", cache), re.sub(r"\s+", "", controller)
    expressions = ["if(CACHE_CONFIG==0)begin:g_dm_baseline",
                   "localparamINDEX_WIDTH=(LINE_COUNT>1)?clog2(LINE_COUNT):1;",
                   "localparamTAG_WIDTH=32-4-INDEX_WIDTH;",
                   "tmp=value-1;clog2=0;while(tmp>0)beginclog2=clog2+1;tmp=tmp>>1;end"]
    if any(compact_cache.count(expression) != 1 for expression in expressions):
        raise ValueError("Source parent index calculation/branch differs")
    expected = ["inputwire[31:0]req_addr,", "reg[INDEX_WIDTH-1:0]miss_index;",
                "localparamL0_IDX_BITS=(L0_ENTRIES>1)?$clog2(L0_ENTRIES):1;",
                "reg[27-L0_IDX_BITS:0]hot_tag[0:L0_ENTRIES-1];", "reg[127:0]hot_line[0:L0_ENTRIES-1];",
                "assignrequest_block=req_addr[31:4];", "assignmiss_block={miss_tag,miss_index};",
                "assignhot_index=request_block[L0_IDX_BITS-1:0];", "assignmiss_hot_index=miss_block[L0_IDX_BITS-1:0];",
                "hot_tag[hot_index]==request_block[27:L0_IDX_BITS]", "assignhot_hit_line=hot_line[hot_index];",
                "localparamHOT_LI_BITS=INDEX_WIDTH-L0_IDX_BITS;",
                "hot_tag[miss_hot_index][HOT_LI_BITS-1:0]==miss_index[INDEX_WIDTH-1:L0_IDX_BITS]"]
    if any(compact.count(expression) != 1 for expression in expected):
        raise ValueError("Exact source array depth/read/slice identity differs")
    index = (values["ICACHE_LINE_COUNT"] - 1).bit_length()
    hot_index = (values["L0_ENTRIES"] - 1).bit_length()
    return {"parameter_values": values, "main_index_bits": index, "hot_index_bits": hot_index,
            "hot_tag_bits": 28 - hot_index, "hot_line_bits": 128,
            "miss_tag_slice_bits": index - hot_index}


def split_words(value, width, widths):
    concat = re.fullmatch(r"\{ (.+) \}", value)
    if not concat:
        raise ValueError("Original eight-word concat required")
    tokens = concat[1].split()
    expressions, atoms, position = [], [], 0
    while position < len(tokens):
        name = tokens[position]
        position += 1
        if name not in widths:
            raise ValueError("B data must be an actual original array wire")
        high, low, expression = widths[name] - 1, 0, name
        if position < len(tokens) and tokens[position].startswith("["):
            selection = re.fullmatch(r"\[(\d+):(\d+)\]", tokens[position])
            if not selection:
                raise ValueError("Unsupported original B slice")
            high, low = int(selection[1]), int(selection[2])
            expression += " " + tokens[position]
            position += 1
        if high < low or high >= widths[name] or high - low + 1 != width:
            raise ValueError("Original B word slice width differs")
        expressions.append(expression)
        atoms.append([(name, bit) for bit in range(high, low - 1, -1)])
    if len(expressions) != 8:
        raise ValueError("Exactly eight original B words required")
    return expressions, atoms


def decoded(cell, support):
    p, c = cell["parameters"], cell["ports"]
    if p.get("\\A_WIDTH") != "3" or p.get("\\A_SIGNED") != "0" or p.get("\\Y_WIDTH") != "1" or c.get("\\A") != support:
        raise ValueError("Actual decoder must use exactly the unsigned free three-bit slice")
    if cell["type"] == "$logic_not":
        if set(p) != {"\\A_WIDTH", "\\A_SIGNED", "\\Y_WIDTH"} or set(c) != {"\\A", "\\Y"}:
            raise ValueError("Unsupported zero decoder")
        return 0
    if cell["type"] != "$eq" or p.get("\\B_SIGNED") != "0":
        raise ValueError("Unsupported actual index decoder")
    constant = re.fullmatch(r"([1-3])'([01]+)", c.get("\\B", ""))
    if not constant or p.get("\\B_WIDTH") != constant[1] or len(constant[2]) != int(constant[1]):
        raise ValueError("Malformed actual decoded constant")
    return int(constant[2], 2)


def evaluate(mux, support, code, width, widths, outputs):
    selector = re.fullmatch(r"\{ (.+) \}", mux["ports"]["\\S"])
    if not selector or len(selector[1].split()) != 8:
        raise ValueError("Exact eight-scalar selector vector required")
    names = selector[1].split()
    _, words = split_words(mux["ports"]["\\B"], width, widths)
    flags = [0 if name == "1'0" else int(code == decoded(outputs[name], support)) for name in names]
    active = [i for i, flag in enumerate(flags) if flag]
    if len(active) > 1:
        raise ValueError("Overlapping selectors cannot be assumed defined")
    return (words[active[0]] if active else [("UNUSED_A_DEFAULT", bit) for bit in range(width - 1, -1, -1)]), flags, not active


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    out = Path(parser.parse_args().out).resolve()
    if out.exists() or not out.is_relative_to(ROOT):
        raise ValueError("New independent review output required")
    bound = memory_cap()
    pair = ["results/icache_hot_default_definedness_20261010_p" + str(n) + ".json" for n in (1, 2)]
    saved = [json.loads((ROOT / path).read_text(encoding="ascii")) for path in pair]
    if saved[0] != saved[1] or hash_file(ROOT / pair[0]) != hash_file(ROOT / pair[1]):
        raise ValueError("Paired receipts differ in bytes or fields")
    inputs = pair + ["scripts/verification/review_icache_hot_definedness.py"]
    for path, expected in saved[0]["input_sha256"].items():
        if hash_file(ROOT / path) != expected:
            raise ValueError("Frozen proof input changed")
        inputs.append(path)
    before = {path: hash_file(ROOT / path) for path in sorted(set(inputs))}
    sources, source_texts = [], []
    for prefix, wrapper in (("hdl/", "asic/soc_dm_4kb/soc_asic_top.v"),
                            ("asic/snapshots/rtl_r14/hdl/", "asic/snapshots/rtl_r14/asic/soc_dm_4kb/soc_asic_top.v")):
        texts = [(ROOT / (prefix + suffix)).read_text(encoding="ascii") for suffix in ("cache/icache_controller.v", "cache/icache.v", "soc_top.v")]
        texts.append((ROOT / wrapper).read_text(encoding="ascii"))
        source_texts.append(texts)
        sources.append(source_facts(*texts))
    if sources[0] != sources[1]:
        raise ValueError("Independent current/signed source width/depth/index facts differ")
    raw = (ROOT / "asic/equiv/lec/gold_flat_r14.il").read_text(encoding="ascii")
    top, first = top_module(raw)
    cells = parse_cells(top, first)
    widths = {}
    for name in [PC, MISS, BASE + ".miss_tag", BASE + ".hot_index", BASE + ".miss_hot_index"] + [BASE + "." + array + "[" + str(i) + "]" for array in ("hot_tag", "hot_line") for i in range(8)]:
        width = unique(r"^  wire width (\d+) " + re.escape(name) + r"\s*$", top, "original wire " + name, re.M)
        widths[name] = int(width[1])
    if [widths[name] for name in (PC, MISS, BASE + ".miss_tag", BASE + ".hot_index", BASE + ".miss_hot_index")] != [32, 8, 20, 3, 3]:
        raise ValueError("Original parent/index wire widths differ")
    for array, width in (("hot_tag", 25), ("hot_line", 128)):
        if any(widths[BASE + "." + array + "[" + str(i) + "]"] != width for i in range(8)):
            raise ValueError("Original array declaration widths differ")
    connections = {BASE + ".req_addr": PC, BASE + ".request_block": PC + " [31:4]",
                   BASE + ".hot_index": PC + " [6:4]", BASE + ".miss_hot_index": MISS + " [2:0]",
                   BASE + ".miss_block": "{ " + BASE + ".miss_tag " + MISS + " }"}
    for name, value in connections.items():
        unique(r"^  connect " + re.escape(name) + " " + re.escape(value) + r"\s*$", top, "raw source/index binding", re.M)
    targets, free_data = [], set()
    for name, array, width, high, support in CASES:
        mux = cells[name]
        if mux["type"] != "$pmux" or mux["parameters"] != {"\\WIDTH": str(width), "\\S_WIDTH": "8"} \
                or mux["ports"]["\\A"] != str(width) + "'x":
            raise ValueError("Actual local mux/default dimensions differ")
        names = mux["ports"]["\\S"][2:-2].split()
        outputs = {}
        for selector in names:
            drivers = [cell for cell in cells.values() if cell["ports"].get("\\Y") == selector]
            if len(drivers) != 1:
                raise ValueError("Original selector driver is not unique")
            outputs[selector] = drivers[0]
        codes = [decoded(outputs[selector], support) for selector in names]
        if len(names) != 8 or len(set(names)) != 8 or set(codes) != set(range(8)):
            raise ValueError("Original decoder does not cover all free three-bit codes")
        truth = []
        for code in range(8):
            atoms, flags, default = evaluate(mux, support, code, width, widths, outputs)
            expected = [(BASE + "." + array + "[" + str(code) + "]", bit) for bit in range(high, -1, -1)]
            if default or sum(flags) != 1 or atoms != expected:
                raise ValueError("Original selected B word/slice differs from source identity")
            free_data.update(atoms)
            truth.append({"free_raw_index": code, "selected_B_bit_atoms_MSB_first": atoms, "A_default_selected": False})
        copied = copy.deepcopy(mux)
        missing = list(names)
        missing[codes.index(7)] = "1'0"
        copied["ports"]["\\S"] = "{ " + " ".join(missing) + " }"
        absent, flags, default = evaluate(copied, support, 7, width, widths, outputs)
        if not default or sum(flags) or absent != [("UNUSED_A_DEFAULT", bit) for bit in range(width - 1, -1, -1)]:
            raise ValueError("Independent copied missing selector did not expose A")
        swapped = copy.deepcopy(mux)
        words, _ = split_words(mux["ports"]["\\B"], width, widths)
        i, j = codes.index(7), codes.index(6)
        words[i], words[j] = words[j], words[i]
        swapped["ports"]["\\B"] = "{ " + " ".join(words) + " }"
        original, _, _ = evaluate(mux, support, 7, width, widths, outputs)
        changed, flags, default = evaluate(swapped, support, 7, width, widths, outputs)
        if default or sum(flags) != 1 or original == changed:
            raise ValueError("Independent actual B word swap not observable")
        witness = {atom: (2 >> bit) & 1 for bit, atom in enumerate(reversed(original))}
        witness.update({atom: (1 >> bit) & 1 for bit, atom in enumerate(reversed(changed))})
        before_value = sum(witness[atom] << bit for bit, atom in enumerate(reversed(original)))
        after_value = sum(witness[atom] << bit for bit, atom in enumerate(reversed(changed)))
        if (before_value, after_value) != (2, 1):
            raise ValueError("Independent free-data swap witness failed")
        targets.append({"name": name, "original_IR_line": mux["original_IR_line"], "width": width,
                        "actual_selector_codes_MSB_first": codes, "all_eight_free_index_cases": truth,
                        "missing_selector_control": {"actual_mutated_S": copied["ports"]["\\S"], "default_selected": True},
                        "actual_B_swap_control": {"actual_mutated_B": swapped["ports"]["\\B"], "original_value": 2, "mutated_value": 1}})
    proof_targets = {target["actual_original_pmux"]["name"]: target for target in saved[0]["targets"]}
    for target in targets:
        old = proof_targets[target["name"]]
        if target["actual_selector_codes_MSB_first"] != list(reversed(old["actual_selector_codes_LSB_first"])):
            raise ValueError("Saved selector order differs from independent reconstruction")
        old_rows = {row["free_raw_index"]: row for row in old["all_eight_free_index_cases"]}
        for row in target["all_eight_free_index_cases"]:
            converted = [list(atom) for atom in reversed(row["selected_B_bit_atoms_MSB_first"])]
            if converted != old_rows[row["free_raw_index"]]["actual_selected_B_bit_atoms_LSB_first"]:
                raise ValueError("Saved B word/slice identity differs from independent reconstruction")
    if saved[0]["whole_Y_definedness"] != "NOT_CLAIMED; selected B atoms may have other undefined origins" \
            or not saved[0]["no_init_reset_invariant_or_reachability_assumption"]:
        raise ValueError("Saved local-only proof scope/premise differs")
    if any(hash_file(ROOT / path) != value for path, value in before.items()):
        raise ValueError("An independent review input changed")
    result = {"status": "PASS_INDEPENDENT_LOCAL_ICACHE_HOT_UNUSED_A_METHOD_REVIEW", "input_sha256": before,
              "memory_enforcement": bound, "saved_pair_byte_and_all_field_equal": True, "ignored_pair_fields": [],
              "independent_method": "Fresh exact-top/target-block parser and MSB-first source-array word/slice decoder; no existing parser, Icache checker or BHT evaluator imported",
              "source_parameter_and_array_contract": sources[0], "raw_bindings": connections, "reviewed_targets": targets,
              "original_local_A_defaults_closed": 3, "all_free_three_bit_cases_checked": 24,
              "unique_original_array_data_bits_free": len(free_data), "semantic_negative_controls": 6,
              "reset_init_invariant_or_reachability_premise_used": False,
              "whole_Y_definedness": "NOT_CLAIMED; other B/data origins remain unconstrained",
              "full_sequential_LEC": "OPEN", "whole_source_undefined_abstraction": "OPEN", "four_state_equivalence": "NOT_CLAIMED",
              "total_local_GOLD_connect_lines_closed": 261, "remaining_GOLD_XZ_connect_lines": 97,
              "count_unit": "Classified connect lines, not bits, defects or whole-chip obligations",
              "source_IR_or_frozen_proofs_modified": False, "external_tool_started": False}
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(result["status"], "3mux24cases/6controls;peak", peak_memory(), flush=True)


if __name__ == "__main__":
    main()
