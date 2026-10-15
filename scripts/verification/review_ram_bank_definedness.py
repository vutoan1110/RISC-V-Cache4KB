"""Separate regex/module parser and MSB-first RAM bank-default review.

Does not import the RAM checker, inventory parser or BHT SigSpec interpreter.
Only read-only digest/memory helpers are reused. No new measurement or solve.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
import gc
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
from review_lec_onehot_cnf import ROOT, digest, memory_cap, peak_memory

RAW = "asic/equiv/lec/gold_flat_r14.il"
READ = "\\u_soc.u_axi_ram.rd_bank_q"
WRITE = "\\u_soc.u_axi_ram.wr_bank_r"


def parse_raw(path):
    text = path.read_text(encoding="ascii")
    starts = [0] + [m.end() for m in re.finditer("\n", text)]
    top = list(re.finditer(r"^module \\soc_asic_top\r?\n(.*?)^end\s*$", text, re.M | re.S))
    if len(top) != 1:
        raise ValueError("Unique complete raw top required")
    body, offset = top[0][1], top[0].start(1)
    wires, cells, outputs = {}, {}, {}
    for match in re.finditer(r"^  wire (.*)$", body, re.M):
        tokens = match[1].split()
        width = int(tokens[tokens.index("width") + 1]) if "width" in tokens else 1
        name = tokens[-1]
        if name in wires:
            raise ValueError("Duplicate raw wire")
        # Unrelated declarations can have source-index offsets. Record them;
        # every selected expression still rejects unsupported indexing below.
        wires[name] = {"width": width, "signed": "signed" in tokens,
                       "unsupported_source_indexing": "offset" in tokens or "upto" in tokens,
                       "line": bisect_right(starts, offset + match.start())}
    for match in re.finditer(r"^  cell (\S+) (\S+)\r?\n(.*?)^  end\s*$", body, re.M | re.S):
        kind, name, block = match.groups()
        if name in cells:
            raise ValueError("Duplicate raw cell")
        p, c = {}, {}
        for line in block.splitlines():
            field = re.fullmatch(r"    (parameter|connect) (\S+) (.*)", line)
            if field is None:
                if line.strip():
                    raise ValueError("Unsupported ignored cell statement")
                continue
            target = p if field[1] == "parameter" else c
            if field[2] in target:
                raise ValueError("Duplicate raw cell field")
            target[field[2]] = field[3]
        cell = {"name": name, "type": kind, "line": bisect_right(starts, offset + match.start()),
                "p": p, "c": c}
        cells[name] = cell
        out = c.get("\\Y")
        if out in wires:
            if out in outputs:
                raise ValueError("Multiple exact raw output drivers")
            outputs[out] = cell
    return wires, cells, outputs


def msb(expression, wires):
    tokens = re.findall(r"[{}]|\[[^]]+\]|[^\s{}]+", expression)
    cursor = 0
    def word():
        nonlocal cursor
        if cursor >= len(tokens):
            raise ValueError("Incomplete raw SigSpec")
        token = tokens[cursor]
        cursor += 1
        if token == "{":
            words = []
            while cursor < len(tokens) and tokens[cursor] != "}":
                words.extend(word())
            if cursor == len(tokens):
                raise ValueError("Missing concat close")
            cursor += 1
            return words
        literal = re.fullmatch(r"(\d+)'([01xz]+)", token)
        if literal:
            width, payload = int(literal[1]), literal[2]
            if len(payload) == 1 and payload in "xz":
                payload = payload * width
            if len(payload) != width:
                raise ValueError("Unsupported constant extension")
            return [int(x) if x in "01" else ("undefined", x, width - i - 1)
                    for i, x in enumerate(payload)]
        if token not in wires:
            raise ValueError("Unknown raw atom")
        if wires[token].get("unsupported_source_indexing", False):
            raise ValueError("Selected raw expression has unsupported offset/upto wire")
        width = wires[token]["width"]
        high, low = width - 1, 0
        if cursor < len(tokens) and tokens[cursor].startswith("["):
            selection = re.fullmatch(r"\[(\d+)(?::(\d+))?\]", tokens[cursor])
            if selection is None:
                raise ValueError("Malformed slice")
            cursor += 1
            high, low = int(selection[1]), int(selection[2] or selection[1])
            if not 0 <= low <= high < width:
                raise ValueError("Out-of-range slice")
        return [(token, bit) for bit in range(high, low - 1, -1)]
    result = word()
    if cursor != len(tokens):
        raise ValueError("Unconsumed SigSpec tokens")
    return result


def integer(bits):
    if any(type(x) is not int or x not in (0, 1) for x in bits):
        raise ValueError("Not a Boolean bitstring")
    return int("".join(str(x) for x in bits), 2) if bits else 0


class Decoder:
    def __init__(self, wires, outputs):
        self.wires, self.outputs, self.used = wires, outputs, {}

    def vector(self, expression, bank, code, seen=None):
        return [self.bit(atom, bank, code, set() if seen is None else seen) for atom in msb(expression, self.wires)]

    def bit(self, atom, bank, code, seen):
        if type(atom) is int:
            return atom
        if len(atom) != 2:
            raise ValueError("Undefined selector")
        net, bit = atom
        if net == bank:
            if self.wires[net]["width"] != 3 or self.wires[net]["signed"] or not 0 <= bit < 3:
                raise ValueError("Bank is not unsigned three-bit free input")
            return int(bool(code & (1 << bit)))
        if net in (READ, WRITE) or net in seen or bit != 0 or self.wires[net]["width"] != 1:
            raise ValueError("Unsupported selector dependence")
        cell = self.outputs[net]
        kind, p, c = cell["type"], cell["p"], cell["c"]
        if p.get("\\A_SIGNED") != "0" or p.get("\\Y_WIDTH") != "1":
            raise ValueError("Unsupported signed/wide selector")
        seen.add(net)
        a = self.vector(c["\\A"], bank, code, seen)
        if len(a) != int(p["\\A_WIDTH"]):
            raise ValueError("Width mismatch")
        if kind == "$logic_not":
            if len(a) != 3 or set(c) != {"\\A", "\\Y"} or set(p) != {"\\A_SIGNED", "\\A_WIDTH", "\\Y_WIDTH"}:
                raise ValueError("Unsupported zero decoder")
            value = int(integer(a) == 0)
        elif kind == "$eq":
            if len(a) != 3 or p.get("\\B_SIGNED") != "0" or set(c) != {"\\A", "\\B", "\\Y"} or set(p) != {"\\A_SIGNED", "\\A_WIDTH", "\\B_SIGNED", "\\B_WIDTH", "\\Y_WIDTH"}:
                raise ValueError("Unsupported equality decoder")
            b = msb(c["\\B"], self.wires)
            if len(b) != int(p["\\B_WIDTH"]) or not 1 <= len(b) <= 3:
                raise ValueError("Unsupported comparison size")
            value = int(integer(a) == integer(b))
        elif kind == "$reduce_or":
            if len(a) != 7 or set(c) != {"\\A", "\\Y"} or set(p) != {"\\A_SIGNED", "\\A_WIDTH", "\\Y_WIDTH"}:
                raise ValueError("Unsupported grouped complement")
            value = int(integer(a) != 0)
        else:
            raise ValueError("Unsupported raw decoder")
        seen.remove(net)
        self.used[cell["name"]] = cell
        return value


def expected(target, wires, code):
    group = target["group"]
    cell = target["actual_raw_PMUX"]
    width = target["width"]
    if group == "main_RAM_read_data_default":
        return msb(f"\\u_soc_u_axi_ram_g_bank_{code}__u_bank__dout0", wires)
    y = cell["ports"]["\\Y"]["expression"]
    match = re.search(r"\\(bank_\w+)\[(\d+)\]", y)
    name, bank = match[1], int(match[2])
    if group == "main_RAM_read_address_default":
        return msb("\\u_soc.u_axi_ram.rd_bank_addr_q", wires) if bank == code else [0] * width
    if bank == code:
        source = {"bank_din0": "wr_data_r", "bank_wmask0": "wr_strb_r", "bank_addr0": "wr_bank_off_r"}.get(name)
        return [0] * width if source is None else msb("\\u_soc.u_axi_ram." + source, wires)
    if name in ("bank_din0", "bank_wmask0"):
        return [0] * width
    return msb(f"$flatten\\u_soc.\\u_axi_ram.$1\\{name}[{bank}][{width-1}:0]", wires)


def json_atoms(atoms):
    return [list(atom) if type(atom) is tuple else atom for atom in atoms]


def selected(data, selector, width, default):
    places = [index for index, bit in enumerate(selector) if bit]
    if len(places) > 1:
        raise ValueError("Multiple selected raw words")
    return data[places[0] * width:(places[0] + 1) * width] if places else default


def source_guards():
    ram_paths = ["asic/snapshots/rtl_r14/asic/soc_dm_4kb/axi_ram_32_asic_macro.v", "asic/soc_dm_4kb/axi_ram_32_asic_macro.v"]
    clean = lambda text: re.sub(r"\s+", "", re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S))
    text = [clean((ROOT / path).read_text()) for path in ram_paths]
    if text[0] != text[1]:
        raise ValueError("Signed/current algorithm differs")
    for clause in ["NBANKS=DEPTH_WORDS/512;", "BANK_BITS=(NBANKS>1)?$clog2(NBANKS):1;", "WORD_BITS=$clog2(DEPTH_WORDS);",
                   "reg[BANK_BITS-1:0]rd_bank_q;", "reg[BANK_BITS-1:0]wr_bank_r;", "assigns_axi_rdata=bank_dout0[rd_bank_q];",
                   "for(gi=0;gi<NBANKS;gi=gi+1)begin:g_bank", ".din0(bank_din0[gi])", ".dout0(bank_dout0[gi])",
                   ".addr0(bank_addr0[gi])", ".csb0(bank_csb0[gi])", ".web0(bank_web0[gi])", ".wmask0(bank_wmask0[gi])"]:
        if clause not in text[0]:
            raise ValueError("Independent source bank/instance guard failed")
    for path in ["asic/snapshots/rtl_r14/hdl/soc_top.v", "hdl/soc_top.v"]:
        if "axi_ram_32#(.DEPTH_WORDS(IMEM_DEPTH+DMEM_DEPTH),.MEMFILE(MEMFILE))u_axi_ram(" not in clean((ROOT / path).read_text()):
            raise ValueError("Independent depth parent binding failed")
    for path in ["asic/snapshots/rtl_r14/asic/soc_dm_4kb/soc_asic_top.v", "asic/soc_dm_4kb/soc_asic_top.v"]:
        text = clean((ROOT / path).read_text())
        if ".IMEM_DEPTH(2048)" not in text or ".DMEM_DEPTH(2048)" not in text:
            raise ValueError("Independent parameter specialization failed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists() or out.with_suffix(".md").exists() or not out.is_relative_to(ROOT):
        raise ValueError("New independent output required")
    guard = memory_cap()
    source_guards()
    paths = ["results/ram_bank_default_definedness_20261010_p1.json", "results/ram_bank_default_definedness_20261010_p2.json",
             "results/ram_bank_definedness_controls_20261010.json", Path(__file__).relative_to(ROOT).as_posix()]
    hashes = {rel: digest(ROOT / rel) for rel in paths}
    pair = [json.loads((ROOT / rel).read_text()) for rel in paths[:2]]
    if pair[0] != pair[1] or hashes[paths[0]] != hashes[paths[1]]:
        raise ValueError("Actual independent pair differs")
    control = json.loads((ROOT / paths[2]).read_text())
    if control["status"] != "PASS_MAIN_RAM_BANK_DEFINEDNESS_PRE_RUN_CONTROLS" or control["frozen_checker_before_main_pair"] is not True or len(control["finite_data_order_and_fail_closed_controls"]) != 15:
        raise ValueError("Frozen pre-run controls incomplete")
    for rel, h in control["source_sha256"].items():
        if digest(ROOT / rel) != h:
            raise ValueError("Frozen control input changed")
        hashes[rel] = h
    for receipt in pair:
        if receipt["status"] != "PROVED_LOCAL_MAIN_RAM_BANK_BOOLEAN_UNUSED_A_ONLY" or receipt["exact49_original_A_default_connect_lines"] != 49 or receipt["all_free_bank_cases"] != 392 or receipt["raw_semantic_negative_controls"] != 98 or receipt["zero_init_reset_FSM_onehot_or_reachability_premise"] is not False or receipt["whole_source_undefined_abstraction"] != "OPEN" or receipt["full_sequential_LEC"] != "OPEN" or receipt["default_A_irrelevance_does_not_prove_whole_Y_definedness"] is not True:
            raise ValueError("Proof count/scope changed")
        for rel, h in receipt["input_sha256"].items():
            if digest(ROOT / rel) != h:
                raise ValueError("Proof input changed")
            hashes[rel] = h
    wires, cells, outputs = parse_raw(ROOT / RAW)
    decoder = Decoder(wires, outputs)
    inventory = json.loads((ROOT / "results/lec_source_x_remaining_20261010/remaining_origins.json").read_text())
    names = {row["cell"] for row in inventory["remaining_origins"] if row["group"].startswith("main_RAM_")}
    if len(names) != 49 or names != {target["cell"] for target in pair[0]["targets"]}:
        raise ValueError("Independent target set differs")
    reviews, unique_data = [], set()
    for target in pair[0]["targets"]:
        cell = cells[target["cell"]]
        raw = target["actual_raw_PMUX"]
        if cell["type"] != "$pmux" or cell["line"] != raw["line"] or cell["p"] != raw["parameters"] or cell["c"] != {port: connection["expression"] for port, connection in raw["ports"].items()}:
            raise ValueError("Separate parser differs from exact saved raw target")
        width, swidth = int(cell["p"]["\\WIDTH"]), int(cell["p"]["\\S_WIDTH"])
        bank = READ if target["group"] in ("main_RAM_read_address_default", "main_RAM_read_data_default") else WRITE
        if target["free_bank_support"] != bank or wires[bank]["width"] != 3 or wires[bank]["signed"]:
            raise ValueError("Independent bank support differs")
        B, S, A = (msb(cell["c"][port], wires) for port in ("\\B", "\\S", "\\A"))
        if len(B) != width * swidth or len(S) != swidth or len(A) != width or any(type(x) is int or x[0:2] != ("undefined", "x") for x in A) or any(type(x) is not int and len(x) != 2 for x in B):
            raise ValueError("Original A/B/S symbolic widths differ")
        unique_data.update(atom for atom in B if type(atom) is not int)
        if len(target["cases"]) != 8 or target["status"] != "PROVED_UNUSED_A_FOR_ALL_EIGHT_FREE_BANK_CODES":
            raise ValueError("Free code population incomplete")
        for code in range(8):
            values = decoder.vector(cell["c"]["\\S"], bank, code)
            word = selected(B, values, width, A)
            if sum(values) != 1 or word != expected(target, wires, code):
                raise ValueError("Independent actual selector/source data order differs")
            saved = target["cases"][code]
            if saved != {"free_bank_code": code, "selectors_LSB_first": values[::-1], "active_selector_count": 1,
                         "A_default_selected": False, "selected_original_B_atoms_LSB_first": json_atoms(word[::-1])}:
                raise ValueError("Saved complete case fields differ")
        remove, data_fault = target["negative_controls"]
        original_s = decoder.vector(cell["c"]["\\S"], bank, 7)
        place = original_s.index(1)
        changed_s = list(S)
        changed_s[place] = 0
        changed_values = [decoder.bit(atom, bank, 7, set()) for atom in changed_s]
        if sum(changed_values) != 0 or remove["free_bank_code"] != 7 or remove["mutated_selector_position_LSB_first"] != swidth - place - 1 or remove["actual_S_atoms_LSB_first"] != json_atoms(S[::-1]) or remove["mutated_S_atoms_LSB_first"] != json_atoms(changed_s[::-1]) or remove["mutated_S_values_LSB_first"] != changed_values[::-1] or remove["A_zero_output"] != [0] * width or remove["A_one_output"] != [1] * width or remove["default_now_selected"] is not True:
            raise ValueError("Actual raw missing-selector fault differs")
        original_word = selected(B, original_s, width, A)
        changed_B = list(B)
        if data_fault["selected_word"] != swidth - place - 1:
            raise ValueError("Fault mutation uses a different actual selected B word")
        kind = data_fault["kind"]
        start = place * width
        if kind == "copied_raw_B_bit_order_swap":
            a, b = data_fault["bit_positions"]
            i, j = start + width - a - 1, start + width - b - 1
            changed_B[i], changed_B[j] = changed_B[j], changed_B[i]
        elif kind == "copied_raw_B_word_substitution":
            alternate = (swidth - data_fault["other_word"] - 1) * width
            changed_B[start:start + width] = B[alternate:alternate + width]
        elif kind == "copied_raw_B_word_swap" and width == 1:
            alternate = swidth - data_fault["other_word"] - 1
            changed_B[place], changed_B[alternate] = changed_B[alternate], changed_B[place]
        else:
            raise ValueError("Unsupported actual raw data fault")
        wrong_word = selected(changed_B, original_s, width, A)
        if data_fault["mutated_B_atoms_LSB_first"] != json_atoms(changed_B[::-1]) or data_fault["selected_B_before"] != json_atoms(original_word[::-1]) or data_fault["selected_B_after"] != json_atoms(wrong_word[::-1]):
            raise ValueError("Separate actual raw B fault reconstruction differs")
        witness = {tuple(row["atom"]): row["value"] for row in data_fault["free_data_witness"]}
        used_atoms = {atom for atom in original_word + wrong_word if type(atom) is not int}
        if set(witness) != used_atoms or any(type(value) is not int or value not in (0, 1) for value in witness.values()):
            raise ValueError("Actual B semantic witness missing/free data assumption")
        evaluate = lambda word: integer([atom if type(atom) is int else witness[atom] for atom in word])
        positive, wrong = evaluate(original_word), evaluate(wrong_word)
        if positive == wrong or positive != data_fault["original_output_integer"] or wrong != data_fault["mutated_output_integer"]:
            raise ValueError("Actual raw B fault is not observable")
        reviews.append({"cell": cell["name"], "IR_cell_line": cell["line"], "status": "PASS",
                        "free_code_cases": 8, "raw_selector_missing_case_control": "PASS",
                        "raw_selected_B_semantic_fault": "PASS", "B_mutation": kind})
    reconstructed = {name: {"type": cell["type"], "line": cell["line"], "parameters": cell["p"], "ports": cell["c"]}
                     for name, cell in decoder.used.items()}
    saved_selectors = {name: {"type": cell["type"], "line": cell["line"], "parameters": cell["parameters"],
                             "ports": {port: row["expression"] for port, row in cell["ports"].items()}}
                       for name, cell in pair[0]["raw_selector_cone_cells"].items()}
    if reconstructed != saved_selectors or len(unique_data) != pair[0]["unique_original_B_data_bit_atoms_free"]:
        raise ValueError("Independent full selector cone or free data count differs")
    # Independent tiny MSB parser controls cover word ordering and malformed
    # concat/ranges; they do not call the paired checker or shared SigSpec parser.
    tiny = {"\\a": {"width": 3}, "\\b": {"width": 2}}
    if msb("{ \\a \\b }", tiny) != [("\\a", 2), ("\\a", 1), ("\\a", 0), ("\\b", 1), ("\\b", 0)] or msb("\\a [2:1]", tiny) != [("\\a", 2), ("\\a", 1)] or msb("4'1010", tiny) != [1, 0, 1, 0]:
        raise ValueError("Separate MSB finite parser failed")
    for expression in ("{ \\a", "\\a [3]", "\\a [0:2]", "\\a \\b", "\\unknown"):
        try:
            msb(expression, tiny)
        except ValueError:
            pass
        else:
            raise ValueError("Separate malformed parser control accepted")
    if any(digest(ROOT / rel) != h for rel, h in hashes.items()):
        raise ValueError("Read-only independent input changed")
    result = {"status": "PASS_INDEPENDENT_MAIN_RAM_BANK_UNUSED_A_REVIEW", "input_sha256": hashes,
              "independent_pair_byte_and_all_field_equal": True, "ignored_fields": [],
              "separate_module_regex_parser": True, "separate_MSB_first_bit_interpreter": True,
              "checker_BHT_or_inventory_parser_imported": False, "no_new_actual_measurement_or_solver": True,
              "reviewed_targets": reviews, "free_bank_cases_rebuilt": 392,
              "actual_raw_semantic_faults_reconstructed": 98, "original_B_data_atoms_free": len(unique_data),
              "whole_Y_definedness_or_RAM_initialization_claimed": False,
              "no_init_reset_onehot_or_state_premise": True, "full_sequential_LEC": "OPEN",
              "whole_source_undefined_abstraction": "OPEN", "candidate_local_line_closure": 49,
              "memory_enforcement": guard, "peak_process_memory": peak_memory()}
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    out.with_suffix(".md").write_text("# Independent main-RAM bank default review\n\nPASS: a separate module-scoped regex parser and MSB-first bit interpreter reconstructed all49 actual PMUX targets and their exact bank/OR-group selector cones. All392 free three-bit bank cases select exactly one original B word in source bank order. All98 actual copied-selector/data-order semantic controls were independently reconstructed and their witnesses re-evaluated. Current/signed source parameter, index-width and macro-instance bindings match. The two saved native executions match every field and byte; no ignored fields.\n\nSelected B data and unreset/macro values stay arbitrary. This closes only the49 unused A-default origins after paired acceptance. It does not prove whole-Y definedness, RAM initial contents, source-X/four-state closure, reset/events or full-chip LEC. No new measurement, solve or frontend ran. Exact hashes, cone rows and memory are in the adjacent JSON.\n", encoding="ascii")
    print(result["status"], "49targets/392cases/98actualfaults;peak", peak_memory(), flush=True)


if __name__ == "__main__":
    main()
