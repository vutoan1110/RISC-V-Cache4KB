"""Bounded exact CNF checks on current ALU one-hot raw Boolean AIG cones.

Watched-literal conflict-driven DPLL learns only checked resolution clauses.
UNSAT requires a separately replayed empty-clause derivation; SAT requires a
direct witness on the original Boolean DAG. Limits give UNKNOWN, never PASS.
"""
from __future__ import annotations

import argparse
import heapq
import json
from pathlib import Path
import time

from lec_onehot_boolean import (ROOT, DAG, BoundReached, case_conditions,
                                enforce_process_memory, sha)
from lec_reset_base import read_aig_bytes

MAX_VARIABLES = 20_000
MAX_CLAUSES = 60_000
MAX_DECISIONS = 10_000
MAX_CONFLICTS = 10_000
MAX_LEARNED = 10_000
MAX_RESOLUTIONS = 100_000
SECONDS_PER_CASE = 10.0


def resolve(left, right, pivot):
    a, b = set(left), set(right)
    if (pivot in a and -pivot in b) == (-pivot in a and pivot in b):
        raise ValueError("Resolution requires exactly opposite pivot signs")
    result = (a | b) - {pivot, -pivot}
    if any(-literal in result for literal in result):
        raise ValueError("Tautological resolvent is not a conflict clause")
    return result


def tseitin(dag, root):
    cone, support = dag.cone(root)
    nodes = sorted(cone | {2 * (i + 1) for i in support})
    if len(nodes) > MAX_VARIABLES:
        raise BoundReached("CNF_VARIABLE_BOUND")
    index = {node: i + 1 for i, node in enumerate(nodes)}
    clauses = []

    def literal(value):
        if value == 0:
            return 0
        if value == 1:
            return True
        variable = index[value & ~1]
        return -variable if value & 1 else variable

    def negate(value):
        return 0 if value is True else True if value == 0 else -value

    def add(*terms):
        if any(term is True for term in terms):
            return
        clause = {term for term in terms if term != 0}
        if any(-term in clause for term in clause):
            return
        clauses.append(tuple(sorted(clause, key=lambda x: (abs(x), x))))
        if len(clauses) > MAX_CLAUSES:
            raise BoundReached("CNF_CLAUSE_BOUND")

    for node in sorted(cone):
        a, b = map(literal, dag.nodes[node])
        y = index[node]
        add(-y, a)
        add(-y, b)
        add(y, negate(a), negate(b))
    add(literal(root))
    return clauses, index


def verify_resolution(initial, certificate, terminal, deadline):
    """Replay clause implications without using watched lists or SAT state."""
    clauses = [tuple(c) for c in initial]
    steps = 0

    def derive(record):
        nonlocal steps
        parent = record["parent"]
        if type(parent) is not int or not 0 <= parent < len(clauses):
            raise ValueError("Certificate refers to absent/future parent")
        result = set(clauses[parent])
        for other, pivot in record["resolution"]:
            if type(other) is not int or not 0 <= other < len(clauses) or \
                    type(pivot) is not int or pivot <= 0:
                raise ValueError("Invalid certificate reason/pivot")
            result = resolve(result, clauses[other], pivot)
            steps += 1
            if steps > MAX_RESOLUTIONS or time.monotonic() > deadline:
                raise BoundReached("CERTIFICATE_RESOURCE_BOUND")
        return result

    for record in certificate:
        if derive(record) != set(record["clause"]):
            raise ValueError("Learned clause is not its exact resolution derivation")
        clauses.append(tuple(record["clause"]))
    if derive(terminal):
        raise ValueError("UNSAT certificate does not derive the empty clause")
    return steps


class Solver:
    def __init__(self, clauses, variables, deadline, decision_bound=MAX_DECISIONS):
        if not 0 <= variables <= MAX_VARIABLES or len(clauses) > MAX_CLAUSES:
            raise BoundReached("CNF_INPUT_BOUND")
        self.clauses = []
        self.positions = []
        self.watch = {}
        self.value = [0] * (variables + 1)
        self.level = [0] * (variables + 1)
        self.reason = [None] * (variables + 1)
        self.phase = [-1] * (variables + 1)
        self.activity = [0] * (variables + 1)
        self.trail = []
        self.limits = []
        self.head = 0
        self.deadline = deadline
        self.decision_bound = decision_bound
        self.decisions = self.conflicts = self.resolutions = self.operations = 0
        self.certificate = []
        self.empty = None
        self.units = []
        for clause in clauses:
            if any(type(lit) is not int or not 1 <= abs(lit) <= variables for lit in clause) or \
                    len(set(clause)) != len(clause) or any(-lit in clause for lit in clause):
                raise ValueError("Invalid unnormalized CNF clause")
            self.add(tuple(clause))
            for literal in clause:
                self.activity[abs(literal)] += 3 if len(clause) <= 2 else 1
        self.heap = [(-self.activity[i], i) for i in range(1, variables + 1)]
        heapq.heapify(self.heap)

    def check(self):
        self.operations += 1
        if self.operations % 128 == 0 and time.monotonic() > self.deadline:
            raise BoundReached("TIME_BOUND")

    def truth(self, literal):
        v = self.value[abs(literal)]
        return v if literal > 0 else -v

    def add(self, clause):
        index = len(self.clauses)
        self.clauses.append(clause)
        if not clause:
            self.positions.append(None)
            self.empty = index
        elif len(clause) == 1:
            self.positions.append(None)
            self.units.append(index)
        else:
            self.positions.append([0, 1])
            for literal in clause[:2]:
                self.watch.setdefault(literal, []).append(index)
        return index

    def enqueue(self, literal, reason):
        var = abs(literal)
        if self.value[var]:
            return self.truth(literal) == 1
        self.value[var] = 1 if literal > 0 else -1
        self.phase[var] = self.value[var]
        self.level[var] = len(self.limits)
        self.reason[var] = reason
        self.trail.append(literal)
        return True

    def propagate(self):
        while self.head < len(self.trail):
            self.check()
            false = -self.trail[self.head]
            self.head += 1
            watched = self.watch.setdefault(false, [])
            pos = 0
            while pos < len(watched):
                self.check()
                index = watched[pos]
                clause, positions = self.clauses[index], self.positions[index]
                which = 0 if clause[positions[0]] == false else 1
                if clause[positions[which]] != false:
                    raise ValueError("Stale watched-literal index")
                other_pos = positions[1 - which]
                other = clause[other_pos]
                if self.truth(other) == 1:
                    pos += 1
                    continue
                replacement = next((i for i, literal in enumerate(clause)
                                    if i not in positions and self.truth(literal) != -1), None)
                if replacement is not None:
                    positions[which] = replacement
                    watched[pos] = watched[-1]
                    watched.pop()
                    self.watch.setdefault(clause[replacement], []).append(index)
                else:
                    if self.truth(other) == -1:
                        return index
                    if not self.enqueue(other, index):
                        raise ValueError("Unit propagation did not agree with assignment")
                    pos += 1
        return None

    def derive(self, conflict, root=False):
        derived = set(self.clauses[conflict])
        trace = []
        current = len(self.limits)
        while derived and (root or sum(self.level[abs(lit)] == current for lit in derived) > 1):
            self.check()
            if any(self.truth(lit) != -1 for lit in derived):
                raise ValueError("Conflict derivation contains a nonfalse literal")
            variables = {abs(x) for x in derived}
            pivot_lit = next((lit for lit in reversed(self.trail)
                              if abs(lit) in variables and
                              (root or self.level[abs(lit)] == current)), None)
            if pivot_lit is None:
                raise ValueError("No trail pivot for conflict derivation")
            pivot = abs(pivot_lit)
            reason = self.reason[pivot]
            if reason is None:
                raise ValueError("Cannot resolve away an unexplained decision")
            derived = resolve(derived, self.clauses[reason], pivot)
            trace.append([reason, pivot])
            self.resolutions += 1
            if self.resolutions > MAX_RESOLUTIONS:
                raise BoundReached("RESOLUTION_BOUND")
        return derived, {"parent": conflict, "resolution": trace}

    def backtrack(self, level):
        if len(self.limits) <= level:
            return
        marker = self.limits[level]
        for literal in self.trail[marker:]:
            var = abs(literal)
            self.value[var], self.level[var], self.reason[var] = 0, 0, None
            heapq.heappush(self.heap, (-self.activity[var], var))
        del self.trail[marker:]
        del self.limits[level:]
        self.head = min(self.head, marker)
        if len(self.heap) > 4 * len(self.value):
            self.heap = [(-self.activity[i], i) for i in range(1, len(self.value)) if not self.value[i]]
            heapq.heapify(self.heap)

    def choose(self):
        while self.heap:
            score, var = heapq.heappop(self.heap)
            if not self.value[var] and score == -self.activity[var]:
                return var
        return None

    def solve(self):
        if time.monotonic() > self.deadline:
            raise BoundReached("TIME_BOUND")
        conflict = self.empty
        if conflict is None:
            for index in self.units:
                if not self.enqueue(self.clauses[index][0], index):
                    conflict = index
                    break
        while True:
            if conflict is None:
                conflict = self.propagate()
            if conflict is not None:
                self.conflicts += 1
                if self.conflicts > MAX_CONFLICTS:
                    raise BoundReached("CONFLICT_BOUND")
                if not self.limits:
                    derived, terminal = self.derive(conflict, root=True)
                    if derived:
                        raise ValueError("Root conflict failed to derive empty clause")
                    return {"status": "UNSAT", "certificate": self.certificate,
                            "terminal": terminal}
                derived, record = self.derive(conflict)
                asserting = [lit for lit in derived if self.level[abs(lit)] == len(self.limits)]
                if len(asserting) != 1:
                    raise ValueError("Learned clause has no unique asserting literal")
                others = sorted(derived - set(asserting),
                                key=lambda lit: (-self.level[abs(lit)], abs(lit), lit))
                clause = tuple(asserting + others)
                backlevel = max((self.level[abs(lit)] for lit in others), default=0)
                if len(self.certificate) >= MAX_LEARNED:
                    raise BoundReached("LEARNED_CLAUSE_BOUND")
                record["clause"] = list(clause)
                # Check the implication here and replay it independently before UNSAT acceptance.
                check_derived = set(self.clauses[record["parent"]])
                for reason, pivot in record["resolution"]:
                    check_derived = resolve(check_derived, self.clauses[reason], pivot)
                if check_derived != set(clause):
                    raise ValueError("Learned clause derivation differs")
                for lit in derived:
                    var = abs(lit)
                    self.activity[var] += 1
                    heapq.heappush(self.heap, (-self.activity[var], var))
                self.backtrack(backlevel)
                index = self.add(clause)
                self.certificate.append(record)
                if not self.enqueue(clause[0], index):
                    raise ValueError("Learned asserting literal conflicts after backtrack")
                conflict = None
            else:
                var = self.choose()
                if var is None:
                    if any(not any(self.truth(lit) == 1 for lit in c) for c in self.clauses):
                        raise ValueError("Reported SAT assignment violates a CNF clause")
                    return {"status": "SAT", "assignment": list(self.value)}
                self.decisions += 1
                if self.decisions > self.decision_bound:
                    raise BoundReached("DECISION_BOUND")
                self.limits.append(len(self.trail))
                self.enqueue(var * self.phase[var], None)


def decide_sat(dag, root, decision_bound=MAX_DECISIONS):
    stats = {}
    try:
        dag.check()
        clauses, index = tseitin(dag, root)
        stats.update({"CNF_variables": len(index), "CNF_initial_clauses": len(clauses)})
        solver = Solver(clauses, len(index), dag.deadline, decision_bound)
        result = solver.solve()
        stats.update({"decisions": solver.decisions, "conflicts": solver.conflicts,
                      "learned_clauses": len(solver.certificate),
                      "resolution_steps": solver.resolutions})
        if result["status"] == "UNSAT":
            replayed = verify_resolution(clauses, result["certificate"], result["terminal"], dag.deadline)
            return {"status": "PROVED_BOOLEAN_CNF", **stats,
                    "resolution_certificate": result["certificate"],
                    "terminal_empty_clause_derivation": result["terminal"],
                    "independently_replayed_resolution_steps": replayed,
                    "counterexample": None}
        assignment = result["assignment"]
        witness = {node // 2 - 1: int(assignment[var] == 1)
                   for node, var in index.items() if node // 2 <= dag.inputs}
        if dag.evaluate(root, witness) != 1:
            raise ValueError("CNF SAT witness fails original Boolean DAG")
        dag.check()
        return {"status": "DISPROVED_UNDER_RECORDED_ASSUMPTIONS", **stats,
                "counterexample": witness, "counterexample_original_DAG_evaluation": 1,
                "CNF_assignment": assignment}
    except (BoundReached, MemoryError, RecursionError) as exc:
        return {"status": "UNKNOWN", "reason": str(exc) if isinstance(exc, BoundReached)
                else type(exc).__name__, **stats, "counterexample": None}


def run(graph, pairs, spec):
    groups = [g for g in spec["onehot_gold"] if g["name"] == "alu_ctrl_e"]
    if len(groups) != 1 or len(groups[0]["gold"]) != 14:
        raise ValueError("Require all 14 exact current ALU group bits")
    group = groups[0]
    reset = {"reset_n": 1, "lec_q_p19088": 1, "lec_q_p19089": 1}
    dnames = {i: f"lec_d_p{k:05d}" for k, (i, _) in enumerate(pairs["pairs"])}
    dnames.update({i: f"lec_d_g{k:05d}" for k, i in enumerate(pairs["gold_only"])})
    if not set(dnames.values()) <= set(graph["output_names"]):
        raise ValueError("Every raw gold D output is required")
    results = []
    for active in range(14):
        assignments = case_conditions(graph, pairs, group, active, reset)
        dag = DAG(graph["inputs"], time.monotonic() + SECONDS_PER_CASE)
        try:
            outputs = dag.cofactor(graph, assignments)
            values = [outputs[dnames[i]] for i in group["gold"]]
            decision = decide_sat(dag, dag.onehot_violation(values))
            if decision["counterexample"] is not None:
                witness = decision["counterexample"]
                full = {i: 0 for i in range(graph["inputs"])}
                full.update(witness)
                code = [dag.evaluate(value, full) for value in values]
                if sum(code) == 1:
                    raise ValueError("SAT witness is not a one-hot violation")
                decision["next_state_counterexample_code"] = code
                decision["counterexample_other_free_inputs_default"] = 0
                decision["counterexample"] = {graph["input_names"][i]: v
                                              for i, v in sorted(witness.items())}
        except (BoundReached, MemoryError, RecursionError) as exc:
            decision = {"status": "UNKNOWN", "reason": str(exc), "counterexample": None}
        results.append({"group": group["name"], "active_current_bit": active,
                        "group_gold_indices": group["gold"], "assignments": assignments,
                        **decision})
        print(group["name"], active, decision["status"], flush=True)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--controls", required=True)
    args = parser.parse_args()
    out, controls = Path(args.out).resolve(), Path(args.controls).resolve()
    if not out.is_relative_to(ROOT) or out.exists() or not controls.is_relative_to(ROOT):
        raise ValueError("New output and controls must be in research")
    memory = enforce_process_memory()
    ctrl = json.loads(controls.read_text())
    if ctrl["status"] != "PASS_BOUNDED_CNF_CHECKER_CONTROLS":
        raise ValueError("Validated current SAT controls are required")
    for rel, digest in ctrl["source_sha256"].items():
        if sha(ROOT / rel) != digest:
            raise ValueError("SAT checker changed since controls")
    paths = [ROOT / p for p in ("asic/equiv/lec/gold_god_r14.aig",
                               "asic/equiv/lec/pairsAR14.json", "asic/equiv/lec/AR14_spec.json",
                               "results/dm_alu_sat_hypothesis_20261010.md",
                               "scripts/verification/lec_reset_base.py",
                               "scripts/verification/lec_onehot_boolean.py",
                               "scripts/verification/lec_onehot_sat.py")]
    paths.append(controls)
    hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    graph = read_aig_bytes(paths[0].read_bytes())
    pairs, spec = json.loads(paths[1].read_text()), json.loads(paths[2].read_text())
    results = run(graph, pairs, spec)
    if any(sha(ROOT / p) != digest for p, digest in hashes.items()):
        raise ValueError("Input changed during exact CNF execution")
    counts = {status: sum(r["status"] == status for r in results) for status in
              ("PROVED_BOOLEAN_CNF", "DISPROVED_UNDER_RECORDED_ASSUMPTIONS", "UNKNOWN")}
    j = {"status": "BOUNDED_EXACT_CNF_MODEL_SUBOBLIGATIONS_ONLY", "full_sequential_LEC": "OPEN",
         "memory_enforcement": memory, "input_sha256": hashes,
         "method": "Exact Tseitin CNF; watched-literal conflict-driven DPLL with resolution-checked learning and separately replayed empty-clause proof; SAT witnesses checked on original DAG",
         "scope": "Only the same recorded deasserted reset conditions and own current group code assigned; all other Q/input symbols remain free. Raw AIG undefined-zero abstraction gap remains OPEN.",
         "limits": {"process_memory_bytes": 512 * 1024 * 1024,
                    "seconds_per_obligation": SECONDS_PER_CASE, "decisions": MAX_DECISIONS,
                    "conflicts": MAX_CONFLICTS, "learned_clauses": MAX_LEARNED,
                    "resolution_steps": MAX_RESOLUTIONS,
                    "CNF_variables": MAX_VARIABLES, "initial_CNF_clauses": MAX_CLAUSES},
         "counts": counts, "obligations": results, "external_formal_tools_executed": False}
    out.write_text(json.dumps(j, indent=2) + "\n", encoding="ascii")
    print(json.dumps(counts), flush=True)


if __name__ == "__main__":
    main()
