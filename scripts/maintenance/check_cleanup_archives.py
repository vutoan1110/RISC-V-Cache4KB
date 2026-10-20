"""Verify the existing 19-run proposal and its archives; prepare, never delete.

Cross-check retained run states and executable inputs for dependencies on the
candidate paths. Historical mentions are reported separately from file inputs.
"""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/workspace_audit"


def sha(path):
    d = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            d.update(block)
    return d.hexdigest()


def main():
    proposal = json.loads((ROOT / "results/cleanup_proposal_20261009.json").read_text())
    candidates = [r for r in proposal["records"] if r["decision"] == "PROPOSE_ONLY"]
    if len(candidates) != 19:
        raise RuntimeError("Expected exactly the previously archived 19-run proposal")
    tags = {r["path"].split("/")[-1]: r["path"] for r in candidates}
    # Path boundary avoids mistaking '_ecomin_r1' for a longer tag or archive.
    expression = re.compile(r"(?:/runs/|\\runs\\)(" + "|".join(map(re.escape, tags)) + r")(?:/|\\|[\"'\s]|$)")
    protected_refs, mentions = [], []
    inventory = []
    with (OUT / "paths.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row["type"] != "file":
                continue
            inventory.append(row)
            rel = row["path"]
            if any(rel.startswith(r["path"] + "/") for r in candidates):
                continue
            if rel.startswith(("results/pd_run_archive/", "asic/openlane-local/", ".git/")):
                continue
            path = ROOT / rel
            if path.suffix not in (".json", ".sh", ".ps1", ".py", ".tcl", ".ys", ".eqy", ".sdc", ".cfg") and path.name != "BRANCHED_FROM":
                continue
            if row["bytes"] > 10 * 1024 * 1024:
                continue
            try:
                body = path.read_text(encoding="utf-8", errors="replace").replace("\\\\", "/")
            except OSError:
                continue
            found = sorted(set(expression.findall(body)))
            if not found:
                continue
            item = {"path": rel, "tags": found}
            if path.name in ("state_in.json", "state_out.json", "resolved.json"):
                protected_refs.append(item)
            else:
                mentions.append(item)
    plans = []
    for row in candidates:
        source = (ROOT / row["path"]).resolve()
        source.relative_to(ROOT.resolve())
        if source.parent.name != "runs" or source.parent.parent.name not in ("soc_dm_4kb", "soc_sa2_4kb", "soc_vc4_4kb"):
            raise RuntimeError(f"Unexpected source directory {source}")
        archive = (ROOT / row["archive"]["path"]).resolve()
        archive.relative_to((ROOT / "results/pd_run_archive").resolve())
        manifest_path = archive / "archive_manifest.json"
        manifest = json.loads(manifest_path.read_text())
        if manifest["source"] != row["path"] or "resolved.json" not in manifest["files"]:
            raise RuntimeError("Archive identity or resolved config missing")
        for rel, entry in manifest["files"].items():
            src, dest = source / rel, archive / rel
            src.resolve().relative_to(source)
            dest.resolve().relative_to(archive)
            if sha(src) != entry["sha256"] or sha(dest) != entry["sha256"]:
                raise RuntimeError(f"Archive mismatch: {row['path']}/{rel}")
        steps = sorted((p for p in source.iterdir() if p.is_dir() and re.match(r"^\d+-", p.name)),
                       key=lambda p: int(p.name.split("-")[0]))
        merged = {}
        for step in steps:
            state = step / "state_out.json"
            if state.is_file():
                merged.update(json.loads(state.read_text())["metrics"])
        if json.loads((archive / "final_metrics.json").read_text()) != merged:
            raise RuntimeError("Archived merged metrics differ")
        listing = [p.name + (" COMPLETE" if (p / "state_out.json").is_file() else " NO_STATE_OUT") for p in steps]
        if (archive / "step_list.txt").read_text().splitlines() != listing:
            raise RuntimeError("Archived step list differs")
        items = [r for r in inventory if r["path"].startswith(row["path"] + "/")]
        record = {"path": row["path"], "resolved_absolute": str(source),
            "files": len(items), "logical_bytes": sum(r["bytes"] for r in items),
            "archive": row["archive"]["path"], "archive_manifest_sha256": sha(manifest_path),
            "archive_files_verified": len(manifest["files"]),
            "archive_bytes_verified": sum(r["bytes"] for r in manifest["files"].values()),
            "last_steps": listing[-4:], "dependent_retained_states": [r for r in protected_refs if source.name in r["tags"]]}
        plans.append(record)
        print(f"[VERIFIED] {source.name}: {record['archive_files_verified']} archive files; {len(record['dependent_retained_states'])} retained state references", flush=True)
    receipt = {"status": "ARCHIVES_VERIFIED_NO_DELETION", "created": datetime.now().astimezone().isoformat(),
        "authorization": "Project owner explicitly requested obsolete-folder cleanup after workspace audit on 2026-10-09",
        "plans": plans, "retained_state_references": protected_refs, "other_references_for_review": mentions,
        "logical_bytes": sum(r["logical_bytes"] for r in plans),
        "archives_verified_bytes": sum(r["archive_bytes_verified"] for r in plans)}
    (OUT / "cleanup_preflight.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print(json.dumps({"count": len(plans), "logical_bytes": receipt["logical_bytes"], "state_dependencies": len(protected_refs), "other_mentions": len(mentions)}))


if __name__ == "__main__":
    main()
