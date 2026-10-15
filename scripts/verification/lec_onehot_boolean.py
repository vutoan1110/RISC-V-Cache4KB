"""Bounded exact ROBDD checks for named current DM one-hot transition cones.

The raw AIG's unassigned inputs remain independent Boolean symbols. Only the
recorded deasserted-reset conditions and the group's own current code are fixed.
This checks a Boolean-model induction sub-obligation, never complete chip LEC.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import time

from lec_reset_base import check_pairs, read_aig_bytes

ROOT = Path(__file__).resolve().parents[2]
MAX_BYTES = 512 * 1024 * 1024
MAX_SUPPORT = 128
MAX_BDD_NODES = 65_536
MAX_APPLY_CACHE = 131_072
SECONDS_PER_CASE = 10.0
_MEMORY_JOB = None


class BoundReached(Exception):
    pass


def enforce_process_memory():
    """A kernel memory limit on this proof process only; no global settings."""
    global _MEMORY_JOB
    if os.name != "nt":
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (MAX_BYTES, MAX_BYTES))
        return "RLIMIT_AS=512MiB"
    from ctypes import wintypes as wt

    class Basic(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64),
                    ("PerJobUserTimeLimit", ctypes.c_int64),
                    ("LimitFlags", wt.DWORD),
                    ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t),
                    ("ActiveProcessLimit", wt.DWORD),
                    ("Affinity", ctypes.c_size_t),
                    ("PriorityClass", wt.DWORD), ("SchedulingClass", wt.DWORD)]

    class IO(ctypes.Structure):
        _fields_ = [(name, ctypes.c_uint64) for name in
                    ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                     "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

    class Extended(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", Basic), ("IoInfo", IO),
                    ("ProcessMemoryLimit", ctypes.c_size_t),
                    ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t),
                    ("PeakJobMemoryUsed", ctypes.c_size_t)]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wt.LPCWSTR]
    kernel.CreateJobObjectW.restype = wt.HANDLE
    kernel.SetInformationJobObject.argtypes = [wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD]
    kernel.SetInformationJobObject.restype = wt.BOOL
    kernel.GetCurrentProcess.restype = wt.HANDLE
    kernel.AssignProcessToJobObject.argtypes = [wt.HANDLE, wt.HANDLE]
    kernel.AssignProcessToJobObject.restype = wt.BOOL
    handle = kernel.CreateJobObjectW(None, None)
    if not handle:
        raise OSError(ctypes.get_last_error(), "Create proof process memory job")
    info = Extended()
    info.BasicLimitInformation.LimitFlags = 0x100  # PROCESS_MEMORY only; no kill-on-close.
    info.ProcessMemoryLimit = MAX_BYTES
    if not kernel.SetInformationJobObject(handle, 9, ctypes.byref(info), ctypes.sizeof(info)) or \
            not kernel.AssignProcessToJobObject(handle, kernel.GetCurrentProcess()):
        raise OSError(ctypes.get_last_error(), "Enforce proof process memory bound")
    _MEMORY_JOB = handle
    return "Windows per-process JobObject commit limit=512MiB"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()


class DAG:
    def __init__(self, inputs, deadline):
        self.inputs = inputs
        self.deadline = deadline
        self.unique = {}
        self.nodes = {}
        self.calls = 0

    def check(self):
        if time.monotonic() > self.deadline:
            raise BoundReached("TIME_BOUND")

    def AND(self, a, b):
        self.calls += 1
        if self.calls % 1024 == 0:
            self.check()
        if a == 0 or b == 0 or a == (b ^ 1):
            return 0
        if a == 1 or a == b:
            return b
        if b == 1:
            return a
        key = min(a, b), max(a, b)
        if key not in self.unique:
            literal = 2 * (self.inputs + len(self.unique) + 1)
            self.unique[key] = literal
            self.nodes[literal] = key
        return self.unique[key]

    def OR(self, a, b):
        return self.AND(a ^ 1, b ^ 1) ^ 1

    def cofactor(self, graph, assignments):
        named = dict(zip(graph["input_names"], range(graph["inputs"])))
        if not set(assignments) <= named.keys() or any(type(v) is not int or v not in (0, 1)
                                                      for v in assignments.values()):
            raise ValueError("Unknown/non-Boolean cofactor input")
        values = [0] + [assignments.get(name, 2 * (i + 1))
                        for i, name in enumerate(graph["input_names"])]
        for a, b in graph["ands"]:
            values.append(self.AND(values[a >> 1] ^ (a & 1), values[b >> 1] ^ (b & 1)))
        return {name: values[x >> 1] ^ (x & 1)
                for name, x in zip(graph["output_names"], graph["outputs"])}

    def onehot_violation(self, values):
        if not values:
            raise ValueError("Empty one-hot output group")
        none, two = 1, 0
        for value in values:
            none = self.AND(none, value ^ 1)
        for i, value in enumerate(values):
            for other in values[:i]:
                two = self.OR(two, self.AND(value, other))
        return self.OR(none, two)

    def cone(self, root):
        reached, support, todo = set(), set(), [root & ~1]
        while todo:
            if len(reached) % 1024 == 0:
                self.check()
            value = todo.pop()
            if not value or value in reached:
                continue
            reached.add(value)
            if value in self.nodes:
                todo.extend(x & ~1 for x in self.nodes[value])
            elif 1 <= value // 2 <= self.inputs:
                support.add(value // 2 - 1)
            else:
                raise ValueError("Cone contains an unclassified Boolean literal")
        return reached - {2 * (i + 1) for i in support}, support

    def evaluate(self, root, assignment):
        cone, support = self.cone(root)
        if not support <= assignment.keys():
            raise ValueError("Counterexample does not bind every cone input")
        values = {0: 0, **{2 * (i + 1): assignment[i] for i in support}}
        for node in sorted(cone):
            a, b = self.nodes[node]
            values[node] = (values[a & ~1] ^ (a & 1)) & (values[b & ~1] ^ (b & 1))
        return values[root & ~1] ^ (root & 1)


class BDD:
    """Ordered reduced BDD; node IDs0/1 are false/true, IDs>=2 triples."""
    def __init__(self, order, deadline, max_nodes=MAX_BDD_NODES, max_cache=MAX_APPLY_CACHE):
        self.order = {variable: rank for rank, variable in enumerate(order)}
        self.nodes = [None, None]
        self.unique = {}
        self.cache = {}
        self.deadline = deadline
        self.max_nodes = max_nodes
        self.max_cache = max_cache
        self.calls = 0

    def check(self):
        self.calls += 1
        if self.calls % 256 == 0 and time.monotonic() > self.deadline:
            raise BoundReached("TIME_BOUND")

    def mk(self, rank, low, high):
        self.check()
        if low == high:
            return low
        key = rank, low, high
        if key not in self.unique:
            if len(self.nodes) - 2 >= self.max_nodes:
                raise BoundReached("BDD_NODE_BOUND")
            self.unique[key] = len(self.nodes)
            self.nodes.append(key)
        return self.unique[key]

    def var(self, variable):
        return self.mk(self.order[variable], 0, 1)

    def NOT(self, node):
        if node < 2:
            return 1 - node
        # Same exact apply engine avoids a second unbounded complement cache.
        return self.apply("xor", node, 1)

    def apply(self, operator, a, b):
        self.check()
        if a > b:
            a, b = b, a
        if operator == "and":
            if a == 0:
                return 0
            if a == 1 or a == b:
                return b
        elif operator == "xor":
            if a == 0:
                return b
            if a == b:
                return 0
            if a == 1 and b == 1:
                return 0
        else:
            raise ValueError("Unsupported BDD operation")
        key = operator, a, b
        if key in self.cache:
            return self.cache[key]
        ranka = self.nodes[a][0] if a >= 2 else float("inf")
        rankb = self.nodes[b][0] if b >= 2 else float("inf")
        rank = min(ranka, rankb)
        if rank == float("inf"):
            return (a & b) if operator == "and" else (a ^ b)
        alow, ahigh = self.nodes[a][1:] if ranka == rank else (a, a)
        blow, bhigh = self.nodes[b][1:] if rankb == rank else (b, b)
        low = self.apply(operator, alow, blow)
        high = self.apply(operator, ahigh, bhigh)
        result = self.mk(rank, low, high)
        if len(self.cache) >= self.max_cache:
            raise BoundReached("BDD_APPLY_CACHE_BOUND")
        self.cache[key] = result
        return result

    def witness(self, root):
        if not root:
            raise ValueError("Zero BDD has no satisfying witness")
        assignment = {variable: 0 for variable in self.order}
        by_rank = {rank: variable for variable, rank in self.order.items()}
        while root >= 2:
            rank, low, high = self.nodes[root]
            if low:
                assignment[by_rank[rank]], root = 0, low
            else:
                assignment[by_rank[rank]], root = 1, high
        assert root == 1
        return assignment


def decide(dag, root, max_support=MAX_SUPPORT, max_nodes=MAX_BDD_NODES,
           max_cache=MAX_APPLY_CACHE):
    """Exact proof or a re-evaluated witness; every resource exception is UNKNOWN."""
    stats = {}
    try:
        dag.check()
        cone, support = dag.cone(root)
        stats.update({"cone_AND_nodes": len(cone), "support_bits": len(support)})
        if len(support) > max_support:
            raise BoundReached("SUPPORT_BOUND")
        bdd = BDD(sorted(support), dag.deadline, max_nodes, max_cache)
        converted = {0: 0, **{2 * (i + 1): bdd.var(i) for i in sorted(support)}}
        def literal(value):
            result = converted[value & ~1]
            return bdd.NOT(result) if value & 1 else result
        for node in sorted(cone):
            a, b = dag.nodes[node]
            converted[node] = bdd.apply("and", literal(a), literal(b))
        result = literal(root)
        stats.update({"BDD_nodes": len(bdd.nodes) - 2, "apply_cache_entries": len(bdd.cache)})
        if result == 0:
            return {"status": "PROVED_BOOLEAN_COFACTOR", **stats,
                    "counterexample": None}
        witness = bdd.witness(result)
        if dag.evaluate(root, witness) != 1:
            raise ValueError("BDD witness fails independent original DAG evaluation")
        return {"status": "DISPROVED_UNDER_RECORDED_ASSUMPTIONS", **stats,
                "counterexample": witness, "counterexample_original_DAG_evaluation": 1}
    except (BoundReached, MemoryError, RecursionError) as exc:
        return {"status": "UNKNOWN", "reason": str(exc) if isinstance(exc, BoundReached)
                else type(exc).__name__, **stats, "counterexample": None}


def case_conditions(graph, pairs, group, active, reset_assignments):
    if not group["gold"] or len(set(group["gold"])) != len(group["gold"]) or \
            not 0 <= active < len(group["gold"]):
        raise ValueError("Invalid one-hot group/code")
    check_pairs(pairs)
    q = {i: f"lec_q_p{k:05d}" for k, (i, _) in enumerate(pairs["pairs"])}
    q.update({i: f"lec_q_g{k:05d}" for k, i in enumerate(pairs["gold_only"])})
    if reset_assignments != {"reset_n": 1, "lec_q_p19088": 1, "lec_q_p19089": 1}:
        raise ValueError("Reset conditions differ from the explicit current-model audit")
    inputs = set(graph["input_names"])
    if any(name.startswith("lec_oh_") for name in inputs):
        raise ValueError("Raw unrestricted Q graph required")
    if any(i not in q for i in group["gold"]):
        raise ValueError("FSM group bit absent from mapped raw state")
    assignments = {**reset_assignments, **{q[i]: int(bit == active)
                                          for bit, i in enumerate(group["gold"])}}
    if len(assignments) != len(reset_assignments) + len(group["gold"]) or not set(assignments) <= inputs:
        raise ValueError("Missing or overlapping group/reset inputs")
    return assignments


def run(graph, pairs, spec):
    wanted = {"axi_last_grant": 3, "axi_source": 3, "alu_ctrl_e": 14}
    selected = [g for g in spec["onehot_gold"] if g["name"] in wanted]
    if {g["name"]: len(g["gold"]) for g in selected} != wanted or len(selected) != 3:
        raise ValueError("Require the complete exact20 current target obligations")
    used = set()
    for group in selected:
        if used & set(group["gold"]):
            raise ValueError("FSM groups overlap")
        used.update(group["gold"])
    reset = {"reset_n": 1, "lec_q_p19088": 1, "lec_q_p19089": 1}
    dnames = {i: f"lec_d_p{k:05d}" for k, (i, _) in enumerate(pairs["pairs"])}
    dnames.update({i: f"lec_d_g{k:05d}" for k, i in enumerate(pairs["gold_only"])})
    if not set(dnames.values()) <= set(graph["output_names"]):
        raise ValueError("Every raw gold D output is required")
    results = []
    for group in selected:
        for active in range(len(group["gold"])):
            assignments = case_conditions(graph, pairs, group, active, reset)
            dag = DAG(graph["inputs"], time.monotonic() + SECONDS_PER_CASE)
            try:
                outputs = dag.cofactor(graph, assignments)
                values = [outputs[dnames[i]] for i in group["gold"]]
                decision = decide(dag, dag.onehot_violation(values))
                if decision["counterexample"] is not None:
                    witness = decision["counterexample"]
                    complete_witness = {i: 0 for i in range(graph["inputs"])}
                    complete_witness.update(witness)
                    code = [dag.evaluate(value, complete_witness) for value in values]
                    if sum(code) == 1:
                        raise ValueError("Counterexample is not a real one-hot violation")
                    decision["next_state_counterexample_code"] = code
                    decision["counterexample_other_free_inputs_default"] = 0
                    decision["counterexample"] = {graph["input_names"][i]: v
                                                  for i, v in sorted(witness.items())}
            except (BoundReached, MemoryError, RecursionError) as exc:
                decision = {"status": "UNKNOWN", "reason": str(exc), "counterexample": None}
            results.append({"group": group["name"], "active_current_bit": active,
                            "group_gold_indices": group["gold"],
                            "assignments": assignments, **decision})
            print(group["name"], active, decision["status"], flush=True)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if not out.is_relative_to(ROOT) or out.exists():
        raise ValueError("Output must be a new path in the research workspace")
    memory = enforce_process_memory()
    paths = [ROOT / p for p in ("asic/equiv/lec/gold_god_r14.aig",
                               "asic/equiv/lec/pairsAR14.json",
                               "asic/equiv/lec/AR14_spec.json",
                               "results/dm_reset_base_structural_20261010_p1.json",
                               "results/lec_model_initialization_audit_20261010.json",
                               "scripts/verification/lec_reset_base.py",
                               "scripts/verification/lec_onehot_boolean.py")]
    hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    graph = read_aig_bytes(paths[0].read_bytes())
    pairs, spec = json.loads(paths[1].read_text()), json.loads(paths[2].read_text())
    results = run(graph, pairs, spec)
    if any(sha(ROOT / p) != digest for p, digest in hashes.items()):
        raise ValueError("Input changed during bounded exact Boolean execution")
    counts = {status: sum(r["status"] == status for r in results) for status in
              ("PROVED_BOOLEAN_COFACTOR", "DISPROVED_UNDER_RECORDED_ASSUMPTIONS", "UNKNOWN")}
    record = {"status": "BOUNDED_EXACT_BOOLEAN_MODEL_SUBOBLIGATIONS_ONLY",
              "full_sequential_LEC": "OPEN",
              "hypothesis": "Exact Boolean reduction resolves structural UNKNOWN without additional assumptions",
              "method": "Canonical ordered reduced BDD; every witness re-evaluated on the original cofactored AND/NOT DAG",
              "memory_enforcement": memory,
              "limits": {"process_memory_bytes": MAX_BYTES, "support_bits": MAX_SUPPORT,
                         "BDD_nodes": MAX_BDD_NODES, "apply_cache_entries": MAX_APPLY_CACHE,
                         "seconds_per_obligation": SECONDS_PER_CASE},
              "scope": "Raw Boolean AIG model after its original setundef-zero conversion. Undefined-value/source-model gap remains OPEN. Only deasserted external/internal reset and the selected group's own code are fixed; other states and inputs are free.",
              "not_an_RTL_defect_claim": "A counterexample can demonstrate a missing reachability/state premise; it must not be attributed to reachable hardware without further proof.",
              "input_sha256": hashes, "counts": counts, "obligations": results}
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="ascii")
    print(json.dumps(counts), flush=True)


if __name__ == "__main__":
    main()
