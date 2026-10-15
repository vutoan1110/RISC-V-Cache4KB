"""Read-only post-cleanup validation of preserved research evidence.

Checks full CSV headers/fields, frozen input hashes, archive identities, removed
paths and coordinator-only document-path changes. It does not rerun a benchmark
or promote a measurement to a second independent execution.
"""
import ast
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/workspace_audit"


def read(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paired(stem, expected, keys):
    tables, headers = [], []
    for p in (1, 2):
        with (ROOT / (stem + f"_p{p}.csv")).open(newline="") as stream:
            reader = csv.DictReader(stream)
            headers.append(reader.fieldnames)
            rows = list(reader)
        assert len(rows) == expected, (stem, len(rows), expected)
        assert len(headers[-1]) == len(set(headers[-1])), (stem, "duplicate columns")
        assert all(None not in row and None not in row.values() for row in rows), stem
        table = {tuple(row[k] for k in keys): row for row in rows}
        assert len(table) == len(rows), (stem, "duplicate keys")
        tables.append(table)
    assert headers[0] == headers[1] and tables[0] == tables[1], stem
    if "result_pass" in headers[0]:
        assert all(r["result_pass"] == "1" and r["invariant_pass"] == "1" for r in tables[0].values()), stem
    return {"source": stem, "rows": expected, "columns": len(headers[0]), "all_fields_equal": True}


def main():
    proof = {"status": "IN_PROGRESS", "created": datetime.now().astimezone().isoformat(),
             "measurement_reexecution": False, "checks": {}}
    manifest = subprocess.run([sys.executable, "scripts/rtl_manifest.py", "--check"], cwd=ROOT,
                              text=True, capture_output=True)
    assert manifest.returncode == 0 and "IDENTICAL" in manifest.stdout, manifest.stdout
    proof["checks"]["manifest"] = {"count": read("results/rtl_manifest.json")["count"], "identical": True}
    proof["checks"]["paired_csvs"] = [paired(stem, expected, keys) for stem, expected, keys in (
        ("results/rfbht_4kb", 72, ("kernel", "config")),
        ("results/rfbhtf_4kb", 60, ("kernel", "config")),
        ("results/coremark_rfbht_4kb", 6, ("kernel", "config")),
        ("results/coremark_rfbhtf_4kb", 5, ("kernel", "config")),
        ("results/upstream_asic_rfbht", 12, ("kernel", "config")),
        ("results/board_reference_6c4ccffd_20261009", 100, ("kernel", "config")),
        ("results/random_diff_rfbht", 50, ("seed",)))]
    ref = read("results/board_reference_6c4ccffd_20261009_inputs.json")
    ref_counts = {}
    for group in ("firmware", "inputs", "compile_artifacts", "case_artifacts", "outputs"):
        for rel, digest in ref[group].items():
            assert sha(ROOT / rel) == digest, (group, rel)
        ref_counts[group] = len(ref[group])
    proof["checks"]["board_reference_hashes"] = ref_counts
    fits = read("results/paired10_6c4ccffd_20261009_plan.json")
    for rel, digest in fits["inputs"].items():
        assert sha(ROOT / rel) == digest, ("fit input", rel)
    progress = read("results/paired10_6c4ccffd_20261009_progress.json")
    for case, item in progress["done"].items():
        # Initial saved cases include per-report hashes; resumed cases carry
        # source CSV/report-directory provenance. Preserve both receipt forms.
        default_csv = "results/paired10_6c4ccffd_20261009_measurements/" + case.replace("/", "_") + ".csv"
        measurement = ROOT / item.get("source_csv", default_csv)
        assert measurement.is_file(), case
        if "measurement_sha256" in item:
            assert sha(measurement) == item["measurement_sha256"], case
        if isinstance(item["reports"], dict):
            assert all(sha(ROOT / rel) == digest for rel, digest in item["reports"].items()), case
        else:
            assert (ROOT / item["reports"]).is_dir(), case
    proof["checks"]["fit_inputs_unchanged"] = len(fits["inputs"])
    proof["checks"]["fit_status"] = {"status": progress["status"], "new_fits": len(progress["done"]), "final_matrix_verified": False}
    removed = read("results/workspace_audit/cleanup_execution.json")
    assert removed["status"] == "COMPLETE_17_ARCHIVED_RUNS_REMOVED" and len(removed["removed"]) == 17
    for row in removed["removed"]:
        assert not (ROOT / row["path"]).exists(), row["path"]
        archive = ROOT / row["archive"]
        assert sha(archive / "archive_manifest.json") == row["archive_manifest_sha256"], row["archive"]
        assert all((archive / x).is_file() for x in ("resolved.json", "final_metrics.json", "step_list.txt")), row["archive"]
    caches = read("results/workspace_audit/cache_cleanup.json")
    assert caches["status"] == "COMPLETE_22_SIMULATOR_CACHES_REMOVED" and len(caches["removed"]) == 22
    assert all(not (ROOT / row["path"]).exists() for row in caches["removed"])
    proof["checks"]["cleanup"] = {"pd_runs": 17, "simulation_libraries": 22,
        "logical_bytes_removed": removed["logical_bytes_removed"] + int(caches["logical_bytes_removed"])}
    preserved = read("results/workspace_audit/cleanup_proposal_outcome.json")
    assert all((ROOT / rel).is_dir() for rel in preserved["retained"])
    assert all((ROOT / rel).is_file() for rel in preserved["additional_blocked_files"])
    archived = read("results/source_archive/retired_sources.json")
    archive = ROOT / archived["archive"]
    assert sha(archive) == archived["archive_sha256"]
    with zipfile.ZipFile(archive) as z:
        for row in archived["files"]:
            assert hashlib.sha256(z.read(row["member"])).hexdigest() == row["sha256"]
            assert sha(ROOT / row["path"]) == row["sha256"], row["path"]
    proof["checks"]["blocked_originals_unchanged"] = len(archived["files"]) + len(preserved["additional_blocked_files"])
    before = (ROOT / "results/source_archive/board_coordinator_before_state_rename.py").read_text(encoding="utf-8")
    after = (ROOT / "scripts/fpga/complete_board_preparation.py").read_text(encoding="utf-8")
    expected = before.replace('"HANDOVER_CODEX.md"', '"PROJECT_STATE.md"')
    assert ast.dump(ast.parse(expected), include_attributes=False) == ast.dump(ast.parse(after), include_attributes=False)
    proof["checks"]["coordinator_logic_unchanged_except_document_path"] = True
    assert (ROOT / "PROJECT_STATE.md").is_file() and not (ROOT / "HANDOVER_CODEX.md").exists()
    supplement = read("results/workspace_audit/asic_input_provenance.json")
    for design in supplement["designs"].values():
        assert len(design["files"]) == 42
        assert all(sha(ROOT / rel) == digest for rel, digest in design["files"].items())
    proof["checks"]["asic_source_lists_unchanged"] = {k: v["source_count"] for k, v in supplement["designs"].items()}
    proof["status"] = "PASS_READ_ONLY_AUDIT_NO_NEW_MEASUREMENT"
    (OUT / "verification.json").write_text(json.dumps(proof, indent=2) + "\n", encoding="ascii")
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()
