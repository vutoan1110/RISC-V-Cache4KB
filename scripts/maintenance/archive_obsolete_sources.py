"""Preserve the audited obsolete sources/coverage before removing their originals.

This tool only archives and verifies. Removal is a separate native PowerShell
operation using the receipt's exact paths and hashes.
"""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "results/source_archive"
PATCHES = ["apply_r9.py", "apply_r10.py", "apply_r10_fix1.py", "apply_r10_fix2.py",
           "apply_r11.py", "apply_r12.py", "apply_r12b.py", "set_branch_port.py",
           "set_branch_keep.py", "set_branch_dedup.py", "build_final_metrics.py"]


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    archive = DEST / "obsolete_sources_20261009.zip"
    receipt_path = DEST / "retired_sources.json"
    if archive.exists() or receipt_path.exists():
        raise RuntimeError("Existing archive: inspect instead of overwriting")
    paths = [("scripts/" + name, "historical_scripts/" + name,
              "one-off historical RTL patch or superseded 8-KiB report; no retained runtime dependency", True) for name in PATCHES]
    paths += [("scripts/metrics/run_review_sims.sh", "historical_scripts/run_review_sims.sh", "obsolete runner targets removed self-written kernels", True),
        ("CODEX_PROMPT.md", "superseded_intake.txt", "duplicate old instructions; current rules retained in QUY_TRINH.md and project state", True),
        ("results/board_6c4ccffd_20261009_seed_comparison.md", "superseded_seed_selection.md", "per-configuration seed choice withdrawn; common seeds 1..10 and board seed2 are binding", True),
        ("scripts/make_golden_snapshot2.py", "golden_snapshot_before_descriptive_rename.py", "preserve original helper before descriptive rename; no golden data changed", False)]
    for name in ("axi_stress_test.cover.txt", "axi_stress_test.log", "axi_stress_test.status", "axi_stress_test.ucdb", "coverage_summary.txt", "merged.ucdb"):
        paths.append(("verification/uvm/out/" + name, "uvm_coverage_20260918/" + name,
                      "legacy functional coverage/stress from 2026-09-18; not current RTL coverage", True))
    rows = []
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for rel, member, reason, remove in paths:
            source = (ROOT / rel).resolve()
            source.relative_to(ROOT.resolve())
            raw = source.read_bytes()
            z.writestr(member, raw)
            rows.append({"path": rel, "member": member, "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(), "reason": reason, "remove_original": remove})
    with zipfile.ZipFile(archive) as z:
        for row in rows:
            if hashlib.sha256(z.read(row["member"])).hexdigest() != row["sha256"]:
                raise RuntimeError("Archive mismatch")
    receipt = {"status": "ARCHIVED_HASH_VERIFIED_NO_REMOVAL", "created": datetime.now().astimezone().isoformat(),
        "archive": archive.relative_to(ROOT).as_posix(), "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "files": rows}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print(f"Archived {len(rows)} files; {sum(r['remove_original'] for r in rows)} originals eligible for removal")


if __name__ == "__main__":
    main()
