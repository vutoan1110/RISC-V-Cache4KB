"""Bounded, local structural audit of mapped performance-counter freeze cones.

No design tool is run.  Original netlists and RTL remain read-only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import itertools
import time
from pathlib import Path

from lec_onehot_boolean import DAG, enforce_process_memory, sha
from lec_onehot_sat import decide_sat

ROOT = Path(__file__).resolve().parents[2]
DM = ROOT / "asic/soc_dm_4kb/runs/r14F_A/55-openroad-fillinsertion/soc_asic_top.nl.v"
SA2 = ROOT / "asic/soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1/56-openroad-fillinsertion/soc_asic_top.nl.v"


def norm(token):
    return token.strip().lstrip("\\")


class Netlist:
    def __init__(self, path):
        self.path = Path(path)
        self.drivers = {}
        self.cells = {}
        self.aliases = {}
        self.full_types = {}
        pending = []
        start = 0
        with self.path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not pending:
                    if not re.match(r"\s*(sky130_fd_sc_hd__|assign )", line):
                        continue
                    start = line_number
                pending.append(line)
                if ";" not in line:
                    if len(pending) > 64:
                        raise ValueError("Oversized selected statement")
                    continue
                statement = "".join(pending)
                pending = []
                if statement.lstrip().startswith("assign "):
                    match = re.fullmatch(r"\s*assign\s+(\S+)\s*=\s*(\S+)\s*;\s*", statement)
                    if not match:
                        raise ValueError(f"Unsupported alias at {start}")
                    left, right = map(norm, match.groups())
                    if left in self.aliases or left in self.drivers:
                        raise ValueError("Duplicate alias driver")
                    self.aliases[left] = (right, start)
                    continue
                match = re.fullmatch(r"\s*(sky130_fd_sc_hd__(\w+)_\d+)\s+(\S+)\s*\((.*)\);\s*", statement, re.S)
                if not match:
                    raise ValueError(f"Unsupported cell at {start}")
                full_type, kind, name, body = match.groups()
                pins = {pin: norm(net) for pin, net in re.findall(r"\.(\w+)\(\s*([^()]*)\s*\)", body)}
                if len(pins) != len(re.findall(r"\.\w+\(", body)):
                    raise ValueError("Malformed/duplicate pins")
                if kind.startswith(("fill", "decap", "diode", "tap")):
                    continue
                outputs = [p for p in ("X", "Y", "Q", "Q_N", "GCLK", "HI", "LO") if p in pins]
                if not outputs and name.startswith("clkload") and set(pins) == {"A"}:
                    # Physical clock-load dummy has no logical output/driver.
                    continue
                if len(outputs) != 1:
                    raise ValueError(f"Unknown output contract {kind} {name} {pins}")
                out = pins[outputs[0]]
                if out in self.drivers or out in self.aliases:
                    raise ValueError(f"Duplicate driver {out}")
                cell = (kind, name, pins, start)
                self.drivers[out] = cell
                self.cells[name] = cell
                self.full_types[name] = full_type

    def canonical(self, net):
        seen = set()
        while net in self.aliases:
            if net in seen:
                raise ValueError("Alias cycle")
            seen.add(net)
            net = self.aliases[net][0]
        return net

    def unbuffer(self, net):
        path = []
        net = self.canonical(net)
        while net in self.drivers and self.drivers[net][0] in ("buf", "clkbuf", "dlymetal6s2s", "dlymetal6s4s", "dlymetal6s6s"):
            cell = self.drivers[net]
            path.append(cell)
            net = self.canonical(cell[2]["A"])
        return net, path

    def tree(self, net, depth=5, visited=None):
        net, buffers = self.unbuffer(net)
        result = {"net": net}
        if buffers:
            result["buffers"] = [c[1] for c in buffers]
        if depth <= 0 or net not in self.drivers or net.startswith("u_soc."):
            return result
        kind, name, pins, line = self.drivers[net]
        result.update(kind=kind, cell=name, line=line)
        result["inputs"] = {p: self.tree(n, depth-1) for p, n in pins.items() if p not in ("X", "Y", "Q", "Q_N", "HI", "LO")}
        return result


class CellModels:
    def __init__(self, path):
        text = Path(path).read_text(encoding="utf-8")
        self.models = {name: (ports, body) for name, ports, body in
                       re.findall(r"module\s+(\S+)\s*\(([^;]*)\);(.*?)endmodule", text, re.S)}
        self.used = set()

    def apply(self, name, values, dag):
        if name not in self.models:
            raise ValueError(f"Missing exact PDK model {name}")
        self.used.add(name)
        ports, body = self.models[name]
        if name == "sky130_fd_sc_hd__udp_mux_2to1":
            # Prove the actual behavioral case table is total and is a mux
            # on all eight Boolean assignments before using its formula.
            records = re.findall(r"3'b([01?]{3}):\s*\{X\}\s*=\s*1'b([01]);", body)
            if len(records) != 6:
                raise ValueError("Changed/unsupported UDP mux model")
            for point in itertools.product((0, 1), repeat=3):
                matching = [int(v) for pattern, v in records if all(p == "?" or int(p) == x for p, x in zip(pattern, point))]
                if not matching or len(set(matching)) != 1 or matching[0] != point[point[2]]:
                    raise ValueError("PDK mux Boolean truth mismatch")
            return {"X": dag.OR(dag.AND(values["S"] ^ 1, values["A0"]), dag.AND(values["S"], values["A1"]))}
        work = dict(values)
        calls = re.findall(r"^\s*(\S+)\s+(\S+)\s*\(([^;]*)\);", body, re.M)
        allowed = {"and", "nand", "or", "nor", "xor", "xnor", "not", "buf", "sky130_fd_sc_hd__udp_mux_2to1"}
        if not calls:
            raise ValueError(f"No supported primitive calls {name}")
        for primitive, instance, args in calls:
            terms = [norm(a) for a in args.split(",")]
            if primitive not in allowed or any(a not in work for a in terms[1:]):
                raise ValueError(f"Unsupported PDK primitive/ordering {name}:{primitive}:{terms}")
            inputs = [work[a] for a in terms[1:]]
            if primitive in ("buf", "not"):
                if len(inputs) != 1:
                    raise ValueError("Non-unary primitive")
                value = inputs[0] ^ int(primitive == "not")
            elif primitive.startswith("sky130"):
                if len(inputs) != 3:
                    raise ValueError("Bad mux primitive arity")
                value = self.apply(primitive, dict(zip(("A0", "A1", "S"), inputs)), dag)["X"]
            elif primitive in ("and", "nand", "or", "nor"):
                value = int(primitive in ("and", "nand"))
                for a in inputs:
                    value = dag.AND(value, a) if primitive in ("and", "nand") else dag.OR(value, a)
                value ^= int(primitive in ("nand", "nor"))
            else:
                value = 0
                for a in inputs:
                    value = dag.OR(dag.AND(value, a ^ 1), dag.AND(value ^ 1, a))
                value ^= int(primitive == "xnor")
            work[terms[0]] = value
        outputs = re.findall(r"output\s+(?:wire\s+)?(\w+)\s*;", body)
        if not outputs or any(p not in work for p in outputs):
            raise ValueError("Missing PDK output")
        return {p: work[p] for p in outputs}


class Compiler:
    def __init__(self, netlist, models):
        self.netlist, self.models = netlist, models
        # Every named state/wire boundary is a symbolic Boolean.  No reset,
        # reachability, zero-init, one-hot or RAM-data premise is imposed.
        self.names = sorted({n for n in netlist.drivers if n.startswith("u_soc.")} | {"reset_sync_q", "reset_meta_q", "reset_n", "clk"})
        self.index = {n: i for i, n in enumerate(self.names)}
        self.dag = DAG(len(self.names), time.monotonic() + 10)
        self.cache = {}
        self.visiting = set()
        self.evidence = {}

    def variable(self, name):
        if name not in self.index:
            raise ValueError(f"Missing named Boolean boundary {name}")
        return 2 * (self.index[name] + 1)

    def compile(self, net, expand_named=False):
        net = self.netlist.canonical(net)
        if net == "u_soc.u_observability.u_perf_counters.mcycle_count_inc[0]":
            # The mapped bit0 D mux uses !Q0 as selector and is optimized
            # using that algebraic relation.  Expand its real driver on both
            # sides instead of assigning independent values to Q0 and !Q0.
            expand_named = True
        key = (net, expand_named)
        if key in self.cache:
            return self.cache[key]
        if net in ("1'b0", "1'b1"):
            return int(net[-1])
        if net in self.index and not expand_named:
            return self.variable(net)
        if net in self.visiting:
            raise ValueError("Combinational cycle")
        if net not in self.netlist.drivers:
            raise ValueError(f"Undriven/unsupported boundary {net}")
        kind, name, pins, line = self.netlist.drivers[net]
        if kind.startswith(("df", "sd", "dl")) and not kind.startswith("dly"):
            raise ValueError(f"Unnamed sequential boundary {net}")
        self.visiting.add(net)
        inputs = {p: self.compile(n) for p, n in pins.items() if p not in ("X", "Y", "Q", "Q_N", "HI", "LO")}
        outputs = self.models.apply(self.netlist.full_types[name], inputs, self.dag)
        selected = [p for p, n in pins.items() if n == net and p in outputs]
        if len(selected) != 1:
            raise ValueError("Unproven cell output pin")
        result = outputs[selected[0]]
        self.visiting.remove(net)
        self.cache[key] = result
        self.evidence[name] = {"module": self.netlist.full_types[name], "line": line, "pins": pins}
        return result

    def both(self, *terms):
        value = 1
        for term in terms:
            value = self.dag.AND(value, term)
        return value

    def equals(self, base, width, expected):
        return self.both(*(self.variable(f"{base}[{i}]") ^ (1 - ((expected >> i) & 1)) for i in range(width)))

    def prove(self, label, actual, expected):
        self.dag.deadline = time.monotonic() + 10
        xor = self.dag.OR(self.dag.AND(actual, expected ^ 1), self.dag.AND(actual ^ 1, expected))
        if xor == 0:
            decision = {"status": "PROVED_STRUCTURAL_BOOLEAN", "counterexample": None}
        else:
            decision = decide_sat(self.dag, xor)
        return {"label": label, "actual_literal": actual, "expected_literal": expected,
                "violation_literal": xor, "decision": decision}


def audit(design, path):
    graph = Netlist(path)
    pdk = ROOT / "asic/soc_dm_4kb/formal_pdk.v"
    compiler = Compiler(graph, CellModels(pdk))
    v, A, O = compiler.variable, compiler.both, compiler.dag.OR
    candidate = "_029058_" if design == "DM" else "_031249_"
    total_n = compiler.compile(candidate)
    freeze_q = v("u_soc.u_observability.u_sysmon.freeze_q")
    apb_access = compiler.equals("u_soc.u_axil2apb.state", 3, 2)
    apb_control = A(apb_access, compiler.equals("u_soc.PADDR_bus", 32, 0x40000304), v("u_soc.PWRITE_bus"), v("u_soc.PSTRB_bus[0]"))
    apb_freeze = A(apb_control, compiler.equals("u_soc.PWDATA_bus", 8, 3))
    clear = A(apb_control, v("u_soc.PWDATA_bus[0]"), v("u_soc.PWDATA_bus[1]") ^ 1,
              *(v(f"u_soc.PWDATA_bus[{i}]") ^ 1 for i in range(3, 8)))
    # At the aligned control address, SB/SH/SW low-byte placement is exactly
    # wr_data_m[7:0].  d_req_write makes mem_access true; address match makes
    # MMIO routing selected and cacheable routing false.  No FSM-state premise.
    early = A(compiler.equals("u_soc.d_req_addr", 32, 0x40000304), v("u_soc.d_req_write"),
              compiler.equals("u_soc.u_core.u_pipeline.datapath.wr_data_m", 8, 3),
              v("reset_sync_q"), v("u_soc.u_core.d_pending") ^ 1,
              v("u_soc.u_core.d_buffer_valid") ^ 1, v("u_soc.u_core.d_store_ack_valid") ^ 1,
              v("u_soc.d_route_pending_q") ^ 1, compiler.equals("u_soc.u_mmio_axil_master.state", 3, 0))
    expected_freeze = O(freeze_q, O(early, apb_freeze))
    rows = [compiler.prove("total_counter_freeze_source_decode", total_n ^ 1, expected_freeze)]
    carry = 1
    for bit in range(32):
        compiler.dag.deadline = time.monotonic() + 10
        q = v(f"u_soc.perf_mcycle_count_dbg[{bit}]")
        expected_inc = O(A(q, carry ^ 1), A(q ^ 1, carry))
        actual_inc = compiler.compile(f"u_soc.u_observability.u_perf_counters.mcycle_count_inc[{bit}]", expand_named=True)
        rows.append(compiler.prove(f"MCYCLE_increment_bit_{bit:02d}_modulo_2pow32", actual_inc, expected_inc))
        carry = A(carry, q)
    # Connect every real MCYCLE state Q to its D consumer; bit zero's increment
    # is expanded (it is !Q0), rather than assumed independently correlated.
    for bit in range(32):
        qname = f"u_soc.perf_mcycle_count_dbg[{bit}]"
        if qname not in graph.drivers or graph.drivers[qname][0] != "dfrtp":
            raise ValueError(f"Missing unique MCYCLE reset flop {qname}")
        flop = graph.drivers[qname]
        actual = compiler.compile(flop[2]["D"])
        incname = f"u_soc.u_observability.u_perf_counters.mcycle_count_inc[{bit}]"
        inc = compiler.compile(incname, expand_named=bit == 0)
        q = v(qname)
        expected = A(clear ^ 1, O(A(expected_freeze, q), A(expected_freeze ^ 1, inc)))
        row = compiler.prove(f"MCYCLE_D_bit_{bit:02d}_clear_hold_increment", actual, expected)
        row.update(bit=bit, flop={"cell": flop[1], "kind": flop[0], "line": flop[3], "pins": flop[2]})
        rows.append(row)
    # Actual wrong observer equations must differ with a real Boolean witness.
    negatives = [compiler.prove("negative_freeze_q_only", total_n ^ 1, freeze_q),
                 compiler.prove("negative_wrong_polarity", total_n, expected_freeze),
                 compiler.prove("negative_omit_request_acceptance", total_n ^ 1, O(freeze_q, apb_freeze))]
    for row in negatives:
        decision = row["decision"]
        if decision.get("counterexample") is not None:
            point = {int(k): value for k, value in decision["counterexample"].items()}
            row["named_boolean_witness"] = {compiler.names[k]: value for k, value in sorted(point.items())}
            row["actual_at_witness"] = compiler.dag.evaluate(row["actual_literal"], point)
            row["wrong_expression_at_witness"] = compiler.dag.evaluate(row["expected_literal"], point)
    proof_ok = all(r["decision"]["status"].startswith("PROVED_") for r in rows)
    negative_ok = all(r["decision"]["status"] == "DISPROVED_UNDER_RECORDED_ASSUMPTIONS" and
                      r["actual_at_witness"] != r["wrong_expression_at_witness"] for r in negatives)
    return {"status": "VERIFIED_COUNTER_FREEZE_ALIAS" if proof_ok and negative_ok else "UNVERIFIED_COUNTER_FREEZE_ALIAS",
            "design": design, "netlist": path.relative_to(ROOT).as_posix(), "netlist_sha256": sha(path),
            "expression": f"~dut.{candidate}", "counter_hold_increment_bridge_verified": proof_ok and negative_ok,
            "MCYCLE_width": 32, "proofs": rows, "negative_controls": negatives,
            "symbolic_named_boundaries": compiler.names, "used_PDK_modules": sorted(compiler.models.used),
            "cone_cells": compiler.evidence, "PDK_sha256": sha(pdk),
            "scope": "Local Boolean counter-freeze observer alias and all32 MCYCLE D clear/hold/increment consumers. No full-SoC LEC, event-delay or initialization proof.",
            "assumptions": [], "source_inputs": {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in
                 [ROOT / "asic/snapshots/rtl_r14/hdl" / f for f in ("apb_performance_monitor.v", "perf_counters.v", "soc_top.v", "riscv_core_native.v", "performance_observability.v", "datapath.v", "bus/soc_address_decoder.v", "axi/axi_lite_to_apb.v", "axi/native_axi_lite_master.v")]},
            "script_sha256": sha(Path(__file__))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--design", choices=("DM", "SA2"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    memory = enforce_process_memory()
    path = DM if args.design == "DM" else SA2
    if args.audit:
        record = audit(args.design, path)
        record["memory_guard"] = memory
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": record["status"], "out": str(args.out), "proofs": len(record["proofs"])}))
        raise SystemExit(0 if record["status"] == "VERIFIED_COUNTER_FREEZE_ALIAS" else 2)
    graph = Netlist(path)
    nets = ("_029058_", "net1976", "net1271", "_022890_", "_029054_") if args.design == "DM" else ("_031249_", "net2697", "net2694", "_024965_", "net3094")
    record = {"status": "DIAGNOSTIC_ONLY", "design": args.design,
              "memory_guard": memory, "netlist_sha256": sha(path),
              "cells": len(graph.cells), "aliases": len(graph.aliases),
              "trees": {n: graph.tree(n, 8) for n in nets}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": record["status"], "out": str(args.out)}))


if __name__ == "__main__":
    main()
