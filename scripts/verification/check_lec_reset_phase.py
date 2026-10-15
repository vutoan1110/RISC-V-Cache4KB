"""Finite reachable/reset-interruption controls; exact raw model checked later."""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

from lec_onehot_boolean import ROOT, enforce_process_memory, sha
from lec_reset_phase import PHASES, conditions_for, relation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--joint-controls", required=True)
    args = parser.parse_args()
    out, controls = Path(args.out).resolve(), Path(args.joint_controls).resolve()
    if out.exists() or not out.is_relative_to(ROOT) or not controls.is_relative_to(ROOT):
        raise ValueError("New research phase control receipt required")
    memory = enforce_process_memory()
    joint = json.loads(controls.read_text())
    if joint["status"] != "PASS_JOINT_INVARIANT_CHECKER_CONTROLS":
        raise ValueError("Successful joint/alias/CNF controls required")
    for rel, digest in joint["source_sha256"].items():
        if sha(ROOT / rel) != digest:
            raise ValueError("Frozen joint/CNF sources changed")
    paths = [ROOT / p for p in ("scripts/verification/lec_reset_phase.py",
                               "scripts/verification/check_lec_reset_phase.py",
                               "scripts/verification/lec_joint_invariant.py",
                               "scripts/verification/lec_onehot_sat.py",
                               "scripts/verification/lec_onehot_boolean.py",
                               "scripts/verification/lec_reset_base.py")]
    paths.append(controls)
    hashes = {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}
    expected = [(e, m, s) for e, m, s in itertools.product((0, 1), repeat=3) if not s or m]
    if len(PHASES) != 6 or len(set(PHASES)) != 6 or set(PHASES) != set(expected):
        raise ValueError("Incomplete or duplicated reachable phase partition")
    rows = [{"name": "Exact six-phase partition of R", "status": "PASS", "phases": [list(p) for p in PHASES]}]
    for m, s in itertools.product((0, 1), repeat=2):
        if relation(m, s) != (not s or bool(m)):
            raise ValueError("R differs from independent Boolean truth table")
        for e in (0, 1):
            nxt = (e, e & m)
            if not relation(*nxt):
                raise ValueError("Synchronizer equation does not preserve R")
            if e == 0 and nxt != (0, 0):
                raise ValueError("Asserted reset does not establish reachable phase")
    rows.append({"name": "Eight phase transitions including unconstrained startup 01", "status": "PASS", "cases": 8})
    visited = set()
    for sequence in itertools.product((0, 1), repeat=8):
        m, s = 0, 0
        for e in sequence:
            phase = e, m, s
            visited.add(phase)
            if phase not in PHASES or not relation(m, s):
                raise ValueError("An interrupted-reset sequence escapes established reachable phases")
            conditions_for(phase)
            m, s = e, e & m
    if visited != set(PHASES):
        raise ValueError("Finite interruption controls did not exercise all six reachable phases")
    rows.append({"name": "256 arbitrary eight-step external reset sequences", "status": "PASS", "steps": 2048,
                 "scope": "Finite checker control, not a substitute for raw-model induction proof"})
    for phase in ((0, 0, 1), (1, 0, 1), (True, 0, 0), (1, True, 0),
                  (1, 1, True), (2, 1, 1), (1, 1), (1, 1, 1, 0)):
        try:
            conditions_for(phase)
        except ValueError:
            rows.append({"name": "Invalid phase rejected " + repr(phase), "status": "PASS"})
        else:
            raise ValueError("Invalid/unreachable/ill-typed phase accepted")
    if any(sha(ROOT / rel) != digest for rel, digest in hashes.items()):
        raise ValueError("Phase sources changed during controls")
    receipt = {"status": "PASS_RESET_PHASE_CHECKER_CONTROLS", "source_sha256": hashes,
               "memory_enforcement": memory, "control_count": len(rows), "controls": rows,
               "scope": "Finite phase/reachability controls plus frozen joint/CNF controls; actual raw-model protocol fault and paired closure still required"}
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print("PASS:", len(rows), "reset-phase checker controls")


if __name__ == "__main__":
    main()
