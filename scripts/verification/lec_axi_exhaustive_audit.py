"""Independent exhaustive Boolean audit of six recorded DM AXI cofactors.

Stream the original binary AIG into packed integer arrays, retain only the six
next-state cones, and enumerate every remaining primary-input assignment. No
BDD, existing AIG parser, simulator, synthesis or external proof tool is used.
This cannot establish full sequential LEC or close the undefined-value model.
"""
from __future__ import annotations

import argparse
from array import array
import ctypes
import gc
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
LIMIT = 256 * 1024 * 1024
MAX_SUPPORT = 13
MAX_CONE = 100_000
RESET = {"reset_n": 1, "lec_q_p19088": 1, "lec_q_p19089": 1}
GROUPS = {"axi_last_grant": [4, 5, 6], "axi_source": [7, 8, 9]}
JOB = None


def need(test, message):
    if not test:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for b in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def memory_limit():
    global JOB
    if os.name != "nt":
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (LIMIT, LIMIT))
        return "RLIMIT_AS=256MiB"
    from ctypes import wintypes as w
    class Basic(ctypes.Structure):
        _fields_ = [("ProcessTime", ctypes.c_int64), ("JobTime", ctypes.c_int64), ("Flags", w.DWORD),
            ("MinWS", ctypes.c_size_t), ("MaxWS", ctypes.c_size_t), ("Active", w.DWORD),
            ("Affinity", ctypes.c_size_t), ("Priority", w.DWORD), ("Scheduling", w.DWORD)]
    class IO(ctypes.Structure):
        _fields_ = [(name, ctypes.c_uint64) for name in ("ReadOps", "WriteOps", "OtherOps", "ReadBytes", "WriteBytes", "OtherBytes")]
    class Extended(ctypes.Structure):
        _fields_ = [("Basic", Basic), ("IO", IO), ("ProcessLimit", ctypes.c_size_t),
            ("JobLimit", ctypes.c_size_t), ("PeakProcess", ctypes.c_size_t), ("PeakJob", ctypes.c_size_t)]
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
    k.CreateJobObjectW.restype = w.HANDLE
    k.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
    k.SetInformationJobObject.restype = w.BOOL
    k.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
    k.AssignProcessToJobObject.restype = w.BOOL
    k.GetCurrentProcess.restype = w.HANDLE
    JOB = k.CreateJobObjectW(None, None)
    info = Extended()
    info.Basic.Flags = 0x100
    info.ProcessLimit = LIMIT
    need(JOB and k.SetInformationJobObject(JOB, 9, ctypes.byref(info), ctypes.sizeof(info))
         and k.AssignProcessToJobObject(JOB, k.GetCurrentProcess()), "UNKNOWN_MEMORY_LIMIT_NOT_ENFORCED")
    return "Windows per-process JobObject commit limit=256MiB"


def peak_memory():
    if os.name != "nt":
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    from ctypes import wintypes as w
    class Counters(ctypes.Structure):
        _fields_ = [("cb", w.DWORD), ("PageFaultCount", w.DWORD)] + [
            (n, ctypes.c_size_t) for n in ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
    c = Counters()
    c.cb = ctypes.sizeof(c)
    k = ctypes.WinDLL("kernel32")
    k.GetCurrentProcess.restype = w.HANDLE
    p = ctypes.WinDLL("psapi")
    p.GetProcessMemoryInfo.argtypes = [w.HANDLE, ctypes.c_void_p, w.DWORD]
    need(p.GetProcessMemoryInfo(k.GetCurrentProcess(), ctypes.byref(c), c.cb), "Cannot read process memory")
    return max(c.PeakWorkingSetSize, c.PeakPagefileUsage)


def read_cones(path, wanted):
    """Packed raw fanins are temporary; only reachable original nodes remain."""
    need(path.stat().st_size <= 32 * 1024 * 1024, "UNKNOWN_AIG_FILE_BOUND")
    with path.open("rb") as stream:
        head = stream.readline().split()
        need(len(head) == 6 and head[0] == b"aig", "Require ordinary binary AIG")
        m, i, l, o, a = map(int, head[1:])
        need(min(m, i, l, o, a) >= 0 and l == 0 and m == i + a and m <= 2_000_000, "Invalid/bounded combinational AIG header")
        outputs = array("I")
        for _ in range(o):
            line = stream.readline()
            need(re.fullmatch(rb"\d+\n", line) is not None, "Malformed AIG output line")
            literal = int(line)
            need(literal <= 2 * m + 1, "Output outside AIG")
            outputs.append(literal)
        first, second = array("I"), array("I")
        def delta():
            value, shift = 0, 0
            while True:
                b = stream.read(1)
                need(b and shift <= 35, "Truncated/oversized binary delta")
                value |= (b[0] & 127) << shift
                if b[0] < 128:
                    return value
                shift += 7
        for n in range(a):
            lhs = 2 * (i + n + 1)
            x = lhs - delta()
            y = x - delta()
            need(0 <= y <= x < lhs, "Invalid raw AND fanins")
            first.append(x)
            second.append(y)
        symbols = {"i": {}, "o": {}}
        for line in stream:
            line = line.rstrip(b"\r\n")
            if line == b"c":
                break
            match = re.fullmatch(rb"([io])(\d+) (.+)", line)
            need(match is not None, "Malformed raw AIG symbol")
            kind, n, name = match[1].decode(), int(match[2]), match[3].decode("ascii")
            need(n not in symbols[kind], "Duplicate AIG symbol index")
            symbols[kind][n] = name
        for kind, count in (("i", i), ("o", o)):
            need(set(symbols[kind]) == set(range(count)) and len(set(symbols[kind].values())) == count, "Incomplete/duplicate raw AIG symbols")
        input_names = {n + 1: name for n, name in symbols["i"].items()}
        output_map = {name: outputs[n] for n, name in symbols["o"].items()}
        need(set(wanted) <= set(output_map) and not any(n.startswith("lec_oh_") for n in input_names.values()), "Raw unrestricted Q model and exact D targets required")
        selected = {name: output_map[name] for name in wanted}
        nodes, pending = {}, [literal >> 1 for literal in selected.values()]
        while pending:
            n = pending.pop()
            if n <= i or n in nodes:
                continue
            need(len(nodes) < MAX_CONE, "UNKNOWN_RAW_CONE_BOUND")
            position = n - i - 1
            need(0 <= position < a, "Invalid reachable AND")
            x, y = first[position], second[position]
            nodes[n] = (x, y)
            pending.extend((x >> 1, y >> 1))
        return dict(inputs=i, maximum=m, and_count=a, output_count=o, nodes=nodes,
                    input_names=input_names, selected=selected, packed_fanin_bytes=(len(first) + len(second)) * first.itemsize)


def cofactor_support(graph, assignments, targets):
    """Exact local identities only; unfixed PIs remain distinct symbolic atoms."""
    names = {name: index for index, name in graph["input_names"].items()}
    need(set(assignments) <= set(names) and all(type(v) is int and v in (0, 1) for v in assignments.values()), "Invalid named Boolean assignment")
    reduced = {0: 0, **{index: assignments.get(name, 2 * index) for index, name in graph["input_names"].items()}}
    created, unique = {}, {}
    def lit(v):
        return reduced[v >> 1] ^ (v & 1)
    def gate(x, y):
        if x == 0 or y == 0 or x == (y ^ 1):
            return 0
        if x == 1:
            return y
        if y == 1 or x == y:
            return x
        key = tuple(sorted((x, y)))
        if key not in unique:
            new = 2 * (graph["inputs"] + len(unique) + 1)
            unique[key] = new
            created[new] = key
        return unique[key]
    for n in sorted(graph["nodes"]):
        x, y = graph["nodes"][n]
        reduced[n] = gate(lit(x), lit(y))
    roots = [lit(graph["selected"][name]) for name in targets]
    reached, support, pending = set(), set(), [r & ~1 for r in roots]
    while pending:
        r = pending.pop()
        if not r or r in reached:
            continue
        reached.add(r)
        if r in created:
            pending.extend(v & ~1 for v in created[r])
        else:
            need(1 <= r // 2 <= graph["inputs"], "Invalid reduced PI")
            support.add(r // 2)
    need(len(support) <= MAX_SUPPORT, "UNKNOWN_EXHAUSTIVE_SUPPORT_BOUND:" + str(len(support)))
    return sorted(support), reduced


def enumerate_raw(graph, assignments, targets):
    support, reduction = cofactor_support(graph, assignments, targets)
    fixed = {index: assignments[name] for index, name in graph["input_names"].items() if name in assignments}
    # Reduction proves any original PI absent from 'support' irrelevant to these
    # next-state outputs. During evaluation it remains symbolic, not defaulted
    # to zero: a demanded unfixed PI is an error. Only constant-reduced raw
    # subexpressions may bypass it. All evaluated nonconstant gates are raw.
    counts = [0] * (1 << len(targets))
    for assignment in range(1 << len(support)):
        values = {0: 0, **fixed, **{n: (assignment >> bit) & 1 for bit, n in enumerate(support)}}
        def value(literal):
            n = literal >> 1
            if n not in values:
                need(reduction[n] in (0, 1), "UNKNOWN_SYMBOLIC_PI_DEMANDED:" + graph["input_names"].get(n, str(n)))
                values[n] = reduction[n]
            return values[n] ^ (literal & 1)
        def evaluate(literal):
            n = literal >> 1
            if n in values or reduction[n] in (0, 1):
                return value(literal)
            need(n in graph["nodes"], "UNKNOWN_SYMBOLIC_PI_DEMANDED:" + graph["input_names"].get(n, str(n)))
            x, y = graph["nodes"][n]
            left = evaluate(x)
            values[n] = 0 if left == 0 else evaluate(y)
            return values[n] ^ (literal & 1)
        code = sum(evaluate(graph["selected"][name]) << bit for bit, name in enumerate(targets))
        counts[code] += 1
    forbidden = sum(count for code, count in enumerate(counts) if code.bit_count() != 1)
    return {"support_bits": len(support), "free_primary_inputs": [graph["input_names"][n] for n in support],
        "assignments_enumerated": 1 << len(support), "next_code_counts_lsb_first": counts,
        "forbidden_zero_or_multihot_count": forbidden, "status": "PROVED_EXHAUSTIVE_BOOLEAN_COFACTOR" if forbidden == 0 else "DISPROVED_EXHAUSTIVE_BOOLEAN_COFACTOR"}


def mapping(pairs, spec):
    q, d = {}, {}
    for k, (gold, _) in enumerate(pairs["pairs"]):
        need(gold not in q, "Duplicate paired gold mapping")
        q[gold], d[gold] = f"lec_q_p{k:05d}", f"lec_d_p{k:05d}"
    for k, gold in enumerate(pairs["gold_only"]):
        need(gold not in q, "Overlapping gold-only mapping")
        q[gold], d[gold] = f"lec_q_g{k:05d}", f"lec_d_g{k:05d}"
    need(set(q) == set(range(len(pairs["gold"]))), "Incomplete gold mapping")
    actual = {g["name"]: g["gold"] for g in spec["onehot_gold"] if g["name"] in GROUPS}
    need(actual == GROUPS, "Actual AXI group indices differ")
    for name, bits in GROUPS.items():
        expected = "last_grant_q" if name == "axi_last_grant" else "source_q"
        for bit, index in enumerate(bits):
            need(any(n.endswith(expected + f" [{bit}]") for n in pairs["gold"][index]["names"]), "Group source state alias differs")
    g88 = pairs["gold_only"][88]
    need(q[g88] == "lec_q_g00088" and spec["const"].get("88") == 0, "Expected previously constrained gold-onlyg88 metadata missing")
    return q, d, pairs["gold"][g88]["names"]


def controls():
    names = {1: "x", 2: "lec_q_g00088"}
    basic = dict(inputs=2, nodes={}, input_names=names, selected={"a": 2, "b": 3})
    good = enumerate_raw(basic, {}, ("a", "b"))
    need(good["assignments_enumerated"] == 2 and good["forbidden_zero_or_multihot_count"] == 0, "Complement one-hot positive failed")
    all_free = dict(inputs=2, nodes={}, input_names=names, selected={"a": 4, "b": 5})
    g88 = enumerate_raw(all_free, {}, ("a", "b"))
    need(g88["free_primary_inputs"] == ["lec_q_g00088"] and g88["assignments_enumerated"] == 2, "Gold-onlyg88 not free")
    for selected, forbidden in (({"a": 0, "b": 0}, 1), ({"a": 2, "b": 2}, 2)):
        result = enumerate_raw(dict(basic, selected=selected), {}, ("a", "b"))
        need(result["forbidden_zero_or_multihot_count"] == forbidden, "Zero/multihot negative failed")
    # Raw AND of x with NOT x is eliminated without assigning x. Its output
    # complement is universally one, including when every PI remains free.
    cancellation = dict(inputs=2, nodes={3: (2, 3)}, input_names=names, selected={"a": 6, "b": 7})
    result = enumerate_raw(cancellation, {}, ("a", "b"))
    need(result["support_bits"] == 0 and result["next_code_counts_lsb_first"] == [0, 0, 1, 0], "Raw complement cancellation failed")
    return {"status": "PASS", "not_a_measurement": True, "checks": ["complement_onehot", "gold_onlyg88_free", "zero_code_rejected", "multihot_code_rejected", "raw_constant_cancellation_without_pi_assumption"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    out = args.out if args.out.is_absolute() else ROOT / args.out
    need(out.resolve().is_relative_to((ROOT / "results").resolve()) and not out.exists(), "Receipt must be new and under research/results")
    bound = memory_limit()
    source_paths = [ROOT / f"results/dm_onehot_boolean_20261010_p{n}.json" for n in (1, 2)]
    receipts = [json.loads(p.read_text()) for p in source_paths]
    need(sha(source_paths[0]) == sha(source_paths[1]) and receipts[0] == receipts[1], "Existing independent BDD receipts not byte-identical")
    state = receipts[0]
    need(state["counts"] == {"PROVED_BOOLEAN_COFACTOR": 6, "DISPROVED_UNDER_RECORDED_ASSUMPTIONS": 0, "UNKNOWN": 14}
         and state["full_sequential_LEC"] == "OPEN", "Unexpected original proof scope")
    inputs = state["input_sha256"]
    need(len(inputs) == 7, "Incomplete recorded input SHA inventory")
    for relative, digest in inputs.items():
        p = (ROOT / relative).resolve()
        need(p.is_relative_to(ROOT) and sha(p) == digest, "Original input SHA differs: " + relative)
    pairs = json.loads((ROOT / "asic/equiv/lec/pairsAR14.json").read_text())
    spec = json.loads((ROOT / "asic/equiv/lec/AR14_spec.json").read_text())
    q, d, g88_names = mapping(pairs, spec)
    del pairs, spec
    gc.collect()
    original_cases = {(r["group"], r["active_current_bit"]): r for r in state["obligations"] if r["status"] == "PROVED_BOOLEAN_COFACTOR"}
    need(set(original_cases) == {(g, n) for g in GROUPS for n in range(3)}, "Original six AXI obligations incomplete/duplicate")
    target_names = [d[index] for bits in GROUPS.values() for index in bits]
    graph = read_cones(ROOT / "asic/equiv/lec/gold_god_r14.aig", target_names)
    results = []
    for name, bits in GROUPS.items():
        for active in range(3):
            case = original_cases[(name, active)]
            assignments = {**RESET, **{q[index]: int(bit == active) for bit, index in enumerate(bits)}}
            need(case["assignments"] == assignments and case["group_gold_indices"] == bits, "Original cofactor includes unknown/additional assumptions")
            need("lec_q_g00088" not in assignments, "Gold-onlyg88 must remain free")
            started = time.monotonic()
            checked = enumerate_raw(graph, assignments, [d[index] for index in bits])
            need(checked["status"] == "PROVED_EXHAUSTIVE_BOOLEAN_COFACTOR" and checked["support_bits"] == case["support_bits"], "Independent original-raw enumeration disagrees with BDD cofactor")
            results.append(dict(group=name, active_current_bit=active, group_gold_indices=bits,
                assignments=assignments, seconds=round(time.monotonic() - started, 6), **checked))
            print(name, active, checked["status"], checked["assignments_enumerated"], flush=True)
    for relative, digest in inputs.items():
        need(sha(ROOT / relative) == digest, "Input changed during independent exhaustive check")
    need(all(sha(p) == sha(source_paths[0]) for p in source_paths), "BDD receipts changed during audit")
    record = dict(status="VERIFIED_SIX_AXI_BOOLEAN_COFACTORS_BY_INDEPENDENT_RAW_EXHAUSTIVE_ENUMERATION",
        full_sequential_LEC="OPEN", alu_ctrl_e_obligations="14_UNKNOWN_UNCHANGED",
        undefined_value_source_model="OPEN_UNCHANGED", method="original_binary_AIG_stream_parse_AND_NOT_truth_enumeration",
        other_unassigned_primary_inputs="symbolic_during_exact_constant_reduction_never_tied_to_zero",
        memory_enforcement=bound, process_memory_limit_bytes=LIMIT, peak_process_bytes=peak_memory(),
        raw_AIG_header={k: graph[k] for k in ("inputs", "maximum", "and_count", "output_count")},
        retained_original_AND_nodes=len(graph["nodes"]), temporary_packed_fanin_bytes=graph["packed_fanin_bytes"],
        original_p1_p2_byte_identical=True, original_receipts={p.relative_to(ROOT).as_posix(): sha(p) for p in source_paths},
        input_sha256=inputs, checker_sha256=sha(Path(__file__)), gold_onlyg88_names=g88_names,
        obligations=results, controls=controls(), new_external_tools_executed=False)
    need(record["peak_process_bytes"] <= LIMIT, "UNKNOWN_PROCESS_MEMORY_BOUND_EXCEEDED")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="ascii") as stream:
        json.dump(record, stream, indent=2)
        stream.write("\n")
    print(record["status"], flush=True)


if __name__ == "__main__":
    try:
        main()
    except (MemoryError, RecursionError) as exc:
        print("UNKNOWN_RESOURCE_BOUND:" + type(exc).__name__, file=sys.stderr)
        raise SystemExit(2)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print("UNKNOWN_OR_REJECTED:" + str(exc), file=sys.stderr)
        raise SystemExit(1)
