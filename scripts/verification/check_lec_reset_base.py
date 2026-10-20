"""Controls for the universal reset sub-proof; fixtures are not chip results."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import lec_reset_base as proof


def fixture():
    names = ["reset_n", "lec_q_p00000", "lec_q_p00001", "lec_q_p00002", "lec_q_p00003",
             "lec_q_g00000", "lec_q_g00001"] + [f"rare_{i}" for i in range(24)]
    graph = {"inputs": len(names), "input_names": names, "ands": [],
             "outputs": [0, 0, 1, 0, 0, 0],
             "output_names": [f"lec_d_p{i:05d}" for i in range(4)] + ["lec_d_g00000", "lec_d_g00001"]}
    pairs = {"gold": [{"names": [name]} for name in (
        "\\reset_meta_q", "\\reset_sync_q", "\\state [0]", "\\state [1]", "\\unused", "\\dup")],
        "gate": [{"names": [str(i)]} for i in range(4)], "pairs": [[i, i] for i in range(4)],
        "gold_only": [4, 5], "gate_only": [], "ambiguous": []}
    spec = {"const": {"0": 0}, "dup": {"1": 3}, "free": [],
            "onehot_gold": [{"name": "state", "gold": [2, 3]}]}
    return graph, pairs, spec


def binary(graph):
    def enc(value):
        answer = bytearray()
        while value >= 128:
            answer.append((value & 127) | 128)
            value >>= 7
        answer.append(value)
        return answer
    i, a, o = graph["inputs"], len(graph["ands"]), len(graph["outputs"])
    answer = bytearray(f"aig {i+a} {i} 0 {o} {a}\n".encode())
    for lit in graph["outputs"]:
        answer.extend(f"{lit}\n".encode())
    for k, pair in enumerate(graph["ands"]):
        lhs = 2 * (i+k+1)
        first, second = sorted(pair, reverse=True)
        answer.extend(enc(lhs-first)); answer.extend(enc(first-second))
    for kind, names in (("i", graph["input_names"]), ("o", graph["output_names"])):
        for k, name in enumerate(names):
            answer.extend(f"{kind}{k} {name}\n".encode())
    return bytes(answer)


def main():
    out = proof.ROOT / "results/lec_reset_base_controls_20261010.json"
    if out.exists():
        raise RuntimeError("Control receipt exists; preserve it before any new run")
    graph, pairs, spec = fixture()
    assert proof.reset_obligations(proof.read_aig_bytes(binary(graph)), pairs, spec)["status"] == \
        "PROVED_GOLD_RESET_SUBOBLIGATIONS_ONLY"
    controls = []

    def reject(name, operation):
        try:
            result = operation()
        except (ValueError, KeyError, IndexError) as exc:
            controls.append({"control": name, "caught": True, "reason": str(exc)})
        else:
            if result["status"] == "PROVED_GOLD_RESET_SUBOBLIGATIONS_ONLY":
                raise AssertionError("Invalid fixture accepted: " + name)
            controls.append({"control": name, "caught": True, "reason": result["status"]})

    def changed(name, category, mutate):
        one = list(copy.deepcopy((graph, pairs, spec)))
        mutate(one[category])
        reject(name, lambda: proof.reset_obligations(*one))

    changed("constant_reset_wrong_value", 2, lambda s: s["const"].update({"0": 1}))
    changed("reset_synchronizer_fixed_wrong_value", 0, lambda g: g["outputs"].__setitem__(0, 1))
    changed("reset_synchronizer_symbolic", 0, lambda g: g["outputs"].__setitem__(0, 16))
    changed("duplicate_reset_mismatch", 0, lambda g: g["outputs"].__setitem__(5, 1))
    changed("onehot_all_zero_reset", 0, lambda g: g["outputs"].__setitem__(2, 0))
    changed("onehot_two_bits_set_reset", 0, lambda g: g["outputs"].__setitem__(3, 1))
    changed("empty_onehot_group", 2, lambda s: s["onehot_gold"][0].update(gold=[]))
    changed("missing_all_onehot_groups", 2, lambda s: s.update(onehot_gold=[]))
    changed("overlapping_onehot_groups", 2, lambda s: s["onehot_gold"].append({"name": "other", "gold": [3]}))
    changed("overlapping_constant_duplicate", 2, lambda s: s["dup"].update({"0": 3}))
    changed("missing_partition_flop", 2, lambda s: s["const"].clear())
    changed("invalid_duplicate_partner", 2, lambda s: s["dup"].update({"1": 4}))
    changed("ambiguous_reset_synchronizer", 1, lambda p: p["gold"][2].update(names=["\\reset_meta_q"]))
    changed("missing_raw_flop_D", 0, lambda g: g["output_names"].__setitem__(4, "hidden_D"))
    changed("onehot_restricted_raw_graph", 0, lambda g: g["input_names"].__setitem__(7, "lec_oh_state_0"))
    changed("duplicated_flop_pair", 1, lambda p: p["pairs"].__setitem__(3, [2, 3]))
    changed("missing_mapped_flop", 1, lambda p: p["gold_only"].pop())
    # A bug activated by all 24 unconstrained inputs being one cannot be proved
    # constant by cofactoring reset, even if a small random test misses it.
    rare = copy.deepcopy(graph)
    rare_lit = 2 * 8
    for index in range(8, 31):
        rare["ands"].append((rare_lit, 2 * (index+1)))
        rare_lit = 2 * (rare["inputs"] + len(rare["ands"]))
    rare["outputs"][4] = rare_lit
    rare = proof.read_aig_bytes(binary(rare))
    reject("rare_24_input_reset_bug", lambda: proof.reset_obligations(rare, pairs, spec))
    # The explicit all-ones assignment is a deterministic witness of this
    # synthetic bug, rather than a timeout/parser failure or sample-based PASS.
    witness, _ = proof.cofactor(rare, {"reset_n": 0, **{f"rare_{i}": 1 for i in range(24)}})
    assert witness["lec_d_g00000"] == 1
    bad = binary(graph)
    malformed = {
        "missing_symbol": bad.replace(b"o5 lec_d_g00001\n", b""),
        "duplicate_symbol_index": bad+b"o0 duplicate\n",
        "noncontiguous_symbol_index": bad.replace(b"o5 ", b"o6 "),
        "sequential_graph_rejected": bad.replace(b"aig 31 31 0 6 0", b"aig 31 30 1 6 0"),
        "out_of_range_output": bad.replace(b"\n0\n", b"\n999\n", 1),
        "truncated_AND_section": binary(rare).split(b"i0 ")[0][:-1],
    }
    for name, data in malformed.items():
        reject(name, lambda data=data: {"status": "PROVED_GOLD_RESET_SUBOBLIGATIONS_ONLY",
                                       "graph": proof.read_aig_bytes(data)})
    record = {"status": "CHECKER_FIXTURES_VERIFIED_NOT_CHIP_PROOF_MEASUREMENTS", "positive_controls": 2,
              "negative_controls": controls, "rare_fixture_bits": 24, "rare_fixture_exact_witness": True,
              "method": "in-memory synthetic graphs/specs; no RTL or preserved proof artifact changed",
              "checker_sha256": proof.sha(Path(proof.__file__)), "controls_sha256": proof.sha(Path(__file__))}
    out.write_text(json.dumps(record, indent=2)+"\n", encoding="ascii")
    print(f"[PASS] {len(controls)} rejection controls and exact synthetic rare-pattern witness")


if __name__ == "__main__":
    main()
