"""Check board-builder rejection paths without changing MIFs or running Quartus.

Synthetic ten-seed fixtures test matrix identity only. They are temporary test
data, never FPGA measurements and never eligible for a PPA table or SOF build.
"""
from __future__ import annotations

import contextlib
import copy
import csv
import io
import json
import sys
import tempfile
from pathlib import Path

import build_board_matrix as builder
from board_common import ROOT, POINTS, UP, MIFS, manifest, sha, stamp


def main():
    before = {str(p.relative_to(ROOT)): sha(p) for p in MIFS}
    frozen = manifest()
    checks = {}

    def rejects(name, action, message):
        try:
            action()
        except RuntimeError as exc:
            if message not in str(exc):
                raise AssertionError(f"{name}: unexpected rejection: {exc}") from exc
            checks[name] = {"pass": True, "reason": str(exc)}
        else:
            raise AssertionError(f"{name}: invalid input was accepted")

    with (ROOT / "results/fpga_points_rfbht_p1.csv").open(newline="") as f:
        seed2 = {r["point"]: r for r in csv.DictReader(f) if r["seed"] == "2"}
    fit = {}
    for point in POINTS:
        for seed in range(1, 11):
            row = dict(seed2[point], point=point if seed == 2 else f"{point}@s{seed}", seed=str(seed))
            fit[row["point"], row["seed"]] = row
    ref = {}
    for name in ("upstream_r14_4kb_p1.csv", "ramsweep_r14_p1.csv", "upfull_r14_4kb_p1.csv"):
        with (ROOT / "results" / name).open(newline="") as f:
            ref.update({(r["kernel"], r["config"]): r for r in csv.DictReader(f)})
    receipt = {"rtl_id": frozen["aggregate"], "common_seed": 2,
        "points": {p: {"config": cfg, "seed": 2, "reference": dict(seed2[p])} for p, cfg in POINTS.items()}}
    firmware = {"fw/ramsweep.hex"} | {f"{folder}/{prefix}{k}.hex"
        for folder, prefix in (("fw", "up_"), ("fw_board", "upfull_")) for k in UP}
    meta = {"rtl_id": frozen["aggregate"], "firmware": {p: sha(ROOT / p) for p in firmware},
            "status": "VERIFIED_100_PAIRED_ROWS_EQUAL_R14"}
    builder.validate_matrix(receipt, meta, fit, ref)
    checks["accept_correct_matrix_identity_fixture"] = {"pass": True}

    wrong_fit = copy.deepcopy(fit)
    row = wrong_fit.pop(("dm_4kb@s10", "10"))
    row.update(point="dm_4kb@s11", seed="11")
    wrong_fit[row["point"], row["seed"]] = row
    rejects("reject_40_rows_with_different_seed_set",
            lambda: builder.validate_matrix(receipt, meta, wrong_fit, ref), "common seeds 1..10")
    wrong_facts = copy.deepcopy(receipt)
    wrong_facts["points"]["sa2_4kb"]["reference"]["le"] = "1"
    rejects("reject_receipt_facts_different_from_seed2",
            lambda: builder.validate_matrix(wrong_facts, meta, fit, ref), "fit facts do not match")
    wrong_ref = copy.deepcopy(ref)
    wrong_ref["other_kernel", "DM"] = wrong_ref.pop(("ramsweep", "DM"))
    rejects("reject_100_rows_with_wrong_kernel",
            lambda: builder.validate_matrix(receipt, meta, fit, wrong_ref), "25 board firmware images")
    wrong_meta = copy.deepcopy(meta)
    wrong_meta["firmware"]["fw/other.hex"] = wrong_meta["firmware"].pop("fw/ramsweep.hex")
    rejects("reject_25_images_with_wrong_firmware",
            lambda: builder.validate_matrix(receipt, wrong_meta, fit, ref), "firmware set differs")
    bad_fit = copy.deepcopy(fit)
    bad_receipt = copy.deepcopy(receipt)
    bad_fit["dm_4kb", "2"]["setup_s85_slack"] = "-0.001"
    bad_receipt["points"]["dm_4kb"]["reference"]["setup_s85_slack"] = "-0.001"
    rejects("reject_negative_board_setup_s85",
            lambda: builder.validate_matrix(bad_receipt, meta, bad_fit, ref), "fails setup at FPGA corner s85")

    # The main-entry guards are exercised while the real fits are running.
    # Any accidental tool invocation is an explicit test failure.
    def forbidden_tool(*args, **kwargs):
        raise AssertionError("Validation attempted a Quartus/MIF operation")

    builder.checked_tool = forbidden_tool
    with tempfile.TemporaryDirectory(prefix="board_guard_fixture_", dir=ROOT / "results") as folder:
        fixture = Path(folder).resolve()
        if not fixture.is_relative_to((ROOT / "results").resolve()):
            raise RuntimeError("Fixture outside research results")
        receipt_path = fixture / "receipt.json"
        meta_path = fixture / "reference_inputs.json"
        tag = fixture.relative_to(ROOT / "results").as_posix() + "/reference"

        def call():
            sys.argv = ["build_board_matrix.py", "--build", "--fit-receipt", str(receipt_path.relative_to(ROOT)),
                        "--reference-tag", tag, "--out", str((fixture / "no_build").relative_to(ROOT))]
            with contextlib.redirect_stdout(io.StringIO()):
                return builder.main()

        if call() != 2:
            raise AssertionError("Missing verified inputs were not held at readiness check")
        checks["wait_for_missing_verified_inputs"] = {"pass": True}
        meta_path.write_text(json.dumps(meta), encoding="ascii")
        wrong_seed = copy.deepcopy(receipt)
        wrong_seed["common_seed"] = 3
        receipt_path.write_text(json.dumps(wrong_seed), encoding="ascii")
        rejects("reject_common_seed_other_than_2", call, "Require common board seed 2")
        mixed = copy.deepcopy(receipt)
        mixed["points"]["vc4_4kb"]["seed"] = 1
        receipt_path.write_text(json.dumps(mixed), encoding="ascii")
        rejects("reject_per_configuration_board_seeds", call, "Per-configuration board seeds are forbidden")
        receipt_path.write_text(json.dumps(receipt), encoding="ascii")
        meta_path.write_text(json.dumps(dict(meta, status="IN_PROGRESS")), encoding="ascii")
        rejects("reject_unfinished_reference", call, "reference is not yet verified")
        if (fixture / "no_build").exists():
            raise AssertionError("A rejected build created an output directory")

    if {str(p.relative_to(ROOT)): sha(p) for p in MIFS} != before or manifest() != frozen:
        raise AssertionError("Validation changed canonical MIFs or frozen RTL")
    checks["canonical_mifs_and_rtl_unchanged"] = {"pass": True}
    report = {"completed": stamp(), "scope": "Board builder guards; no Quartus, no MIF mutation",
        "fixtures": "Synthetic identities only, not FPGA measurements", "checks": checks,
        "canonical_mif_sha256": before, "passed": True}
    out = ROOT / "results/board_builder_guard_validation_20261009.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(f"[PASS] {len(checks)} board builder checks; canonical MIFs and RTL unchanged -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
