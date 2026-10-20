"""Independent bounded review of the explicit current-gold joint invariant.

Rebuilds raw symbolic aliasing, the simultaneous premise, and every saved
target. Reuses only the separate independent review's parser/encoder/replayer,
never the author's cofactor/parser/resolution implementations for proof replay.
The frozen author helper is imported only for finite controls. No new SoC solve
or external frontend is launched. Full sequential/source-model closure is OPEN.
"""
from __future__ import annotations

import argparse
from array import array
import gc
import itertools
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
from review_lec_onehot_cnf import (ROOT, IndependentGraph, content_digest, digest,
                                   encode, mapping_names, memory_cap, peak_memory,
                                   read_graph, reject, replay)


class AliasModel(IndependentGraph):
    def __init__(self, graph, assignments, aliases):
        self.inputs = graph["inputs"]
        self.unique = {}
        self.left, self.right = array("I"), array("I")
        self.positions = {name: i for i, name in enumerate(graph["input_names"])}
        if set(aliases).intersection(assignments) or set(aliases).intersection(aliases.values()) \
                or not set(assignments).union(aliases, aliases.values()) <= set(self.positions) \
                or any(type(value) is not int or value not in (0, 1) for value in assignments.values()):
            raise ValueError("Invalid independent symbolic alias substitution")
        self.assignments, self.aliases = assignments, aliases
        values = array("I", [0])
        values.extend(self.q(name) for name in graph["input_names"])
        for a, b in zip(graph["first"], graph["second"]):
            values.append(self.and_gate(values[a // 2] ^ (a % 2), values[b // 2] ^ (b % 2)))
        self.outputs = {name: values[x // 2] ^ (x % 2)
                        for name, x in zip(graph["output_names"], graph["outputs"])}

    def q(self, name):
        target = self.aliases.get(name, name)
        return self.assignments.get(target, 2 * (self.positions[target] + 1))

    def premise(self, groups):
        value = 1
        for group in groups:
            value = self.and_gate(value, self.violation([self.q(name) for name in group["Q"]]) ^ 1)
        return value

    def unequal(self, a, b):
        return self.or_gate(self.and_gate(a, b ^ 1), self.and_gate(a ^ 1, b))


def raw_evaluation(graph, complete):
    if set(complete) != set(graph["input_names"]) \
            or any(type(v) is not int or v not in (0, 1) for v in complete.values()):
        raise ValueError("Complete Boolean raw witness required")
    values = array("B", [0])
    values.extend(complete[name] for name in graph["input_names"])
    for a, b in zip(graph["first"], graph["second"]):
        values.append((values[a // 2] ^ (a % 2)) & (values[b // 2] ^ (b % 2)))
    return {name: values[x // 2] ^ (x % 2)
            for name, x in zip(graph["output_names"], graph["outputs"])}


def satisfies(point, info, phase):
    return all(point[name] == value for name, value in info["constants"].items()) \
        and all(point[source] == point[target] for source, target in info["duplicate_aliases"].items()) \
        and all(sum(point[name] for name in g["Q"]) == 1 for g in info["onehot_groups"]) \
        and all(point[name] == value for name, value in phase.items())


def nonvacuity_point(graph, info, phase, free_value):
    point = dict.fromkeys(graph["input_names"], free_value)
    point.update(info["constants"])
    for group in info["onehot_groups"]:
        point.update({name: int(i == 0) for i, name in enumerate(group["Q"])})
    point.update(phase)
    for source, target in info["duplicate_aliases"].items():
        point[source] = point[target]
    if not satisfies(point, info, phase):
        raise ValueError("Joint premise has no recorded legal witness")
    return point


def independent_spec(graph, pairs, spec):
    q, d = mapping_names(pairs)
    const, dup, free = (set(map(int, spec[name])) for name in ("const", "dup", "free"))
    if const & dup or const & free or dup & free \
            or const | dup | free != set(range(len(pairs["gold_only"]))):
        raise ValueError("Gold-only partition is incomplete or overlapping")
    constants = {"lec_q_g%05d" % int(index): value for index, value in spec["const"].items()}
    aliases = {"lec_q_g%05d" % int(index): "lec_q_p%05d" % partner
               for index, partner in spec["dup"].items()}
    if len(constants) != 235 or len(aliases) != 28 \
            or any(type(v) is not int or v not in (0, 1) for v in constants.values()) \
            or any(type(v) is not int or not 0 <= v < len(pairs["pairs"]) for v in spec["dup"].values()) \
            or set(constants).intersection(aliases) or set(aliases).intersection(aliases.values()):
        raise ValueError("Invalid recorded constant/duplicate constraints")
    names = set(graph["input_names"])
    if not set(q.values()).union(constants, aliases, aliases.values()) <= names \
            or not set(d.values()) <= set(graph["output_names"]) \
            or any(name.startswith("lec_oh_") for name in names):
        raise ValueError("Unrestricted raw Q/D graph required")
    groups, used = [], set()
    for group in spec["onehot_gold"]:
        gold = group["gold"]
        if any(type(i) is not int or i not in q for i in gold) \
                or len(set(gold)) != len(gold) or used.intersection(gold):
            raise ValueError("Ambiguous or overlapping one-hot groups")
        used.update(gold)
        group_q = [q[i] for i in gold]
        if set(group_q).intersection(set(constants).union(aliases)):
            raise ValueError("Group premise overlaps substituted invariant target")
        groups.append({"name": group["name"], "gold_indices": gold,
                       "Q": group_q, "D": [d[i] for i in gold]})
    if [(g["name"], len(g["Q"])) for g in groups] != [
            ("lcd_en_phase", 3), ("axi_last_grant", 3), ("axi_source", 3), ("alu_ctrl_e", 14)]:
        raise ValueError("Four exact current groups required")
    for label, expected in (("reset_meta_q", 19088), ("reset_sync_q", 19089)):
        found = [index for index, (gold, _) in enumerate(pairs["pairs"])
                 if "\\" + label in {name.replace(" [", "[") for name in pairs["gold"][gold]["names"]}]
        if found != [expected]:
            raise ValueError("Reset synchronizer state identities differ")
    return {"constants": dict(sorted(constants.items())), "duplicate_aliases": dict(sorted(aliases.items())),
            "onehot_groups": groups, "other_raw_Q_and_inputs": "Independent symbolic inputs",
            "gold_only_partition_counts": {"const": len(const), "dup": len(dup), "free": len(free)},
            "mapping_ambiguity_metadata_records": len(pairs.get("ambiguous", []))}


def finite_alias_controls(author):
    names = ["lec_q_g00000", "lec_q_p00000", "unreset_memory_q", "other_input", "reset_n",
             "lec_q_g00056"] + ["lec_q_p%05d" % i for i in range(1, 10)]
    graph = {"inputs": len(names), "input_names": names, "first": array("I"),
             "second": array("I"), "outputs": [], "output_names": []}
    def gate(a, b):
        node = 2 * (len(names) + len(graph["first"]) + 1)
        graph["first"].append(a)
        graph["second"].append(b)
        return node
    source, target, memory, other = 2, 4, 6, 8
    roots = [source, target, memory, gate(source, memory), gate(target, memory),
             gate(gate(source, other ^ 1) ^ 1, gate(source ^ 1, other) ^ 1) ^ 1]
    graph["outputs"], graph["output_names"] = roots, ["out%d" % i for i in range(len(roots))]
    graph_author = {**graph, "ands": list(zip(graph["first"], graph["second"]))}
    aliases = {"lec_q_g00000": "lec_q_p00000"}
    substitutions = 0
    for target_value in (None, 0, 1):
        assignments = {"reset_n": 1, "lec_q_g00056": 0}
        if target_value is not None:
            assignments["lec_q_p00000"] = target_value
        model = AliasModel(graph, assignments, aliases)
        dag = author.DAG(graph["inputs"], time.monotonic() + 5)
        outputs = author.alias_cofactor(dag, graph_author, assignments, aliases, aliases)
        if outputs != model.outputs or model.outputs["out2"] != memory:
            raise ValueError("Exact recorded aliasing or untouched free state differs")
        for bits in itertools.product((0, 1), repeat=4):
            point = dict.fromkeys(names, 0)
            point.update(assignments)
            for name, bit in zip(("lec_q_p00000", "unreset_memory_q", "other_input", "lec_q_p00001"), bits):
                if name not in assignments:
                    point[name] = bit
            point["lec_q_g00000"] = point["lec_q_p00000"]
            numeric = {i: point[name] for i, name in enumerate(names)}
            raw = raw_evaluation(graph, point)
            for name in graph["output_names"]:
                if model.evaluate(model.outputs[name], numeric) != raw[name] \
                        or dag.evaluate(outputs[name], numeric) != raw[name]:
                    raise ValueError("Symbolic aliasing differs from raw constrained truth table")
            substitutions += 1
    groups = [{"name": "g%d" % i, "Q": names[6 + lo:6 + hi], "D": []}
              for i, (lo, hi) in enumerate(((0, 2), (2, 4), (4, 6), (6, 9)))]
    info = {"constants": {"lec_q_g00056": 0}, "duplicate_aliases": aliases, "onehot_groups": groups}
    assignments = {"reset_n": 1, **info["constants"]}
    model = AliasModel(graph, assignments, aliases)
    own = model.premise(groups)
    dag = author.DAG(graph["inputs"], time.monotonic() + 5)
    original = author.joint_predicate(dag, graph_author, info, assignments)
    premise_cases = 0
    for bits in itertools.product((0, 1), repeat=9):
        point = dict.fromkeys(names, 0)
        point.update(assignments)
        point.update(dict(zip(names[6:], bits)))
        numeric = {i: point[name] for i, name in enumerate(names)}
        expected = int(sum(bits[:2]) == 1 and sum(bits[2:4]) == 1 and
                       sum(bits[4:6]) == 1 and sum(bits[6:9]) == 1)
        if model.evaluate(own, numeric) != expected or dag.evaluate(original, numeric) != expected:
            raise ValueError("Simultaneous four-group premise differs from direct truth table")
        premise_cases += 1
    for base in (0, 1):
        if not satisfies(nonvacuity_point(graph, info, {"reset_n": 1}, base), info, {"reset_n": 1}):
            raise ValueError("Nonvacuity fixture failed")
    impossible = {"reset_n": 1, **dict.fromkeys(groups[0]["Q"], 0)}
    reject(lambda: nonvacuity_point(graph, info, impossible, 0))
    rejects = [({"lec_q_g00000": "lec_q_p00002"}, aliases, assignments),
               (aliases, aliases, {**assignments, "lec_q_g00000": 0}),
               ({"lec_q_g00000": "unreset_memory_q"}, {"lec_q_g00000": "unreset_memory_q"}, assignments),
               ({"lec_q_p00000": "lec_q_p00000"}, {"lec_q_p00000": "lec_q_p00000"}, assignments),
               (aliases, aliases, {**assignments, "reset_n": True}),
               (aliases, aliases, {**assignments, "missing_input": 0})]
    for candidate, allowed, fixed in rejects:
        reject(lambda candidate=candidate, allowed=allowed, fixed=fixed:
               author.alias_cofactor(dag, graph_author, fixed, candidate, allowed))
    return {"status": "PASS", "raw_truth_substitution_cases": substitutions,
            "four_group_direct_truth_cases": premise_cases, "free_state_both_values_tested": True,
            "nonvacuity_zero_and_one_completions": 2, "invalid_alias_rejections": len(rejects),
            "contradictory_group_premise_rejected": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", required=True)
    parser.add_argument("--second", required=True)
    parser.add_argument("--controls", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if out.exists() or out.with_suffix(".md").exists() or not out.is_relative_to(ROOT):
        raise ValueError("New independent research review output required")
    memory = memory_cap()
    started = time.monotonic()
    first, second, controls_path = (Path(p).resolve() for p in (args.first, args.second, args.controls))
    if any(not p.is_relative_to(ROOT) for p in (first, second, controls_path)):
        raise ValueError("All review evidence must be in research")
    paths = [ROOT / p for p in ("asic/equiv/lec/gold_god_r14.aig", "asic/equiv/lec/pairsAR14.json",
                               "asic/equiv/lec/AR14_spec.json", "scripts/verification/lec_joint_invariant.py",
                               "scripts/verification/review_lec_joint_invariant.py",
                               "scripts/verification/review_lec_onehot_cnf.py",
                               "results/lec_onehot_cnf_independent_review_20261010.json")]
    fault_paths = [ROOT / ("results/dm_joint_model_fault_20261010_p%d.json" % i) for i in (1, 2)]
    paths.extend(fault_paths)
    paths.extend((first, second, controls_path))
    hashes = {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}
    controls = json.loads(controls_path.read_text())
    if controls["status"] != "PASS_JOINT_INVARIANT_CHECKER_CONTROLS" \
            or controls["control_count"] != 15 or len(controls["controls"]) != 15 \
            or any(row["status"] != "PASS" for row in controls["controls"]):
        raise ValueError("Complete frozen joint controls required")
    for rel, value in controls["source_sha256"].items():
        if digest(ROOT / rel) != value:
            raise ValueError("Joint source not frozen against controls")
        hashes[rel] = value
    import lec_joint_invariant as author
    finite = finite_alias_controls(author)
    paired = [json.loads(p.read_text()) for p in (first, second)]
    if paired[0] != paired[1] or digest(first) != digest(second):
        raise ValueError("Joint independent execution pair differs")
    for receipt in paired:
        if receipt["status"] != "BOUNDED_JOINT_CURRENT_GOLD_INDUCTION_SUBPROOF_ONLY" \
                or receipt["full_sequential_LEC"] != "OPEN" \
                or receipt["source_undefined_zero_abstraction_gap"] != "OPEN" \
                or receipt["interrupted_or_arbitrary_reset_phase_invariant_closure"] != "OPEN" \
                or len(receipt["obligations"]) != 286:
            raise ValueError("Joint receipt scope or obligation count differs")
        for rel, value in receipt["input_sha256"].items():
            if digest(ROOT / rel) != value:
                raise ValueError("Joint proof input hash differs")
            hashes[rel] = value
    graph = read_graph(paths[0])
    pairs, spec = (json.loads(p.read_text()) for p in paths[1:3])
    info = independent_spec(graph, pairs, spec)
    reset = {"reset_n": 1, "lec_q_p19088": 1, "lec_q_p19089": 1}
    if paired[0]["joint_invariant_I_Q"] != info or paired[0]["reset_phase"] != reset:
        raise ValueError("Joint premise differs from independently extracted source partition")
    # Reset-base evidence is a separate prerequisite; check its complete target identities.
    bases = [json.loads((ROOT / rel).read_text()) for rel in paired[0]["input_sha256"]
             if rel.startswith("results/dm_reset_base_structural_20261010_p")]
    if len(bases) != 2 or bases[0] != bases[1] or bases[0]["status"] != "PROVED_GOLD_RESET_SUBOBLIGATIONS_ONLY":
        raise ValueError("Paired exact reset-base prerequisite absent")
    for key, wanted in (("constant_reset", 235), ("duplicate_reset", 28), ("onehot_reset", 4)):
        if len(bases[0][key]) != wanted or any(row["status"] != "PROVED" for row in bases[0][key]):
            raise ValueError("Reset-base prerequisite contains a gap")
    for rel, value in bases[0]["inputs"].items():
        if digest(ROOT / rel) != value:
            raise ValueError("Reset base tied to different model inputs")
    base_constants = {"lec_q_g%05d" % row["gold_only"]: row["expected"] for row in bases[0]["constant_reset"]}
    base_aliases = {"lec_q_g%05d" % row["gold_only"]: "lec_q_p%05d" % row["partner"]
                    for row in bases[0]["duplicate_reset"]}
    if base_constants != info["constants"] or base_aliases != info["duplicate_aliases"]:
        raise ValueError("Joint constraints differ from reset-base claims")
    protocols = []
    for phase, expected in (({"reset_n": 0}, [0, 0]),
                            ({"reset_n": 1, "lec_q_p19088": 0}, [1, 0]),
                            ({"reset_n": 1, "lec_q_p19088": 1}, [1, 1])):
        model = AliasModel(graph, phase, {})
        actual = [model.outputs["lec_d_p19088"], model.outputs["lec_d_p19089"]]
        if actual != expected:
            raise ValueError("Synchronizer protocol does not structurally match")
        protocols.append({"assignments": phase, "expected_meta_sync_D": expected,
                          "actual_meta_sync_D_literals": actual, "status": "PROVED_STRUCTURAL_PROTOCOL",
                          "any_joint_invariant_assumed": False})
        del model
        gc.collect()
    if paired[0]["synchronizer_protocol"] != protocols:
        raise ValueError("Saved synchronizer protocol differs")

    # Actual-model negative controls are checked from the independent raw parser.
    fault_pair = [json.loads(p.read_text()) for p in fault_paths]
    if fault_pair[0] != fault_pair[1] or digest(fault_paths[0]) != digest(fault_paths[1]):
        raise ValueError("Joint actual-model negative-control pair differs")
    fault_reviews = []
    for pass_index, saved in enumerate(fault_pair, 1):
        if saved["status"] != "PASS_ACTUAL_RAW_MODEL_JOINT_PREMISE_RARE_FAULT_CONTROL" \
                or saved["joint_invariant_I_Q"] != info or saved["full_sequential_LEC"] != "OPEN" \
                or saved["source_undefined_zero_abstraction_gap"] != "OPEN" \
                or saved["unreset_state_zero_axiom_used"]:
            raise ValueError("Joint actual-model control has wrong invariant/scope")
        for rel, expected in saved["input_sha256"].items():
            if digest(ROOT / rel) != expected:
                raise ValueError("Joint fault-control input changed")
            hashes[rel] = expected
        group = info["onehot_groups"][0]
        phase = {**reset, **{name: int(i == 0) for i, name in enumerate(group["Q"])}}
        if saved["group"] != group["name"] or saved["reset_and_own_code_conditions"] != phase:
            raise ValueError("Joint fault-control selected code differs")
        model = AliasModel(graph, {**info["constants"], **phase}, info["duplicate_aliases"])
        premise = model.premise(info["onehot_groups"])
        values = [model.outputs[name] for name in group["D"]]
        baseline_violation = model.violation(values)
        baseline_root = model.and_gate(premise, baseline_violation)
        baseline = saved["baseline"]
        if baseline["joint_premise_literal"] != premise or baseline["D_violation_literal"] != baseline_violation \
                or baseline["conditional_violation_literal"] != baseline_root:
            raise ValueError("Fault-control baseline graph differs")
        if baseline["decision"]["status"] == "PROVED_STRUCTURAL_COFACTOR":
            if baseline_root != 0:
                raise ValueError("Fault-control baseline is not structural zero")
            baseline_steps = 0
        elif baseline["decision"]["status"] == "PROVED_BOOLEAN_CNF":
            initial, mapping = encode(model, baseline_root)
            baseline_steps = replay(initial, baseline["decision"]["resolution_certificate"],
                                    baseline["decision"]["terminal_empty_clause_derivation"])
        else:
            raise ValueError("Fault-control baseline has no positive proof")
        excluded = set(phase).union(info["constants"], info["duplicate_aliases"],
                                   {name for g in info["onehot_groups"] for name in g["Q"]})
        triggers = [name for name in graph["input_names"] if name not in excluded][:24]
        if len(triggers) != 24 or triggers != saved["trigger_inputs"] \
                or saved["activation_fraction"] != "1 / 16777216":
            raise ValueError("Fault-control triggers are not exact24 independently free symbols")
        rare = 1
        for name in triggers:
            rare = model.and_gate(rare, 2 * (model.positions[name] + 1))
        mutated = [model.or_gate(values[0], rare), model.or_gate(values[1], rare), *values[2:]]
        violation = model.violation(mutated)
        root = model.and_gate(premise, violation)
        negative = saved["negative"]
        if negative["joint_premise_literal"] != premise or negative["D_violation_literal"] != violation \
                or negative["conditional_violation_literal"] != root:
            raise ValueError("Fault-control mutated predicate differs")
        decision = negative["decision"]
        clauses, mapping = encode(model, root)
        assignment = decision["CNF_assignment"]
        if decision["status"] != "DISPROVED_UNDER_RECORDED_ASSUMPTIONS" \
                or decision["CNF_variables"] != len(mapping) or decision["CNF_initial_clauses"] != len(clauses) \
                or len(assignment) != len(mapping) + 1 or any(x not in (-1, 1) for x in assignment[1:]) \
                or not all(any(assignment[abs(x)] == (1 if x > 0 else -1) for x in c) for c in clauses):
            raise ValueError("Joint rare witness fails independent exact CNF")
        witness = {graph["input_names"][node // 2 - 1]: int(assignment[var] == 1)
                   for node, var in mapping.items() if node <= 2 * model.inputs}
        if witness != decision["counterexample"] or any(witness.get(name) != 1 for name in triggers):
            raise ValueError("Joint rare witness differs from raw-input map/trigger")
        if model.evaluate(root, {model.positions[name]: bit for name, bit in witness.items()}) != 1:
            raise ValueError("Joint rare witness fails independent conditional violation")
        complete = dict.fromkeys(graph["input_names"], 0)
        complete.update(witness)
        complete.update(info["constants"])
        complete.update(phase)
        for source, target in info["duplicate_aliases"].items():
            complete[source] = complete[target]
        if not satisfies(complete, info, phase):
            raise ValueError("Actual raw-model rare witness fails a joint premise")
        raw = raw_evaluation(graph, complete)
        original = [raw[name] for name in group["D"]]
        mutation = [original[0] | 1, original[1] | 1, *original[2:]]
        numeric = {i: complete[name] for i, name in enumerate(graph["input_names"])}
        if original != saved["original_raw_D_code_at_witness"] or mutation != saved["mutated_D_code_at_witness"] \
                or sum(original) != 1 or sum(mutation) < 2 \
                or [model.evaluate(v, numeric) for v in mutated] != mutation:
            raise ValueError("Actual raw-model rare mutation is not observable")
        fault_reviews.append({"pass": pass_index, "status": "PASS", "baseline_replayed_steps": baseline_steps,
                              "trigger_bits": 24, "every_original_joint_premise_satisfied": True,
                              "CNF_and_raw_graph_witness_independently_validated": True,
                              "original_raw_D_code": original, "mutated_D_code": mutation})
        del model, clauses, mapping
        gc.collect()

    reviewed, certificate_count, steps_total = [], 0, 0
    statuses = {key: 0 for key in ("PROVED_STRUCTURAL_COFACTOR", "PROVED_BOOLEAN_CNF",
                                 "DISPROVED_UNDER_RECORDED_ASSUMPTIONS", "UNKNOWN")}
    structural_targets = 0

    def inspect(model, row_index, phase, descriptor, premise, violation):
        nonlocal certificate_count, steps_total, structural_targets
        root = model.and_gate(premise, violation)
        point0 = nonvacuity_point(graph, info, phase, 0)
        point1 = nonvacuity_point(graph, info, phase, 1)
        nonvacuity = {"joint_premise_satisfiable": True,
                      "onehot_Q_codes": {g["name"]: [point0[n] for n in g["Q"]] for g in info["onehot_groups"]},
                      "other_free_values_at_this_witness_only": 0, "unreset_state_zero_axiom_used": False}
        row = paired[0]["obligations"][row_index]
        for key, wanted in {**descriptor, "reset_conditions": phase, "nonvacuity": nonvacuity,
                            "joint_premise_literal": premise, "D_violation_literal": violation,
                            "conditional_violation_literal": root}.items():
            if row.get(key) != wanted:
                raise ValueError("Saved target/premise differs at row%d key%s" % (row_index, key))
        if model.evaluate(premise, {i: point0[name] for i, name in enumerate(graph["input_names"])}) != 1 \
                or model.evaluate(premise, {i: point1[name] for i, name in enumerate(graph["input_names"])}) != 1:
            raise ValueError("Joint encoded premise contradicts explicit nonvacuity witnesses")
        decision = row["decision"]
        status = decision["status"]
        if status not in statuses:
            raise ValueError("Unrecognised semantic status")
        statuses[status] += 1
        detail = {"row_index": row_index, **descriptor, "status": status,
                  "nonvacuity_with_other_free_zero_and_one": True,
                  "all_unassigned_Q_and_inputs_remain_symbolic": True}
        if status == "PROVED_STRUCTURAL_COFACTOR":
            if root != 0 or decision != {"status": status, "counterexample": None}:
                raise ValueError("Claimed structural proof is not exact literal0")
            structural_targets += 1
        elif status == "PROVED_BOOLEAN_CNF":
            if root == 0 or decision["counterexample"] is not None:
                raise ValueError("Malformed Boolean proof status")
            clauses, mapping = encode(model, root)
            if decision["CNF_variables"] != len(mapping) or decision["CNF_initial_clauses"] != len(clauses) \
                    or decision["learned_clauses"] != len(decision["resolution_certificate"]):
                raise ValueError("Joint saved CNF shape differs")
            replayed = []
            for saved in paired:
                d = saved["obligations"][row_index]["decision"]
                steps = replay(clauses, d["resolution_certificate"], d["terminal_empty_clause_derivation"])
                if steps != d["resolution_steps"] or steps != d["independently_replayed_resolution_steps"]:
                    raise ValueError("Joint resolution count differs")
                steps_total += steps
                certificate_count += 1
                replayed.append(steps)
            detail.update({"CNF_variables": len(mapping), "CNF_clauses": len(clauses),
                           "CNF_sha256": content_digest(clauses),
                           "variable_map_sha256": content_digest(sorted(mapping.items())),
                           "paired_resolution_replay_steps": replayed})
        elif status == "DISPROVED_UNDER_RECORDED_ASSUMPTIONS":
            clauses, mapping = encode(model, root)
            assignment = decision["CNF_assignment"]
            if decision["CNF_variables"] != len(mapping) or decision["CNF_initial_clauses"] != len(clauses) \
                    or len(assignment) != len(mapping) + 1 or any(x not in (-1, 1) for x in assignment[1:]) \
                    or not all(any(assignment[abs(x)] == (1 if x > 0 else -1) for x in c) for c in clauses):
                raise ValueError("Joint SAT assignment fails exact independent CNF")
            raw_witness = {graph["input_names"][node // 2 - 1]: int(assignment[var] == 1)
                           for node, var in mapping.items() if node <= 2 * model.inputs}
            if raw_witness != decision["counterexample"]:
                raise ValueError("Named joint witness differs from independent variable map")
            numeric = {model.positions[name]: value for name, value in raw_witness.items()}
            if model.evaluate(root, numeric) != 1:
                raise ValueError("Joint witness fails independently reconstructed conditional violation")
            complete = dict.fromkeys(graph["input_names"], 0)
            complete.update(raw_witness)
            complete.update(info["constants"])
            complete.update(phase)
            for source, target in info["duplicate_aliases"].items():
                complete[source] = complete[target]
            if not satisfies(complete, info, phase):
                raise ValueError("Joint witness fails original premise")
            raw = raw_evaluation(graph, complete)
            if descriptor["kind"] == "constant":
                actual = raw[descriptor["D"]]
                violation_confirmed = actual != descriptor["expected"]
            elif descriptor["kind"] == "duplicate":
                actual = [raw[descriptor["D"]], raw[descriptor["paired_D"]]]
                violation_confirmed = actual[0] != actual[1]
            else:
                actual = [raw[name] for name in descriptor["D"]]
                violation_confirmed = sum(actual) != 1
            if not violation_confirmed or actual != row["original_raw_D_at_counterexample"] \
                    or not row["counterexample_satisfies_every_joint_premise"] \
                    or not row["default_is_witness_completion_only_not_state_axiom"]:
                raise ValueError("Original raw witness is not the claimed joint violation")
            detail["independent_original_raw_counterexample_validated"] = True
        else:
            if decision["counterexample"] is not None or not decision.get("reason"):
                raise ValueError("UNKNOWN lacks explicit failed bound/reason")
            detail["not_promoted_to_semantic_proof"] = True
        reviewed.append(detail)

    # Match exact sorted iteration order, including persistent canonical nodes.
    model = AliasModel(graph, {**info["constants"], **reset}, info["duplicate_aliases"])
    premise = model.premise(info["onehot_groups"])
    row_index = 0
    for qname, expected in info["constants"].items():
        dname = qname.replace("lec_q_", "lec_d_")
        inspect(model, row_index, reset, {"kind": "constant", "Q": qname, "D": dname, "expected": expected},
                premise, model.outputs[dname] ^ expected)
        row_index += 1
    for qname, partner in info["duplicate_aliases"].items():
        dname, pd = qname.replace("lec_q_", "lec_d_"), partner.replace("lec_q_", "lec_d_")
        descriptor = {"kind": "duplicate", "Q": qname, "paired_Q": partner, "D": dname, "paired_D": pd}
        inspect(model, row_index, reset, descriptor, premise, model.unequal(model.outputs[dname], model.outputs[pd]))
        row_index += 1
    del model
    gc.collect()
    for group in info["onehot_groups"]:
        for active in range(len(group["Q"])):
            phase = {**reset, **{name: int(i == active) for i, name in enumerate(group["Q"])}}
            model = AliasModel(graph, {**info["constants"], **phase}, info["duplicate_aliases"])
            premise = model.premise(info["onehot_groups"])
            descriptor = {"kind": "onehot", "group": group["name"], "active_current_bit": active,
                          "group_Q": group["Q"], "D": group["D"]}
            inspect(model, row_index, phase, descriptor, premise,
                    model.violation([model.outputs[name] for name in group["D"]]))
            print("Independent joint review", row_index, group["name"], active, reviewed[-1]["status"], flush=True)
            row_index += 1
            del model
            gc.collect()
    if row_index != 286 or statuses != paired[0]["counts"]:
        raise ValueError("Joint target population or reported semantic counts differ")
    if any(digest(ROOT / rel) != expected for rel, expected in hashes.items()):
        raise ValueError("Frozen review source/model/evidence changed")
    receipt = {"status": "PASS_INDEPENDENT_JOINT_INVARIANT_REVIEW", "full_sequential_LEC": "OPEN",
               "source_undefined_zero_abstraction_gap": "OPEN",
               "interrupted_or_arbitrary_reset_phase_invariant_closure": "OPEN",
               "scope": "Only the exact raw-gold I(Q)=>I(D) subobligation in the recorded deasserted reset phase; the paired reset base and protocol equations are separate prerequisites, not proof of every reset sequence or full-chip equivalence.",
               "input_sha256": hashes, "memory_enforcement": memory, "peak_memory": peak_memory(),
               "elapsed_seconds": round(time.monotonic() - started, 3),
               "finite_independent_alias_and_joint_controls": finite,
               "paired_actual_raw_model_rare_fault_review": fault_reviews,
               "author_frozen_control_groups": 15, "exact_joint_I_Q": info,
               "population": {"constant_targets": 235, "duplicate_targets": 28,
                              "onehot_group_code_targets": 23, "total_targets_per_pass": 286},
               "paired_semantic_counts": statuses, "structurally_proved_targets_per_pass": structural_targets,
               "paired_resolution_certificates_replayed": certificate_count,
               "paired_resolution_steps_replayed": steps_total, "target_reviews": reviewed,
               "original_unassigned_state_zero_axiom_used": False,
               "author_cofactor_parser_resolution_used_for_actual_replay": False,
               "new_SoC_SAT_or_external_frontend_executions": 0,
               "deasserted_step_closed": not statuses["UNKNOWN"] and not statuses["DISPROVED_UNDER_RECORDED_ASSUMPTIONS"]}
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    prose = """# Independent current-gold joint invariant review

The adjacent JSON reports the bounded review result and all286 exact targets
per execution:235 constant constraints,28 duplicate equalities and23 current
codes across the four legal one-hot groups. The two saved execution receipts
must be byte- and field-identical; every frozen input is checked before/after.

The reviewer independently extracts the raw-state partition and synchronizer
identities, applies only exact recorded duplicate aliases and constant premises,
and reconstructs all four simultaneous one-hot predicates. All other Q/input
symbols remain arbitrary. Both zero and one completions are used only as
explicit nonvacuity witnesses, never as an unreset-state axiom. Separate finite
truth tables compare aliasing with original graph evaluation and all four-group
predicate combinations; incorrect substitutions and contradictory premises are
rejected.

Every structural proof must reconstruct to literal0. Every saved CNF proof is
independently encoded and its empty-clause resolution certificate replayed.
Every SAT witness must satisfy the independent CNF, every original joint
premise and the original raw-model D violation. UNKNOWN remains unresolved.
No new SoC solve, external frontend, WSL process or input modification occurs.
The review process is hard-limited to256MiB.

This review covers only I(Q)=>I(D) with external and both synchronizer reset
symbols deasserted. It checks separate exact synchronizer equations and the
complete paired reset-base prerequisite without claiming closure for every
interrupted/arbitrary reset sequence. Undefined-to-zero source abstraction,
gate-model induction and full-chip sequential LEC remain OPEN. A closed
deasserted induction step is not an unconditional full equivalence verdict.
"""
    out.with_suffix(".md").write_text(prose, encoding="ascii")
    print(receipt["status"], statuses, flush=True)


if __name__ == "__main__":
    main()
