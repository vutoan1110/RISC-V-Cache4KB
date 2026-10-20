"""Mapped performance-counter freeze alias for the RTL 6c4ccffd layouts (2026-10-20).

mapped_counter_freeze.py proves, for the two R14 netlists, that one internal net is the active-low "total counter
freeze" of the sysmon (freeze_q | APB control write of 3 | the early store of 3 to 0x40000304) and that every one of the
32 MCYCLE flops loads clear / hold / increment from it; the exact-window GLS observes that net. The net name changes
with every netlist, so this script finds it in a new netlist and runs the same proof (classes reused unchanged from
mapped_counter_freeze.py; the old script is not edited, its receipts keep their script hash).

    python mapped_counter_freeze_rtl6c4c.py --design DM --netlist <final .nl.v> --out <json> [--candidate <net>]

Search: nets in the D-input cones (depth <= 6, buffers skipped) of all 32 u_soc.perf_mcycle_count_dbg flops, common
to every bit; each candidate is compiled and must prove ~net == expected_freeze (active low, as the R14 aliases) or
net == expected_freeze (active high); the first proved candidate is audited in full (all 32 D bits, MCYCLE increment,
three negative controls). Source inputs are hashed from asic/snapshots/rtl_rfbht.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from mapped_counter_freeze import ROOT, CellModels, Compiler, Netlist, sha
from lec_onehot_boolean import enforce_process_memory

SNAP = ROOT / "asic/snapshots/rtl_rfbht/hdl"
SOURCES = ("apb_performance_monitor.v", "perf_counters.v", "soc_top.v", "riscv_core_native.v",
           "performance_observability.v", "datapath.v", "bus/soc_address_decoder.v", "axi/axi_lite_to_apb.v",
           "axi/native_axi_lite_master.v")


def cone(graph, net, depth, out):
    net, _ = graph.unbuffer(net)
    out.add(net)
    if depth <= 0 or net not in graph.drivers or net.startswith("u_soc."):
        return
    kind, name, pins, line = graph.drivers[net]
    if kind.startswith(("df", "sd", "dl")) and not kind.startswith("dly"):
        return
    for p, n in pins.items():
        if p not in ("X", "Y", "Q", "Q_N", "HI", "LO"):
            cone(graph, n, depth - 1, out)


def expected_terms(compiler):
    v, A, O = compiler.variable, compiler.both, compiler.dag.OR
    freeze_q = v("u_soc.u_observability.u_sysmon.freeze_q")
    apb_access = compiler.equals("u_soc.u_axil2apb.state", 3, 2)
    apb_control = A(apb_access, compiler.equals("u_soc.PADDR_bus", 32, 0x40000304), v("u_soc.PWRITE_bus"),
                    v("u_soc.PSTRB_bus[0]"))
    apb_freeze = A(apb_control, compiler.equals("u_soc.PWDATA_bus", 8, 3))
    clear = A(apb_control, v("u_soc.PWDATA_bus[0]"), v("u_soc.PWDATA_bus[1]") ^ 1,
              *(v(f"u_soc.PWDATA_bus[{i}]") ^ 1 for i in range(3, 8)))
    early = A(compiler.equals("u_soc.d_req_addr", 32, 0x40000304), v("u_soc.d_req_write"),
              compiler.equals("u_soc.u_core.u_pipeline.datapath.wr_data_m", 8, 3),
              v("reset_sync_q"), v("u_soc.u_core.d_pending") ^ 1,
              v("u_soc.u_core.d_buffer_valid") ^ 1, v("u_soc.u_core.d_store_ack_valid") ^ 1,
              v("u_soc.d_route_pending_q") ^ 1, compiler.equals("u_soc.u_mmio_axil_master.state", 3, 0))
    return freeze_q, apb_freeze, clear, O(freeze_q, O(early, apb_freeze))


def find(graph, compiler, expected):
    common = None
    for bit in range(32):
        q = f"u_soc.perf_mcycle_count_dbg[{bit}]"
        if q not in graph.drivers:
            raise ValueError(f"Missing MCYCLE flop {q}")
        s = set()
        cone(graph, graph.drivers[q][2]["D"], 6, s)
        common = s if common is None else common & s
    tried = []
    for net in sorted(n for n in common if not n.startswith("u_soc.") and n not in ("1'b0", "1'b1")):
        try:
            lit = compiler.compile(net)
        except ValueError as e:
            tried.append({"net": net, "skip": str(e)})
            continue
        for polarity, actual in (("active_low", lit ^ 1), ("active_high", lit)):
            row = compiler.prove("candidate_" + net, actual, expected)
            tried.append({"net": net, "polarity": polarity, "status": row["decision"]["status"]})
            if row["decision"]["status"].startswith("PROVED_"):
                return net, polarity, tried
    return None, None, tried


def audit(design, path, candidate, polarity):
    graph = Netlist(path)
    pdk = ROOT / "asic/soc_dm_4kb/formal_pdk.v"
    compiler = Compiler(graph, CellModels(pdk))
    v, A, O = compiler.variable, compiler.both, compiler.dag.OR
    freeze_q, apb_freeze, clear, expected_freeze = expected_terms(compiler)
    lit = compiler.compile(candidate)
    freeze_lit = lit ^ 1 if polarity == "active_low" else lit
    rows = [compiler.prove("total_counter_freeze_source_decode", freeze_lit, expected_freeze)]
    carry = 1
    for bit in range(32):
        compiler.dag.deadline = time.monotonic() + 10
        q = v(f"u_soc.perf_mcycle_count_dbg[{bit}]")
        expected_inc = O(A(q, carry ^ 1), A(q ^ 1, carry))
        actual_inc = compiler.compile(f"u_soc.u_observability.u_perf_counters.mcycle_count_inc[{bit}]", expand_named=True)
        rows.append(compiler.prove(f"MCYCLE_increment_bit_{bit:02d}_modulo_2pow32", actual_inc, expected_inc))
        carry = A(carry, q)
    for bit in range(32):
        qname = f"u_soc.perf_mcycle_count_dbg[{bit}]"
        if qname not in graph.drivers or graph.drivers[qname][0] != "dfrtp":
            raise ValueError(f"Missing unique MCYCLE reset flop {qname}")
        flop = graph.drivers[qname]
        actual = compiler.compile(flop[2]["D"])
        inc = compiler.compile(f"u_soc.u_observability.u_perf_counters.mcycle_count_inc[{bit}]", expand_named=bit == 0)
        q = v(qname)
        expected = A(clear ^ 1, O(A(expected_freeze, q), A(expected_freeze ^ 1, inc)))
        row = compiler.prove(f"MCYCLE_D_bit_{bit:02d}_clear_hold_increment", actual, expected)
        row.update(bit=bit, flop={"cell": flop[1], "kind": flop[0], "line": flop[3], "pins": flop[2]})
        rows.append(row)
    negatives = [compiler.prove("negative_freeze_q_only", freeze_lit, freeze_q),
                 compiler.prove("negative_wrong_polarity", freeze_lit ^ 1, expected_freeze),
                 compiler.prove("negative_omit_request_acceptance", freeze_lit, O(freeze_q, apb_freeze))]
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
    expr = ("~dut." if polarity == "active_low" else "dut.") + candidate
    return {"status": "VERIFIED_COUNTER_FREEZE_ALIAS" if proof_ok and negative_ok else "UNVERIFIED_COUNTER_FREEZE_ALIAS",
            "design": design, "netlist": path.relative_to(ROOT).as_posix(), "netlist_sha256": sha(path),
            "expression": expr, "candidate_polarity": polarity,
            "counter_hold_increment_bridge_verified": proof_ok and negative_ok, "MCYCLE_width": 32,
            "proofs": rows, "negative_controls": negatives, "symbolic_named_boundaries": compiler.names,
            "used_PDK_modules": sorted(compiler.models.used), "cone_cells": compiler.evidence, "PDK_sha256": sha(pdk),
            "scope": "Local Boolean counter-freeze observer alias and all32 MCYCLE D clear/hold/increment consumers. "
                     "No full-SoC LEC, event-delay or initialization proof.",
            "assumptions": [], "source_inputs": {(SNAP / f).relative_to(ROOT).as_posix(): sha(SNAP / f) for f in SOURCES},
            "script_sha256": sha(Path(__file__)), "library_script_sha256": sha(ROOT / "scripts/verification/mapped_counter_freeze.py")}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--design", required=True)
    ap.add_argument("--netlist", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--candidate")
    a = ap.parse_args()
    memory = enforce_process_memory()
    path = a.netlist.resolve()
    tried = []
    if a.candidate:
        candidate, polarity = a.candidate, None
        graph = Netlist(path)
        compiler = Compiler(graph, CellModels(ROOT / "asic/soc_dm_4kb/formal_pdk.v"))
        expected = expected_terms(compiler)[3]
        lit = compiler.compile(candidate)
        for pol, actual in (("active_low", lit ^ 1), ("active_high", lit)):
            if compiler.prove("candidate", actual, expected)["decision"]["status"].startswith("PROVED_"):
                polarity = pol
                break
    else:
        graph = Netlist(path)
        compiler = Compiler(graph, CellModels(ROOT / "asic/soc_dm_4kb/formal_pdk.v"))
        candidate, polarity, tried = find(graph, compiler, expected_terms(compiler)[3])
    if not candidate or not polarity:
        record = {"status": "NO_CANDIDATE", "design": a.design, "netlist_sha256": sha(path), "tried": tried}
    else:
        record = audit(a.design, path, candidate, polarity)
        record["search"] = tried
    record["memory_guard"] = memory
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": record["status"], "expression": record.get("expression"), "out": str(a.out)}))
    raise SystemExit(0 if record["status"] == "VERIFIED_COUNTER_FREEZE_ALIAS" else 2)


if __name__ == "__main__":
    main()
