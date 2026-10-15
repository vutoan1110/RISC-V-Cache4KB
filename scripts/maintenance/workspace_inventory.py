"""Inventory every local path without following links; describe authored text.

This records a filesystem snapshot, not functional verification. Raw tools,
binary artefacts and third-party code are catalogued without claiming a
byte-by-byte semantic review. It never modifies source inputs.
"""
import ast
from collections import defaultdict
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/workspace_audit"
VENDOR = ("asic/openlane-local/", "asic/eqy-local/", "sw/coremark/",
          "sw/embench_upstream/", "verification/architecture/riscv-arch-test/")
TEXT = {".md", ".py", ".sh", ".ps1", ".tcl", ".do", ".v", ".sv", ".svh",
        ".c", ".h", ".s", ".ld", ".json", ".yml", ".yaml", ".qsf", ".qpf",
        ".cfg", ".sdc", ".ys", ".eqy", ".html", ".css", ".js", ".txt"}


def role(rel):
    parts = rel.split("/")
    base = parts[-1]
    if rel.startswith(".git/"):
        return "git_metadata", "Git history/index/objects; protected repository metadata"
    if rel.startswith(VENDOR):
        return "vendor", "Third-party tools/benchmarks; retain source and licence provenance"
    if rel.startswith(("results/pd_run_archive/", "results/source_archive/")):
        return "archived_evidence", "Preserved PD diagnostic/config/report evidence; not current sign-off"
    if "/runs/" in rel or rel.startswith(("evidence_runs/", "asic/fp_explore/", "asic/pd_exp/")):
        return "experiment_evidence", "Physical-design experiment source/state/report; see run classification"
    if rel.startswith(("asic/equiv/", "scripts/rf_bht_m9k/", "scripts/r16_fasthit/")):
        return "formal", "Equivalence/formal proof or its inputs/controls; preserve reproducibility"
    if rel.startswith(("asic/snapshots/", "backups/")):
        return "snapshot", "Frozen/historical source input; retain identity and provenance"
    if parts[0].startswith("work") or parts[0] in ("db", "incremental_db") or rel.endswith((".vcd", ".wlf", ".pyc")):
        return "rebuildable", "Compiled simulator/fitter cache or waveform; only remove when no reader is active"
    if parts[0].startswith("output_files_board_matrix"):
        return "board_output", "Board SOF/firmware/index package; current versus legacy identity must be checked"
    if parts[0].startswith("output_files"):
        return "fpga_output", "Quartus result/database/report; retain fit source/seed evidence before pruning"
    if rel.startswith(("verification/results/", "verification/coverage/", "results/")):
        return "result", "Measurement/log/report/provenance; validity depends on paired execution and RTL identity"
    if rel.startswith("hdl/"):
        return "rtl", "Current SoC implementation; manifest-protected, no edits in cleanup"
    if rel.startswith(("tb/", "verification/")):
        return "verification", "Testbench/checker/reference/run driver; coverage must be assessed separately"
    if rel.startswith(("fw/", "fw_board/", "sw_metrics/", "sw/")):
        return "firmware", "Benchmark/test firmware or firmware build source; preserve canonical images"
    if rel.startswith(("scripts/", "asic/")):
        return "flow_source", "Build/measurement/diagnostic driver or ASIC configuration/input"
    if rel.startswith("quartus/") or Path(base).suffix.lower() in (".qsf", ".qpf"):
        return "fpga_source", "FPGA project/device/pin constraints and board utilities"
    if len(parts) == 1 and Path(base).suffix.lower() in (".md", ".txt"):
        return "document", "Project policy/state/history/review documentation; see document catalogue"
    return "other", "Unclassified path; review before any deletion"


def synopsis(path, category):
    document = path.suffix.lower() == ".md" and category not in {"vendor", "archived_evidence", "git_metadata"}
    if not document and category not in {"rtl", "verification", "firmware", "flow_source", "fpga_source", "document", "snapshot", "formal"}:
        return None
    if path.suffix.lower() not in TEXT or path.stat().st_size > 2 * 1024 * 1024:
        return None
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin1")
    info = {"sha256": hashlib.sha256(raw).hexdigest(), "text_bytes_read": len(raw)}
    if path.suffix.lower() == ".py":
        try:
            tree = ast.parse(text)
            info["purpose"] = (ast.get_docstring(tree) or "").split("\n")[0]
            info["symbols"] = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        except SyntaxError:
            info["syntax_extraction"] = "unavailable"
    elif path.suffix.lower() in (".v", ".sv", ".svh"):
        info["symbols"] = re.findall(r"(?m)^\s*(?:module|interface|package|class)\s+(\w+)", text)
    elif path.suffix.lower() == ".md":
        info["headings"] = re.findall(r"(?m)^#{1,4}\s+(.+)$", text)
    elif path.suffix.lower() in (".c", ".h"):
        info["symbols"] = re.findall(r"(?m)^\s*(?:static\s+)?(?:unsigned\s+)?(?:void|int|long|char|uint\w+|bool|size_t)\s+\**(\w+)\s*\(", text)
    elif path.suffix.lower() == ".qsf":
        info["assignments"] = re.findall(r"(?m)^set_parameter -name (\w+) (.+)$", text)
    elif path.suffix.lower() in (".sh", ".ps1", ".tcl", ".do", ".ys"):
        info["purpose"] = " / ".join(s.strip("# ") for s in text.splitlines()[:8] if s.startswith("#") and not s.startswith("#!"))[:600]
    elif path.suffix.lower() == ".json":
        try:
            value = json.loads(text)
            if isinstance(value, dict):
                info["keys"] = list(value)[:35]
        except ValueError:
            info["json_extraction"] = "unavailable"
    info["legacy_revision_name"] = bool(re.search(r"(?i)(?:^|[_/])r(?:1[0-9]|[2-9][0-9])(?:[_/.]|$)|final[0-9]|(?:^|_)v[0-9]", path.relative_to(ROOT).as_posix()))
    return info


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    retired_path = ROOT / "results/source_archive/retired_sources.json"
    retired = {r["path"]: r for r in json.loads(retired_path.read_text(encoding="utf-8-sig"))["files"]} if retired_path.is_file() else {}
    manifest_files = set(json.loads((ROOT / "results/rtl_manifest.json").read_text())["files"])
    totals = defaultdict(lambda: {"files": 0, "bytes": 0})
    categories = defaultdict(lambda: {"files": 0, "bytes": 0})
    folders = set()
    authored = []
    errors = []
    count = byte_count = 0
    with (OUT / "paths.jsonl").open("w", encoding="utf-8") as stream:
        def visit(parent):
            nonlocal count, byte_count
            try:
                entries = sorted(os.scandir(parent), key=lambda e: e.name.lower())
            except OSError as exc:
                errors.append({"path": str(parent), "error": str(exc)})
                return
            for entry in entries:
                path = Path(entry.path)
                rel = path.relative_to(ROOT).as_posix()
                if rel.startswith("results/workspace_audit/"):
                    continue  # Avoid a self-growing inventory; output directory is documented separately.
                try:
                    stat = entry.stat(follow_symlinks=False)
                    is_link = entry.is_symlink() or bool(getattr(stat, "st_file_attributes", 0) & 0x400)
                    if is_link:
                        stream.write(json.dumps({"path": rel, "type": "link_not_followed"}) + "\n")
                    elif entry.is_dir(follow_symlinks=False):
                        folders.add(rel)
                        stream.write(json.dumps({"path": rel, "type": "directory"}) + "\n")
                        visit(path)
                    else:
                        cat, purpose = role(rel)
                        row = {"path": rel, "type": "file", "bytes": stat.st_size,
                               "mtime_ns": stat.st_mtime_ns, "category": cat, "role": purpose}
                        if rel in retired:
                            row["status"] = "LEGACY_ARCHIVED_ORIGINAL_RETAINED_POLICY_BLOCK"
                            row["role"] = retired[rel]["reason"]
                        elif rel in manifest_files:
                            row["status"] = "FROZEN_MANIFEST_INPUT"
                        elif cat in {"snapshot", "formal", "archived_evidence", "experiment_evidence"}:
                            row["status"] = "PROVENANCE_RETAINED"
                        elif cat == "vendor":
                            row["status"] = "THIRD_PARTY_RETAINED"
                        elif cat == "document":
                            row["status"] = "MAINTAINED_DOCUMENT"
                        else:
                            row["status"] = "SEE_WORKSPACE_MAP_FOR_VALIDITY"
                        stream.write(json.dumps(row) + "\n")
                        count += 1
                        byte_count += stat.st_size
                        categories[cat]["files"] += 1
                        categories[cat]["bytes"] += stat.st_size
                        parts = rel.split("/")
                        for n in range(1, len(parts)):
                            prefix = "/".join(parts[:n])
                            totals[prefix]["files"] += 1
                            totals[prefix]["bytes"] += stat.st_size
                        info = synopsis(path, cat)
                        if info is not None:
                            authored.append({**row, **info})
                except OSError as exc:
                    errors.append({"path": rel, "error": str(exc)})
        visit(ROOT)
    summary = {"created": datetime.now().astimezone().isoformat(), "root": str(ROOT),
        "file_count": count, "directory_count": len(folders), "logical_bytes": byte_count,
        "categories": dict(categories), "folders": dict(sorted(totals.items())), "errors": errors,
        "authored_text_files_read": len(authored),
        "authored_text_bytes_read": sum(a["text_bytes_read"] for a in authored),
        "coverage": "All paths catalogued except this audit output; links not followed; text synopsis is not semantic verification; logical bytes are not unique physical disk usage"}
    (OUT / "inventory.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (OUT / "source_catalog.json").write_text(json.dumps(authored, indent=2) + "\n", encoding="utf-8")
    lines = ["# Danh muc file nguon va tai lieu", "", "Moi dong la mot file text da doc de trich heading / symbol / docstring. "
             "Vai tro tu dong la chi muc, khong thay the ket luan kiem chung trong WORKSPACE_MAP.md. "
             "File build, binary, log ket qua va ma ben thu ba nam trong paths.jsonl.", ""]
    by_parent = defaultdict(list)
    for row in authored:
        by_parent[str(Path(row["path"]).parent).replace("\\", "/")].append(row)
    for parent, rows in sorted(by_parent.items()):
        lines += ["## " + parent, "", "| File | Trang thai | Vai tro / noi dung trich tu file |", "|---|---|---|"]
        for row in rows:
            detail = row["role"] if row["path"] in retired else row.get("purpose") or "; ".join(row.get("symbols", [])[:18]) or "; ".join(row.get("headings", [])[:5]) or row["role"]
            detail = detail.replace("|", "\\|").replace("\n", " ")[:600]
            target = (ROOT / row["path"]).as_posix()
            lines.append(f"| [{row['path']}](<{target}>) | {row['status']} | {detail} |")
        lines.append("")
    rendered = unicodedata.normalize("NFKD", "\n".join(lines)).replace("đ", "d").replace("Đ", "D").encode("ascii", "backslashreplace").decode()
    (OUT / "SOURCE_CATALOG.md").write_text(rendered, encoding="ascii")
    print(json.dumps({k: summary[k] for k in ("file_count", "directory_count", "logical_bytes", "authored_text_files_read", "authored_text_bytes_read", "errors")}))
    for folder, value in totals.items():
        if "/" not in folder:
            print(f"{folder}: {value['files']} files, {value['bytes'] / 1024**3:.3f} GiB")


if __name__ == "__main__":
    main()
