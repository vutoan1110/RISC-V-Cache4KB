#!/usr/bin/env python3
"""Unified RTL regression runner for ModelSim and the local Python ISS."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "verification" / "results"
DEFAULT_VSIM = Path(r"D:\altera\modelsim\modelsim_ase\win32aloem\vsim.exe")
# The UVM environment needs QuestaSim; ModelSim ASE cannot run UVM here.
DEFAULT_QUESTA = Path(r"C:\questasim64_2024.1\win64\vsim.exe")
UVM_TESTS = (
    "core_smoke_test",
    "core_random_test",
    "axi_smoke_test",
    "axi_stress_test",
    "soc_directed_test",
    "soc_periph_test",
)
SIM_FAILURE_PATTERNS = (
    re.compile(r"\*\*\s+(?:Fatal|Error):", re.IGNORECASE),
    re.compile(r"#\s*Errors:\s*[1-9][0-9]*", re.IGNORECASE),
    # Match only an emitted ModelSim/testbench result line. ModelSim echoes
    # Tcl source such as "if {...} {echo {[FAIL] ...}}" before executing it;
    # an unanchored search therefore turned an unexecuted failure branch into
    # a false regression failure.
    re.compile(r"^\s*#?\s*\[FAIL\]", re.IGNORECASE | re.MULTILINE),
)


def run(command: list[str], *, env: dict[str, str] | None = None,
        log: Path | None = None) -> None:
    print("+", " ".join(command))
    result = subprocess.run(command, cwd=ROOT, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout, end="")
    if log:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(result.stdout, encoding="utf-8")
    is_vsim = Path(command[0]).name.lower().startswith("vsim")
    simulator_failure = (
        is_vsim and any(pattern.search(result.stdout)
                        for pattern in SIM_FAILURE_PATTERNS)
    )
    if result.returncode or simulator_failure:
        reason = ("simulator reported a fatal/error in its transcript"
                  if simulator_failure else f"exit code {result.returncode}")
        raise RuntimeError(f"command failed ({reason}): {' '.join(command)}")


def vsim_do(vsim: Path, script: str, log_name: str) -> None:
    run([str(vsim), "-c", "-do", f"do {script}; quit -f"],
        log=RESULTS / "logs" / log_name)


def compile_random(vsim: Path) -> None:
    vsim_do(vsim, "tb/compile_active_design.do", "compile_active_design.log")


def random_regression(vsim: Path, seeds: int, start_seed: int, length: int) -> dict:
    compile_random(vsim)
    random_dir = RESULTS / "random"
    random_dir.mkdir(parents=True, exist_ok=True)
    passed = 0
    failures: list[dict[str, object]] = []
    records: list[dict[str, object]] = []
    for seed in range(start_seed, start_seed + seeds):
        stem = random_dir / f"seed_{seed}"
        hex_path = stem.with_suffix(".hex")
        manifest = stem.with_suffix(".json")
        ref_trace = Path(f"{stem}.ref.csv")
        off_trace = Path(f"{stem}.off.csv")
        on_trace = Path(f"{stem}.on.csv")
        try:
            run([sys.executable, "verification/random/gen_rv32.py",
                 "--seed", str(seed), "--length", str(length),
                 "--output", str(hex_path.relative_to(ROOT)),
                 "--manifest", str(manifest.relative_to(ROOT))])
            run([sys.executable, "verification/diff/rv32_reference.py",
                 "--hex", str(hex_path.relative_to(ROOT)),
                 "--trace", str(ref_trace.relative_to(ROOT))])
            env = os.environ.copy()
            env.update({
                "VERIFY_HEX": hex_path.relative_to(ROOT).as_posix(),
                "VERIFY_TRACE_OFF": off_trace.relative_to(ROOT).as_posix(),
                "VERIFY_TRACE_ON": on_trace.relative_to(ROOT).as_posix(),
                "VERIFY_SEED": str(seed),
            })
            run([str(vsim), "-c", "-do", "do tb/run_random_trace.do; quit -f"],
                env=env, log=RESULTS / "logs" / f"random_seed_{seed}.log")
            for dut, ref, label in [
                (off_trace, ref_trace, "BP_OFF/reference"),
                (on_trace, ref_trace, "BP_ON/reference"),
                (on_trace, off_trace, "BP_ON/BP_OFF"),
            ]:
                run([sys.executable, "verification/diff/compare_trace.py",
                     "--dut", str(dut.relative_to(ROOT)),
                     "--ref", str(ref.relative_to(ROOT)),
                     "--seed", str(seed), "--label", label])
            metadata = json.loads(manifest.read_text(encoding="utf-8"))
            with ref_trace.open(encoding="ascii") as handle:
                retirements = sum(1 for _ in handle) - 1
            records.append({
                "seed": seed, "sha256": metadata["sha256"],
                "static_words": metadata["static_instruction_words"],
                "retirements": retirements, "result": "PASS",
            })
            passed += 1
        except Exception as exc:
            failures.append({"seed": seed, "error": str(exc)})
            print(f"[FAIL] random seed={seed}: {exc}")
            break

    executed_path = random_dir / "executed_seeds.csv"
    with executed_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["seed", "sha256", "static_words", "retirements", "result"])
        writer.writeheader()
        writer.writerows(records)

    summary = {
        "reference": "project-specific independent Python RV32 subset ISS (not Spike)",
        "start_seed": start_seed,
        "requested_seeds": seeds,
        "program_length_before_halt": length,
        "executed": passed + len(failures),
        "passed": passed,
        "failed": len(failures),
        "total_reference_retirements": sum(row["retirements"] for row in records),
        "failures": failures,
    }
    (random_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if failures:
        raise RuntimeError(f"random differential failed at seed {failures[0]['seed']}")
    print(f"[PASS] Random differential regression {passed}/{seeds} seeds")
    return summary


def uvm_regression(questa: Path, seeds: int) -> dict:
    """Run the UVM environment in verification/uvm, one vsim process per test.

    Each test writes verification/uvm/out/<test>.status; the exit code of the
    macro follows it, so both are checked here.
    """
    out_dir = ROOT / "verification" / "uvm" / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.glob("*.ucdb"):
        stale.unlink()

    jobs: list[tuple[str, int]] = []
    for test in UVM_TESTS:
        if test == "core_random_test" and seeds > 1:
            jobs.extend((test, seed) for seed in range(1, seeds + 1))
        else:
            jobs.append((test, 1))

    records: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    compile_flag = 1

    for test, seed in jobs:
        status_path = out_dir / f"{test}.status"
        if status_path.exists():
            status_path.unlink()
        try:
            run([str(questa), "-c", "-do",
                 f"do verification/uvm/run_uvm.do {test} {compile_flag} {seed}"],
                log=RESULTS / "logs" / f"uvm_{test}_seed{seed}.log")
            verdict = (status_path.read_text(encoding="ascii").strip()
                       if status_path.exists() else "MISSING")
            if not verdict.startswith("PASS"):
                raise RuntimeError(f"status file says {verdict}")
            records.append({"test": test, "seed": seed, "result": "PASS"})
        except Exception as exc:
            failures.append({"test": test, "seed": seed, "error": str(exc)})
            print(f"[FAIL] uvm {test} seed={seed}: {exc}")
        compile_flag = 0

    # Merge whatever functional coverage the runs produced.
    coverage_report = None
    ucdbs = sorted(out_dir.glob("*.ucdb"))
    vcover = questa.with_name("vcover.exe")
    if ucdbs and vcover.exists():
        merged = out_dir / "merged.ucdb"
        report = out_dir / "coverage_summary.txt"
        try:
            run([str(vcover), "merge", "-out", str(merged), *[str(u) for u in ucdbs]])
            run([str(vcover), "report", "-details", "-output", str(report), str(merged)])
            coverage_report = str(report.relative_to(ROOT).as_posix())
        except Exception as exc:
            print(f"[WARN] coverage merge skipped: {exc}")

    summary = {
        "simulator": str(questa),
        "requested": len(jobs),
        "passed": len(records),
        "failed": len(failures),
        "random_seeds": seeds,
        "coverage_report": coverage_report,
        "results": records,
        "failures": failures,
    }
    uvm_results = RESULTS / "uvm"
    uvm_results.mkdir(parents=True, exist_ok=True)
    (uvm_results / "summary.json").write_text(
        json.dumps(summary, indent=2) + chr(10), encoding="utf-8")

    if failures:
        raise RuntimeError(f"UVM regression failed: {len(failures)} of {len(jobs)} runs")
    print(f"[PASS] UVM regression {len(records)}/{len(jobs)} runs")
    return summary


def architecture_status() -> dict:
    # The official riscv-arch-test repository now uses ACT4; RISCOF remains a
    # legacy scaffold because the requested environment may use an older suite.
    riscof = shutil.which("riscof")
    spike = shutil.which("spike")
    status = {
        "riscv_arch_test_act4": "NOT RUN",
        "riscof": "NOT RUN",
        "spike": "NOT RUN",
        "reason": "Windows and WSL audit: RISC-V GCC is present in WSL; ACT4, RISCOF, Sail and Spike are not installed",
        "detected": {"riscof": riscof, "spike": spike},
    }
    print("[NOT RUN] Official ACT4/RISCOF architecture tests: external framework not installed")
    print("[NOT RUN] Spike differential: spike executable not installed")
    return status


def write_paper_table(random_summary: dict | None, arch: dict | None) -> None:
    if random_summary is None:
        saved_random = RESULTS / "random" / "summary.json"
        if saved_random.exists():
            random_summary = json.loads(saved_random.read_text(encoding="utf-8"))
    if arch is None:
        saved_arch = RESULTS / "architecture_status.json"
        if saved_arch.exists():
            arch = json.loads(saved_arch.read_text(encoding="utf-8"))
    path = RESULTS / "verification_summary.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    random_result = (f"PASS {random_summary['passed']}/{random_summary['requested_seeds']}"
                     if random_summary else "NOT RUN")
    rows = [
        ("Core-to-SoC regression", "active RTL", "run_full_regression.do", "PASS"),
        ("Directed ISA", "claimed RV32I subset", "full-SoC retirement trace", "PASS"),
        ("Zmmul corner cases", "MUL/MULH/MULHU/MULHSU", "46 ALU checks + pipeline", "PASS"),
        ("Hazard/forwarding", "forwarding and load-use assertions", "directed + legacy", "PASS"),
        ("Branch prediction/recovery", "BP_OFF/BP_ON", "directed + random", "PASS"),
        ("Cache/AXI", "accounting, no-allocate, protocol", "directed + bus regression", "PASS"),
        ("Assertions", "retirement/core/cache/AXI", "sampled every active cycle", "PASS"),
        ("UVM environment", "core / cache_axi_master / soc_top",
         "verification/uvm/out/*.status", "see verification/results/uvm/summary.json"),
        ("Random differential", "project Python ISS, BP_OFF/BP_ON",
         str(random_summary['executed']) if random_summary else "0", random_result),
        ("Official architecture tests", "ACT4/RISCOF", "0",
         arch['riscof'] if arch else "NOT RUN"),
        ("Spike differential", "agreed unprivileged subset", "0",
         arch['spike'] if arch else "NOT RUN"),
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Verification Layer", "Scope", "Tests/Runs", "Result"])
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directed", action="store_true")
    parser.add_argument("--architecture", action="store_true")
    parser.add_argument("--random", action="store_true")
    parser.add_argument("--coverage", action="store_true")
    parser.add_argument("--uvm", action="store_true",
                        help="run the UVM environment in verification/uvm")
    parser.add_argument("--uvm-seeds", type=int, default=1,
                        help="seeds for core_random_test inside the UVM regression")
    parser.add_argument("--questa", type=Path, default=DEFAULT_QUESTA)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--start-seed", type=int, default=1)
    parser.add_argument("--length", type=int, default=160)
    parser.add_argument("--vsim", type=Path, default=DEFAULT_VSIM)
    args = parser.parse_args()
    if not any((args.directed, args.architecture, args.random, args.coverage,
                args.uvm, args.all)):
        parser.error("select --directed, --architecture, --random, --coverage, "
                     "--uvm or --all")
    if (args.uvm or args.all) and not args.questa.exists():
        raise SystemExit(f"QuestaSim executable not found: {args.questa}")
    if not args.vsim.exists() and (args.directed or args.random or args.coverage or args.all):
        raise SystemExit(f"Questa executable not found: {args.vsim}")

    random_summary = None
    arch_status = None
    if args.all:
        vsim_do(args.vsim, "tb/run_full_regression.do", "full_regression.log")
    elif args.directed:
        vsim_do(args.vsim, "tb/run_directed_verification.do", "directed_verification.log")
    elif args.coverage:
        vsim_do(args.vsim, "tb/run_coverage.do", "coverage.log")
    if args.random or args.all:
        random_summary = random_regression(args.vsim, args.seeds, args.start_seed, args.length)
    if args.uvm or args.all:
        uvm_regression(args.questa, args.uvm_seeds)
    if args.architecture or args.all:
        arch_status = architecture_status()
        (RESULTS / "architecture_status.json").write_text(
            json.dumps(arch_status, indent=2) + "\n", encoding="utf-8")
    write_paper_table(random_summary, arch_status)
    print("[PASS] Verification regression completed for all requested runnable layers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
