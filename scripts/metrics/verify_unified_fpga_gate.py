"""Check complete FPGA table evidence and reject synthetic invalid metadata.

Only in-memory copies are changed. No fit, simulator or PD tool is launched,
and no measured CSV, report, receipt or earlier audit is rewritten.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
from pathlib import Path

import unified_table as table


def main():
    tag, root = table.FPGA_TAG, table.ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="results/unified_fpga_table_gate_20261010.json")
    args = parser.parse_args()
    out = (root / args.out).resolve()
    if not out.is_relative_to((root / "results").resolve()):
        raise RuntimeError("Table audit must remain inside the research results folder")
    if out.exists():
        raise RuntimeError("Audit exists; preserve it and choose a new dated audit before repeating")
    selected, evidence = table.verified_fpga()
    import run_fpga_points
    import continue_common_seed_preparation as audit
    cols = run_fpga_points.COLS
    paths = {kind: root / f"results/{tag}_{kind}.json"
             for kind in ("plan", "progress", "board_fit_receipt", "ppa")}
    meta = {kind: json.loads(path.read_text()) for kind, path in paths.items()}

    def read(name):
        with (root / "results" / name).open(newline="", encoding="utf-8") as stream:
            return list(csv.DictReader(stream))

    raw = [read(f"fpga_points_{tag}_p{n}.csv") for n in (1, 2)]
    maps = table.fpga_hardware_pair(raw, cols, range(1, 11))
    baseline = table.fpga_hardware_pair([read(f"fpga_points_rfbht_p{n}.csv") for n in (1, 2)],
                                       cols, range(1, 5))
    rtl_id = audit.manifest()["aggregate"]
    plan_sha = table.digest(paths["plan"])
    checks = []

    def reject(name, operation):
        try:
            operation()
        except (RuntimeError, ValueError, KeyError) as exc:
            checks.append({"control": name, "caught": True, "reason": str(exc)})
        else:
            raise AssertionError("Invalid FPGA evidence accepted: " + name)

    def metadata(name, group, mutate):
        one = copy.deepcopy(meta)
        mutate(one[group])
        reject(name, lambda: table.check_fpga_completion(one["plan"], one["progress"],
            one["board_fit_receipt"], one["ppa"], maps, baseline, cols, rtl_id, plan_sha))

    def matrix(name, mutate):
        one = copy.deepcopy(raw)
        mutate(one)
        reject(name, lambda: table.fpga_hardware_pair(one, cols, range(1, 11)))

    # Runtime may vary; every recorded hardware field must agree.
    runtime = copy.deepcopy(raw)
    runtime[1][0]["seconds"] = "different elapsed time"
    assert table.fpga_hardware_pair(runtime, cols, range(1, 11))
    matrix("missing_seed_row", lambda d: d[1].pop())
    matrix("duplicate_point_seed", lambda d: d[1].__setitem__(-1, copy.deepcopy(d[1][0])))
    matrix("different_hardware_field", lambda d: d[1][0].update(pow_core_static_mw="999"))
    matrix("empty_hardware_field", lambda d: d[1][0].update(cur_vcca_ma=""))
    matrix("wrong_cache_geometry", lambda d: d[0][0].update(capacity_bytes="1024"))
    matrix("wrong_configuration", lambda d: d[0][0].update(cache_config="5"))
    matrix("unapproved_seed", lambda d: d[1][0].update(seed="11", point="dm_4kb@s11"))
    matrix("extra_field", lambda d: d[1][0].update(unrecorded="1"))
    metadata("wrong_rtl", "plan", lambda d: d.update(rtl_id="0" * 64))
    metadata("per_configuration_seed_policy", "plan", lambda d: d.update(common_seed={"DM": 3, "SA2": 3}))
    metadata("incomplete_fit_status", "progress", lambda d: d.update(status="FITTING"))
    metadata("different_plan_hash", "progress", lambda d: d.update(plan_sha256="0" * 64))
    metadata("missing_new_fit", "progress", lambda d: d["done"].pop("p2/dse_4kb/s2"))
    metadata("missing_origin", "progress", lambda d: d["row_origins"].pop("p2/dse_4kb/s1"))
    metadata("same_source_csv_twice", "progress", lambda d: d["row_origins"]["p2/dm_4kb/s2"].update(
        source_csv=d["row_origins"]["p1/dm_4kb/s2"]["source_csv"]))
    metadata("same_report_set_twice", "progress", lambda d: d["row_origins"]["p2/dm_4kb/s2"].update(
        reports=d["row_origins"]["p1/dm_4kb/s2"]["reports"]))
    metadata("wrong_reuse_provenance", "progress", lambda d: d["row_origins"]["p2/dm_4kb/s3"].update(
        kind="new_independent_measurement"))
    metadata("receipt_other_pass_csv", "board_fit_receipt", lambda d: d.update(fit_p2=d["fit_p1"]))
    metadata("missing_fit_report_hash", "board_fit_receipt", lambda d: d["reports"].pop(
        "output_files_sa2_4kb/point_sa2_4kb.fit.rpt"))
    metadata("different_settings_hash", "board_fit_receipt", lambda d: d["settings"].update(
        {"scripts/run_fpga_points.py": "0" * 64}))
    metadata("missing_seed2_configuration", "board_fit_receipt", lambda d: d["points"].pop("vc4_4kb"))
    metadata("changed_seed2_row", "board_fit_receipt", lambda d: d["points"]["dm_4kb"]["reference"].update(le="999"))
    metadata("wrong_timing_corner", "ppa", lambda d: d.update(timing_corner="Fast 0 C"))
    metadata("unsupported_power_method", "ppa", lambda d: d.update(power_method="measured board power"))
    metadata("wrong_pair_count", "ppa", lambda d: d.update(paired_rows=39))
    metadata("missing_paired_csv_hash", "ppa", lambda d: d["sources"].pop(next(iter(d["sources"]))))
    bad_hash = {"results/fpga_points_" + tag + "_p1.csv": "0" * 64}
    reject("changed_measurement_hash", lambda: audit.verify_hashes(bad_hash))
    bad_report = {"results/fpga_points/" + tag + "_p2/dse_4kb/s2/point_dse_4kb.fit.rpt": "0" * 64}
    reject("changed_fit_report_hash", lambda: audit.verify_hashes(bad_report))
    bad_baseline = copy.deepcopy(baseline)
    bad_baseline[1]["dm_4kb", 2]["le"] = "999"
    reject("seed2_refit_differs_from_old_evidence", lambda: table.check_fpga_completion(
        meta["plan"], meta["progress"], meta["board_fit_receipt"], meta["ppa"], maps, bad_baseline,
        cols, rtl_id, plan_sha))
    assert all(table.digest((root / rel.replace("\\", "/")).resolve()) == sha for rel, sha in evidence.items())
    report = {"status": "TABLE_GATE_FIXTURES_VERIFIED_NOT_NEW_MEASUREMENTS",
              "positive_control": f"40 independently paired rows; all 115 hardware fields; {len(evidence)} evidence hashes",
              "runtime_difference_accepted": True, "negative_controls": checks,
              "generator_sha256": table.digest(Path(table.__file__)), "test_sha256": table.digest(Path(__file__)),
              "evidence_hashes": evidence,
              "seed2": {p: {k: row[k] for k in ("seed", "le", "fmax")} for p, row in selected.items()}}
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    print(f"[PASS] complete FPGA evidence and {len(checks)} invalid-evidence controls; {out.relative_to(root)}")


if __name__ == "__main__":
    main()
