"""Exact local two-state unused-A proof for49 main-RAM bank PMUX defaults.

Only the original raw bank selector cones are evaluated. Every B-data bit,
including macro data and unreset state, stays an arbitrary original bit atom.
No frontend, solver, reset, one-hot or initial-state premise is used.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
from review_lec_onehot_cnf import ROOT, digest, memory_cap, peak_memory
from review_bht_definedness import bits
sys.path.insert(0, str(ROOT / "results/lec_source_x_remaining_20261010"))
from classify_remaining import parse

RAW = "asic/equiv/lec/gold_flat_r14.il"
MAP = "results/lec_source_x_remaining_20261010/remaining_origins.json"
RAM = "asic/snapshots/rtl_r14/asic/soc_dm_4kb/axi_ram_32_asic_macro.v"
READ_BANK = "\\u_soc.u_axi_ram.rd_bank_q"
WRITE_BANK = "\\u_soc.u_axi_ram.wr_bank_r"


def compact(text):
    return re.sub(r"\s+", "", re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S))


def source_contracts():
    paths = [RAM, "asic/soc_dm_4kb/axi_ram_32_asic_macro.v", "hdl/soc_top.v",
             "asic/snapshots/rtl_r14/hdl/soc_top.v", "asic/soc_dm_4kb/soc_asic_top.v",
             "asic/snapshots/rtl_r14/asic/soc_dm_4kb/soc_asic_top.v"]
    sources = {rel: compact((ROOT / rel).read_text()) for rel in paths}
    if sources[paths[0]] != sources[paths[1]]:
        raise ValueError("Current/signed main-RAM algorithm tokens differ")
    ram = sources[RAM]
    required = ["parameter DEPTH_WORDS = 4096", "localparam integer NBANKS = DEPTH_WORDS / 512;",
                "localparam integer BANK_BITS = (NBANKS > 1) ? $clog2(NBANKS) : 1;",
                "localparam integer WORD_BITS = $clog2(DEPTH_WORDS);",
                "reg [BANK_BITS-1:0] rd_bank_q;", "reg [BANK_BITS-1:0] wr_bank_r;",
                "assign s_axi_rdata = bank_dout0[rd_bank_q];",
                "for (gi = 0; gi < NBANKS; gi = gi + 1) begin : g_bank",
                ".clk0 (clk)", ".csb0 (bank_csb0[gi])", ".web0 (bank_web0[gi])",
                ".wmask0(bank_wmask0[gi])", ".addr0 (bank_addr0[gi])", ".din0 (bank_din0[gi])", ".dout0 (bank_dout0[gi])"]
    for clause in required:
        if compact(clause) not in ram:
            raise ValueError("Unsupported main-RAM source contract: " + clause)
    drive = """always @(*) begin
        for (rb = 0; rb < NBANKS; rb = rb + 1) begin
            bank_csb0[rb] = 1'b1; bank_web0[rb] = 1'b1;
            bank_wmask0[rb] = 4'b0000; bank_addr0[rb] = 9'd0; bank_din0[rb] = 32'd0;
        end
        if (rd_state == RD_FETCH) begin
            bank_csb0[rd_bank_q] = 1'b0; bank_web0[rd_bank_q] = 1'b1;
            bank_addr0[rd_bank_q] = rd_bank_addr_q;
        end
        if (wr_state == WR_COMMIT) begin
            bank_csb0[wr_bank_r] = 1'b0; bank_web0[wr_bank_r] = 1'b0;
            bank_wmask0[wr_bank_r] = wr_strb_r; bank_addr0[wr_bank_r] = wr_bank_off_r;
            bank_din0[wr_bank_r] = wr_data_r;
        end
    end"""
    if compact(drive) not in ram:
        raise ValueError("Changed main-RAM read/write-priority drive algorithm")
    for rel in paths[2:4]:
        if compact("axi_ram_32 #(.DEPTH_WORDS (IMEM_DEPTH + DMEM_DEPTH), .MEMFILE (MEMFILE)) u_axi_ram (") not in sources[rel]:
            raise ValueError("Main-RAM parent parameter binding differs")
    for rel in paths[4:]:
        if ".IMEM_DEPTH(2048)" not in sources[rel] or ".DMEM_DEPTH(2048)" not in sources[rel]:
            raise ValueError("Exact DM source instance depth is not4096words")
    return paths, {"current_and_signed_RAM_algorithm_tokens_equal": True,
                   "IMEM_DEPTH": 2048, "DMEM_DEPTH": 2048, "DEPTH_WORDS": 4096,
                   "NBANKS": 8, "BANK_BITS": 3, "WORD_BITS": 12,
                   "main_macro_port0_source_binding_checked": True,
                   "clock_timing_or_initial_contents_proved": False,
                   "exact_combinational_read_then_write_priority_source_guard": True}


class RawSelectors:
    def __init__(self, widths, cells):
        self.widths, self.cells = widths, cells
        self.drivers = {}
        self.used = {}
        for cell in cells.values():
            output = cell["ports"].get("\\Y", {}).get("expression")
            if output is not None and output in widths and widths[output] == 1:
                if output in self.drivers:
                    raise ValueError("Multiple raw selector drivers")
                self.drivers[output] = cell

    def vector(self, expression, bank, code, stack=None):
        return [self.atom(atom, bank, code, set() if stack is None else stack) for atom in bits(expression, self.widths)]

    def atom(self, atom, bank, code, stack):
        if type(atom) is int:
            return atom
        if len(atom) != 2:
            raise ValueError("Undefined raw selector atom")
        wire, bit = atom
        if wire == bank:
            if self.widths[wire] != 3 or not 0 <= bit < 3:
                raise ValueError("Unsupported actual bank support width")
            return (code >> bit) & 1
        if wire in (READ_BANK, WRITE_BANK) and wire != bank:
            raise ValueError("Selector mixes read/write bank support")
        if bit != 0 or self.widths[wire] != 1 or wire not in self.drivers or wire in stack:
            raise ValueError("Unsupported/free/non-scalar selector support")
        cell = self.drivers[wire]
        p, c = cell["parameters"], cell["ports"]
        if p.get("\\A_SIGNED") != "0" or p.get("\\Y_WIDTH") != "1":
            raise ValueError("Unsupported signed/wide selector primitive")
        stack.add(wire)
        a = self.vector(c["\\A"]["expression"], bank, code, stack)
        if len(a) != int(p["\\A_WIDTH"]):
            raise ValueError("Actual selector A width mismatch")
        if cell["type"] == "$logic_not":
            if set(c) != {"\\A", "\\Y"} or set(p) != {"\\A_SIGNED", "\\A_WIDTH", "\\Y_WIDTH"} or len(a) != 3:
                raise ValueError("Changed raw zero decoder contract")
            result = int(not any(a))
        elif cell["type"] == "$eq":
            if set(c) != {"\\A", "\\B", "\\Y"} or set(p) != {"\\A_SIGNED", "\\A_WIDTH", "\\B_SIGNED", "\\B_WIDTH", "\\Y_WIDTH"} or p["\\B_SIGNED"] != "0" or len(a) != 3:
                raise ValueError("Changed raw equality decoder contract")
            b = bits(c["\\B"]["expression"], self.widths)
            if len(b) != int(p["\\B_WIDTH"]) or not 1 <= len(b) <= 3 or any(type(x) is not int for x in b):
                raise ValueError("Unsupported decoder comparison")
            result = int(sum(x << i for i, x in enumerate(a)) == sum(x << i for i, x in enumerate(b)))
        elif cell["type"] == "$reduce_or":
            if set(c) != {"\\A", "\\Y"} or set(p) != {"\\A_SIGNED", "\\A_WIDTH", "\\Y_WIDTH"} or len(a) != 7:
                raise ValueError("Unsupported grouped bank complement")
            result = int(any(a))
        else:
            raise ValueError("Unsupported raw selector primitive:" + cell["type"])
        stack.remove(wire)
        self.used[cell["name"]] = cell
        return result


def symbolic_expected(target, widths, code):
    group = target["group"]
    cell = target["actual_cell"]
    width = int(cell["parameters"]["\\WIDTH"])
    y = cell["ports"]["\\Y"]["expression"]
    if group == "main_RAM_read_data_default":
        return bits(f"\\u_soc_u_axi_ram_g_bank_{code}__u_bank__dout0", widths)
    match = re.search(r"\\(bank_\w+)\[(\d+)\]", y)
    if match is None:
        raise ValueError("Unexpected selected RAM bank output")
    signal, bank = match[1], int(match[2])
    if group == "main_RAM_read_address_default":
        return bits("\\u_soc.u_axi_ram.rd_bank_addr_q", widths) if code == bank else [0] * width
    active = code == bank
    if signal == "bank_din0":
        return bits("\\u_soc.u_axi_ram.wr_data_r", widths) if active else [0] * width
    if signal == "bank_wmask0":
        return bits("\\u_soc.u_axi_ram.wr_strb_r", widths) if active else [0] * width
    if signal == "bank_addr0" and active:
        return bits("\\u_soc.u_axi_ram.wr_bank_off_r", widths)
    if signal in ("bank_csb0", "bank_web0") and active:
        return [0] * width
    # Prior combinational read-stage values are original free wire bits here;
    # this proof does not assume their initialization or source-X closure.
    previous = f"$flatten\\u_soc.\\u_axi_ram.$1\\{signal}[{bank}][{width-1}:0]"
    return bits(previous, widths)


def select_word(data, selectors, width, default):
    active = [position for position, value in enumerate(selectors) if value]
    if len(active) > 1:
        raise ValueError("Actual PMUX has multiple active selectors")
    return data[active[0] * width:(active[0] + 1) * width] if active else default


def prove():
    paths, source = source_contracts()
    paths += [RAW, MAP, "scripts/verification/check_ram_bank_default_definedness.py",
              "scripts/verification/review_bht_definedness.py", "scripts/verification/review_lec_onehot_cnf.py",
              "results/lec_source_x_remaining_20261010/classify_remaining.py"]
    hashes = {rel: digest(ROOT / rel) for rel in paths}
    inventory = json.loads((ROOT / MAP).read_text())
    if inventory["remaining_connect_lines"] != 97 or inventory["previously_accepted_local_A_closures"] != 261 or digest(ROOT / RAW) != inventory["input_sha256"][RAW]:
        raise ValueError("Accepted exact remaining-source map changed")
    targets = [row for row in inventory["remaining_origins"] if row["group"].startswith("main_RAM_")]
    if len(targets) != 49 or len({target["cell"] for target in targets}) != 49:
        raise ValueError("Exactly49 distinct main-RAM A targets required")
    wires, cells, aliases, raw_rows = parse(ROOT / RAW)
    widths = {name: declaration["width"] for name, declaration in wires.items()}
    if any(wires[name]["width"] != 3 or wires[name]["offset"] != 0 for name in (READ_BANK, WRITE_BANK)):
        raise ValueError("Raw RAM bank support is not exact unsigned three-bit storage")
    selectors = RawSelectors(widths, cells)
    proved, B_atoms = [], set()
    for target in targets:
        name = target["cell"]
        cell = cells[name]
        if cell != target["actual_cell"] or cell["type"] != "$pmux" or set(cell["ports"]) != {"\\A", "\\B", "\\S", "\\Y"} or set(cell["parameters"]) != {"\\S_WIDTH", "\\WIDTH"}:
            raise ValueError("Actual original RAM PMUX shape/map differs")
        width, swidth = int(cell["parameters"]["\\WIDTH"]), int(cell["parameters"]["\\S_WIDTH"])
        if swidth not in (2, 8) or width not in (1, 4, 9, 32):
            raise ValueError("Unsupported main-RAM PMUX widths")
        bank = READ_BANK if target["group"] in ("main_RAM_read_data_default", "main_RAM_read_address_default") else WRITE_BANK
        data = bits(cell["ports"]["\\B"]["expression"], widths)
        default = bits(cell["ports"]["\\A"]["expression"], widths)
        s = bits(cell["ports"]["\\S"]["expression"], widths)
        if len(data) != width * swidth or len(s) != swidth or len(default) != width or any(type(x) is int or x[:2] != ("UNDEFINED", "x") for x in default) or any(type(x) is not int and len(x) != 2 for x in data):
            raise ValueError("Raw A/B/S widths or undefined placement differ")
        B_atoms.update(x for x in data if type(x) is not int)
        cases = []
        for code in range(8):
            selected = selectors.vector(cell["ports"]["\\S"]["expression"], bank, code)
            if len(selected) != swidth or sum(selected) != 1:
                raise ValueError("CONDITIONAL_OR_UNCOVERED_BANK_DEFAULT:" + name + ":" + str(code))
            result = select_word(data, selected, width, default)
            expected = symbolic_expected(target, widths, code)
            if result != expected:
                raise ValueError("Actual RAM B data order differs from original source bank role")
            cases.append({"free_bank_code": code, "selectors_LSB_first": selected,
                          "active_selector_count": 1, "A_default_selected": False,
                          "selected_original_B_atoms_LSB_first": result})
        # The selected original branch is disabled in a copied actual S
        # SigSpec; every other raw selector is left unchanged.
        code = 7
        original_s = selectors.vector(cell["ports"]["\\S"]["expression"], bank, code)
        position = original_s.index(1)
        mutant_s_atoms = list(s)
        mutant_s_atoms[position] = 0
        mutant_s = [0 if atom == 0 else selectors.atom(atom, bank, code, set()) for atom in mutant_s_atoms]
        if sum(mutant_s) != 0:
            raise ValueError("Raw missing-selector mutation did not expose default")
        low = select_word(data, mutant_s, width, [0] * width)
        high = select_word(data, mutant_s, width, [1] * width)
        if low == high:
            raise ValueError("Raw missing-selector control failed semantic A dependence")
        # A raw B bit permutation changes the selected data function at the
        # same free code. Test an actual symbolic atom when width>1; on1-bit
        # cells swap two raw B words and give free previous-data bits value1.
        selected_atoms = select_word(data, original_s, width, default)
        mutant_data = list(data)
        if width > 1:
            left = position * width
            unequal = next((i for i in range(1, width) if data[left + i] != data[left]), None)
            if unequal is None:
                # Selected all-zero data still has a distinct other B word.
                other = next((j for j in range(swidth) if data[j * width:(j + 1) * width] != selected_atoms), None)
                if other is None:
                    raise ValueError("No actual distinguishable raw B control")
                alternate = mutant_data[other * width:(other + 1) * width]
                mutant_data[left:left + width] = alternate
                mutation = {"kind": "copied_raw_B_word_substitution", "selected_word": position, "other_word": other}
            else:
                mutant_data[left], mutant_data[left + unequal] = mutant_data[left + unequal], mutant_data[left]
                mutation = {"kind": "copied_raw_B_bit_order_swap", "selected_word": position, "bit_positions": [0, unequal]}
        else:
            other = next(j for j in range(swidth) if data[j] != selected_atoms[0])
            mutant_data[position], mutant_data[other] = mutant_data[other], mutant_data[position]
            mutation = {"kind": "copied_raw_B_word_swap", "selected_word": position, "other_word": other}
        wrong = select_word(mutant_data, original_s, width, default)
        all_atoms = {x for x in selected_atoms + wrong if type(x) is not int}
        unequal = next(i for i in range(width) if selected_atoms[i] != wrong[i])
        binding = {atom: 0 for atom in all_atoms}
        a, b = selected_atoms[unequal], wrong[unequal]
        if type(a) is not int:
            binding[a] = 1 - b if type(b) is int else 1
        elif type(b) is not int:
            binding[b] = 1 - a
        value = lambda atoms: sum((atom if type(atom) is int else binding[atom]) << bit for bit, atom in enumerate(atoms))
        if value(selected_atoms) == value(wrong):
            raise ValueError("Raw selected B mutation was not semantically observable")
        proved.append({"cell": name, "IR_cell_line": cell["line"], "IR_A_connect_line": target["IR_line"],
                       "group": target["group"], "width": width, "S_width": swidth,
                       "free_bank_support": bank, "actual_raw_PMUX": cell, "cases": cases,
                       "undefined_A_bits_arbitrary": width,
                       "status": "PROVED_UNUSED_A_FOR_ALL_EIGHT_FREE_BANK_CODES",
                       "negative_controls": [{"kind": "copied_actual_S_selected_bit_zero", "free_bank_code": code,
                           "mutated_selector_position_LSB_first": position, "actual_S_atoms_LSB_first": s,
                           "mutated_S_atoms_LSB_first": mutant_s_atoms, "mutated_S_values_LSB_first": mutant_s,
                           "default_now_selected": True, "A_zero_output": low, "A_one_output": high},
                          {**mutation, "free_bank_code": code, "mutated_B_atoms_LSB_first": mutant_data,
                           "selected_B_before": selected_atoms, "selected_B_after": wrong,
                           "free_data_witness": [{"atom": atom, "value": val} for atom, val in sorted(binding.items())],
                           "original_output_integer": value(selected_atoms), "mutated_output_integer": value(wrong)}]})
    if any(digest(ROOT / path) != h for path, h in hashes.items()):
        raise ValueError("Frozen local proof input changed")
    return {"status": "PROVED_LOCAL_MAIN_RAM_BANK_BOOLEAN_UNUSED_A_ONLY", "input_sha256": hashes,
            "source_contracts": source, "targets": proved, "raw_selector_cone_cells": selectors.used,
            "exact49_original_A_default_connect_lines": len(proved), "all_free_bank_cases": 392,
            "unique_original_B_data_bit_atoms_free": len(B_atoms), "B_data_atoms_symbolic": True,
            "raw_semantic_negative_controls": 98, "zero_init_reset_FSM_onehot_or_reachability_premise": False,
            "default_A_irrelevance_does_not_prove_whole_Y_definedness": True,
            "four_state_equivalence": "NOT_CLAIMED", "full_sequential_LEC": "OPEN",
            "whole_source_undefined_abstraction": "OPEN", "candidate_locally_closed_connect_lines": 310,
            "candidate_remaining_connect_lines": 48, "promotion_requires_paired_and_independent_method_review": True,
            "external_frontend_or_solver_started": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists() or not out.is_relative_to(ROOT):
        raise ValueError("New research proof output required")
    guard = memory_cap()
    result = prove()
    result["memory_enforcement"] = guard
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(result["status"], "49targets/392cases/98rawnegative; peak", peak_memory(), flush=True)


if __name__ == "__main__":
    main()
