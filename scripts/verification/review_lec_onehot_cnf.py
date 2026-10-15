"""Independent bounded review of saved raw-model CNF proofs.

The AIG parser, cofactor DAG, CNF encoder, resolution replay, and brute-force
oracle below do not import the author's implementations. The frozen SAT solver
and encoder are imported only as systems under test on small finite controls
and on a read-only adapter of the independently reconstructed cone.
No SoC SAT solve, frontend, WSL process, or source modification is performed.
"""
from __future__ import annotations

import argparse
from array import array
import copy
import ctypes
import gc
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
CAP = 256 * 1024 * 1024
FROZEN_SAT_SHA = "acf21bb52b4dd019021dd3c39aed34cf6c8874bd6e55919aefaa8fe2b1e468ba"
_JOB = None


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def content_digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode("ascii")).hexdigest()


def memory_cap():
    global _JOB
    if os.name != "nt":
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (CAP, CAP))
        return "RLIMIT_AS=256MiB"
    from ctypes import wintypes as w

    class Basic(ctypes.Structure):
        _fields_ = [("a", ctypes.c_int64), ("b", ctypes.c_int64), ("flags", w.DWORD),
                    ("lo", ctypes.c_size_t), ("hi", ctypes.c_size_t),
                    ("active", w.DWORD), ("affinity", ctypes.c_size_t),
                    ("priority", w.DWORD), ("schedule", w.DWORD)]

    class IO(ctypes.Structure):
        _fields_ = [("x" + str(i), ctypes.c_uint64) for i in range(6)]

    class Limits(ctypes.Structure):
        _fields_ = [("basic", Basic), ("io", IO), ("process", ctypes.c_size_t),
                    ("job", ctypes.c_size_t), ("peakp", ctypes.c_size_t),
                    ("peakj", ctypes.c_size_t)]

    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
    k.CreateJobObjectW.restype = w.HANDLE
    k.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
    k.SetInformationJobObject.restype = w.BOOL
    k.GetCurrentProcess.restype = w.HANDLE
    k.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
    k.AssignProcessToJobObject.restype = w.BOOL
    job = k.CreateJobObjectW(None, None)
    limits = Limits()
    limits.basic.flags, limits.process = 0x100, CAP
    if not job or not k.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)) \
            or not k.AssignProcessToJobObject(job, k.GetCurrentProcess()):
        raise OSError(ctypes.get_last_error(), "Cannot bound independent review process")
    _JOB = job
    return "Windows per-process JobObject commit limit=256MiB"


def peak_memory():
    if os.name != "nt":
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    from ctypes import wintypes as w

    class Counters(ctypes.Structure):
        _fields_ = [("cb", w.DWORD), ("faults", w.DWORD)] + [
            (x, ctypes.c_size_t) for x in ("peakws", "ws", "peakpaged", "paged",
                                         "peaknonpaged", "nonpaged", "pagefile", "peakpagefile")]
    c = Counters()
    c.cb = ctypes.sizeof(c)
    k = ctypes.WinDLL("kernel32")
    k.GetCurrentProcess.restype = w.HANDLE
    p = ctypes.WinDLL("psapi")
    p.GetProcessMemoryInfo.argtypes = [w.HANDLE, ctypes.c_void_p, w.DWORD]
    if not p.GetProcessMemoryInfo(k.GetCurrentProcess(), ctypes.byref(c), c.cb):
        raise OSError("Peak-memory query failed")
    return {"peak_working_set_bytes": c.peakws, "peak_pagefile_bytes": c.peakpagefile}


def read_graph(path):
    """Separate streaming binary-AIGER implementation with compact fanin arrays."""
    first, second = array("I"), array("I")
    with Path(path).open("rb") as f:
        fields = f.readline().split()
        if len(fields) != 6 or fields[0] != b"aig":
            raise ValueError("Combinational binary AIGER required")
        maximum, ni, nl, no, na = map(int, fields[1:])
        if nl or maximum != ni + na or min(maximum, ni, no, na) < 0 or maximum > 2_000_000:
            raise ValueError("Invalid or excessive graph header")
        outputs = [int(f.readline()) for _ in range(no)]
        if any(not 0 <= x <= 2 * maximum + 1 for x in outputs):
            raise ValueError("Output outside graph")

        def number():
            result = 0
            for shift in range(0, 36, 7):
                raw = f.read(1)
                if not raw:
                    raise ValueError("Truncated AIG delta")
                byte = raw[0]
                result += (byte % 128) << shift
                if byte < 128:
                    return result
            raise ValueError("Oversized AIG delta")

        for pos in range(na):
            left = 2 * (ni + pos + 1) - number()
            right = left - number()
            if not 0 <= right <= left < 2 * (ni + pos + 1):
                raise ValueError("Non-topological fanin")
            first.append(left)
            second.append(right)
        table = {"i": {}, "o": {}}
        for raw in f:
            line = raw.rstrip(b"\r\n")
            if line == b"c":
                break
            if not line:
                continue
            tag, name = line.split(b" ", 1)
            kind, index = tag[:1].decode("ascii"), int(tag[1:])
            if kind not in table or index in table[kind] or not name:
                raise ValueError("Bad symbol table")
            table[kind][index] = name.decode("latin1")
    for kind, size in (("i", ni), ("o", no)):
        if set(table[kind]) != set(range(size)) or len(set(table[kind].values())) != size:
            raise ValueError("Incomplete/duplicate graph names")
    return {"inputs": ni, "first": first, "second": second, "outputs": outputs,
            "input_names": [table["i"][i] for i in range(ni)],
            "output_names": [table["o"][i] for i in range(no)]}


class IndependentGraph:
    """Canonical complemented-edge DAG, independently built from raw fanins."""
    def __init__(self, graph, assumptions):
        self.inputs = graph["inputs"]
        self.unique = {}
        self.left, self.right = array("I"), array("I")
        names = graph["input_names"]
        if not set(assumptions) <= set(names) or any(type(v) is not int or v not in (0, 1)
                                                   for v in assumptions.values()):
            raise ValueError("Invalid raw-model assumptions")
        values = array("I", [0])
        values.extend(assumptions.get(name, 2 * (i + 1)) for i, name in enumerate(names))
        for a, b in zip(graph["first"], graph["second"]):
            values.append(self.and_gate(values[a // 2] ^ (a % 2), values[b // 2] ^ (b % 2)))
        self.outputs = {name: values[x // 2] ^ (x % 2)
                        for name, x in zip(graph["output_names"], graph["outputs"])}

    def and_gate(self, a, b):
        if not a or not b or a ^ b == 1:
            return 0
        if a == 1 or a == b:
            return b
        if b == 1:
            return a
        key = (a, b) if a < b else (b, a)
        old = self.unique.get(key)
        if old is None:
            old = 2 * (self.inputs + len(self.left) + 1)
            self.unique[key] = old
            self.left.append(key[0])
            self.right.append(key[1])
        return old

    def or_gate(self, a, b):
        return self.and_gate(a ^ 1, b ^ 1) ^ 1

    def violation(self, code):
        no_active, multiple = 1, 0
        for x in code:
            no_active = self.and_gate(no_active, x ^ 1)
        for i, x in enumerate(code):
            for y in code[:i]:
                multiple = self.or_gate(multiple, self.and_gate(x, y))
        return self.or_gate(no_active, multiple)

    def children(self, node):
        pos = node // 2 - self.inputs - 1
        if not 0 <= pos < len(self.left):
            raise ValueError("Unknown internal node")
        return self.left[pos], self.right[pos]

    def cone(self, root):
        internal, support, seen = set(), set(), set()
        stack = [root // 2 * 2]
        while stack:
            x = stack.pop()
            if not x or x in seen:
                continue
            seen.add(x)
            if x <= 2 * self.inputs:
                support.add(x // 2 - 1)
            else:
                internal.add(x)
                stack.extend(y // 2 * 2 for y in self.children(x))
        return internal, support

    def evaluate(self, root, binding):
        internal, support = self.cone(root)
        if not support <= set(binding):
            raise ValueError("Incomplete independent witness")
        value = {0: 0, **{2 * (i + 1): binding[i] for i in support}}
        for node in sorted(internal):
            a, b = self.children(node)
            value[node] = (value[a // 2 * 2] ^ (a % 2)) & (value[b // 2 * 2] ^ (b % 2))
        return value[root // 2 * 2] ^ (root % 2)


def encode(model, root):
    """Exact y iff a AND b, with signed constants rather than Python bools."""
    internal, support = model.cone(root)
    ordered = sorted(internal | {2 * (i + 1) for i in support})
    mapping = {node: i + 1 for i, node in enumerate(ordered)}
    clauses = []

    def term(aig_literal):
        if aig_literal < 2:
            return ("constant", aig_literal)
        return ("variable", mapping[aig_literal // 2 * 2] * (-1 if aig_literal % 2 else 1))

    def inverted(item):
        kind, value = item
        return kind, 1 - value if kind == "constant" else -value

    def add(items):
        if any(kind == "constant" and value == 1 for kind, value in items):
            return
        lits = set(value for kind, value in items if kind == "variable")
        if any(-x in lits for x in lits):
            return
        clauses.append(tuple(sorted(lits, key=lambda x: (abs(x), x))))

    for node in sorted(internal):
        a, b = map(term, model.children(node))
        y = ("variable", mapping[node])
        add([inverted(y), a])
        add([inverted(y), b])
        add([y, inverted(a), inverted(b)])
    add([term(root)])
    return clauses, mapping


def replay(initial, learned, terminal):
    """Set-theoretic resolution verifier with no call to the author's kernel."""
    clauses = []
    maximum = max((abs(x) for clause in initial for x in clause), default=0)
    for clause in initial:
        if any(type(x) is not int or not 1 <= abs(x) <= maximum for x in clause) \
                or len(set(clause)) != len(clause) or any(-x in clause for x in clause):
            raise ValueError("Malformed independent initial clause")
        clauses.append(frozenset(clause))
    count = 0

    def derive(record):
        nonlocal count
        parent = record["parent"]
        if type(parent) is not int or parent < 0 or parent >= len(clauses):
            raise ValueError("Absent/future resolution parent")
        result = clauses[parent]
        for step in record["resolution"]:
            if type(step) not in (list, tuple) or len(step) != 2:
                raise ValueError("Malformed resolution step")
            reason, pivot = step
            if type(reason) is not int or not 0 <= reason < len(clauses) \
                    or type(pivot) is not int or not 1 <= pivot <= maximum:
                raise ValueError("Invalid reason or pivot")
            other = clauses[reason]
            positive = pivot in result and -pivot in other
            negative = -pivot in result and pivot in other
            if positive == negative:
                raise ValueError("No unique opposite pivot")
            result = frozenset(x for x in result.union(other) if abs(x) != pivot)
            if any(-x in result for x in result):
                raise ValueError("Tautological conflict resolvent")
            count += 1
            if count > 100_000:
                raise ValueError("Independent certificate step cap")
        return result

    for record in learned:
        saved = record["clause"]
        if any(type(x) is not int or not 1 <= abs(x) <= maximum for x in saved) \
                or len(set(saved)) != len(saved) or any(-x in saved for x in saved):
            raise ValueError("Malformed learned clause")
        actual = derive(record)
        if actual != frozenset(saved):
            raise ValueError("Incorrect learned resolution clause")
        clauses.append(actual)
    if derive(terminal):
        raise ValueError("Terminal derivation is not empty")
    return count


def mapping_names(pairs):
    for total, unique, column in ((len(pairs["gold"]), "gold_only", 0),
                                  (len(pairs["gate"]), "gate_only", 1)):
        linked = [link[column] for link in pairs["pairs"]]
        extra = pairs[unique]
        if any(type(x) is not int or not 0 <= x < total for x in linked + extra) \
                or len(set(linked)) != len(linked) or len(set(extra)) != len(extra) \
                or set(linked).intersection(extra) or set(linked).union(extra) != set(range(total)):
            raise ValueError("Non-bijective raw state partition")
    q = {gold: "lec_q_p%05d" % i for i, (gold, _) in enumerate(pairs["pairs"])}
    q.update({gold: "lec_q_g%05d" % i for i, gold in enumerate(pairs["gold_only"])})
    d = {gold: name.replace("lec_q_", "lec_d_", 1) for gold, name in q.items()}
    return q, d


def conditions(group, active, q):
    return {"reset_n": 1, "lec_q_p19088": 1, "lec_q_p19089": 1,
            **{q[gold]: int(i == active) for i, gold in enumerate(group["gold"])}}


def reject(call):
    try:
        call()
    except ValueError:
        return True
    raise ValueError("Negative control unexpectedly accepted")


def finite_controls(sat):
    rows, total, learned_total = [], 0, 0
    verdicts = {"SAT": 0, "UNSAT": 0}

    def brute(clauses, n):
        for mask in range(1 << n):
            if all(any(((mask >> (abs(x) - 1)) & 1) == int(x > 0) for x in c)
                   for c in clauses):
                return mask
        return None

    def check(clauses, n):
        nonlocal total, learned_total
        actual = sat.Solver(clauses, n, time.monotonic() + 2).solve()
        expected = brute(clauses, n)
        if (actual["status"] == "SAT") != (expected is not None):
            raise ValueError("Frozen solver differs from independent exhaustive oracle")
        if actual["status"] == "UNSAT":
            replay(clauses, actual["certificate"], actual["terminal"])
            learned_total += len(actual["certificate"])
        else:
            assignment = actual["assignment"]
            if len(assignment) != n + 1 or any(x not in (-1, 1) for x in assignment[1:]) \
                    or not all(any(assignment[abs(x)] == (1 if x > 0 else -1) for x in c)
                               for c in clauses):
                raise ValueError("SAT assignment fails independent complete-clause check")
        total += 1
        verdicts[actual["status"]] += 1
        return actual

    pool = [(1,), (-1,), (2,), (-2,), (1, 2), (1, -2), (-1, 2), (-1, -2)]
    for mask in range(256):
        check([pool[i] for i in range(8) if mask >> i & 1], 2)
    check([[]], 0)
    check([], 0)
    rng = random.Random(0xA19C20261010)
    for i in range(2400):
        n = 1 + i % 8
        clauses = []
        for _ in range(rng.randrange(0, 36)):
            width = min(n, rng.randrange(2, 5)) if i % 2 else rng.randrange(1, n + 1)
            picked = rng.sample(range(1, n + 1), width)
            rng.shuffle(picked)
            clauses.append(tuple(x if rng.getrandbits(1) else -x for x in picked))
        check(clauses, n)
    pigeon = [[1, 2], [3, 4], [5, 6], [-1, -3], [-1, -5], [-3, -5],
              [-2, -4], [-2, -6], [-4, -6]]
    proof = check(pigeon, 6)
    if not proof.get("certificate") or not learned_total or not all(verdicts.values()):
        raise ValueError("Finite controls failed to exercise learned UNSAT and both verdicts")
    rows.append({"name": "Independent exhaustive oracle and resolution replay",
                 "cases": total, "verdicts": verdicts, "learned_clauses_replayed": learned_total,
                 "random_seed": "0xA19C20261010", "random_cases": 2400,
                 "maximum_random_variables": 8, "status": "PASS"})

    corruptions = {
        "future_parent": lambda p: p["certificate"][0].update(parent=99999),
        "wrong_learned_clause": lambda p: p["certificate"][0].update(clause=[1]),
        "wrong_pivot": lambda p: p["certificate"][0]["resolution"][0].__setitem__(1, 99999),
        "boolean_reason": lambda p: p["certificate"][0]["resolution"][0].__setitem__(0, True),
        "negative_pivot": lambda p: p["certificate"][0]["resolution"][0].__setitem__(1, -1),
        "nonempty_terminal": lambda p: p["terminal"].update(parent=0, resolution=[]),
        "boolean_learned_literal": lambda p: p["certificate"][0].update(clause=[True]),
        "duplicate_learned_literal": lambda p: p["certificate"][0].update(clause=[1, 1]),
        "tautological_learned_clause": lambda p: p["certificate"][0].update(clause=[1, -1]),
    }
    for name, mutate in corruptions.items():
        bad = copy.deepcopy(proof)
        mutate(bad)
        reject(lambda: replay(pigeon, bad["certificate"], bad["terminal"]))
        rows.append({"name": "Independent verifier rejects " + name, "status": "PASS"})

    for clause in ([0], [True], [1, 1], [1, -1], [9]):
        reject(lambda clause=clause: sat.Solver([clause], 8, time.monotonic() + 2))
    rows.append({"name": "Frozen solver malformed-input rejections", "cases": 5, "status": "PASS"})
    # Small author DAG is a test subject; truth values are direct formulas.
    dag = sat.DAG(4, time.monotonic() + 10)
    a, b, c, d = 2, 4, 6, 8
    xor = dag.OR(dag.AND(a, b ^ 1), dag.AND(a ^ 1, b))
    roots = [(0, lambda v: 0), (1, lambda v: 1), (a, lambda v: v[0]),
             (a ^ 1, lambda v: 1 - v[0]), (dag.AND(a, b), lambda v: v[0] & v[1]),
             (dag.OR(a, b), lambda v: v[0] | v[1]), (xor, lambda v: v[0] ^ v[1]),
             (dag.AND(xor, dag.OR(c, d)), lambda v: (v[0] ^ v[1]) & (v[2] | v[3])),
             (dag.onehot_violation([a, b, c, d]), lambda v: int(sum(v) != 1))]
    encoding_cases = 0
    for root, formula in roots:
        clauses, index = sat.tseitin(dag, root)
        for bits in itertools.product((0, 1), repeat=4):
            fixed = list(clauses) + [(var if bits[node // 2 - 1] else -var,)
                                     for node, var in index.items() if node <= 8]
            result = sat.Solver(fixed, len(index), time.monotonic() + 2).solve()
            if (result["status"] == "SAT") != bool(formula(bits)):
                raise ValueError("Frozen Tseitin semantics differs from independent Boolean formula")
            if result["status"] == "UNSAT":
                replay(fixed, result["certificate"], result["terminal"])
            encoding_cases += 1
    rows.append({"name": "Encoder complements/constants and direct Boolean formula truth tables",
                 "roots": len(roots), "assignments": encoding_cases, "status": "PASS"})

    limit_rows = []
    def bound(label, call, expected):
        try:
            call()
        except sat.BoundReached as e:
            if str(e) != expected:
                raise
            limit_rows.append(label)
        else:
            raise ValueError("Bound did not stop frozen solver: " + label)
    bound("expired_deadline", lambda: sat.Solver([], 0, time.monotonic() - 1).solve(), "TIME_BOUND")
    bound("zero_decision", lambda: sat.Solver([(1, 2)], 2, time.monotonic() + 2, 0).solve(), "DECISION_BOUND")
    for attr, expected, clauses, n in (("MAX_CONFLICTS", "CONFLICT_BOUND", [(1,), (-1,)], 1),
                                     ("MAX_LEARNED", "LEARNED_CLAUSE_BOUND", pigeon, 6),
                                     ("MAX_RESOLUTIONS", "RESOLUTION_BOUND", pigeon, 6),
                                     ("MAX_CLAUSES", "CNF_INPUT_BOUND", [(1,)], 1),
                                     ("MAX_VARIABLES", "CNF_INPUT_BOUND", [(1,)], 1)):
        prior = getattr(sat, attr)
        try:
            setattr(sat, attr, 0)
            bound(attr, lambda clauses=clauses, n=n: sat.Solver(clauses, n, time.monotonic() + 2).solve(), expected)
        finally:
            setattr(sat, attr, prior)
    small = sat.DAG(2, time.monotonic() + 2)
    unknown = sat.decide_sat(small, small.OR(2, 4), decision_bound=0)
    if unknown["status"] != "UNKNOWN" or unknown["reason"] != "DECISION_BOUND" or unknown["counterexample"] is not None:
        raise ValueError("Decision exhaustion was promoted to semantic verdict")
    rows.append({"name": "Bounds stop; public decision wrapper returns UNKNOWN",
                 "solver_bounds": limit_rows, "wrapper_checks": 1, "status": "PASS"})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    output = Path(args.out).resolve()
    report = output.with_suffix(".md")
    if output.exists() or report.exists() or not output.is_relative_to(ROOT):
        raise ValueError("Independent review requires new research outputs")
    enforcement = memory_cap()
    started = time.monotonic()
    inputs = ["asic/equiv/lec/gold_god_r14.aig", "asic/equiv/lec/pairsAR14.json",
              "asic/equiv/lec/AR14_spec.json", "scripts/verification/lec_onehot_sat.py",
              "scripts/verification/lec_onehot_boolean.py", "scripts/verification/lec_reset_base.py",
              "scripts/verification/check_lec_onehot_sat.py",
              "scripts/verification/check_lec_onehot_sat_model_fault.py",
              "results/lec_onehot_sat_controls_20261010.json",
              "results/dm_alu_onehot_cnf_20261010_p1.json", "results/dm_alu_onehot_cnf_20261010_p2.json",
              "results/dm_onehot_cnf_model_fault_20261010_p1.json",
              "results/dm_onehot_cnf_model_fault_20261010_p2.json",
              "scripts/verification/review_lec_onehot_cnf.py"]
    hashes = {p: digest(ROOT / p) for p in inputs}
    if hashes["scripts/verification/lec_onehot_sat.py"] != FROZEN_SAT_SHA:
        raise ValueError("Reviewed SAT source is not the authorised frozen kernel")
    author_controls = json.loads((ROOT / inputs[8]).read_text())
    if author_controls["status"] != "PASS_BOUNDED_CNF_CHECKER_CONTROLS" \
            or author_controls["control_count"] != 20 or len(author_controls["controls"]) != 20 \
            or any(r["status"] != "PASS" for r in author_controls["controls"]):
        raise ValueError("Author controls not complete")
    for rel, expected in author_controls["source_sha256"].items():
        if hashes[rel] != expected:
            raise ValueError("Author control source hash mismatch")
    import lec_onehot_sat as sat
    controls = finite_controls(sat)
    graph = read_graph(ROOT / inputs[0])
    pairs = json.loads((ROOT / inputs[1]).read_text())
    spec = json.loads((ROOT / inputs[2]).read_text())
    q, d = mapping_names(pairs)
    if any(name.startswith("lec_oh_") for name in graph["input_names"]) \
            or not set(d.values()) <= set(graph["output_names"]):
        raise ValueError("Graph is not unrestricted-Q with complete raw D outputs")
    groups = {g["name"]: g for g in spec["onehot_gold"]}
    alu = groups["alu_ctrl_e"]
    if len(alu["gold"]) != 14 or len(set(alu["gold"])) != 14:
        raise ValueError("Exact current14 ALU group required")
    receipts = [json.loads((ROOT / rel).read_text()) for rel in inputs[9:11]]
    if receipts[0] != receipts[1] or hashes[inputs[9]] != hashes[inputs[10]]:
        raise ValueError("Independent executions differ")
    for receipt in receipts:
        if receipt["status"] != "BOUNDED_EXACT_CNF_MODEL_SUBOBLIGATIONS_ONLY" \
                or receipt["full_sequential_LEC"] != "OPEN" \
                or receipt["counts"] != {"PROVED_BOOLEAN_CNF": 14,
                                         "DISPROVED_UNDER_RECORDED_ASSUMPTIONS": 0, "UNKNOWN": 0} \
                or len(receipt["obligations"]) != 14:
            raise ValueError("Proof receipt has incomplete or excessive scope")
        for rel, expected in receipt["input_sha256"].items():
            if digest(ROOT / rel) != expected:
                raise ValueError("Proof input hash mismatch")

    cases = []
    total_replayed = 0
    for active in range(14):
        assumptions = conditions(alu, active, q)
        if len(assumptions) != 17:
            raise ValueError("Selected own-group/reset assumptions overlap")
        model = IndependentGraph(graph, assumptions)
        values = [model.outputs[d[gold]] for gold in alu["gold"]]
        root = model.violation(values)
        clauses, index = encode(model, root)
        internal, support = model.cone(root)
        # Author encoder sees only the independent cone; no author cofactor/parser.
        class Adapter:
            nodes = {node: model.children(node) for node in internal}
            def cone(self, unused):
                if unused != root:
                    raise ValueError("Adapter wrong root")
                return internal, support
        author_clauses, author_index = sat.tseitin(Adapter(), root)
        if clauses != author_clauses or index != author_index:
            raise ValueError("Independent CNF clauses or variable map differ from frozen encoder")
        steps = []
        for pass_index, receipt in enumerate(receipts, 1):
            row = receipt["obligations"][active]
            if row["group"] != "alu_ctrl_e" or row["active_current_bit"] != active \
                    or row["group_gold_indices"] != alu["gold"] or row["assignments"] != assumptions \
                    or row["status"] != "PROVED_BOOLEAN_CNF" or row["counterexample"] is not None \
                    or row["CNF_variables"] != len(index) or row["CNF_initial_clauses"] != len(clauses) \
                    or row["learned_clauses"] != len(row["resolution_certificate"]):
                raise ValueError("Saved case assumptions, shape or count differ")
            count = replay(clauses, row["resolution_certificate"], row["terminal_empty_clause_derivation"])
            if count != row["resolution_steps"] or count != row["independently_replayed_resolution_steps"]:
                raise ValueError("Resolution step count differs")
            steps.append(count)
            total_replayed += count
        cases.append({"active_current_bit": active, "status": "PASS",
                      "assumptions": assumptions, "all_other_inputs_unassigned": True,
                      "CNF_variables": len(index), "CNF_clauses": len(clauses),
                      "free_support_bits": len(support), "cofactored_root_literal": root,
                      "CNF_sha256": content_digest(clauses),
                      "variable_map_sha256": content_digest(sorted(index.items())),
                      "encoder_clauses_and_map_equal": True, "paired_certificate_replay_steps": steps})
        del model, clauses, index, author_clauses, author_index, Adapter
        gc.collect()
        print("Independent ALU certificate replay", active, steps, flush=True)

    faults = [json.loads((ROOT / rel).read_text()) for rel in inputs[11:13]]
    if faults[0] != faults[1] or hashes[inputs[11]] != hashes[inputs[12]]:
        raise ValueError("Actual model fault controls are not byte/field equal")
    fault_cases = []
    for pass_index, receipt in enumerate(faults, 1):
        if receipt["status"] != "PASS_ACTUAL_RAW_MODEL_CNF_RARE_ONEHOT_FAULT_CONTROL":
            raise ValueError("Fault control not complete")
        for rel, expected in receipt["input_sha256"].items():
            if digest(ROOT / rel) != expected:
                raise ValueError("Fault-control source hash mismatch")
        group = groups[receipt["group"]]
        assumptions = conditions(group, receipt["active_current_bit"], q)
        if assumptions != receipt["assignments"]:
            raise ValueError("Fault assumptions differ from raw mapping")
        model = IndependentGraph(graph, assumptions)
        code = [model.outputs[d[gold]] for gold in group["gold"]]
        baseline_root = model.violation(code)
        baseline_clauses, baseline_index = encode(model, baseline_root)
        baseline = receipt["baseline"]
        if baseline["status"] != "PROVED_BOOLEAN_CNF" \
                or baseline["CNF_variables"] != len(baseline_index) \
                or baseline["CNF_initial_clauses"] != len(baseline_clauses):
            raise ValueError("Baseline fault-control CNF differs")
        steps = replay(baseline_clauses, baseline["resolution_certificate"],
                       baseline["terminal_empty_clause_derivation"])
        if steps != baseline["resolution_steps"]:
            raise ValueError("Fault-control baseline replay count differs")
        total_replayed += steps
        positions = {name: i for i, name in enumerate(graph["input_names"])}
        triggers = receipt["trigger_inputs"]
        if len(triggers) != 24 or len(set(triggers)) != 24 \
                or set(triggers).intersection(assumptions) or not set(triggers) <= set(positions):
            raise ValueError("Rare trigger is not24 unrestricted distinct raw inputs")
        rare = 1
        for name in triggers:
            rare = model.and_gate(rare, 2 * (positions[name] + 1))
        mutated = [model.or_gate(code[0], rare), model.or_gate(code[1], rare), *code[2:]]
        fault_root = model.violation(mutated)
        fault_clauses, fault_index = encode(model, fault_root)
        negative = receipt["negative"]
        if negative["status"] != "DISPROVED_UNDER_RECORDED_ASSUMPTIONS" \
                or negative["CNF_variables"] != len(fault_index) \
                or negative["CNF_initial_clauses"] != len(fault_clauses):
            raise ValueError("Mutated CNF or negative verdict differs")
        assignment = negative["CNF_assignment"]
        if len(assignment) != len(fault_index) + 1 or any(x not in (-1, 1) for x in assignment[1:]) \
                or not all(any(assignment[abs(x)] == (1 if x > 0 else -1) for x in c)
                           for c in fault_clauses):
            raise ValueError("Saved fault CNF witness is false")
        reconstructed = {graph["input_names"][node // 2 - 1]: int(assignment[var] == 1)
                         for node, var in fault_index.items() if node <= 2 * model.inputs}
        if reconstructed != negative["counterexample"]:
            raise ValueError("Named raw-input witness differs from exact CNF map")
        witness = {positions[name]: bit for name, bit in reconstructed.items()}
        if model.evaluate(fault_root, witness) != 1 or any(reconstructed[name] != 1 for name in triggers):
            raise ValueError("Saved rare-fault witness fails independent DAG")
        complete = dict.fromkeys(range(model.inputs), 0)
        complete.update(witness)
        original_code = [model.evaluate(x, complete) for x in code]
        mutated_code = [model.evaluate(x, complete) for x in mutated]
        if original_code != receipt["original_code_at_fault_witness"] \
                or mutated_code != receipt["mutated_code_at_fault_witness"] \
                or sum(original_code) != 1 or sum(mutated_code) == 1:
            raise ValueError("Actual model rare mutation is not observable")
        fault_cases.append({"pass": pass_index, "status": "PASS", "baseline_replayed_steps": steps,
                            "negative_CNF_and_raw_DAG_witness_validated": True,
                            "trigger_bits": 24, "original_code": original_code, "mutated_code": mutated_code})
        del model, baseline_clauses, baseline_index, fault_clauses, fault_index
        gc.collect()

    if any(digest(ROOT / rel) != expected for rel, expected in hashes.items()):
        raise ValueError("Frozen inputs changed during independent review")
    receipt = {"status": "PASS_INDEPENDENT_BOUNDED_CNF_AND_CERTIFICATE_REVIEW",
               "full_sequential_LEC": "OPEN", "source_to_Boolean_model_closure": "OPEN",
               "scope": "Exact saved raw-AIG Boolean subobligations only; original undefined-zero abstraction, source/clock bridge, reachability and full-chip sequential LEC remain outside this review.",
               "reviewed_input_sha256": hashes, "memory_enforcement": enforcement,
               "peak_memory": peak_memory(), "elapsed_seconds": round(time.monotonic() - started, 3),
               "independent_implementation": {"raw_AIG_parser": True, "raw_cofactor_hash_consing": True,
                                              "Tseitin_encoder": True, "resolution_replayer": True,
                                              "truth_table_oracle": True,
                                              "author_resolve_or_verify_resolution_called": False,
                                              "new_actual_ALU_solver_executions": 0,
                                              "external_formal_or_WSL_tools_executed": False},
               "author_controls_review": {"groups": 20, "source_hashes_current": True,
                                          "all_finite_and_negative_controls_reported_PASS": True},
               "new_finite_controls": controls, "paired_ALU_cases": cases,
               "paired_ALU_certificate_count": 28, "paired_fault_baseline_certificate_count": 2,
               "total_saved_resolution_steps_replayed": total_replayed,
               "paired_fault_control_review": fault_cases,
               "source_review_findings": [
                   {"severity": "scope", "finding": "Native CLI success means bounded execution completed; callers must inspect all semantic case statuses/counts. UNKNOWN can return process code0 by design."},
                   {"severity": "coverage", "finding": "Finite controls and saved exact resolution certificates are strong evidence for these subobligations, not an exhaustive verification of arbitrary large solver inputs."},
                   {"severity": "open_obligation", "finding": "The raw AIG was created with undefined-to-zero conversion; this review preserves that model without closing its source semantics or full-chip sequential LEC."}],
               "soundness_defect_found_in_reviewed_saved_proofs": False}
    output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    text = """# Independent review of bounded raw-model CNF proofs

PASS for the saved Boolean subobligations. Full sequential LEC and the
source-to-Boolean-model abstraction remain OPEN. This does not promote the
raw model into a full-chip RTL-to-PD proof.

The reviewer independently parsed the original binary AIG, retained every
unassigned raw Q/input as a free symbol, rebuilt each cofactored complemented-
edge DAG, encoded its one-hot violation into CNF, and replayed every saved
resolution derivation. No author parser, cofactor, resolution function, or
certificate verifier was used for those computations. The frozen author
encoder was compared against the independently constructed CNF and complete
variable map using a read-only adapter of each independently built cone.

All 14 ALU current codes in each of two independent saved executions passed:
28 terminal empty-clause certificates, each with 4958 variables and 12142
initial clauses. The paired proof receipts are byte- and field-identical.
Every recorded assignment was independently reconstructed from the raw state
partition: only external/internal deasserted resets and the group's own
current code were fixed; every other state/input remained free.

Both actual-model fault-control baseline certificates also passed replay.
The saved rare24-input counterexamples satisfy the independently built
mutated CNFs and their original raw-DAG evaluations. The baseline next code
has one active bit; the in-memory mutation has two. Source/AIG/RTL inputs did
not change.

Additional independent finite controls compare the frozen solver against
exhaustive enumeration on 256 two-variable CNF subsets, empty formula/clause,
2400 differently seeded random CNFs up to eight variables, and a learned
pigeonhole contradiction. Every UNSAT is replayed by the independent verifier;
every SAT assignment is checked against every original clause. Direct Boolean
formula truth tables test constants, complements, AND/OR/XOR and one-hot
encoding. Invalid certificates and malformed CNFs are rejected. Resource
limits stop computation; the public decision wrapper returns UNKNOWN.

Static kernel review covered signed literal/constant distinctions, watched
literal replacement, unit propagation, first-UIP conflict resolution,
asserting learned clauses, backtracking, exact proof replay and bounds. No
soundness defect was found in the reviewed saved proofs. This is not an
exhaustive proof of the solver for arbitrary inputs. A successful native
process return code means the bounded CLI completed; semantic acceptance must
inspect each case status and UNKNOWN count.

No new actual ALU solve, frontend, external formal tool or WSL process ran.
The process had a hard256MiB commit limit. Frozen source/evidence hashes were
checked before and after. Numeric details, memory observations, all control
rows and input digests are in the adjacent JSON receipt.
"""
    report.write_text(text, encoding="ascii")
    print(receipt["status"], "saved certificate count30; steps", total_replayed, flush=True)


if __name__ == "__main__":
    main()
