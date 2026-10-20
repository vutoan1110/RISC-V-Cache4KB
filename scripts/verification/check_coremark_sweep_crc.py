"""Check sweep metadata/profile rejection with preserved reference data."""
from __future__ import annotations

import copy
import csv
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_coremark_sweep_crc as runner


def main():
    output = runner.ROOT / "results/coremark_sweep_crc_controls_20261010"
    output.mkdir(exist_ok=False)
    cases, refs = runner.baselines()
    spec = importlib.util.spec_from_file_location("grid_controls", runner.ROOT / "scripts/m2/run_m2_sweep.py")
    sweep = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sweep)
    grid = {p["point"]: p for p in sweep.grid()}
    with refs[0].open(newline="") as stream:
        reader = csv.DictReader(stream)
        header = reader.fieldnames
        rows = [r for r in reader if r["workload"] == "coremark"]
    checks = []

    def check(label, action, accept=False):
        try:
            action()
            rejected = False
        except (ValueError, RuntimeError):
            rejected = True
        if rejected == accept:
            raise AssertionError("Control verdict failed: " + label)
        checks.append({"label": label, "expected": "ACCEPT" if accept else "REJECT", "pass": True})

    check("all_92_preserved_paired_reference_points", runner.baselines, True)

    def csv_case(label, changed_rows, changed_header=None, fast=0):
        path = output / (label + ".csv")
        with path.open("w", newline="", encoding="ascii") as stream:
            writer = csv.DictWriter(stream, fieldnames=changed_header or header, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(changed_rows)
        check(label, lambda: runner.read_reference(path, grid, fast))

    csv_case("missing_point", rows[:-1])
    csv_case("duplicate_point", rows + [rows[0]])
    for field, value in (("cfg", "4"), ("cap_bytes", "8191"), ("line_bytes", "8"),
                         ("lines", "63"), ("vc", "8"), ("org", "SA4"),
                         ("point", "unknown"), ("mcycle", "-1"), ("minstret", "0"),
                         ("result_pass", "0"), ("invariant_pass", "")):
        changed = copy.deepcopy(rows)
        changed[0][field] = value
        csv_case("wrong_" + field, changed)
    changed = copy.deepcopy(rows)
    changed[0]["point"] = runner.EXCLUDED
    csv_case("unsupported_small_sa4_point", changed)
    csv_case("missing_counter_header", rows, [k for k in header if k != "trap_ev"])
    csv_case("duplicate_counter_header", rows, [*header, "mcycle"])
    csv_case("extra_header", rows, [*header, "unexpected"])
    csv_case("dm_in_fast_sweep", rows, fast=1)

    case = cases[0]
    values = {k: case[k] for k in runner.PARAMETERS}
    values.update(d_lines=case["lines"], imem_words=4096, dmem_words=4096, l0_entries=8, predictor=1)

    def profile(data):
        return "# COREMARK_SWEEP_PROFILE " + " ".join(f"{k}={data[k]}" for k in runner.PROFILE) + "\n"

    good = profile(values)
    check("actual_elaborated_profile", lambda: runner.validate_profile(good, case), True)
    for key in runner.PROFILE:
        wrong = dict(values)
        wrong[key] += 1
        check("wrong_elaborated_" + key, lambda p=profile(wrong): runner.validate_profile(p, case))
    check("missing_profile", lambda: runner.validate_profile("", case))
    check("duplicate_profile", lambda: runner.validate_profile(good + good, case))
    check("profile_cannot_mask_simulator_fatal", lambda: runner.validate_profile(good + "# ** Fatal: fixture\n", case))
    check("profile_cannot_mask_simulator_error", lambda: runner.validate_profile(good + "# ** Error: fixture\n", case))
    check("profile_cannot_mask_failed_case", lambda: runner.validate_profile(good + "# [FAIL] fixture\n", case))
    source = (HERE / "coremark_uart_observer.sv").read_text()
    check("original_observer_rejected_if_forwarding_anchor_changes",
          lambda: runner.wrapper_text(source.replace(".IMEM_DEPTH(IMEM_DEPTH)", ".IMEM_DEPTH(2048)")))
    wrapper = runner.wrapper_text(source)
    if any(s not in wrapper for s in (".CACHE_LINE_WORDS(CACHE_LINE_WORDS)",
             ".VICTIM_ENTRIES(VICTIM_ENTRIES)", "bench.DCACHE_LINE_COUNT", "bench.BRANCH_PREDICT_ENABLE")):
        raise AssertionError("Generated wrapper lacks required forwarding/profile")
    receipt = {"status": "PASS", "not_a_measurement": True, "checks": checks,
        "checker_sha256": runner.sha(Path(__file__)), "runner_sha256": runner.sha(HERE / "run_coremark_sweep_crc.py"),
        "reference_sha256": {p.relative_to(runner.ROOT).as_posix(): runner.sha(p) for p in refs},
        "generated_wrapper_sha256": __import__("hashlib").sha256(wrapper.encode("ascii")).hexdigest()}
    runner.write_json(output / "verification.json", receipt)
    print(f"[PASS] {len(checks)} sweep reference/profile controls; no simulation/RTL modification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
