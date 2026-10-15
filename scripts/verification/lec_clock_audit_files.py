#!/usr/bin/env python3
"""Clock/edge audit of lec_clock_audit.py (unchanged, imported) on any list of flattened LEC models (2026-10-13; the
original script hard-codes the four DM models). Same obligation and same verdict rules: every flop clock is literally
the scalar input clk and every flop is positive edge; anything else is OPEN / FAIL.
usage: python lec_clock_audit_files.py --out <new json inside the workspace> --label <text> FILE [FILE ...]"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lec_clock_audit as base  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if not out.is_relative_to(base.ROOT) or out.exists():
        raise RuntimeError("output must be new and inside the research workspace")
    records = {}
    for name in args.files:
        p = Path(name).resolve()
        print("STREAM " + str(p), flush=True)
        records[str(p.relative_to(base.ROOT)) if p.is_relative_to(base.ROOT) else str(p)] = rec = base.audit(p)
        print(json.dumps({"file": str(p), "status": rec["status"], "flop_cells": rec["flop_cells"],
                          "flop_bits": rec["flop_bits"], "clock_roots": rec["clock_roots"]}), flush=True)
    verdict = all(row["status"] == "VERIFIED_CLOCK_EDGE_DOMAIN_AUDIT" for row in records.values())
    output = {"created": datetime.now().astimezone().isoformat(timespec="seconds"), "label": args.label,
              "status": "VERIFIED_CLOCK_EDGE_DOMAIN_AUDIT" if verdict else "OPEN_CLOCK_OBLIGATIONS",
              "sources": {"scripts/verification/lec_clock_audit.py": base.digest(Path(base.__file__)),
                          "scripts/verification/lec_clock_audit_files.py": base.digest(Path(__file__))},
              "inputs": records,
              "scope": "Clock/positive-edge obligation only (as lec_clock_audit.py)."}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print("VERDICT " + output["status"])
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
