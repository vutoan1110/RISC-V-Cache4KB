"""Universal structural reset-base checks on an unrestricted binary AIG.

All unassigned inputs remain symbolic. Exact Boolean cofactoring and structural
hashing can prove a constant/equality; unresolved expressions remain UNKNOWN.
This is a reset sub-proof, never a complete RTL-to-netlist equivalence verdict.
No sampling, SAT, Yosys, WSL or external process is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_aig_bytes(data):
    """Parse the complete combinational AIG body and indexed symbol tables."""
    end = data.index(b"\n")
    header = data[:end].split()
    if len(header) != 6 or header[0] != b"aig":
        raise ValueError("Require an ordinary binary AIGER combinational graph")
    maximum, inputs, latches, outputs, count = map(int, header[1:])
    if min(maximum, inputs, latches, outputs, count) < 0 or latches or maximum != inputs + count:
        raise ValueError("Invalid/combinational-only AIGER header")
    if maximum > 2_000_000 or len(data) > 128 * 1024 * 1024:
        raise ValueError("Graph exceeds the explicit lightweight parser resource bound")
    position = end + 1
    olits = []
    for _ in range(outputs):
        end = data.index(b"\n", position)
        literal = int(data[position:end])
        if not 0 <= literal <= 2 * maximum + 1:
            raise ValueError("Output literal leaves the graph")
        olits.append(literal)
        position = end + 1

    def delta():
        nonlocal position
        value, shift = 0, 0
        while True:
            if position >= len(data) or shift > 35:
                raise ValueError("Truncated/oversized binary AND delta")
            byte = data[position]
            position += 1
            value |= (byte & 127) << shift
            if byte < 128:
                return value
            shift += 7

    ands = []
    for index in range(count):
        lhs = 2 * (inputs + index + 1)
        first = lhs - delta()
        second = first - delta()
        if not 0 <= second <= first < lhs:
            raise ValueError("AND fanin is not a valid earlier literal")
        ands.append((first, second))
    symbols = {"i": {}, "o": {}}
    for line in data[position:].splitlines():
        if line == b"c":
            break
        if not line:
            continue
        key, separator, name = line.partition(b" ")
        if not separator or key[:1] not in (b"i", b"o") or not key[1:].isdigit() or not name:
            raise ValueError("Invalid symbol table entry")
        kind, index = key[:1].decode(), int(key[1:])
        if index in symbols[kind]:
            raise ValueError("Duplicate symbol index")
        symbols[kind][index] = name.decode("latin1")
    for kind, size in (("i", inputs), ("o", outputs)):
        names = symbols[kind]
        if set(names) != set(range(size)) or len(set(names.values())) != size:
            raise ValueError("Require complete, contiguous and unique input/output symbols")
    return {"inputs": inputs, "outputs": olits, "ands": ands,
            "input_names": [symbols["i"][i] for i in range(inputs)],
            "output_names": [symbols["o"][i] for i in range(outputs)]}


def cofactor(graph, assignments):
    """Canonical AND/NOT DAG after constant assignment, with all other PIs free."""
    positions = {name: i for i, name in enumerate(graph["input_names"])}
    if not assignments or not set(assignments) <= positions.keys() or any(v not in (0, 1) for v in assignments.values()):
        raise ValueError("Require explicit named Boolean reset assignments")
    inputs = graph["inputs"]
    values = [0] + [assignments.get(name, 2 * (i + 1)) for i, name in enumerate(graph["input_names"])]
    unique = {}

    def AND(a, b):
        if a == 0 or b == 0 or a == (b ^ 1):
            return 0
        if a == 1 or a == b:
            return b
        if b == 1:
            return a
        key = (min(a, b), max(a, b))
        if key not in unique:
            unique[key] = 2 * (inputs + len(unique) + 1)
        return unique[key]

    def literal(lit):
        return values[lit >> 1] ^ (lit & 1)

    for first, second in graph["ands"]:
        values.append(AND(literal(first), literal(second)))
    output = {name: literal(lit) for name, lit in zip(graph["output_names"], graph["outputs"])}
    return output, AND


def check_pairs(pairs):
    """Require a bijective mapped partition; ambiguity stays separately visible."""
    left, right = pairs["gold"], pairs["gate"]
    links = pairs["pairs"]
    for size, side, column in ((len(left), "gold_only", 0), (len(right), "gate_only", 1)):
        paired = [p[column] for p in links]
        only = pairs[side]
        if any(type(i) is not int or not 0 <= i < size for i in paired + only) or \
                len(set(paired)) != len(paired) or len(set(only)) != len(only) or \
                set(paired) & set(only) or set(paired) | set(only) != set(range(size)):
            raise ValueError("Mapping is not a complete disjoint one-to-one flop partition")


def reset_obligations(graph, pairs, spec, external="reset_n"):
    check_pairs(pairs)
    outputs = set(graph["output_names"])
    all_gold_d = {"lec_d_p%05d" % k for k in range(len(pairs["pairs"]))} | {
        "lec_d_g%05d" % k for k in range(len(pairs["gold_only"]))}
    if not all_gold_d <= outputs or any(name.startswith("lec_oh_") for name in graph["input_names"]):
        raise ValueError("Reset base requires every raw gold D, with no one-hot decoder restrictions")
    normalized = lambda name: name.replace(" [", "[")
    sync = {}
    for target in ("reset_meta_q", "reset_sync_q"):
        matches = [k for k, (i, _) in enumerate(pairs["pairs"])
                   if "\\" + target in {normalized(n) for n in pairs["gold"][i]["names"]}]
        if len(matches) != 1:
            raise ValueError("Reset synchronizer is missing/ambiguous: " + target)
        sync[target] = matches[0]
    first, _ = cofactor(graph, {external: 0})
    protocol = {name: first["lec_d_p%05d" % k] for name, k in sync.items()}
    if any(lit != 0 for lit in protocol.values()):
        return {"status": "UNKNOWN_RESET_PROTOCOL", "protocol_literals": protocol,
                "warning": "Synchronizer Q=0 cannot be assumed until universally justified"}
    conditions = {external: 0, **{"lec_q_p%05d" % k: 0 for k in sync.values()}}
    reset, AND = cofactor(graph, conditions)
    claimed = [set(map(int, spec.get(key, {} if key != "free" else []))) for key in ("const", "dup", "free")]
    if any(claimed[i] & claimed[j] for i in range(3) for j in range(i)) or \
            set.union(*claimed) != set(range(len(pairs["gold_only"]))):
        raise ValueError("Constants/duplicates/free do not cover the exact gold-only partition")
    const = []
    for index, value in sorted((int(k), v) for k, v in spec["const"].items()):
        if type(value) is not int or value not in (0, 1):
            raise ValueError("Constant premise must be Boolean")
        actual = reset["lec_d_g%05d" % index]
        const.append({"gold_only": index, "expected": value,
                      "status": "PROVED" if actual == value else "DISPROVED" if actual in (0, 1) else "UNKNOWN"})
    dup = []
    for index, partner in sorted((int(k), v) for k, v in spec["dup"].items()):
        if type(partner) is not int or not 0 <= partner < len(pairs["pairs"]):
            raise ValueError("Duplicate partner is not a paired flop")
        a, b = reset["lec_d_g%05d" % index], reset["lec_d_p%05d" % partner]
        dup.append({"gold_only": index, "partner": partner,
                    "status": "PROVED" if a == b else "DISPROVED" if a in (0, 1) and b in (0, 1) else "UNKNOWN"})
    d_name = {i: "lec_d_p%05d" % k for k, (i, _) in enumerate(pairs["pairs"])}
    d_name.update({i: "lec_d_g%05d" % k for k, i in enumerate(pairs["gold_only"])})
    groups, used = [], set()
    for group in spec["onehot_gold"]:
        bits = group["gold"]
        if not group["name"] or not bits or len(set(bits)) != len(bits) or used & set(bits) or any(i not in d_name for i in bits):
            raise ValueError("Empty, overlapping or invalid one-hot reset group")
        used.update(bits)
        literals = [reset[d_name[i]] for i in bits]
        none, two = 1, 0
        OR = lambda a, b: AND(a ^ 1, b ^ 1) ^ 1
        for lit in literals:
            none = AND(none, lit ^ 1)
        for i, lit in enumerate(literals):
            for other in literals[:i]:
                two = OR(two, AND(lit, other))
        violation = OR(none, two)
        groups.append({"name": group["name"], "bits": len(bits),
                       "reset_code": literals if all(lit in (0, 1) for lit in literals) else "symbolic",
                       "status": "PROVED" if violation == 0 else "DISPROVED" if violation == 1 else "UNKNOWN"})
    if not groups:
        raise ValueError("No one-hot reset groups recorded")
    states = {"fixed_zero": 0, "fixed_one": 0, "symbolic": 0}
    for k in range(len(pairs["pairs"])):
        lit = reset["lec_d_p%05d" % k]
        states["fixed_zero" if lit == 0 else "fixed_one" if lit == 1 else "symbolic"] += 1
    proven = all(item["status"] == "PROVED" for item in const + dup + groups)
    return {"status": "PROVED_GOLD_RESET_SUBOBLIGATIONS_ONLY" if proven else "UNRESOLVED_GOLD_RESET_SUBOBLIGATIONS",
            "reset_protocol": "external reset asserted; both synchronizer D=0 for every remaining symbolic input",
            "assignments_after_reset_edge": conditions, "constant_reset": const, "duplicate_reset": dup,
            "onehot_reset": groups, "paired_gold_reset_states": states,
            "ambiguity_records": pairs.get("ambiguous", []),
            "missing_full_equivalence_obligations": [
                "Raw N1 and final-netlist reset relation to every paired gold state, including unreset symbolic state",
                "Inductive closure of every constant/duplicate and every actual recoded FSM group on these exact inputs",
                "All mapped outputs and SRAM pin boundaries, multiplier closure, negative controls, independent complete passes"],
            "full_lec_status": "NOT_ESTABLISHED_BY_THIS_SUBPROOF"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aig", required=True)
    parser.add_argument("--pairs", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    paths = [Path(args.aig).resolve(), Path(args.pairs).resolve(), Path(args.spec).resolve()]
    out = Path(args.out).resolve()
    if any(not p.is_relative_to(ROOT) for p in paths + [out]) or out.exists():
        raise ValueError("Inputs/output must be in research and output must be new")
    records = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    result = reset_obligations(read_aig_bytes(paths[0].read_bytes()),
                               json.loads(paths[1].read_text()), json.loads(paths[2].read_text()))
    if any(sha(ROOT / rel) != digest for rel, digest in records.items()):
        raise ValueError("Input changed during universal reset-base check")
    result.update({"method": "exact Boolean cofactor/structural hashing; all other inputs symbolic; no sampling",
                   "inputs": records, "checker_sha256": sha(Path(__file__)), "new_external_proof_tools_executed": False})
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(result["status"] + "; full LEC is not established by this sub-proof")


if __name__ == "__main__":
    main()
