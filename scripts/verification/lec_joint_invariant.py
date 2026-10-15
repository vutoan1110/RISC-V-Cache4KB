"""Bounded exact current-gold joint invariant step, with explicit premises.

This checks I(Q) => I(D) only in the recorded deasserted reset phase. It never
changes the source model, ties unreset memory to zero, or proves complete LEC.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from lec_onehot_boolean import ROOT, DAG, BoundReached, enforce_process_memory, sha
from lec_onehot_sat import decide_sat
from lec_reset_base import check_pairs, read_aig_bytes

RESET = {"reset_n": 1, "lec_q_p19088": 1, "lec_q_p19089": 1}
SECONDS = 10.0


def specification(graph, pairs, spec):
    check_pairs(pairs)
    names = set(graph["input_names"])
    if any(name.startswith("lec_oh_") for name in names):
        raise ValueError("Raw unrestricted Q graph required")
    constants, aliases = {}, {}
    partitions = [set(map(int, spec[key])) for key in ("const", "dup", "free")]
    if any(partitions[i] & partitions[j] for i in range(3) for j in range(i)) or \
            set.union(*partitions) != set(range(len(pairs["gold_only"]))):
        raise ValueError("Recorded gold-only partition is incomplete or overlapping")
    for text, value in spec["const"].items():
        if type(value) is not int or value not in (0, 1):
            raise ValueError("Constant premise must be Boolean")
        constants[f"lec_q_g{int(text):05d}"] = value
    for text, target in spec["dup"].items():
        if type(target) is not int or not 0 <= target < len(pairs["pairs"]):
            raise ValueError("Duplicate may alias only its recorded paired Q")
        aliases[f"lec_q_g{int(text):05d}"] = f"lec_q_p{target:05d}"
    if len(constants) != 235 or len(aliases) != 28 or \
            not set(constants) | set(aliases) | set(aliases.values()) <= names:
        raise ValueError("Exact current constant/duplicate population is required")
    qnames = {i: f"lec_q_p{k:05d}" for k, (i, _) in enumerate(pairs["pairs"])}
    qnames.update({i: f"lec_q_g{k:05d}" for k, i in enumerate(pairs["gold_only"])})
    dnames = {i: qname.replace("lec_q_", "lec_d_") for i, qname in qnames.items()}
    if not set(qnames.values()) <= names or not set(dnames.values()) <= set(graph["output_names"]):
        raise ValueError("Every exact raw gold Q and D must be exposed")
    groups, used = [], set()
    for group in spec["onehot_gold"]:
        bits = group["gold"]
        if not group["name"] or not bits or len(set(bits)) != len(bits) or used & set(bits) or \
                any(type(i) is not int or i not in qnames for i in bits):
            raise ValueError("Current one-hot groups must be complete and disjoint")
        used.update(bits)
        group_q = [qnames[i] for i in bits]
        if set(group_q) & (set(constants) | set(aliases)):
            raise ValueError("Current group code overlaps a substituted invariant target")
        groups.append({"name": group["name"], "gold_indices": bits,
                       "Q": group_q, "D": [dnames[i] for i in bits]})
    if [(g["name"], len(g["Q"])) for g in groups] != [
            ("lcd_en_phase", 3), ("axi_last_grant", 3), ("axi_source", 3), ("alu_ctrl_e", 14)]:
        raise ValueError("Exact current four one-hot groups are required")
    if not set(RESET) <= names:
        raise ValueError("Recorded reset symbols missing")
    normalized = lambda name: name.replace(" [", "[")
    for wanted, index in (("reset_meta_q", 19088), ("reset_sync_q", 19089)):
        matches = [k for k, (i, _) in enumerate(pairs["pairs"])
                   if "\\" + wanted in {normalized(n) for n in pairs["gold"][i]["names"]}]
        if matches != [index]:
            raise ValueError("Current synchronizer index is not independently identified")
    return {"constants": dict(sorted(constants.items())), "duplicate_aliases": dict(sorted(aliases.items())),
            "onehot_groups": groups, "other_raw_Q_and_inputs": "Independent symbolic inputs",
            "gold_only_partition_counts": dict(zip(("const", "dup", "free"), map(len, partitions))),
            "mapping_ambiguity_metadata_records": len(pairs.get("ambiguous", []))}


def alias_cofactor(dag, graph, assignments, aliases, allowed_aliases):
    """Exact substitution only under the recorded constant/equality premises."""
    names = dict(zip(graph["input_names"], range(graph["inputs"])))
    if aliases != allowed_aliases or any(not target.startswith("lec_q_p") for target in aliases.values()) or \
            set(aliases) & set(assignments) or set(aliases) & set(aliases.values()):
        raise ValueError("Unrecorded, cyclic or conflicting duplicate substitution")
    if not set(assignments) | set(aliases) | set(aliases.values()) <= names.keys() or \
            any(type(v) is not int or v not in (0, 1) for v in assignments.values()):
        raise ValueError("Unknown/non-Boolean substitution")
    replacements = {name: assignments.get(target, 2 * (names[target] + 1))
                    for name, target in aliases.items()}
    values = [0] + [replacements.get(name, assignments.get(name, 2 * (i + 1)))
                    for i, name in enumerate(graph["input_names"])]
    for a, b in graph["ands"]:
        values.append(dag.AND(values[a >> 1] ^ (a & 1), values[b >> 1] ^ (b & 1)))
    return {name: values[x >> 1] ^ (x & 1)
            for name, x in zip(graph["output_names"], graph["outputs"])}


def effective_q(graph, name, assignments, aliases):
    if name in aliases:
        name = aliases[name]
    if name in assignments:
        return assignments[name]
    return 2 * (graph["input_names"].index(name) + 1)


def joint_predicate(dag, graph, info, assignments):
    premise = 1
    for group in info["onehot_groups"]:
        values = [effective_q(graph, name, assignments, info["duplicate_aliases"])
                  for name in group["Q"]]
        premise = dag.AND(premise, dag.onehot_violation(values) ^ 1)
    return premise


def satisfies_joint(full, info, conditions):
    return all(full[name] == value for name, value in info["constants"].items()) and \
        all(full[source] == full[target] for source, target in info["duplicate_aliases"].items()) and \
        all(sum(full[name] for name in group["Q"]) == 1 for group in info["onehot_groups"]) and \
        all(full[name] == value for name, value in conditions.items())


def nonvacuity(graph, info, conditions):
    point = dict.fromkeys(graph["input_names"], 0)
    point.update(info["constants"])
    for group in info["onehot_groups"]:
        point[group["Q"][0]] = 1
    point.update(conditions)
    for source, target in info["duplicate_aliases"].items():
        point[source] = point[target]
    if not satisfies_joint(point, info, conditions):
        raise ValueError("Joint premise is contradictory/vacuous")
    return {"joint_premise_satisfiable": True,
            "onehot_Q_codes": {g["name"]: [point[n] for n in g["Q"]] for g in info["onehot_groups"]},
            "other_free_values_at_this_witness_only": 0,
            "unreset_state_zero_axiom_used": False}


def evaluate_raw(graph, full):
    if set(full) != set(graph["input_names"]) or any(type(v) is not int or v not in (0, 1) for v in full.values()):
        raise ValueError("Complete Boolean original-model witness required")
    values = [0] + [full[name] for name in graph["input_names"]]
    for a, b in graph["ands"]:
        values.append((values[a >> 1] ^ (a & 1)) & (values[b >> 1] ^ (b & 1)))
    return {name: values[x >> 1] ^ (x & 1)
            for name, x in zip(graph["output_names"], graph["outputs"])}


def xor(dag, a, b):
    return dag.OR(dag.AND(a, b ^ 1), dag.AND(a ^ 1, b))


def assess(dag, premise, violation):
    root = None
    try:
        root = dag.AND(premise, violation)
        dag.check()
        if root == 0:
            decision = {"status": "PROVED_STRUCTURAL_COFACTOR", "counterexample": None}
        else:
            decision = decide_sat(dag, root)
    except (BoundReached, MemoryError, RecursionError) as exc:
        decision = {"status": "UNKNOWN", "reason": str(exc), "counterexample": None}
    return {"joint_premise_literal": premise, "D_violation_literal": violation,
            "conditional_violation_literal": root, "decision": decision}


def recheck_counterexample(graph, info, conditions, row):
    decision = row["decision"]
    if decision["counterexample"] is None:
        return
    witness = decision["counterexample"]
    full = dict.fromkeys(graph["input_names"], 0)
    full.update({graph["input_names"][i]: value for i, value in witness.items()})
    full.update(info["constants"])
    full.update(conditions)
    for source, target in info["duplicate_aliases"].items():
        full[source] = full[target]
    if not satisfies_joint(full, info, conditions):
        raise ValueError("SAT witness fails a recorded joint premise")
    outputs = evaluate_raw(graph, full)
    if row["kind"] == "constant":
        violated = outputs[row["D"]] != row["expected"]
        actual = outputs[row["D"]]
    elif row["kind"] == "duplicate":
        actual = [outputs[row["D"]], outputs[row["paired_D"]]]
        violated = actual[0] != actual[1]
    else:
        actual = [outputs[name] for name in row["D"]]
        violated = sum(actual) != 1
    if not violated:
        raise ValueError("SAT witness fails to violate the original raw-model D obligation")
    decision["counterexample"] = {graph["input_names"][i]: value for i, value in sorted(witness.items())}
    row.update({"original_raw_D_at_counterexample": actual,
                "counterexample_satisfies_every_joint_premise": True,
                "counterexample_other_free_values_default": 0,
                "default_is_witness_completion_only_not_state_axiom": True})


def protocol_checks(graph):
    rows = []
    for conditions, expected in (({"reset_n": 0}, [0, 0]),
                                 ({"reset_n": 1, "lec_q_p19088": 0}, [1, 0]),
                                 ({"reset_n": 1, "lec_q_p19088": 1}, [1, 1])):
        dag = DAG(graph["inputs"], time.monotonic() + SECONDS)
        try:
            outputs = dag.cofactor(graph, conditions)
            actual = [outputs["lec_d_p19088"], outputs["lec_d_p19089"]]
            status = "PROVED_STRUCTURAL_PROTOCOL" if actual == expected else "UNKNOWN"
        except (BoundReached, MemoryError, RecursionError) as exc:
            actual, status = str(exc), "UNKNOWN"
        rows.append({"assignments": conditions, "expected_meta_sync_D": expected,
                     "actual_meta_sync_D_literals": actual, "status": status,
                     "any_joint_invariant_assumed": False})
    return rows


def run(graph, info):
    rows = []
    constants = info["constants"]
    aliases = info["duplicate_aliases"]
    conditions = dict(RESET)
    assignments = {**constants, **conditions}
    dag = DAG(graph["inputs"], time.monotonic() + SECONDS)
    outputs = alias_cofactor(dag, graph, assignments, aliases, aliases)
    premise = joint_predicate(dag, graph, info, assignments)
    point = nonvacuity(graph, info, conditions)
    for qname, expected in constants.items():
        dag.deadline = time.monotonic() + SECONDS
        dname = qname.replace("lec_q_", "lec_d_")
        row = {"kind": "constant", "Q": qname, "D": dname, "expected": expected,
               "reset_conditions": conditions, "nonvacuity": point}
        row.update(assess(dag, premise, outputs[dname] ^ expected))
        recheck_counterexample(graph, info, conditions, row)
        rows.append(row)
    for qname, partner in aliases.items():
        dag.deadline = time.monotonic() + SECONDS
        dname, pname = qname.replace("lec_q_", "lec_d_"), partner.replace("lec_q_", "lec_d_")
        row = {"kind": "duplicate", "Q": qname, "paired_Q": partner,
               "D": dname, "paired_D": pname, "reset_conditions": conditions, "nonvacuity": point}
        row.update(assess(dag, premise, xor(dag, outputs[dname], outputs[pname])))
        recheck_counterexample(graph, info, conditions, row)
        rows.append(row)
    print("constant/duplicate closures", len(rows), flush=True)
    del dag, outputs
    for group in info["onehot_groups"]:
        for active in range(len(group["Q"])):
            conditions = {**RESET, **{name: int(i == active) for i, name in enumerate(group["Q"])}}
            row = {"kind": "onehot", "group": group["name"], "active_current_bit": active,
                   "group_Q": group["Q"], "D": group["D"], "reset_conditions": conditions,
                   "nonvacuity": nonvacuity(graph, info, conditions)}
            dag = DAG(graph["inputs"], time.monotonic() + SECONDS)
            try:
                assignments = {**constants, **conditions}
                outputs = alias_cofactor(dag, graph, assignments, aliases, aliases)
                premise = joint_predicate(dag, graph, info, assignments)
                row.update(assess(dag, premise, dag.onehot_violation([outputs[name] for name in group["D"]])))
                recheck_counterexample(graph, info, conditions, row)
            except (BoundReached, MemoryError, RecursionError) as exc:
                row["decision"] = {"status": "UNKNOWN", "reason": str(exc), "counterexample": None}
            rows.append(row)
            print(group["name"], active, row["decision"]["status"], flush=True)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--controls", required=True)
    args = parser.parse_args()
    out, controls = Path(args.out).resolve(), Path(args.controls).resolve()
    if out.exists() or not out.is_relative_to(ROOT) or not controls.is_relative_to(ROOT):
        raise ValueError("New research output and existing controls required")
    memory = enforce_process_memory()
    ctrl = json.loads(controls.read_text())
    if ctrl["status"] != "PASS_JOINT_INVARIANT_CHECKER_CONTROLS":
        raise ValueError("Validated joint checker controls required")
    for rel, digest in ctrl["source_sha256"].items():
        if sha(ROOT / rel) != digest:
            raise ValueError("Joint checker changed since controls")
    paths = [ROOT / p for p in ("asic/equiv/lec/gold_god_r14.aig", "asic/equiv/lec/pairsAR14.json",
                               "asic/equiv/lec/AR14_spec.json", "results/dm_joint_invariant_hypothesis_20261010.md",
                               "results/dm_reset_base_structural_20261010_p1.json",
                               "results/dm_reset_base_structural_20261010_p2.json",
                               "scripts/verification/lec_joint_invariant.py",
                               "scripts/verification/lec_reset_base.py",
                               "scripts/verification/lec_onehot_boolean.py",
                               "scripts/verification/lec_onehot_sat.py")]
    paths.append(controls)
    hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    bases = [json.loads(p.read_text()) for p in paths[4:6]]
    if bases[0] != bases[1] or bases[0]["status"] != "PROVED_GOLD_RESET_SUBOBLIGATIONS_ONLY":
        raise ValueError("Independent reset base proof is required")
    for rel, digest in bases[0]["inputs"].items():
        if sha(ROOT / rel) != digest:
            raise ValueError("Reset base inputs do not match current graph")
    graph = read_aig_bytes(paths[0].read_bytes())
    pairs, spec = json.loads(paths[1].read_text()), json.loads(paths[2].read_text())
    info = specification(graph, pairs, spec)
    if len(bases[0]["constant_reset"]) != 235 or len(bases[0]["duplicate_reset"]) != 28 or \
            len(bases[0]["onehot_reset"]) != 4:
        raise ValueError("Reset base population differs from exact joint invariant")
    protocols = protocol_checks(graph)
    rows = run(graph, info)
    if len(rows) != 286 or any(sha(ROOT / rel) != digest for rel, digest in hashes.items()):
        raise ValueError("Obligation population or frozen input changed")
    counts = {status: sum(r["decision"]["status"] == status for r in rows)
              for status in ("PROVED_STRUCTURAL_COFACTOR", "PROVED_BOOLEAN_CNF",
                             "DISPROVED_UNDER_RECORDED_ASSUMPTIONS", "UNKNOWN")}
    receipt = {"status": "BOUNDED_JOINT_CURRENT_GOLD_INDUCTION_SUBPROOF_ONLY",
               "full_sequential_LEC": "OPEN", "source_undefined_zero_abstraction_gap": "OPEN",
               "independent_kernel_review": "PENDING_SEPARATE_REVIEW_RECEIPT",
               "input_sha256": hashes, "memory_enforcement": memory,
               "joint_invariant_I_Q": info, "reset_phase": RESET,
               "scope": "I(Q) implies I(D) only in the recorded deasserted reset phase; constant/duplicate values and all four one-hot groups are explicit simultaneous premises, with all other raw Q/input symbols arbitrary",
               "synchronizer_protocol": protocols,
               "interrupted_or_arbitrary_reset_phase_invariant_closure": "OPEN",
               "counts": counts, "obligations": rows,
               "fixed_algorithm": "Structural raw AND/NOT cofactor, then the frozen exact CNF/resolution-certified SAT algorithm",
               "limits": {"process_memory_bytes": 512 * 1024 * 1024, "seconds_per_obligation": SECONDS},
               "external_formal_tools_executed": False}
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print(json.dumps(counts), flush=True)


if __name__ == "__main__":
    main()
