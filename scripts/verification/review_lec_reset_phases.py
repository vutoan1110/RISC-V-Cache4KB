"""Independent bounded replay of current-gold sampled reset-phase evidence.

Own raw parser/cofactor/encoder/resolution code verifies all six phase closures,
startup protocol equations, premise nonvacuity and actual semantic controls.
No actual SoC solve or external tool is executed; source/event/full LEC is OPEN.
"""
from __future__ import annotations

import argparse
import gc
import itertools
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
from review_lec_onehot_cnf import ROOT, content_digest, digest, encode, memory_cap, peak_memory, read_graph, replay
from review_lec_joint_invariant import AliasModel, independent_spec, nonvacuity_point, raw_evaluation, satisfies


def phase_conditions(phase):
    e, m, s = phase
    return {"reset_n": e, "lec_q_p19088": m, "lec_q_p19089": s}


def legal(m, s):
    return (s == 0) or (m == 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if out.exists() or out.with_suffix(".md").exists() or not out.is_relative_to(ROOT):
        raise ValueError("New independent reset-phase review output required")
    memory = memory_cap()
    started = time.monotonic()
    sources = ["asic/equiv/lec/gold_god_r14.aig", "asic/equiv/lec/pairsAR14.json",
               "asic/equiv/lec/AR14_spec.json", "results/lec_reset_phase_controls_20261010.json",
               "results/dm_reset_phase_20261010_p1.json", "results/dm_reset_phase_20261010_p2.json",
               "results/dm_reset_phase_fault_20261010_p1.json", "results/dm_reset_phase_fault_20261010_p2.json",
               "scripts/verification/review_lec_reset_phases.py",
               "scripts/verification/review_lec_joint_invariant.py",
               "scripts/verification/review_lec_onehot_cnf.py"]
    hashes = {rel: digest(ROOT / rel) for rel in sources}
    control = json.loads((ROOT / sources[3]).read_text())
    if control["status"] != "PASS_RESET_PHASE_CHECKER_CONTROLS" or control["control_count"] != 11 \
            or len(control["controls"]) != 11 or any(row["status"] != "PASS" for row in control["controls"]):
        raise ValueError("Complete frozen phase controls required")
    for rel, expected in control["source_sha256"].items():
        if digest(ROOT / rel) != expected:
            raise ValueError("Frozen phase source changed")
        hashes[rel] = expected
    import lec_reset_phase as subject
    phases = [list(p) for p in itertools.product((0, 1), repeat=3) if legal(p[1], p[2])]
    if [list(p) for p in subject.PHASES] != phases:
        raise ValueError("Author phase population/order differs from independent exact R partition")
    for e, m, s in itertools.product((0, 1), repeat=3):
        if subject.relation(m, s) != legal(m, s) or not legal(e, e & m):
            raise ValueError("Checker phase relation differs from independent truth table")
    for invalid in ((0, 0, 1), (1, 0, 1), (True, 0, 0), (1, True, 0),
                    (1, 1, True), (2, 1, 1), (1, 1), (1, 1, 1, 0)):
        try:
            subject.conditions_for(invalid)
        except ValueError:
            pass
        else:
            raise ValueError("Invalid/unestablished/ill-typed phase accepted")
    graph = read_graph(ROOT / sources[0])
    pairs, spec = [json.loads((ROOT / rel).read_text()) for rel in sources[1:3]]
    info = independent_spec(graph, pairs, spec)
    saved = [json.loads((ROOT / rel).read_text()) for rel in sources[4:6]]
    if saved[0] != saved[1] or hashes[sources[4]] != hashes[sources[5]]:
        raise ValueError("Actual independent phase-execution pair differs")
    for receipt in saved:
        if receipt["status"] != "BOUNDED_REACHABLE_SAMPLED_RESET_PHASE_SUBPROOF_ONLY" \
                or receipt["joint_invariant_I_Q"] != info or receipt["phase_order"] != phases \
                or receipt["phase_count"] != 6 or receipt["closure_obligations_per_phase"] != 286 \
                or receipt["total_closure_obligations"] != 1716 \
                or any(receipt[name] != "OPEN" for name in ("between_edge_asynchronous_source_events",
                          "source_undefined_zero_abstraction_gap", "raw_N1_final_reset_coupling", "full_sequential_LEC")):
            raise ValueError("Phase receipt completeness/scope differs")
        for rel, expected in receipt["input_sha256"].items():
            if digest(ROOT / rel) != expected:
                raise ValueError("Phase proof input changed")
            hashes[rel] = expected
    prerequisite = json.loads((ROOT / "results/lec_joint_reset_base_independent_review_20261010.json").read_text())
    if prerequisite["status"] != "PASS_INDEPENDENT_RAW_JOINT_RESET_PREREQUISITE_REVIEW" \
            or prerequisite["counts"] != {"constant": 235, "duplicate": 28, "onehot_group": 4}:
        raise ValueError("Independent raw reset-base prerequisite missing")
    # Include both startup01 codes: no unreachable-power-on state is assumed.
    protocol_rows = []
    for phase in itertools.product((0, 1), repeat=3):
        conditions = phase_conditions(phase)
        model = AliasModel(graph, conditions, {})
        actual = [model.outputs["lec_d_p19088"], model.outputs["lec_d_p19089"]]
        e, m, s = phase
        if actual != [e, e & m]:
            raise ValueError("Original unrestricted raw synchronizer equation differs")
        protocol_rows.append({"phase": list(phase), "actual_raw_meta_sync_D": actual,
                              "R_D_true": legal(*actual), "I_Q_assumed": False,
                              "current_R_Q_assumed": False, "status": "PASS"})
        del model
        gc.collect()
    reviews, certificates, total_steps = [], 0, 0
    for phase_index, phase in enumerate(phases):
        phase_evidence = saved[0]["phases"][phase_index]
        phase_conditions0 = phase_conditions(phase)
        e, m, s = phase
        wanted_protocol = {"phase": phase, "assignments": phase_conditions0,
                           "expected_next_meta_sync": [e, e & m], "actual_D_literals": [e, e & m],
                           "expected_next_relation_R": True, "status": "PROVED_STRUCTURAL_PHASE_TRANSITION",
                           "joint_invariant_assumed_for_protocol": False}
        if phase_evidence["phase"] != phase or not phase_evidence["phase_relation_R"] \
                or phase_evidence["protocol"] != wanted_protocol or len(phase_evidence["obligations"]) != 286:
            raise ValueError("Phase saved protocol/shape differs")
        counts = {name: 0 for name in ("PROVED_STRUCTURAL_COFACTOR", "PROVED_BOOLEAN_CNF",
                                      "DISPROVED_UNDER_RECORDED_ASSUMPTIONS", "UNKNOWN")}
        target_rows = []

        def check(model, index, descriptor, conditions, premise, violation):
            nonlocal certificates, total_steps
            row = phase_evidence["obligations"][index]
            root = model.and_gate(premise, violation)
            point0 = nonvacuity_point(graph, info, conditions, 0)
            point1 = nonvacuity_point(graph, info, conditions, 1)
            nonvacuity = {"joint_premise_satisfiable": True,
                          "onehot_Q_codes": {g["name"]: [point0[n] for n in g["Q"]] for g in info["onehot_groups"]},
                          "other_free_values_at_this_witness_only": 0, "unreset_state_zero_axiom_used": False}
            for key, expected in {**descriptor, "reset_conditions": conditions, "nonvacuity": nonvacuity,
                                  "joint_premise_literal": premise, "D_violation_literal": violation,
                                  "conditional_violation_literal": root}.items():
                if row.get(key) != expected:
                    raise ValueError("Phase exact target differs: phase%s row%d key%s" % (phase, index, key))
            for point in (point0, point1):
                if model.evaluate(premise, {i: point[name] for i, name in enumerate(graph["input_names"])}) != 1:
                    raise ValueError("Encoded joint phase premise is vacuous")
            decision = row["decision"]
            status = decision["status"]
            if status not in counts or decision["counterexample"] is not None:
                raise ValueError("Saved phase proof is unresolved or has a counterexample")
            counts[status] += 1
            detail = {"row_index": index, **descriptor, "status": status,
                      "nonvacuity_other_free_zero_and_one": True, "arbitrary_unassigned_state_preserved": True}
            if status == "PROVED_STRUCTURAL_COFACTOR":
                if root != 0 or decision != {"status": status, "counterexample": None}:
                    raise ValueError("Phase structural proof is not exact literal0")
            elif status == "PROVED_BOOLEAN_CNF":
                clauses, mapping = encode(model, root)
                if root == 0 or decision["CNF_variables"] != len(mapping) \
                        or decision["CNF_initial_clauses"] != len(clauses) \
                        or decision["learned_clauses"] != len(decision["resolution_certificate"]):
                    raise ValueError("Phase CNF shape differs from independent reconstruction")
                steps = []
                for proof in saved:
                    d = proof["phases"][phase_index]["obligations"][index]["decision"]
                    count = replay(clauses, d["resolution_certificate"], d["terminal_empty_clause_derivation"])
                    if count != d["resolution_steps"] or count != d["independently_replayed_resolution_steps"]:
                        raise ValueError("Phase certificate replay count differs")
                    certificates += 1
                    total_steps += count
                    steps.append(count)
                detail.update({"CNF_sha256": content_digest(clauses), "variables": len(mapping),
                               "clauses": len(clauses), "variable_map_sha256": content_digest(sorted(mapping.items())),
                               "paired_replay_steps": steps})
            else:
                raise ValueError("UNKNOWN/DISPROVED cannot close the sampled-phase proof")
            target_rows.append(detail)

        model = AliasModel(graph, {**info["constants"], **phase_conditions0}, info["duplicate_aliases"])
        premise = model.premise(info["onehot_groups"])
        index = 0
        for qname, expected in info["constants"].items():
            dn = qname.replace("lec_q_", "lec_d_")
            check(model, index, {"kind": "constant", "Q": qname, "D": dn, "expected": expected},
                  phase_conditions0, premise, model.outputs[dn] ^ expected)
            index += 1
        for qname, partner in info["duplicate_aliases"].items():
            dn, pd = qname.replace("lec_q_", "lec_d_"), partner.replace("lec_q_", "lec_d_")
            check(model, index, {"kind": "duplicate", "Q": qname, "paired_Q": partner, "D": dn, "paired_D": pd},
                  phase_conditions0, premise, model.unequal(model.outputs[dn], model.outputs[pd]))
            index += 1
        del model
        gc.collect()
        for group in info["onehot_groups"]:
            for active in range(len(group["Q"])):
                conditions = {**phase_conditions0, **{name: int(i == active) for i, name in enumerate(group["Q"])}}
                model = AliasModel(graph, {**info["constants"], **conditions}, info["duplicate_aliases"])
                premise = model.premise(info["onehot_groups"])
                check(model, index, {"kind": "onehot", "group": group["name"], "active_current_bit": active,
                                    "group_Q": group["Q"], "D": group["D"]}, conditions, premise,
                      model.violation([model.outputs[name] for name in group["D"]]))
                index += 1
                del model
                gc.collect()
        if index != 286 or counts != phase_evidence["counts"]:
            raise ValueError("Per-phase target/count population differs")
        reviews.append({"phase": phase, "status": "PASS", "counts": counts, "target_reviews": target_rows})
        print("Independent reset-phase review", phase, counts, flush=True)

    faults = [json.loads((ROOT / rel).read_text()) for rel in sources[6:8]]
    if faults[0] != faults[1] or hashes[sources[6]] != hashes[sources[7]]:
        raise ValueError("Paired actual rare reset-phase fault differs")
    fault_reviews = []
    for pass_index, fault in enumerate(faults, 1):
        if fault["status"] != "PASS_ACTUAL_RAW_MODEL_RARE_RESET_PHASE_FAULT_CONTROL" \
                or fault["phase"] != [0, 1, 1] or fault["joint_invariant_I_Q"] != info:
            raise ValueError("Rare phase control uses different actual source premise")
        for rel, value in fault["input_sha256"].items():
            if digest(ROOT / rel) != value:
                raise ValueError("Actual rare phase source changed")
            hashes[rel] = value
        conditions = phase_conditions(fault["phase"])
        if fault["assignments"] != conditions or fault["unreset_state_zero_axiom_used"]:
            raise ValueError("Rare phase conditions or unreset contract differ")
        model = AliasModel(graph, {**info["constants"], **conditions}, info["duplicate_aliases"])
        premise = model.premise(info["onehot_groups"])
        meta, sync = [model.outputs[name] for name in ("lec_d_p19088", "lec_d_p19089")]
        baseline_violation = model.and_gate(sync, meta ^ 1)
        baseline_root = model.and_gate(premise, baseline_violation)
        baseline = fault["baseline"]
        if baseline["joint_premise_literal"] != premise or baseline["D_violation_literal"] != baseline_violation \
                or baseline["conditional_violation_literal"] != baseline_root or baseline_root != 0 \
                or baseline["decision"]["status"] != "PROVED_STRUCTURAL_COFACTOR":
            raise ValueError("Actual rare phase baseline is not independently structural zero")
        excluded = set(conditions).union(info["constants"], info["duplicate_aliases"],
                                   {n for g in info["onehot_groups"] for n in g["Q"]})
        triggers = [n for n in graph["input_names"] if n not in excluded][:24]
        if triggers != fault["trigger_inputs"] or len(triggers) != 24:
            raise ValueError("Rare protocol trigger is not exact24 free symbols")
        rare = 1
        for name in triggers:
            rare = model.and_gate(rare, 2 * (model.positions[name] + 1))
        mutated_sync = model.or_gate(sync, rare)
        violation = model.and_gate(mutated_sync, meta ^ 1)
        root = model.and_gate(premise, violation)
        negative = fault["negative"]
        if negative["joint_premise_literal"] != premise or negative["D_violation_literal"] != violation \
                or negative["conditional_violation_literal"] != root:
            raise ValueError("Rare protocol graph differs from independent reconstruction")
        decision = negative["decision"]
        clauses, mapping = encode(model, root)
        assignment = decision["CNF_assignment"]
        if decision["status"] != "DISPROVED_UNDER_RECORDED_ASSUMPTIONS" \
                or decision["CNF_variables"] != len(mapping) or decision["CNF_initial_clauses"] != len(clauses) \
                or len(assignment) != len(mapping) + 1 or any(x not in (-1, 1) for x in assignment[1:]) \
                or not all(any(assignment[abs(x)] == (1 if x > 0 else -1) for x in c) for c in clauses):
            raise ValueError("Rare reset-phase witness fails independent CNF")
        witness = {graph["input_names"][node // 2 - 1]: int(assignment[var] == 1)
                   for node, var in mapping.items() if node <= 2 * model.inputs}
        if witness != decision["counterexample"] or any(witness.get(n) != 1 for n in triggers) \
                or model.evaluate(root, {model.positions[n]: v for n, v in witness.items()}) != 1:
            raise ValueError("Rare phase witness fails raw support/map/DAG checks")
        complete = dict.fromkeys(graph["input_names"], 0)
        complete.update(witness)
        complete.update(info["constants"])
        complete.update(conditions)
        for source, target in info["duplicate_aliases"].items():
            complete[source] = complete[target]
        if not satisfies(complete, info, conditions) or not legal(complete["lec_q_p19088"], complete["lec_q_p19089"]):
            raise ValueError("Original rare phase witness fails I(Q) or R(Q)")
        raw = raw_evaluation(graph, complete)
        original = [raw["lec_d_p19088"], raw["lec_d_p19089"]]
        mutated = [original[0], original[1] | 1]
        if original != [0, 0] or mutated != [0, 1] or not legal(*original) or legal(*mutated) \
                or original != fault["original_raw_next_meta_sync"] or mutated != fault["mutated_next_meta_sync"]:
            raise ValueError("Rare protocol semantic fault is not reproduced on the original raw model")
        fault_reviews.append({"pass": pass_index, "status": "PASS", "I_Q_and_R_Q_satisfied": True,
                              "original_next": original, "mutated_next": mutated,
                              "trigger_bits": 24, "CNF_and_original_raw_witness_validated": True})
        del model, clauses, mapping
        gc.collect()
    if any(digest(ROOT / rel) != value for rel, value in hashes.items()):
        raise ValueError("Frozen phase review input changed")
    receipt = {"status": "PASS_INDEPENDENT_SAMPLED_RESET_PHASE_REVIEW",
               "full_sequential_LEC": "OPEN", "source_undefined_zero_abstraction_gap": "OPEN",
               "between_edge_asynchronous_source_events": "OPEN", "raw_N1_final_reset_coupling": "OPEN",
               "scope": "All six exact raw-gold completed-clock-step phases satisfying R after the established sampled reset base. Startup01 is included in the independent protocol equation check, not assumed away. No source asynchronous or four-state bridge is inferred.",
               "input_sha256": hashes, "memory_enforcement": memory, "peak_memory": peak_memory(),
               "elapsed_seconds": round(time.monotonic() - started, 3),
               "exact_six_phase_partition": phases, "protocol_checks_all8_including_startup01": protocol_rows,
               "paired_all_fields_and_bytes_equal": True,
               "targets_per_phase_per_pass": 286, "targets_per_pass": 1716,
               "structural_targets_per_pass": 1696, "CNF_targets_per_pass": 20,
               "paired_CNF_certificates_replayed": certificates, "paired_resolution_steps_replayed": total_steps,
               "phase_reviews": reviews, "paired_actual_rare_protocol_fault_review": fault_reviews,
               "sampled_model_phase_bridge_closed_after_stated_reset_base": True,
               "unreset_memory_or_register_zero_axiom_used": False,
               "author_parser_cofactor_resolution_used_for_actual_replay": False,
               "new_SoC_solver_or_external_tools_executed": False}
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    out.with_suffix(".md").write_text("""# Independent sampled reset-phase review

PASS on the existing raw-gold Boolean completed-clock-step model. All six phases
of R=(not syncQ) OR metaQ were independently reconstructed, with286 exact joint
targets in each phase and1716 per independent saved execution. There are1696
structural-zero targets and20 exact CNF targets per pass. Every saved CNF proof
is independently encoded and replayed for both passes. No actual SoC solve ran.

The original raw protocol equations were independently checked for all eight
external/meta/sync codes, including startup01: Dmeta=external and
Dsync=external AND meta. They establish00 on an asserted sampled edge and
preserve R for arbitrary later sampled external values. The already independently
reviewed reset base establishes I on a subsequent asserted sampled step. Both
free-state0/1 completions demonstrate premise nonvacuity only; neither imposes
zero initialization. The exact all-other-state-symbolic contract is retained.

Both rare24 actual-model controls were independently replayed through CNF and
original raw graph evaluation, satisfying I(Q) and R(Q), and changing next
meta/sync00 into01 solely through an in-memory copied Dsync mutation.

The sampled phase bridge is closed within this model and stated reset base.
Source undefined-to-zero abstraction, asynchronous events between clock edges,
raw N1/final reset coupling and full sequential LEC remain OPEN. This result
must not be described as complete chip equivalence or four-state RTL closure.
No source, old helper, PD input, global environment or prior evidence changed.
Detailed targets, hashes, counts and the hard256MiB process limit are recorded
in the adjacent JSON.
""", encoding="ascii")
    print(receipt["status"], "1716targets/pass; certificates", certificates, "steps", total_steps, flush=True)


if __name__ == "__main__":
    main()
