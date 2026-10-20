"""Negative controls for the final SOF/evidence audit, using tiny synthetic files."""
from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

import complete_board_preparation as completion
from board_common import ROOT, MIFS, manifest, sha


def main():
    before = {p.name: sha(p) for p in MIFS}
    rtl = manifest()["aggregate"]
    refs = []
    for name in ("upstream_r14_4kb_p1.csv", "ramsweep_r14_p1.csv", "upfull_r14_4kb_p1.csv"):
        with (ROOT / "results" / name).open(newline="") as f:
            refs.extend(csv.DictReader(f))
    checks = {}

    def write_csv(path, rows):
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

    def reject(name, reason):
        try:
            completion.audit_sofs()
        except RuntimeError as exc:
            if reason not in str(exc):
                raise AssertionError(f"Unexpected rejection: {exc}") from exc
            checks[name] = {"pass": True, "reason": str(exc)}
        else:
            raise AssertionError(f"Audit accepted invalid fixture: {name}")

    with tempfile.TemporaryDirectory(prefix="board_audit_fixture_", dir=ROOT / "results") as folder:
        fixture = Path(folder).resolve()
        assert fixture.is_relative_to((ROOT / "results").resolve())
        completion.ROOT = fixture
        out = fixture / "sofs"
        out.mkdir()
        completion.OUT = out
        (fixture / "results").mkdir()
        for p in (1, 2):
            write_csv(fixture / f"results/{completion.REF_TAG}_p{p}.csv", refs)
        state = {"state": "READY_FOR_PHYSICAL_SESSION", "rtl_id": rtl, "common_seed": 2,
                 "canonical_restoration": "PASS", "canonical_mif_sha256": before}
        (out / "BUILD_STATE.json").write_text(json.dumps(state))
        rows = []
        for r in refs:
            key = f"{r['kernel']}_{r['config']}"
            sof = out / (key + ".sof")
            sof.write_text("SYNTHETIC TEST FILE " + key, encoding="ascii")
            fw = fixture / (key + ".hex")
            fw.write_text("SYNTHETIC TEST FIRMWARE " + key, encoding="ascii")
            rows.append({"kernel": r["kernel"], "config": r["config"], "sof": sof.name, "fw": fw.name,
                "sha256": sha(sof), "fw_sha256": sha(fw), "fit_seed": "2", "rtl_aggregate": rtl,
                "expected_mcycle": r["mcycle"], "expected_minstret": r["minstret"],
                "expected_mcycle_hex": f"{int(r['mcycle']):08X}", "expected_minstret_hex": f"{int(r['minstret']):08X}"})
        write_csv(out / "INDEX.csv", rows)
        template = []
        for p in (1, 2):
            for r in rows:
                template.append({"pass": str(p), "kernel": r["kernel"], "config": r["config"],
                    "fit_seed": "2", "sof_sha256": r["sha256"], "expected_mcycle_hex": r["expected_mcycle_hex"],
                    "expected_minstret_hex": r["expected_minstret_hex"], "observed_ledr_hex": "",
                    "observed_mcycle_hex": "", "observed_minstret_hex": "", "uart_log": "", "photo": "", "status": "NOT_RUN"})
        write_csv(out / "BOARD_RESULTS_TEMPLATE.csv", template)
        result = completion.audit_sofs()
        assert result["sof_count"] == 100 and result["physical_status"] == "NOT_RUN"
        checks["accept_matching_synthetic_matrix"] = {"pass": True}
        rows[0]["fit_seed"] = "3"
        write_csv(out / "INDEX.csv", rows)
        reject("reject_mixed_board_seed", "Wrong board seed/RTL")
        rows[0]["fit_seed"] = "2"
        write_csv(out / "INDEX.csv", rows)
        template[0]["sof_sha256"] = template[1]["sof_sha256"]
        write_csv(out / "BOARD_RESULTS_TEMPLATE.csv", template)
        reject("reject_swapped_sof_in_result_template", "template differs from the SOF index")
        template[0]["sof_sha256"] = rows[0]["sha256"]
        write_csv(out / "BOARD_RESULTS_TEMPLATE.csv", template)
        cycle = rows[0]["expected_mcycle"]
        rows[0]["expected_mcycle"] = str(int(cycle) + 1)
        write_csv(out / "INDEX.csv", rows)
        reject("reject_changed_expected_cycle", "Expected mcycle differs")
        rows[0]["expected_mcycle"] = cycle
        write_csv(out / "INDEX.csv", rows)
        (out / rows[0]["sof"]).write_text("CORRUPTED TEST FILE", encoding="ascii")
        reject("reject_changed_sof_bytes", "checksum mismatch")
    assert {p.name: sha(p) for p in MIFS} == before and manifest()["aggregate"] == rtl
    report = {"scope": "SOF evidence association audit", "fixtures": "Synthetic files only; not SOFs or measurements",
              "checks": checks, "canonical_mifs_and_rtl_unchanged": True, "passed": True}
    path = ROOT / "results/board_preparation_audit_validation_20261009.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(f"[PASS] {len(checks)} final board audit checks; canonical MIFs and RTL unchanged -> {path}")


if __name__ == "__main__":
    main()
