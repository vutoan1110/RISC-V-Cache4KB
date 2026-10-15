"""Stage byte-exact legacy LEC inputs and proposed path-only reader updates.

Default mode inspects. --stage creates archive copies, original reader copies,
proposed reader files and a reviewable patch. Existing readers, result reports,
RTL, signed layouts and the source run are never changed or deleted.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WSL_ROOT = "/mnt/e/Projects/RISCV-research"
OLD_REL = "asic/soc_dm_4kb/runs/final_B"
OLD_WSL = WSL_ROOT + "/" + OLD_REL
ARCHIVE_REL = "results/pd_run_archive/final_B"
ARCHIVE_INPUT_REL = ARCHIVE_REL + "/dependency_inputs"
ARCHIVE_INPUT_WSL = WSL_ROOT + "/" + ARCHIVE_INPUT_REL
STAGING_REL = "results/final_b_dependency_migration_20261009"
DEPS = (
    "79-yosys-eqy/formal_pdk.v",
    "54-openroad-fillinsertion/soc_asic_top.nl.v",
    "06-yosys-synthesis/config.json",
    "06-yosys-synthesis/extra.json",
    "06-yosys-synthesis/soc_asic_top.nl.v",
    "tmp/a9294d35c654454a8e4663955b2f6670.lib",
)
FORMAL_PATH = WSL_ROOT + "/asic/soc_dm_4kb/formal_pdk.v"
OLD_NET = OLD_WSL + "/54-openroad-fillinsertion/soc_asic_top.nl.v"
NEW_NET = ARCHIVE_INPUT_WSL + "/54-openroad-fillinsertion/soc_asic_top.nl.v"
YS_READERS = (
    "asic/equiv/sec/gate_front_end.ys",
    "asic/equiv/sec/gate_front_end_RB.ys",
    "asic/equiv/sec/gate_front_end_R14NEG.ys",
    "asic/equiv/sec/gate_front_end_R14FA.ys",
    "asic/equiv/sec/gate_front_end_R14FB.ys",
    "asic/equiv/sec/gate_front_end_F3A.ys",
    "asic/equiv/sec/gate_front_end_F3B.ys",
    "asic/equiv/sec/pass2/gate_front_end.ys",
)
PS_READERS = (
    "asic/equiv/lec/run_lec_r14.ps1",
    "asic/equiv/lec/run_lec_r14_pass2.ps1",
    "asic/equiv/lec/stepB_new.ps1",
)
SH_READERS = tuple(f"asic/equiv/lec/{name}/run_replay.sh" for name in
                   ("synth_replay", "synth_replay_t1", "synth_replay_t1b"))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def check_archive(allow_missing_source=False):
    archive = ROOT / ARCHIVE_REL
    manifest = json.loads((archive / "archive_manifest.json").read_text(encoding="utf-8"))
    if manifest["source"] != OLD_REL:
        raise RuntimeError("Existing evidence archive is for a different run")
    source = ROOT / OLD_REL
    for rel, info in manifest["files"].items():
        target, original = archive / rel, source / rel
        if not original.exists() and not allow_missing_source:
            raise RuntimeError("Original evidence source is missing before migration: " + str(original))
        for one in ((target, original) if original.exists() else (target,)):
            if one.stat().st_size != info["bytes"] or sha(one) != info["sha256"]:
                raise RuntimeError("Existing archived evidence differs: " + str(one))
    return manifest


def replace_exact(data, old, new, expected=1):
    before, after = old.encode("ascii"), new.encode("ascii")
    if data.count(before) != expected:
        raise RuntimeError(f"Expected {expected} path anchors: {old}")
    changed = data.replace(before, after)
    if changed.replace(after, before) != data:
        raise RuntimeError("Path substitution is not exactly reversible")
    return changed


def proposals():
    result = {}
    formal_old = OLD_WSL + "/79-yosys-eqy/formal_pdk.v"
    for rel in YS_READERS:
        before = (ROOT / rel).read_bytes()
        changed = replace_exact(before, formal_old, FORMAL_PATH)
        if OLD_NET.encode("ascii") in changed:
            changed = replace_exact(changed, OLD_NET, NEW_NET)
        if OLD_WSL.encode("ascii") in changed:
            raise RuntimeError("Unresolved live-run reference in proposed Yosys reader: " + rel)
        result[rel] = before, changed
    for rel in PS_READERS:
        before = (ROOT / rel).read_bytes()
        result[rel] = before, replace_exact(before, OLD_NET, NEW_NET)
    for rel in SH_READERS:
        before = (ROOT / rel).read_bytes()
        changed = replace_exact(before, "S=$R/soc_dm_4kb/runs/final_B/06-yosys-synthesis",
                                "S=" + ARCHIVE_INPUT_WSL + "/06-yosys-synthesis")
        changed = replace_exact(changed, "--config-in $S/config.json", "--config-in $S/config.portable.json")
        changed = replace_exact(changed, "--extra-in $S/extra.json", "--extra-in $S/extra.portable.json")
        result[rel] = before, changed
    return result


def scan():
    # -uu includes ignored retained PD states; historical reports are classified,
    # never rewritten. Path searches are bounded to the research workspace.
    common = ["rg", "-uu", "-l", "--glob", "!results/**", "--glob", "!.git/**",
              "--glob", "!asic/openlane-local/**", "--glob", "!" + OLD_REL + "/**"]
    state_cmd = common + ["--glob", "state*.json", "--glob", "resolved.json", "--glob", "BRANCHED_FROM", OLD_WSL + "/", "asic"]
    states = subprocess.run(state_cmd, cwd=ROOT, capture_output=True, text=True)
    if states.returncode not in (0, 1):
        raise RuntimeError("State dependency scan failed: " + states.stderr)
    if states.stdout.strip():
        raise RuntimeError("Retained PD state reads final_B: " + states.stdout)
    code_cmd = common + ["--glob", "!asic/soc_dm_4kb/runs/**", "--glob", "!asic/soc_sa2_4kb/runs/**",
                         "--glob", "!asic/soc_vc4_4kb/runs/**", "--glob", "!asic/soc_dm_control/runs/**"]
    for extension in ("ys", "ps1", "sh", "py", "eqy", "tcl", "do"):
        code_cmd += ["--glob", "*." + extension]
    code_cmd += [r"(/|\\)final_B(/|\\)", "."]
    code = subprocess.run(code_cmd, cwd=ROOT, capture_output=True, text=True)
    if code.returncode not in (0, 1):
        raise RuntimeError("Source reader scan failed: " + code.stderr)
    known = set(YS_READERS + PS_READERS + SH_READERS)
    comments_only = []
    for line in code.stdout.splitlines():
        rel = Path(line).as_posix().removeprefix("./")
        if rel == Path(__file__).relative_to(ROOT).as_posix():
            continue  # This maintenance tool intentionally names the source.
        if rel in known:
            continue
        text = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
        refs = [s.strip() for s in text.splitlines() if "/final_B/" in s or "\\final_B\\" in s]
        if all(s.startswith("#") for s in refs):
            comments_only.append(rel)
        elif rel == "backups/pre_ram16k_20260929/scripts/cleanup_20260927b.py" and all(s.startswith("(") for s in refs):
            # Only a paragraph of its original module docstring refers to the
            # old replay; no executable input is read from final_B.
            comments_only.append(rel)
        else:
            raise RuntimeError("New unclassified source dependency: " + rel)
    return {"retained_state_references": [], "reader_scan_files": code.stdout.splitlines(),
            "historical_comment_only_files_unchanged": comments_only,
            "state_scan_command": state_cmd, "code_scan_command": code_cmd}


def verify_staged(receipt, applied=False):
    for group in ("dependency_files", "reader_files"):
        for item in receipt[group]:
            if group == "dependency_files":
                a, b = ROOT / item["source"], ROOT / item["archive"]
                if sha(b) != item["sha256"]:
                    raise RuntimeError("Dependency copy differs: " + item["source"])
                if a.exists():
                    if sha(a) != item["sha256"] or a.read_bytes() != b.read_bytes():
                        raise RuntimeError("Original dependency differs: " + item["source"])
                elif not applied:
                    raise RuntimeError("Dependency source missing before migration")
            else:
                expected = item["after_sha256"] if applied else item["before_sha256"]
                if sha(ROOT / item["source"]) != expected:
                    raise RuntimeError("Existing reader does not match reviewed state: " + item["source"])
                if sha(ROOT / item["old_code_archive"]) != item["before_sha256"]:
                    raise RuntimeError("Original reader archive differs")
                if sha(ROOT / item["proposed_file"]) != item["after_sha256"]:
                    raise RuntimeError("Proposed reader changed")
    portable = ROOT / ARCHIVE_INPUT_REL / "06-yosys-synthesis"
    original_extra = (portable / "extra.json").read_bytes()
    expected = replace_exact(original_extra, OLD_WSL + "/tmp/a9294d35c654454a8e4663955b2f6670.lib",
                             ARCHIVE_INPUT_WSL + "/tmp/a9294d35c654454a8e4663955b2f6670.lib")
    if (portable / "extra.portable.json").read_bytes() != expected:
        raise RuntimeError("Portable extra has changes other than its Liberty path")
    if (portable / "config.portable.json").read_bytes() != (portable / "config.json").read_bytes():
        raise RuntimeError("Portable config differs from original config")
    root_formal = ROOT / "asic/soc_dm_4kb/formal_pdk.v"
    if root_formal.read_bytes() != (ROOT / ARCHIVE_INPUT_REL / DEPS[0]).read_bytes():
        raise RuntimeError("Stable formal model differs from archived original")
    for item in receipt["replay_rtl_inputs"]:
        if sha(ROOT / item["path"]) != item["sha256"]:
            raise RuntimeError("Old frozen RTL snapshot input changed")
    if sha(ROOT / "results/rtl_manifest.json") != receipt["rtl_manifest_before_sha256"]:
        raise RuntimeError("RTL manifest changed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", action="store_true")
    parser.add_argument("--verify-staged", action="store_true")
    parser.add_argument("--verify-applied", action="store_true", help="Read-only check after a separately reviewed reader patch; also works after source-run deletion")
    args = parser.parse_args()
    if sum((args.stage, args.verify_staged, args.verify_applied)) > 1:
        parser.error("Choose stage, verify-staged or verify-applied")
    evidence = check_archive(allow_missing_source=args.verify_applied)
    if args.verify_applied:
        receipt = json.loads((ROOT / STAGING_REL / "verification.json").read_text())
        verify_staged(receipt, applied=True)
        inventory = scan()
        for rel in YS_READERS + PS_READERS + SH_READERS:
            active = [line for line in (ROOT / rel).read_text(encoding="utf-8-sig").splitlines()
                      if not line.lstrip().startswith("#")]
            if any(OLD_WSL + "/" in line or "$R/soc_dm_4kb/runs/final_B/" in line for line in active):
                raise RuntimeError("Applied reader still points to the deleted run: " + rel)
        print(f"[VERIFIED] reviewed reader paths,6 archived inputs,{len(evidence['files'])} original evidence files; no retained-state dependency")
        return 0
    inventory = scan()
    proposed = proposals()
    source = ROOT / OLD_REL
    dep_sizes = {rel: (source / rel).stat().st_size for rel in DEPS}
    original_config = json.loads((source / DEPS[2]).read_text())
    old_rtl = []
    for path in original_config["VERILOG_FILES"]:
        if not path.startswith(WSL_ROOT + "/asic/snapshots/rtl_r12b/"):
            raise RuntimeError("Unexpected legacy synthesis RTL source: " + path)
        rel = path[len(WSL_ROOT) + 1:]
        old_rtl.append({"path": rel, "sha256": sha(ROOT / rel)})
    original_bytes = sum(path.stat().st_size for path in source.rglob("*") if path.is_file())
    print(f"[PLAN] archive6 dependency files ({sum(dep_sizes.values()):,} bytes), propose{len(proposed)} reader updates; no existing edits/deletion")
    print(f"[CHECK] {len(evidence['files'])} archived evidence files match original;42 frozen legacy RTL inputs exist; no retained-state dependency")
    destination = ROOT / STAGING_REL
    if args.verify_staged:
        receipt = json.loads((destination / "verification.json").read_text())
        verify_staged(receipt)
        print("[VERIFIED] staged copies and path-only proposals; existing readers remain unchanged")
        return 0
    if not args.stage:
        return 0
    destination.mkdir(exist_ok=False)
    inputs = ROOT / ARCHIVE_INPUT_REL
    inputs.mkdir(exist_ok=False)
    receipt = {"status": "STAGED_REVIEW_REQUIRED_NO_EXISTING_EDITS_NO_DELETION",
               "source_run": OLD_REL, "archive_inputs": ARCHIVE_INPUT_REL,
               "existing_archive_verified_files": len(evidence["files"]),
               "existing_archive_verified_bytes": sum(info["bytes"] for info in evidence["files"].values()),
               "source_run_logical_bytes": original_bytes, "dependencies_logical_bytes": sum(dep_sizes.values()),
               "dependency_files": [], "reader_files": [], "replay_rtl_inputs": old_rtl,
               "scan": inventory, "rtl_manifest_before_sha256": sha(ROOT / "results/rtl_manifest.json"),
               "proof_scope": "Path-only updates with byte-identical referenced models/netlists/config/Liberty; no new formal proof or changed logical assumptions",
               "historical_reports": "Existing logs/reports/proof receipts/state snapshots remain unchanged; their historical paths are provenance, not a resume contract."}
    for rel in DEPS:
        a, b = source / rel, inputs / rel
        b.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(a, b)
        receipt["dependency_files"].append({"source": a.relative_to(ROOT).as_posix(), "archive": b.relative_to(ROOT).as_posix(),
                                           "bytes": a.stat().st_size, "sha256": sha(a)})
    portable = inputs / "06-yosys-synthesis"
    shutil.copy2(portable / "config.json", portable / "config.portable.json")
    changed_extra = replace_exact((portable / "extra.json").read_bytes(),
                                 OLD_WSL + "/tmp/a9294d35c654454a8e4663955b2f6670.lib",
                                 ARCHIVE_INPUT_WSL + "/tmp/a9294d35c654454a8e4663955b2f6670.lib")
    (portable / "extra.portable.json").write_bytes(changed_extra)
    receipt["portable_files"] = {p.relative_to(ROOT).as_posix(): sha(p) for p in
                                 (portable / "config.portable.json", portable / "extra.portable.json")}
    patch = []
    for rel, (before, after) in proposed.items():
        old_copy, new_copy = destination / "original_readers" / rel, destination / "proposed_readers" / rel
        old_copy.parent.mkdir(parents=True, exist_ok=True)
        new_copy.parent.mkdir(parents=True, exist_ok=True)
        old_copy.write_bytes(before)
        new_copy.write_bytes(after)
        receipt["reader_files"].append({"source": rel, "old_code_archive": old_copy.relative_to(ROOT).as_posix(),
                                        "proposed_file": new_copy.relative_to(ROOT).as_posix(),
                                        "before_sha256": hashlib.sha256(before).hexdigest(),
                                        "after_sha256": hashlib.sha256(after).hexdigest(),
                                        "change": "literal input path substitutions only"})
        patch.extend(difflib.unified_diff(before.decode("utf-8-sig").splitlines(True), after.decode("utf-8-sig").splitlines(True),
                                          fromfile="a/" + rel, tofile="b/" + rel))
    (destination / "proposed.patch").write_text("".join(patch), encoding="utf-8", newline="")
    verify_staged(receipt)
    added_bytes = sum(p.stat().st_size for p in inputs.rglob("*") if p.is_file()) + \
                  sum(p.stat().st_size for p in destination.rglob("*") if p.is_file())
    receipt["new_staging_logical_bytes_before_receipt"] = added_bytes
    receipt["potential_net_logical_bytes_reclaimed"] = original_bytes - added_bytes
    receipt["physical_space_note"] = "Logical file-size estimate only; NTFS allocation and hard links can change actual free-space recovery. Source is still retained."
    if sha(ROOT / "results/rtl_manifest.json") != receipt["rtl_manifest_before_sha256"]:
        raise RuntimeError("RTL manifest changed during preparation")
    (destination / "verification.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print(f"[STAGED] {destination}; proposed patch only, six archive inputs byte-exact; old readers/source untouched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
