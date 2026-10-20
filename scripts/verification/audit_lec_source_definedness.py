"""Bounded source-definedness and restricted-cut audit; no full LEC claim.

Checks the paired local BHT receipts, an exact-source missing-case control,
restricted AIG support and actual common-Q connections in bounded IR tails.
No compiler/frontend/simulator/solver is started; original files stay unchanged.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
from review_lec_onehot_cnf import ROOT, digest, memory_cap, peak_memory, read_graph
from check_bht_default_definedness import source_case


def reachable_inputs(graph):
    seen = bytearray(graph["inputs"] + len(graph["first"]) + 1)
    stack, support = [x // 2 for x in graph["outputs"]], set()
    while stack:
        node = stack.pop()
        if not node or seen[node]:
            continue
        seen[node] = 1
        if node <= graph["inputs"]:
            support.add(graph["input_names"][node - 1])
        else:
            pos = node - graph["inputs"] - 1
            stack.extend((graph["first"][pos] // 2, graph["second"][pos] // 2))
    return support


def fragment(path):
    length = path.stat().st_size
    offset = max(0, length - 8 * 1024 * 1024)
    with path.open("rb") as stream:
        stream.seek(offset)
        data = stream.read()
    return data.decode("ascii"), {"file_bytes": length, "read_offset": offset,
                                  "read_bytes": len(data), "fragment_sha256": hashlib.sha256(data).hexdigest(),
                                  "whole_file_read_or_hashed": offset == 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if out.exists() or not out.is_relative_to(ROOT):
        raise ValueError("New bounded research audit output required")
    enforcement = memory_cap()
    inputs = ["results/bht_default_definedness_20261010_p1.json",
              "results/bht_default_definedness_20261010_p2.json", "hdl/predictor/bht_2bit.v",
              "asic/snapshots/rtl_r14/hdl/predictor/bht_2bit.v",
              "asic/equiv/lec/evert.py", "asic/equiv/lec/build_pair.ps1",
              "asic/equiv/lec/AR14_gate_aig.ys", "asic/equiv/lec/BR14FA_gate_aig.ys",
              "asic/equiv/lec/AR14_gold_aig.ys", "asic/equiv/lec/BR14FA_gold_aig.ys",
              "asic/equiv/lec/gold_god_r14_aig.ys", "asic/equiv/lec/gold_flat_r14.ys",
              "asic/equiv/lec/n1_flat_r14.ys", "asic/equiv/lec/gate_flat_R14FA.ys",
              "asic/equiv/lec/synth_replay_r14/synthesize.py",
              "asic/equiv/lec/AR14_gate.aig", "asic/equiv/lec/BR14FA_gate.aig",
              "asic/equiv/lec/AR14_spec.json", "asic/equiv/lec/BR14FA_spec.json",
              "asic/equiv/lec/pairsAR14.json", "asic/equiv/lec/pairsB_R14FA.json",
              "scripts/verification/check_bht_default_definedness.py",
              "scripts/verification/audit_lec_source_definedness.py",
              "scripts/verification/review_lec_onehot_cnf.py",
              "results/lec_model_initialization_audit_20261010.json"]
    hashes = {rel: digest(ROOT / rel) for rel in inputs}
    paired = [json.loads((ROOT / rel).read_text()) for rel in inputs[:2]]
    if paired[0] != paired[1] or hashes[inputs[0]] != hashes[inputs[1]] \
            or paired[0]["status"] != "PROVED_LOCAL_BHT_BOOLEAN_DEFAULT_DEFINEDNESS_ONLY" \
            or paired[0]["IR_undefined_default_cells_checked"] != 256 \
            or paired[0]["IR_selector_truth_cases"] != 1024:
        raise ValueError("Paired BHT proof not complete or equal")
    for rel, expected in paired[0]["input_sha256"].items():
        if digest(ROOT / rel) != expected:
            raise ValueError("BHT proof source changed")
        hashes[rel] = expected
    source = source_case(ROOT / inputs[2])
    text = (ROOT / inputs[2]).read_text(encoding="ascii")
    reset = re.search(r"parameter\s+\[1:0\]\s+BHT_RESET_STATE\s*=\s*2'b([01]{2})", text)
    if not reset:
        raise ValueError("Explicit current default reset parameter required")
    default = int(reset[1], 2)
    # Delete only the actual state's case branch in a source-body copy.
    modified, count = re.subn(r"2'b11\s*:\s*next_counter_state\s*=\s*taken\s*\?\s*2'b11\s*:\s*2'b10\s*;", "", source["case_body_normalized"])
    if count != 1 or "default: next_counter_state = BHT_RESET_STATE;" not in modified:
        raise ValueError("Source negative control did not mutate exactly the intended branch")
    matched = re.findall(r"2'b([01]{2})\s*:\s*next_counter_state\s*=\s*taken\s*\?\s*2'b([01]{2})\s*:\s*2'b([01]{2})", modified)
    mutant_case = {int(s, 2): {0: int(no, 2), 1: int(yes, 2)} for s, yes, no in matched}
    witness_state, taken = 3, 1
    original = source["case"][witness_state][taken]
    mutant = mutant_case.get(witness_state, {0: default, 1: default})[taken]
    if set(mutant_case) != {0, 1, 2} or original == mutant:
        raise ValueError("Missing exact-source case did not give an observable local semantic fault")
    source_negative = {"status": "DISPROVED_COMPLETE_CASE_COVERAGE_IN_SOURCE_COPY",
                       "removed_source_case": "2'b11", "raw_state": witness_state, "taken": taken,
                       "source_default_now_selected": True, "BHT_RESET_STATE": default,
                       "original_function_value": original, "mutated_function_value": mutant,
                       "mutation_written_to_source": False,
                       "source_default_coerced_zero_would_differ": default != 0,
                       "scope": "Exact supported source function semantics only; no mutated frontend or whole-chip reachable trace is claimed"}
    cuts, fragments = [], {}
    base = ROOT / "asic/equiv/lec"
    for tag, pair_file in (("AR14", "pairsAR14.json"), ("BR14FA", "pairsB_R14FA.json")):
        spec = json.loads((base / (tag + "_spec.json")).read_text())
        pairs = json.loads((base / pair_file).read_text())
        graph = read_graph(base / (tag + "_gate.aig"))
        support = reachable_inputs(graph)
        restricted = [k for group in spec["onehot"] for k in group["pairs"]]
        if len(restricted) != 22 or len(set(restricted)) != 22:
            raise ValueError("Exact paired one-hot restriction population required")
        if any("lec_q_p%05d" % k in support for k in restricted):
            raise ValueError("Restricted paired Q unexpectedly retains raw support")
        if sum(name.startswith("lec_oh_") for name in graph["input_names"]) != 10 \
                or sum(name.startswith("lec_oh_") for name in support) != 10:
            raise ValueError("Actual restricted selector interface/support differs")
        rel = "asic/equiv/lec/" + tag + "_gate.il"
        tail, fragments[rel] = fragment(ROOT / rel)
        lines = set(tail.splitlines())
        missing = [k for k, (_, j) in enumerate(pairs["pairs"]) if k not in restricted and
                   "  connect %s \\lec_q_p%05d" % (pairs["gate"][j]["q"], k) not in lines]
        if missing:
            raise ValueError("Bounded tail does not verify all unrestricted common-Q connections")
        cuts.append({"tag": tag, "gate_AIG": "asic/equiv/lec/" + tag + "_gate.aig",
                     "restricted_graph_not_raw_initialization_proof": True,
                     "paired_state_count": len(pairs["pairs"]), "gold_only_state_count": len(pairs["gold_only"]),
                     "gate_only_state_count": len(pairs["gate_only"]),
                     "onehot_pair_restrictions": spec["onehot"], "restricted_paired_Q_count": len(restricted),
                     "restricted_paired_Q_raw_ports_have_no_output_support": True,
                     "onehot_selector_input_count": 10, "onehot_selector_used_count": 10,
                     "unrestricted_common_arbitrary_paired_Q_connections_verified": len(pairs["pairs"]) - len(restricted),
                     "gold_only_constant_substitutions_on_gold_side": len(spec["const"]),
                     "gold_only_duplicate_substitutions_on_gold_side": len(spec["dup"]),
                     "gold_only_free_population_on_gold_side": len(spec["free"]),
                     "gate_AIG_gold_only_Q_used_in_any_compared_output": sum(name.startswith("lec_q_g") for name in support),
                     "AIG_inputs": graph["inputs"], "AIG_outputs": len(graph["outputs"]),
                     "AIG_AND_nodes": len(graph["first"]), "all_output_support_bits": len(support),
                     "zero_initialization_argument_available": False})
        del graph, pairs, tail, lines
        gc.collect()
    for rel, before in fragments.items():
        _, after = fragment(ROOT / rel)
        if after != before:
            raise ValueError("Inspected cut IR fragment changed")
    if any(digest(ROOT / rel) != expected for rel, expected in hashes.items()):
        raise ValueError("Frozen source-definedness audit input changed")
    receipt = {"status": "PASS_LOCAL_BHT_PAIRED_SOURCE_AND_RESTRICTED_CUT_AUDIT",
               "full_sequential_LEC": "OPEN", "whole_source_undefined_abstraction": "OPEN",
               "input_sha256": hashes, "bounded_IR_fragments": fragments, "memory_enforcement": enforcement,
               "BHT_pair_field_and_byte_equal": True, "BHT_local_default_cells_closed": 256,
               "BHT_paired_selector_truth_cases": 2048, "BHT_source_negative_control": source_negative,
               "BHT_IR_negative_control": paired[0]["semantic_negative_control"], "restricted_gate_cuts": cuts,
               "count_scope": "X/Z connect lines are classification units, not bits or hardware defects",
               "historical_gold_X_connect_origins": 358,
               "remaining_gold_X_connect_origins_outside_BHT_update_check": 102,
               "four_state_behavior_equivalence_claimed": False,
               "external_frontend_simulator_or_solver_executed": False,
               "remaining_concrete_source_checks": [
                   "Remaining68 gold pmux default-X origins, including1BHT read mux,49AXI RAM wrappers and18cache/UART/control origins; selector coverage or full enabled-observability must be proved individually.",
                   "Seven gold mux X-connect lines (six cells): disabled regfile write data/hold temporary, I/D tag write data and address. Need exact sink/enable relation or no-consumer proof; source guard alone is not whole-cone closure.",
                   "27gold and57N1 module X/Z connect lines: classify every optimized-unused instruction/product/address/function temporary against all compared D/top/SRAM sinks; otherwise retain arbitrary undefined symbols.",
                   "Two N1 PC-low X muxes have static control masking evidence only; fresh exact raw cone proof and real process controls still required before global abstraction claim.",
                   "Final PDK20800pmux defaults have local complete Boolean UDP tables; must bind every instantiated default/consumer cone and cover undriven inputs, not infer four-state equivalence."]}
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print(receipt["status"], "BHT256 origins locally closed; restricted cuts verified", flush=True)
    print("Peak memory", peak_memory(), flush=True)


if __name__ == "__main__":
    main()
