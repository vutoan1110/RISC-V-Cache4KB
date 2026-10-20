"""Independent bounded replay of the saved mapped MCYCLE observer proofs.

The netlist parser and PDK primitive interpreter below are separate from the
author's checker. Only previously independently reviewed DAG/CNF/resolution
helpers are reused. No new SAT solve or design-tool process is run.
"""
from __future__ import annotations

import argparse
import gc
import itertools
import json
from pathlib import Path
import re
import sys
import time

sys.dont_write_bytecode = True
from review_lec_onehot_cnf import (ROOT, IndependentGraph, content_digest,
                                  digest, encode, memory_cap, peak_memory, replay)

AUTHOR_SHA = "f990f209b9293059d0c7496d6f0308a3e850adf74b8f32ec294b8c2fabe2bbdf"
HELPER_SHA = "14ddabd9d2b0f842be8b74ef4ea43013e710221edc79df785d55e297bd6aa9c4"
OUTPUTS = {"X", "Y", "Q", "Q_N", "GCLK", "HI", "LO"}
INC = "u_soc.u_observability.u_perf_counters.mcycle_count_inc"
Q = "u_soc.perf_mcycle_count_dbg"
PROOF_DIR = ROOT / "results/mapped_counter_freeze_checked_20261010"
PATHS = {
    "DM": "asic/soc_dm_4kb/runs/r14F_A/55-openroad-fillinsertion/soc_asic_top.nl.v",
    "SA2": "asic/soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1/56-openroad-fillinsertion/soc_asic_top.nl.v",
}
PDK = "asic/soc_dm_4kb/formal_pdk.v"


def identifier(text):
    text = text.strip()
    if text.startswith("\\"):
        text = text[1:]
    if not text or re.search(r"\s", text):
        raise ValueError("Unsupported net token")
    return text


class RawCells:
    """Statement-by-statement parser with complete selected pin syntax checks."""
    def __init__(self, path):
        self.driver, self.alias = {}, {}
        self.count = 0
        pending = []
        with Path(path).open(encoding="utf-8") as source:
            for line_number, line in enumerate(source, 1):
                if not pending:
                    stripped = line.lstrip()
                    if not (stripped.startswith("sky130_fd_sc_hd__") or stripped.startswith("assign ")):
                        continue
                    start = line_number
                pending.append(line)
                if len(pending) > 64:
                    raise ValueError("Selected statement exceeds parser bound")
                if ";" not in line:
                    continue
                statement = "".join(pending).strip()
                pending = []
                if statement.startswith("assign "):
                    left, right = re.fullmatch(r"assign\s+(\S+)\s*=\s*(\S+)\s*;", statement).groups()
                    left, right = identifier(left), identifier(right)
                    if left in self.alias or left in self.driver:
                        raise ValueError("Multiple net driver")
                    self.alias[left] = (right, start)
                    continue
                match = re.fullmatch(r"(sky130_fd_sc_hd__([A-Za-z0-9_]+)_\d+)\s+(\S+)\s*\((.*)\)\s*;", statement, re.S)
                if match is None:
                    raise ValueError("Unsupported selected cell statement")
                module, kind, instance, body = match.groups()
                pins = {}
                position = 0
                pattern = re.compile(r"\s*\.(\w+)\s*\(\s*([^()]*)\s*\)\s*(?:,\s*|$)")
                while position < len(body):
                    pin = pattern.match(body, position)
                    if pin is None or pin[1] in pins:
                        raise ValueError("Unconsumed or duplicate cell pin")
                    pins[pin[1]] = identifier(pin[2])
                    position = pin.end()
                self.count += 1
                if kind.startswith(("fill", "decap", "diode", "tap")):
                    continue
                selected = set(pins) & OUTPUTS
                if not selected and instance.startswith("clkload") and set(pins) == {"A"}:
                    continue
                if len(selected) != 1:
                    raise ValueError("Ambiguous cell output")
                output = selected.pop()
                net = pins[output]
                if net in self.driver or net in self.alias:
                    raise ValueError("Multiple net driver")
                self.driver[net] = (module, kind, instance, pins, output, start)
        if pending:
            raise ValueError("Unterminated selected statement")

    def canonical(self, name):
        seen = set()
        while name in self.alias:
            if name in seen:
                raise ValueError("Alias cycle")
            seen.add(name)
            name = self.alias[name][0]
        return name


class RawPrimitiveModels:
    """Parse complete combinational model statements and interpret actual pins."""
    def __init__(self, path):
        self.modules = {}
        self.used = set()
        source = Path(path).read_text(encoding="utf-8")
        for match in re.finditer(r"\bmodule\s+(\S+)\s*\(([^;]*)\);(.*?)\bendmodule", source, re.S):
            name, ports, body = match.groups()
            if name in self.modules:
                raise ValueError("Duplicate PDK module")
            self.modules[name] = (tuple(x.strip() for x in ports.split(",")), body)

    def contract(self, name):
        ports, body = self.modules[name]
        if name == "sky130_fd_sc_hd__udp_mux_2to1":
            if ports != ("X", "A0", "A1", "S"):
                raise ValueError("Changed UDP pin order")
            rows = re.findall(r"3'b([01?]{3})\s*:\s*\{X\}\s*=\s*1'b([01])\s*;", body)
            if len(rows) != 6 or not re.search(r"casez\s*\(\s*\{A0,A1,S\}\s*\)", body):
                raise ValueError("Unsupported UDP truth table")
            for code in itertools.product(range(2), repeat=3):
                selected = {int(value) for pattern, value in rows
                            if all(p == "?" or int(p) == x for p, x in zip(pattern, code))}
                if selected != {code[code[2]]}:
                    raise ValueError("Actual UDP table does not implement two-state mux")
            return ("X",), ("A0", "A1", "S"), None
        outputs, inputs, calls = [], [], []
        for statement in body.split(";"):
            statement = statement.strip()
            if not statement:
                continue
            declaration = re.fullmatch(r"(input|output|wire)\s+(\w+)\s*", statement)
            if declaration:
                direction, wire = declaration.groups()
                if direction == "input":
                    inputs.append(wire)
                elif direction == "output":
                    outputs.append(wire)
                continue
            call = re.fullmatch(r"(\w+)\s+(\w+)\s*\(([^()]*)\)", statement)
            if call is None:
                raise ValueError("Unsupported/ignored PDK statement: " + name + ":" + statement)
            operation, unused, arguments = call.groups()
            if operation not in {"and", "nand", "or", "nor", "xor", "xnor", "not", "buf", "sky130_fd_sc_hd__udp_mux_2to1"}:
                raise ValueError("Unsupported PDK primitive")
            calls.append((operation, tuple(identifier(x) for x in arguments.split(","))))
        if len(outputs) != 1 or len(set(inputs + outputs)) != len(inputs + outputs) or set(ports) != set(inputs + outputs):
            raise ValueError("PDK declaration/port mismatch")
        return tuple(outputs), tuple(inputs), calls

    def symbolic(self, name, supplied, dag):
        self.used.add(name)
        outputs, inputs, calls = self.contract(name)
        if set(inputs) != set(supplied):
            raise ValueError("PDK cell pin contract mismatch")
        if calls is None:
            s, a, b = supplied["S"], supplied["A0"], supplied["A1"]
            return {"X": dag.or_gate(dag.and_gate(s ^ 1, a), dag.and_gate(s, b))}
        values = dict(supplied)
        for operation, terms in calls:
            if terms[0] in values or any(x not in values for x in terms[1:]):
                raise ValueError("PDK primitive has multiple/undefined driver")
            args = [values[x] for x in terms[1:]]
            if operation in {"buf", "not"}:
                if len(args) != 1:
                    raise ValueError("Unary primitive arity")
                value = args[0] ^ (operation == "not")
            elif operation == "sky130_fd_sc_hd__udp_mux_2to1":
                if len(args) != 3:
                    raise ValueError("Mux primitive arity")
                value = self.symbolic(operation, dict(zip(("A0", "A1", "S"), args)), dag)["X"]
            elif operation in {"and", "nand", "or", "nor"}:
                value = int(operation in {"and", "nand"})
                for x in args:
                    value = dag.and_gate(value, x) if operation in {"and", "nand"} else dag.or_gate(value, x)
                value ^= operation in {"nand", "nor"}
            else:
                value = 0
                for x in args:
                    value = dag.or_gate(dag.and_gate(value, x ^ 1), dag.and_gate(value ^ 1, x))
                value ^= operation == "xnor"
            values[terms[0]] = value
        return {name: values[name] for name in outputs}

    def concrete(self, name, supplied):
        outputs, inputs, calls = self.contract(name)
        if set(supplied) != set(inputs) or any(type(v) is not int or v not in (0, 1) for v in supplied.values()):
            raise ValueError("Invalid concrete PDK inputs")
        if calls is None:
            return {"X": supplied[("A0", "A1")[supplied["S"]]]}
        values = dict(supplied)
        for operation, terms in calls:
            bits = [values[x] for x in terms[1:]]
            if operation == "buf":
                value = bits[0]
            elif operation == "not":
                value = 1 - bits[0]
            elif operation == "sky130_fd_sc_hd__udp_mux_2to1":
                value = self.concrete(operation, dict(zip(("A0", "A1", "S"), bits)))["X"]
            elif operation in {"and", "nand"}:
                value = int(all(bits)) ^ int(operation == "nand")
            elif operation in {"or", "nor"}:
                value = int(any(bits)) ^ int(operation == "nor")
            else:
                value = (sum(bits) % 2) ^ int(operation == "xnor")
            values[terms[0]] = value
        return {wire: values[wire] for wire in outputs}


class Cone:
    def __init__(self, cells, models):
        self.cells, self.models = cells, models
        self.names = sorted({n for n in cells.driver if n.startswith("u_soc.")} | {"reset_sync_q", "reset_meta_q", "reset_n", "clk"})
        self.position = {name: i for i, name in enumerate(self.names)}
        self.dag = IndependentGraph({"inputs": len(self.names), "input_names": self.names,
                                     "first": [], "second": [], "outputs": [], "output_names": []}, {})
        self.memo, self.active, self.evidence = {}, set(), {}

    def symbol(self, name):
        return 2 * (self.position[name] + 1)

    def conjunction(self, *terms):
        value = 1
        for term in terms:
            value = self.dag.and_gate(value, term)
        return value

    def match_word(self, name, width, expected):
        return self.conjunction(*(self.symbol(f"{name}[{bit}]") ^ (1 - ((expected >> bit) & 1)) for bit in range(width)))

    def build(self, net, expand=False):
        net = self.cells.canonical(net)
        if net == INC + "[0]":
            expand = True
        key = (net, expand)
        if key in self.memo:
            return self.memo[key]
        if net in {"1'b0", "1'b1"}:
            return int(net[-1])
        if net in self.position and not expand:
            return self.symbol(net)
        if net in self.active:
            raise ValueError("Combinational loop")
        module, kind, instance, pins, output, line = self.cells.driver[net]
        if kind.startswith(("df", "sd", "dl")) and not kind.startswith("dly"):
            raise ValueError("Unnamed state boundary")
        self.active.add(net)
        supplied = {pin: self.build(wire) for pin, wire in pins.items() if pin not in OUTPUTS}
        result = self.models.symbolic(module, supplied, self.dag)
        if set(result) != {output}:
            raise ValueError("Actual cell output differs from PDK declaration")
        self.active.remove(net)
        self.memo[key] = result[output]
        self.evidence[instance] = {"module": module, "line": line, "pins": pins}
        return result[output]

    def difference(self, label, actual, expected):
        root = self.dag.or_gate(self.dag.and_gate(actual, expected ^ 1), self.dag.and_gate(actual ^ 1, expected))
        return {"label": label, "actual_literal": actual, "expected_literal": expected, "violation_literal": root}

    def concrete(self, net, witness, expand=False, memo=None):
        if memo is None:
            memo = {}
        net = self.cells.canonical(net)
        if net == INC + "[0]":
            expand = True
        key = (net, expand)
        if key in memo:
            return memo[key]
        if net in {"1'b0", "1'b1"}:
            return int(net[-1])
        if net in self.position and not expand:
            return witness[net]
        module, kind, instance, pins, output, line = self.cells.driver[net]
        values = {pin: self.concrete(wire, witness, memo=memo) for pin, wire in pins.items() if pin not in OUTPUTS}
        memo[key] = self.models.concrete(module, values)[output]
        return memo[key]


def obligations(cone, design):
    v, both, equal, logical_or = cone.symbol, cone.conjunction, cone.match_word, cone.dag.or_gate
    candidate = {"DM": "_029058_", "SA2": "_031249_"}[design]
    actual_freeze_n = cone.build(candidate)
    frozen = v("u_soc.u_observability.u_sysmon.freeze_q")
    apb = both(equal("u_soc.u_axil2apb.state", 3, 2), equal("u_soc.PADDR_bus", 32, 0x40000304),
               v("u_soc.PWRITE_bus"), v("u_soc.PSTRB_bus[0]"))
    snapshot = both(apb, equal("u_soc.PWDATA_bus", 8, 3))
    clear = both(apb, v("u_soc.PWDATA_bus[0]"), v("u_soc.PWDATA_bus[1]") ^ 1,
                 *(v(f"u_soc.PWDATA_bus[{bit}]") ^ 1 for bit in range(3, 8)))
    early = both(equal("u_soc.d_req_addr", 32, 0x40000304), v("u_soc.d_req_write"),
                 equal("u_soc.u_core.u_pipeline.datapath.wr_data_m", 8, 3), v("reset_sync_q"),
                 v("u_soc.u_core.d_pending") ^ 1, v("u_soc.u_core.d_buffer_valid") ^ 1,
                 v("u_soc.u_core.d_store_ack_valid") ^ 1, v("u_soc.d_route_pending_q") ^ 1,
                 equal("u_soc.u_mmio_axil_master.state", 3, 0))
    full_freeze = logical_or(frozen, logical_or(early, snapshot))
    rows = [cone.difference("total_counter_freeze_source_decode", actual_freeze_n ^ 1, full_freeze)]
    carry = 1
    for bit in range(32):
        q = v(f"{Q}[{bit}]")
        expected = logical_or(both(q, carry ^ 1), both(q ^ 1, carry))
        actual = cone.build(f"{INC}[{bit}]", True)
        rows.append(cone.difference(f"MCYCLE_increment_bit_{bit:02d}_modulo_2pow32", actual, expected))
        carry = both(carry, q)
    for bit in range(32):
        net = f"{Q}[{bit}]"
        module, kind, instance, pins, output, line = cone.cells.driver[net]
        if kind != "dfrtp" or output != "Q" or set(pins) != {"CLK", "D", "RESET_B", "Q"}:
            raise ValueError("Actual MCYCLE consumer is not unique reset flop")
        actual = cone.build(pins["D"])
        inc = cone.build(f"{INC}[{bit}]", bit == 0)
        expected = both(clear ^ 1, logical_or(both(full_freeze, v(net)), both(full_freeze ^ 1, inc)))
        row = cone.difference(f"MCYCLE_D_bit_{bit:02d}_clear_hold_increment", actual, expected)
        row.update(bit=bit, flop={"cell": instance, "kind": kind, "line": line, "pins": pins})
        rows.append(row)
    faults = [cone.difference("negative_freeze_q_only", actual_freeze_n ^ 1, frozen),
              cone.difference("negative_wrong_polarity", actual_freeze_n, full_freeze),
              cone.difference("negative_omit_request_acceptance", actual_freeze_n ^ 1, logical_or(frozen, snapshot))]
    return candidate, rows, faults


def source_contracts():
    """Exact local source reductions; no source parser or global LEC claim."""
    def compact(text):
        text = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
        return re.sub(r"\s+", "", text)
    contracts = {
        "soc_top.v": [
            "wire perf_freeze_early = d_req_valid && d_req_ready && data_sel_sysmon && d_req_write && (d_req_addr[7:0] == 8'h04) && (d_req_wdata[7:0] == 8'h03);",
            "assign d_req_ready = d_route_pending_q ? 1'b0 : data_sel_cacheable ? dcache_req_ready : data_sel_mmio ? mmio_req_ready : data_sel_unmapped ? 1'b1 : 1'b0;",
            ".PSEL (PSEL_bus && apb_sel_sysmon)", ".PENABLE (PENABLE_bus && apb_sel_sysmon)",
            ".PADDR (PADDR_bus[11:0])", ".freeze_early (perf_freeze_early)",
            ".reset_n (reset_n)", ".req_valid (mmio_cpu_req_valid)",
            "wire mmio_cpu_req_valid = d_req_valid && !d_route_pending_q && data_sel_mmio;"],
        "riscv_core_native.v": [
            "assign mem_access = mem_wr_m || mem_rd_m;",
            "assign d_req_valid = reset_n && mem_access && !d_pending && !d_buffer_valid && !d_store_ack_valid;",
            "assign d_req_write = mem_wr_m;", "assign d_req_addr = alu_result_m;",
            "assign d_req_wdata = !mem_wr_m ? 32'h0000_0000 : (mem_funct3_m == 3'b000) ? ({24'h0, wr_data_m[7:0]} << (8 * alu_result_m[1:0])) : (mem_funct3_m == 3'b001) ? ({16'h0, wr_data_m[15:0]} << (8 * alu_result_m[1:0])) : wr_data_m;"],
        "bus/soc_address_decoder.v": [
            "assign sel_sysmon = (addr[31:8] == 24'h4000_03);",
            "assign sel_cacheable = (addr[31:16] == 16'h0000);",
            "assign sel_mmio = sel_uart || sel_display || sel_timer || sel_sysmon;"],
        "axi/native_axi_lite_master.v": ["localparam [2:0] ST_IDLE = 3'd0;", "assign req_ready = (state == ST_IDLE);"],
        "axi/axi_lite_to_apb.v": ["localparam [2:0] ST_APB_ACCESS= 3'd2;", "assign PSEL = (state == ST_APB_SETUP) || (state == ST_APB_ACCESS);", "assign PENABLE = (state == ST_APB_ACCESS);"],
        "apb_performance_monitor.v": [
            "wire apb_wr = PSEL && PENABLE && PWRITE;",
            "wire ctrl_wr = apb_wr && (PADDR[7:0] == 8'h04) && PSTRB[0];",
            "wire [7:0] command = PWDATA[7:0];",
            "wire do_clear = ctrl_wr && ((command == CMD_CLEAR_START) || (command == CMD_CLEAR_FROZEN));",
            "wire do_freeze_snapshot = ctrl_wr && (command == CMD_FREEZE_SNAPSHOT);",
            "localparam [7:0] CMD_CLEAR_START = 8'h01;",
            "localparam [7:0] CMD_FREEZE_SNAPSHOT = 8'h03;",
            "localparam [7:0] CMD_CLEAR_FROZEN = 8'h05;",
            "wire freeze_early_active = (freeze_early === 1'b1);",
            "assign counter_clear = do_clear;",
            "assign counter_freeze = freeze_q || freeze_early_active || do_freeze_snapshot;"],
        "perf_counters.v": [
            "wire [31:0] mcycle_count_inc = mcycle_count + 32'd1;",
            "else if(counter_clear) begin mcycle_count <= 32'h0000_0000;",
            "else if(!counter_freeze && (PERF_COUNTERS_ENABLE != 0)) begin mcycle_count <= mcycle_count_inc;"],
        "performance_observability.v": [".counter_clear (counter_clear)", ".counter_freeze (counter_freeze)", ".freeze_early (freeze_early)", ".mcycle_count (mcycle_count_dbg)"],
    }
    hashes, rows = {}, []
    for relative, required in contracts.items():
        for directory in ("asic/snapshots/rtl_r14/hdl", "hdl"):
            path = ROOT / directory / relative
            source = compact(path.read_text())
            for clause in required:
                if compact(clause) not in source:
                    raise ValueError("Source local contract changed: " + str(path.relative_to(ROOT)) + " : " + clause)
            rel = path.relative_to(ROOT).as_posix()
            hashes[rel] = digest(path)
            rows.append({"source": rel, "exact_local_contracts": len(required), "status": "PASS"})
    # Explicit finite reductions of the unsigned low-byte commands and all
    # possible store funct3 values at the exactly aligned control address.
    for code in range(256):
        clear = (code & 1) and not (code & 2) and not (code & 0xf8)
        if bool(clear) != (code in (1, 5)):
            raise ValueError("Clear command reduction changed")
    for funct3 in range(8):
        for low in range(256):
            arbitrary_upper = 0xa5723100
            data = arbitrary_upper | low
            placed = (data & 255) if funct3 == 0 else (data & 65535) if funct3 == 1 else data
            if (placed & 255) != low:
                raise ValueError("Aligned native write low-byte reduction changed")
    return hashes, {"exact_source_contracts": rows, "all_low_byte_commands": 256,
                    "all_funct3_and_low_byte_codes": 2048,
                    "aligned_low_byte_upper_data_irrelevant_by_mask": True,
                    "address": "0x40000304", "states_unconstrained_in_local_model": True,
                    "four_state_case_equality_not_claimed": True}


def validate_saved(cone, row, saved, negative=False):
    for key, value in row.items():
        if saved[key] != value:
            raise ValueError("Independent raw reconstruction differs: " + row["label"] + ":" + key)
    decision = saved["decision"]
    root = row["violation_literal"]
    if not negative and root == 0:
        if decision != {"status": "PROVED_STRUCTURAL_BOOLEAN", "counterexample": None}:
            raise ValueError("Structural root has nonstructural verdict")
        return {"label": row["label"], "method": "STRUCTURAL_ZERO_ROOT", "status": "PASS"}
    clauses, index = encode(cone.dag, root)
    if decision["CNF_variables"] != len(index) or decision["CNF_initial_clauses"] != len(clauses):
        raise ValueError("Independent CNF count differs")
    result = {"label": row["label"], "CNF_variables": len(index), "CNF_clauses": len(clauses),
              "CNF_sha256": content_digest(clauses), "CNF_map_sha256": content_digest(sorted(index.items())),
              "violation_literal": root, "status": "PASS"}
    if not negative:
        if decision["status"] != "PROVED_BOOLEAN_CNF" or decision["counterexample"] is not None or decision["learned_clauses"] != len(decision["resolution_certificate"]):
            raise ValueError("Saved semantic proof status incomplete")
        steps = replay(clauses, decision["resolution_certificate"], decision["terminal_empty_clause_derivation"])
        if steps != decision["resolution_steps"] or steps != decision["independently_replayed_resolution_steps"]:
            raise ValueError("Saved proof replay count differs")
        result.update(method="EXACT_CNF_EMPTY_CLAUSE_REPLAY", resolution_steps=steps)
    else:
        if decision["status"] != "DISPROVED_UNDER_RECORDED_ASSUMPTIONS":
            raise ValueError("Negative control is not an actual counterexample")
        assignment = decision["CNF_assignment"]
        if len(assignment) != len(index) + 1 or any(type(x) is not int or x not in (-1, 1) for x in assignment[1:]) or not all(any(assignment[abs(x)] == (1 if x > 0 else -1) for x in c) for c in clauses):
            raise ValueError("Negative CNF witness invalid")
        point = {node // 2 - 1: int(assignment[var] == 1) for node, var in index.items() if node <= 2 * cone.dag.inputs}
        recorded = {int(key): bit for key, bit in decision["counterexample"].items()}
        if point != recorded or decision["counterexample_original_DAG_evaluation"] != 1 or cone.dag.evaluate(root, point) != 1:
            raise ValueError("CNF variable map/negative DAG witness invalid")
        names = {cone.names[bit]: value for bit, value in sorted(point.items())}
        actual = cone.dag.evaluate(row["actual_literal"], point)
        expected = cone.dag.evaluate(row["expected_literal"], point)
        if names != saved["named_boolean_witness"] or actual != saved["actual_at_witness"] or expected != saved["wrong_expression_at_witness"] or actual == expected:
            raise ValueError("Named witness does not demonstrate semantic difference")
        result.update(method="ACTUAL_SAT_WITNESS_REEVALUATION", named_witness=names,
                      actual_at_witness=actual, wrong_expression_at_witness=expected)
    return result


def model_truth_controls(cone):
    controls = []
    for module in sorted(cone.models.used):
        outputs, inputs, unused = cone.models.contract(module)
        dag = IndependentGraph({"inputs": len(inputs), "input_names": list(inputs), "first": [], "second": [], "outputs": [], "output_names": []}, {})
        result = cone.models.symbolic(module, {name: 2 * (i + 1) for i, name in enumerate(inputs)}, dag)
        points = 0
        for bits in itertools.product(range(2), repeat=len(inputs)):
            direct = cone.models.concrete(module, dict(zip(inputs, bits)))
            boolean = {out: dag.evaluate(literal, dict(enumerate(bits))) for out, literal in result.items()}
            if direct != boolean:
                raise ValueError("Separate direct primitive truth differs from symbolic model")
            points += 1
        controls.append({"module": module, "all_boolean_assignments": points, "status": "PASS"})
    return controls


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    output = args.out.resolve()
    if output.exists() or output.with_suffix(".md").exists() or not output.is_relative_to(ROOT):
        raise ValueError("Review requires new research output")
    guard = memory_cap()
    started = time.monotonic()
    bound_inputs = {"scripts/verification/mapped_counter_freeze.py": AUTHOR_SHA,
                    "scripts/verification/review_lec_onehot_cnf.py": HELPER_SHA}
    if any(digest(ROOT / path) != expected for path, expected in bound_inputs.items()):
        raise ValueError("Frozen author or independently reviewed helper changed")
    bound_inputs[PDK] = digest(ROOT / PDK)
    source_hashes, source_review = source_contracts()
    bound_inputs.update(source_hashes)
    bound_inputs[Path(__file__).relative_to(ROOT).as_posix()] = digest(Path(__file__))
    designs, all_steps = [], 0
    for design, relative in PATHS.items():
        first, second = (PROOF_DIR / f"{design.lower()}_p{number}.json" for number in (1, 2))
        pair_sha = [digest(path) for path in (first, second)]
        if pair_sha[0] != pair_sha[1]:
            raise ValueError("Two independent saved executions differ in bytes")
        for path, expected in zip((first, second), pair_sha):
            bound_inputs[path.relative_to(ROOT).as_posix()] = expected
        bound_inputs[relative] = digest(ROOT / relative)
        cells = RawCells(ROOT / relative)
        cone = Cone(cells, RawPrimitiveModels(ROOT / PDK))
        candidate, proofs, negatives = obligations(cone, design)
        if len(proofs) != 65 or len(negatives) != 3:
            raise ValueError("Incomplete local-obligation construction")
        truth = model_truth_controls(cone)
        passes = []
        for pass_number, path in enumerate((first, second), 1):
            saved = json.loads(path.read_text())
            if saved["status"] != "VERIFIED_COUNTER_FREEZE_ALIAS" or saved["design"] != design or saved["netlist"] != relative or saved["netlist_sha256"] != bound_inputs[relative] or saved["script_sha256"] != AUTHOR_SHA or saved["PDK_sha256"] != bound_inputs[PDK] or saved["expression"] != "~dut." + candidate or saved["MCYCLE_width"] != 32 or saved["assumptions"] != [] or saved["counter_hold_increment_bridge_verified"] is not True:
                raise ValueError("Saved top-level scope/inputs mismatch")
            if saved["symbolic_named_boundaries"] != cone.names or saved["cone_cells"] != cone.evidence or saved["used_PDK_modules"] != sorted(cone.models.used):
                raise ValueError("Exact input boundary or mapped-cone evidence differs")
            for rel, expected in saved["source_inputs"].items():
                if digest(ROOT / rel) != expected:
                    raise ValueError("Pinned source changed")
                bound_inputs[rel] = expected
            if len(saved["proofs"]) != 65 or len(saved["negative_controls"]) != 3:
                raise ValueError("Saved obligation completeness differs")
            reviewed = [validate_saved(cone, row, original) for row, original in zip(proofs, saved["proofs"])]
            faults = [validate_saved(cone, row, original, True) for row, original in zip(negatives, saved["negative_controls"])]
            for fault in faults:
                witness = fault["named_witness"]
                mapped_n = cone.concrete(candidate, witness)
                observed = mapped_n if fault["label"] == "negative_wrong_polarity" else mapped_n ^ 1
                if observed != fault["actual_at_witness"]:
                    raise ValueError("Independent direct raw PDK witness differs from CNF/DAG")
                fault["separate_direct_raw_cell_witness_evaluation"] = observed
            counts = {"structural": sum(r["method"] == "STRUCTURAL_ZERO_ROOT" for r in reviewed),
                      "CNF_certificates": sum(r["method"] == "EXACT_CNF_EMPTY_CLAUSE_REPLAY" for r in reviewed),
                      "actual_semantic_witnesses": len(faults)}
            if counts != {"structural": 2, "CNF_certificates": 63, "actual_semantic_witnesses": 3}:
                raise ValueError("Local proof method counts differ")
            steps = sum(r.get("resolution_steps", 0) for r in reviewed)
            all_steps += steps
            passes.append({"pass": pass_number, "status": "PASS", "counts": counts,
                           "resolution_steps": steps, "positive_obligations": reviewed, "negative_controls": faults})
            del saved
            gc.collect()
            print(design, "pass", pass_number, counts, "resolution steps", steps, flush=True)
        designs.append({"design": design, "status": "PASS", "paired_bytes_and_all_fields_equal": True,
                        "expression": "~dut." + candidate, "symbolic_named_boundaries": len(cone.names),
                        "mapped_cone_cells": len(cone.evidence), "all32_actual_increment_and_D_consumers": True,
                        "PDK_truth_table_controls": truth, "passes": passes})
        del cone, cells
        gc.collect()
    if any(digest(ROOT / rel) != expected for rel, expected in bound_inputs.items()):
        raise ValueError("Read-only inputs changed during review")
    result = {"status": "PASS_INDEPENDENT_MAPPED_MCYCLE_FREEZE_REVIEW", "scope": "Exact local Boolean mapped observer alias, all32 increment functions and clear/hold/increment D consumers for the recorded DM/SA2 netlists. Does not prove asynchronous/reset/event/delay behavior, source-X closure, reachability, other counters or full-SoC LEC.",
              "full_sequential_LEC": "OPEN", "source_to_Boolean_model_closure": "OPEN",
              "no_initial_state_or_onehot_assumptions": True,
              "named_state_and_wire_boundaries_symbolic": True,
              "same_bit0_increment_driver_expanded_on_both_sides": True,
              "higher_increment_consumer_boundaries_connected_by_all32_separate_increment_lemmas": True,
              "independent_implementation": {"raw_netlist_parser": True, "PDK_primitive_parser": True,
                  "direct_PDK_Boolean_interpreter": True, "DAG_CNF_certificate_helpers_previously_independently_reviewed": True,
                  "author_checker_parser_compiler_or_SAT_imported": False, "new_actual_SAT_solves": 0,
                  "design_tool_or_WSL_processes": 0},
              "source_local_contract_review": source_review, "designs": designs,
              "paired_CNF_certificates_replayed": 252, "paired_structural_roots_checked": 8,
              "paired_actual_negative_witnesses_checked": 12, "total_resolution_steps_replayed": all_steps,
              "read_only_input_sha256": bound_inputs, "memory_enforcement": guard,
              "peak_process_memory": peak_memory(), "elapsed_seconds": round(time.monotonic() - started, 3)}
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    output.with_suffix(".md").write_text("# Independent mapped MCYCLE freeze review\n\nPASS for the exact recorded DM and SA2 Boolean observer aliases and all32 actual increment/D-consumer cones. The separate raw-netlist and PDK interpreter reconstructed every saved root and mapped cell; independent CNF encoding and resolution replay checked all252 paired certificates, eight structural zero roots and12 actual semantic counterexamples. A separate direct PDK interpreter re-evaluated the negative witnesses. Source decode, aligned low-byte placement, clear commands1/5 and clear priority are checked in both the signed source snapshot and current RTL. No named state/wire value was zero-initialized or constrained by one-hot/reachability assumptions. Bit0's actual complement driver is expanded consistently; all32 increment lemmas connect the higher increment boundaries to their D consumers.\n\nThis supports these local GLS observer expressions. It does not establish full-chip LEC, other performance counters, source-X/four-state closure, initialization, asynchronous events or delay equivalence. No new SAT solve, frontend or WSL job ran. Frozen input hashes were checked before/after under a hard256MiB process cap. See the adjacent JSON for exact source/netlist identities, all proof rows, truth controls, witnesses, memory and counts.\n", encoding="ascii")
    print(result["status"], "certificates252; steps", all_steps, flush=True)


if __name__ == "__main__":
    main()
