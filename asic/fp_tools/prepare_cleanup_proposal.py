"""Classify the handover inventory and archive eligible evidence; never delete.

Signed-off runs, their protected source runs, synthesis provenance and VC4
floorplan controls still needed for T5 are excluded from the proposal.
"""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASIC = ROOT / "asic"
INVENTORY = ROOT / "results/cleanup_candidates_20261009_sizes.txt"
OUT = ROOT / "results/cleanup_proposal_20261009.json"
SIGNED_SA2 = "sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf"
PROTECTED = {"r14F_A", "r14F_B", "final3_A", "final3_B", "dmuA", "dmuB",
             SIGNED_SA2 + "_r1", SIGNED_SA2 + "_r2", SIGNED_SA2 + "_ecomaxmin_r1", SIGNED_SA2 + "_ecomaxmin_r2"}
DEFER = {"vc4_corr3600x3400_f220_r1", "vc4_corr3800x3400_f220_r1"}


def sha(path):
    d = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            d.update(b)
    return d.hexdigest()


def merged_metrics(run):
    m = {}
    steps = sorted((p for p in run.iterdir() if p.is_dir() and re.match(r"^\d+-", p.name)),
                   key=lambda p: int(p.name.split("-")[0]))
    for p in steps:
        state = p / "state_out.json"
        if state.is_file():
            m.update(json.loads(state.read_text())["metrics"])
    return steps, m


def archive(run):
    dest = ROOT / "results/pd_run_archive" / run.name
    if not (run / "resolved.json").is_file():
        return {"status": "MISSING_RESOLVED_CONFIG_NOT_ELIGIBLE", "path": dest.relative_to(ROOT).as_posix()}
    if dest.exists():
        manifest = dest / "archive_manifest.json"
        if manifest.is_file():
            recorded = json.loads(manifest.read_text())
            if recorded.get("source") != run.relative_to(ROOT).as_posix() or "resolved.json" not in recorded.get("files", {}):
                raise RuntimeError(f"Existing archive provenance is incomplete: {dest}")
            for rel, item in recorded["files"].items():
                source, target = run / rel, dest / rel
                source.resolve().relative_to(run.resolve())
                target.resolve().relative_to(dest.resolve())
                if sha(source) != item["sha256"] or sha(target) != item["sha256"]:
                    raise RuntimeError(f"Existing archive/source mismatch: {rel}")
            if not (dest / "final_metrics.json").is_file() or not (dest / "step_list.txt").is_file():
                raise RuntimeError(f"Existing archive metrics or step list missing: {dest}")
            return {"status": "EVIDENCE_ARCHIVED_NO_DELETION", "path": dest.relative_to(ROOT).as_posix(),
                    "files": len(recorded["files"]), "bytes": sum(v["bytes"] for v in recorded["files"].values())}
        return {"status": "EXISTING_ARCHIVE_REQUIRES_REVIEW", "path": dest.relative_to(ROOT).as_posix()}
    steps, metrics = merged_metrics(run)
    dest.mkdir(parents=True)
    paths = set(run.glob("*.log")) | set(run.glob("*.json")) | set(run.glob("logs/*.log"))
    if (run / "BRANCHED_FROM").is_file():
        paths.add(run / "BRANCHED_FROM")
    for step in steps:
        paths.update(p for p in step.rglob("*") if p.is_file() and
                     (p.suffix in (".log", ".rpt") or p.name in ("state_out.json", "runtime.txt", "COMMANDS")))
    copied = {}
    for source in sorted(paths):
        source.resolve().relative_to(run.resolve())
        target = dest / source.relative_to(run)
        target.parent.mkdir(parents=True, exist_ok=True)
        before = sha(source)
        shutil.copy2(source, target)
        if sha(source) != before or sha(target) != before:
            raise RuntimeError(f"Archive mismatch or source changed: {source}")
        copied[source.relative_to(run).as_posix()] = {"sha256": before, "bytes": source.stat().st_size}
    if "resolved.json" not in copied:
        raise RuntimeError(f"Required resolved.json missing: {run}")
    (dest / "final_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="ascii")
    listing = [p.name + (" COMPLETE" if (p / "state_out.json").is_file() else " NO_STATE_OUT") for p in steps]
    (dest / "step_list.txt").write_text("\n".join(listing) + "\n", encoding="ascii")
    (dest / "archive_manifest.json").write_text(json.dumps({"status": "EVIDENCE_ARCHIVED_NO_DELETION",
        "source": run.relative_to(ROOT).as_posix(), "files": copied, "metrics_are_diagnostic_if_run_failed": True},
        indent=2) + "\n", encoding="ascii")
    return {"status": "EVIDENCE_ARCHIVED_NO_DELETION", "path": dest.relative_to(ROOT).as_posix(),
            "files": len(copied), "bytes": sum(v["bytes"] for v in copied.values())}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", action="store_true", help="copy text evidence only; never delete source files")
    args = ap.parse_args()
    if OUT.exists():
        raise RuntimeError("Proposal already exists; review instead of overwriting")
    records = []
    for line in INVENTORY.read_text().splitlines():
        mb, rel, date = line.split()
        run = (ASIC / rel).resolve()
        run.relative_to(ASIC.resolve())
        if run.parent.name != "runs" or run.parent.parent.name not in ("soc_dm_4kb", "soc_sa2_4kb", "soc_vc4_4kb"):
            raise RuntimeError(f"Unexpected inventory path: {rel}")
        if not run.is_dir():
            raise RuntimeError(f"Inventory path no longer exists: {run}")
        tag = run.name
        decision, reason = "PROPOSE_ONLY", "failed or superseded run; explicit owner approval still required"
        if tag in PROTECTED:
            decision, reason = "KEEP", "locked/sign-off/source run or reported corridor control"
        elif "synth" in tag:
            decision, reason = "DEFER", "synthesis provenance; do not delete before the relevant proof inputs are reviewed"
        elif tag in DEFER:
            decision, reason = "DEFER", "old VC4 die/clock-routing control still needed until T5"
        elif tag == "sa2uB":
            decision, reason = "KEEP", "reported 54-iteration routing trajectory and sign-off baseline"
        row = {"path": run.relative_to(ROOT).as_posix(), "inventory_mb": int(mb),
               "inventory_date": date, "decision": decision, "reason": reason}
        if args.archive and decision == "PROPOSE_ONLY":
            row["archive"] = archive(run)
            if row["archive"]["status"] != "EVIDENCE_ARCHIVED_NO_DELETION":
                row["decision"] = "DEFER"
                row["reason"] = "required archive evidence incomplete; not eligible for deletion approval"
            print(f"[ARCHIVE] {tag}: {row['archive']['status']}", flush=True)
        records.append(row)
    proposal = {"status": "OWNER_APPROVAL_REQUIRED_NO_DELETION", "inventory_source": INVENTORY.relative_to(ROOT).as_posix(),
        "inventory_sha256": sha(INVENTORY), "sizes_are_original_inventory_not_guaranteed_reclaimed_space": True,
        "proposed_count": sum(r["decision"] == "PROPOSE_ONLY" for r in records),
        "proposed_inventory_mb": sum(r["inventory_mb"] for r in records if r["decision"] == "PROPOSE_ONLY"),
        "records": records}
    OUT.write_text(json.dumps(proposal, indent=2) + "\n", encoding="ascii")
    lines = ["# Cleanup proposal: approval required, no deletion performed", "",
        "The handover size file is an inventory containing protected runs as well as possible candidates. "
        "The list below separates them. Sizes are the original inventory MB, not a freshly measured or guaranteed "
        "reclaimed amount. Synthesis evidence and VC4 controls needed by T5 are deferred.", "",
        "Text evidence archives include resolved config, merged metrics, step list, flow/step logs, "
        "warning/error logs and timing reports; copied files are hash-checked. No source is removed. "
        "A deletion would require explicit approval and a separate log entry for each removed run.", "",
        "| inventory path under asic/ | MB | decision | reason | archive |", "|---|---:|---|---|---|"]
    for r in records:
        lines.append(f"| {r['path'][5:]} | {r['inventory_mb']} | {r['decision']} | {r['reason']} | "
                     f"{r.get('archive', {}).get('status', 'not archived for deletion')} |")
    OUT.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"[PREPARED] {proposal['proposed_count']} proposed runs, {proposal['proposed_inventory_mb']} original inventory MB; no deletion", flush=True)


if __name__ == "__main__":
    main()
