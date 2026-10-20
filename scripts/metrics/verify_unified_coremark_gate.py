"""Negative controls for promoting the current CoreMark CRC evidence to a table.

Only temporary synthetic receipt copies are changed; measured evidence and
source files remain untouched. No simulator, PD or power tool is launched.
"""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
from pathlib import Path

from unified_table import ROOT, COREMARK_RESULTS, verified_coremark


def main():
    original_path = COREMARK_RESULTS / "verification.json"
    original_sha256 = hashlib.sha256(original_path.read_bytes()).hexdigest()
    original = json.loads(original_path.read_text())
    selected = verified_coremark()
    assert set(selected) == {"DM", "SA2", "DM_VC4", "DM_DSE", "SA4", "SA2N"}
    variants = {}

    def changed(name, mutator):
        one = copy.deepcopy(original)
        mutator(one)
        variants[name] = one

    changed("incomplete_status", lambda d: d.update(status="IN_PROGRESS"))
    changed("wrong_ram_scope", lambda d: d.update(ram_bytes=16384))
    changed("wrong_cache_scope", lambda d: d.update(cache_bytes_each=1024))
    changed("official_score_claim", lambda d: d.update(official_score=True))
    changed("wrong_validation_method", lambda d: d.update(method="completion_marker_only"))
    changed("wrong_rtl", lambda d: d.update(rtl_id="0" * 64))
    changed("changed_source_hash", lambda d: d["inputs"].update({"fw/coremark.hex": "0" * 64}))
    changed("changed_artifact_hash", lambda d: d["artifacts"].update({
        "results/coremark_crc_checked_20261009/results_p1.csv": "0" * 64}))
    changed("missing_source_coverage", lambda d: d["inputs"].pop("scripts/snapshot_fields.py"))
    changed("missing_raw_artifact_coverage", lambda d: d["artifacts"].pop(
        "results/coremark_crc_checked_20261009/p2_c5_fast.uart.txt"))
    changed("missing_case", lambda d: d["cases"].pop())
    changed("duplicate_case", lambda d: d["cases"].__setitem__(-1, copy.deepcopy(d["cases"][0])))
    changed("failed_crc_case", lambda d: d["cases"][0].update(crc_pass=False))
    changed("failed_counter_match", lambda d: d["cases"][0].update(counters_equal_current_reference=False))
    changed("same_library_twice", lambda d: d.update(libraries=["same", "same"]))
    checks = []
    with tempfile.TemporaryDirectory(dir=ROOT / "results", prefix="coremark_table_gate_fixtures_") as temp:
        receipt = Path(temp) / "synthetic_receipt.json"
        for name, metadata in variants.items():
            receipt.write_text(json.dumps(metadata), encoding="ascii")
            try:
                verified_coremark(receipt)
            except (RuntimeError, ValueError, KeyError) as exc:
                checks.append({"control": name, "caught": True, "reason": str(exc)})
            else:
                raise AssertionError("Invalid evidence accepted: " + name)
    assert hashlib.sha256(original_path.read_bytes()).hexdigest() == original_sha256
    report = {"status": "TABLE_GATE_FIXTURES_VERIFIED_NOT_NEW_MEASUREMENTS", "positive_control": True,
              "negative_controls": checks, "receipt_sha256": hashlib.sha256(original_path.read_bytes()).hexdigest(),
              "generator_sha256": hashlib.sha256((ROOT / "scripts/metrics/unified_table.py").read_bytes()).hexdigest()}
    (ROOT / "results/coremark_table_gate_20261009.json").write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(f"[PASS] current 11-point evidence and {len(checks)} invalid-receipt negative controls")


if __name__ == "__main__":
    main()
