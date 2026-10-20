#!/usr/bin/env python3
"""Run every generated ACT4 self-checking ELF on the active RTL harness."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SUITE = ROOT / "verification/results/act4/work/rv32i-zmmul/elfs"
DEFAULT_OUT = ROOT / "verification/results/act4/dut"
RUN_ONE = ROOT / "verification/architecture/run_signature.py"
BIN_TO_HEX = ROOT / "verification/scripts/bin_to_word_hex.py"
OBJCOPY = "$HOME/tools/riscv-gcc16/bin/riscv64-unknown-elf-objcopy"
NM = "$HOME/tools/riscv-gcc16/bin/riscv64-unknown-elf-nm"


WSL_DISTRO = os.environ.get("ACT4_WSL_DISTRO", "Ubuntu")
WSL_USER = os.environ.get("ACT4_WSL_USER", os.environ.get("USER", "riscv"))


def wsl_path(path: Path) -> str:
    resolved = path.resolve()
    drive = resolved.drive
    if len(drive) != 2 or drive[1] != ":":
        raise ValueError(f"expected a Windows drive path, got {resolved}")
    suffix = resolved.as_posix()[2:]
    return f"/mnt/{drive[0].lower()}{suffix}"


def wsl_tool(tool: str, *args: str, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["wsl.exe", "-d", WSL_DISTRO, "-u", WSL_USER, "--", tool, *args],
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        check=True,
    )


def symbols(elf: Path) -> dict[str, int]:
    output = wsl_tool(NM, "-n", wsl_path(elf), capture=True).stdout
    wanted = {"rvtest_entry_point", "begin_signature", "end_signature", "tohost"}
    found: dict[str, int] = {}
    for line in output.splitlines():
        fields = line.split()
        if len(fields) >= 3 and fields[-1] in wanted:
            found[fields[-1]] = int(fields[0], 16)
    missing = wanted - found.keys()
    if missing:
        raise RuntimeError(f"{elf.name}: missing ELF symbols {sorted(missing)}")
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--pattern", default="*.elf")
    parser.add_argument("--max-tests", type=int)
    parser.add_argument("--max-cycles", type=int, default=2_000_000)
    parser.add_argument("--keep-images", action="store_true")
    args = parser.parse_args()

    suite = args.suite.resolve()
    out = args.output.resolve()
    logs = out / "logs"
    signatures = out / "signatures"
    images = out / "images"
    for directory in (logs, signatures):
        directory.mkdir(parents=True, exist_ok=True)
    if args.keep_images:
        images.mkdir(parents=True, exist_ok=True)

    elfs = sorted(suite.rglob(args.pattern))
    if args.max_tests is not None:
        elfs = elfs[: args.max_tests]
    if not elfs:
        raise SystemExit(f"no ELF matched {args.pattern!r} below {suite}")

    started = time.time()
    results: list[dict[str, object]] = []
    compile_needed = True

    with tempfile.TemporaryDirectory(prefix="act4-rv32i-zmmul-") as temp_name:
        temp = Path(temp_name)
        for index, elf in enumerate(elfs, start=1):
            relative = elf.relative_to(suite)
            test_id = "__".join(relative.with_suffix("").parts)
            binary = (images if args.keep_images else temp) / f"{test_id}.bin"
            word_hex = (images if args.keep_images else temp) / f"{test_id}.hex"
            signature = signatures / f"{test_id}.signature"
            log_path = logs / f"{test_id}.log"
            record: dict[str, object] = {
                "test": relative.as_posix(),
                "extension": relative.parts[-2],
                "elf": str(elf),
                "status": "FAIL",
            }
            test_started = time.time()
            try:
                sym = symbols(elf)
                record["symbols"] = {name: f"0x{value:08x}" for name, value in sym.items()}
                wsl_tool(OBJCOPY, "-O", "binary", wsl_path(elf), wsl_path(binary))
                subprocess.run(
                    [sys.executable, str(BIN_TO_HEX), str(binary), str(word_hex),
                     "--base-address", hex(sym["rvtest_entry_point"])],
                    cwd=ROOT, check=True, text=True,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                )
                command = [
                    sys.executable, str(RUN_ONE),
                    "--hex", str(word_hex),
                    "--signature", str(signature),
                    "--sig-begin", hex(sym["begin_signature"]),
                    "--sig-end", hex(sym["end_signature"]),
                    "--tohost-addr", hex(sym["tohost"]),
                    "--max-cycles", str(args.max_cycles),
                ]
                if not compile_needed:
                    command.append("--no-compile")
                completed = subprocess.run(
                    command, cwd=ROOT, text=True,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
                )
                compile_needed = False
                transcript = completed.stdout or ""
                log_path.write_text(transcript, encoding="utf-8")
                if completed.returncode != 0:
                    raise RuntimeError(f"RTL runner exit code {completed.returncode}")
                if "[PASS] signature written" not in transcript:
                    raise RuntimeError("RTL runner PASS marker absent")
                record["status"] = "PASS"
            except Exception as exc:  # continue to expose the full failing set
                record["error"] = str(exc)
                if not log_path.exists():
                    log_path.write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
            record["seconds"] = round(time.time() - test_started, 3)
            results.append(record)
            print(f"[{record['status']}] {index:02d}/{len(elfs):02d} {relative.as_posix()} "
                  f"({record['seconds']} s)", flush=True)

    passed = sum(item["status"] == "PASS" for item in results)
    by_extension: dict[str, dict[str, int]] = {}
    for item in results:
        ext = str(item["extension"])
        bucket = by_extension.setdefault(ext, {"total": 0, "passed": 0, "failed": 0})
        bucket["total"] += 1
        bucket["passed" if item["status"] == "PASS" else "failed"] += 1
    summary = {
        "schema": "act4-rv32i-zmmul-dut-summary-v1",
        "scope": "ACT4 unprivileged RV32I and Zmmul self-checking ELFs",
        "suite_root": str(suite),
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "by_extension": by_extension,
        "elapsed_seconds": round(time.time() - started, 3),
        "results": results,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("total", "passed", "failed", "by_extension")}, indent=2))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
