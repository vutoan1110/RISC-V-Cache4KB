"""Verify continuation evidence and rejection guards without running Quartus."""
from __future__ import annotations

import copy
import io
import json
from pathlib import Path
from unittest.mock import patch

import continue_common_seed_preparation as continuation


def main():
    driver = continuation.fitter()
    original, progress, baseline, tables, evidence, meta, reference = continuation.inspect_source(driver)
    checks = [{"name": "all_32_original_inputs_51_measurements_and_100_reference_pairs", "status": "PASS"}]

    def reject(name, fn, contains):
        try:
            fn()
        except (RuntimeError, KeyError, ValueError) as exc:
            if contains not in str(exc):
                raise AssertionError(f"{name}: unexpected rejection: {exc}") from exc
            checks.append({"name": name, "status": "PASS", "rejection": str(exc)})
        else:
            raise AssertionError(f"{name}: unsafe input was accepted")

    rel = next(iter(original["inputs"]))
    reject("changed_original_input_hash", lambda: continuation.verify_hashes({rel: "0" * 64}), "Frozen evidence changed")
    bad = copy.deepcopy(progress)
    bad["done"]["p2/sa2_4kb/s2"] = bad["done"].pop("p1/dm_4kb/s5")
    reject("out_of_order_completed_measurement", lambda: continuation.validate_progress(bad, tables, baseline, driver.COLS), "ordered prefix")
    bad_tables = copy.deepcopy(tables)
    bad_tables[1]["dse_4kb", 10] = copy.deepcopy(tables[0]["dse_4kb", 10])
    reject("unrecorded_aggregate_measurement", lambda: continuation.validate_progress(progress, bad_tables, baseline, driver.COLS), "unrecorded")
    row = copy.deepcopy(tables[0]["dm_4kb", 2])
    bad_row = copy.deepcopy(row)
    bad_row["le"] = ""
    reject("missing_hardware_field", lambda: continuation.check_row(bad_row, "dm_4kb", 2, driver.COLS), "Incomplete")
    bad_row = copy.deepcopy(row)
    bad_row["cache_config"] = "3"
    reject("wrong_cache_configuration", lambda: continuation.check_row(bad_row, "dm_4kb", 2, driver.COLS), "cache configuration")
    bad_row = copy.deepcopy(row)
    bad_row["seed"] = "9"
    reject("wrong_measurement_seed", lambda: continuation.check_row(bad_row, "dm_4kb", 2, driver.COLS), "measurement identity")
    bad_row = copy.deepcopy(row)
    bad_row["le"] = str(int(row["le"]) + 1)
    reject("different_hardware_field", lambda: continuation.same_row(row, bad_row, "control", ignore=("seconds",)), "Measurement differs")
    different_time = copy.deepcopy(row)
    different_time["seconds"] = "999999"
    continuation.same_row(row, different_time, "runtime_control", ignore=("seconds",))
    checks.append({"name": "runtime_difference_is_not_a_hardware_difference", "status": "PASS"})
    first_key = "p1/dm_4kb/s2"
    bad = copy.deepcopy(progress)
    bad["done"][first_key]["measurement_sha256"] = "0" * 64
    reject("changed_completed_measurement_hash", lambda: continuation.validate_progress(bad, tables, baseline, driver.COLS), "measurement hash differs")
    bad = copy.deepcopy(progress)
    bad["done"][first_key]["reports"] = {}
    reject("missing_report_hashes", lambda: continuation.validate_progress(bad, tables, baseline, driver.COLS), "report hashes are incomplete")
    bad = copy.deepcopy(progress)
    bad["row_origins"][first_key]["kind"] = "existing_independent_measurement"
    reject("completed_fit_relabeled_as_reused", lambda: continuation.validate_progress(bad, tables, baseline, driver.COLS), "completed-fit provenance")
    with patch.object(Path, "read_text", return_value="Fitter Initial Placement Seed ; 9\nEP4CE115F29C7"):
        reject("wrong_seed_in_fitter_report", lambda: continuation.check_seed_report("dm_4kb", 2, Path("unused")), "wrong seed")
    with patch.object(Path, "read_text", return_value="Fitter Initial Placement Seed ; 2\nOTHER_DEVICE"):
        reject("wrong_device_in_fitter_report", lambda: continuation.check_seed_report("dm_4kb", 2, Path("unused")), "Wrong FPGA device")
    with patch.object(Path, "open", return_value=io.StringIO("point,seed\ndm_4kb,2\ndm_4kb,2\n")):
        reject("duplicate_csv_key", lambda: continuation.load_csv(Path("unused")), "duplicate")
    bad_meta = copy.deepcopy(meta)
    bad_meta["status"] = "IN_PROGRESS"
    with patch.object(continuation, "read_json", return_value=bad_meta):
        reject("reference_not_double_verified", continuation.verify_reference, "not independently verified")

    def memory_guard():
        state = {}
        writes = []
        with patch.object(Path, "exists", return_value=False), patch.object(continuation, "check_idle"), \
             patch.object(continuation, "free_mb", return_value=5999), \
             patch.object(continuation, "write_json", side_effect=lambda p, s: writes.append(copy.deepcopy(s))), \
             patch.object(continuation.time, "sleep", side_effect=RuntimeError("guarded_wait_control")):
            reject("5999_mb_starts_no_measurement", lambda: continuation.wait_for_memory(state, Path("unused")), "guarded_wait_control")
        assert writes and writes[-1]["status"] == "WAITING_FOR_MEMORY" and writes[-1]["available_mb"] == 5999
    memory_guard()
    with patch.object(Path, "exists", return_value=False), patch.object(continuation, "check_idle"), \
         patch.object(continuation, "free_mb", return_value=6000):
        assert continuation.wait_for_memory({}, Path("unused")) == 6000
    checks.append({"name": "6000_mb_guard_boundary_accepted", "status": "PASS"})
    with patch.object(Path, "exists", return_value=False), \
         patch.object(continuation, "check_idle", side_effect=RuntimeError("Another Quartus job is running")):
        reject("concurrent_quartus_is_rejected", lambda: continuation.wait_for_memory({}, Path("unused")), "Another Quartus")
    with patch.object(Path, "exists", return_value=True):
        reject("cooperative_abort_starts_no_tool", lambda: continuation.wait_for_memory({}, Path("unused")), "Cooperative abort")

    summary = {"created": continuation.stamp(), "status": "PASS", "checks": checks,
        "source_script": continuation.relative(Path(continuation.__file__)),
        "source_sha256": continuation.sha(Path(continuation.__file__)),
        "test_sha256": continuation.sha(Path(__file__)), "original_input_count": 32,
        "preserved_completed_measurements": 51, "verified_reference_pairs": 100,
        "tools_launched": 0, "rtl_or_existing_evidence_mutations": 0}
    out = continuation.ROOT / "results/fpga_common_seed_continuation_validation_20261009.json"
    if out.exists():
        raise RuntimeError("Validation artifact already exists; preserve it and use a new dated name")
    continuation.write_json(out, summary)
    print(f"[VERIFIED] {len(checks)} evidence/guard controls; no Quartus or simulation launched; {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
