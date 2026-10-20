"""FAST_HIT counterpart of the standard-duration CoreMark matrix (2026-10-21, paper note N06).

The fixed matrix (run_coremark_standard_apb_matrix.py, results/coremark_standard_apb_matrix_20261011) runs the four
cache configurations with CACHE_FAST_HIT 0. This runner repeats it for the three DSE-core configurations with
CACHE_FAST_HIT 1 (SA2 = 1, DM_VC4 = 2, DM_DSE = 3; DM has no FAST_HIT variant), both profiles (performance /
validation), two independent passes (separately compiled Verilator models), the same two independent firmware builds,
32 KiB simulation RAM, 50 MHz. Every case passes the same checks as the fixed matrix: source-known CRCs, final iterate
interval >= 10 s, APB timer delta equal to the independently counted clock edges and 20 ns time, elaborated profile
(here with fast = 1). Pass 2 must equal pass 1 on every measurement field. Simulation only: no board measurement and
no EEMBC certification.
    python3 scripts/verification/run_coremark_standard_apb_matrix_fast.py --build-p1 <build.json> --build-p2 <build.json>
        --output results/<new folder> [--lanes N] [--run]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import coremark_standard_apb_gate as gate  # noqa: E402
import run_coremark_standard as common  # noqa: E402
import run_coremark_standard_verilator as native  # noqa: E402
from run_coremark_standard import sha  # noqa: E402

ALLOWED_WARNINGS = {"TIMESCALEMOD", "WIDTHEXPAND"}
CONFIGS = (1, 2, 3)
FAST = 1


def validate_fast(log, uart, profile, cfg, build, max_cycles):
    """run_coremark_standard.validate_case + coremark_standard_apb_gate.validate_case with fast = 1.

    The elaborated-profile line is the only check that names FAST_HIT; it is verified here and then rewritten in a
    private copy of the log (fast=1 -> fast=0) so that every other check runs on the unmodified validators."""
    text = Path(log).read_text(encoding="utf-8", errors="strict")
    actual = tuple(map(int, common.once(text,
        r"COREMARK_STANDARD_PROFILE cfg=(\d+) fast=(\d+) i_lines=(\d+) d_lines=(\d+) line_words=(\d+) l0=(\d+) predictor=(\d+) imem=(\d+) dmem=(\d+)\s*$",
        "elaborated profile")))
    if actual != (cfg, FAST, 256, 256, 4, 8, 1, 4096, 4096):
        raise ValueError("Wrong actual RTL profile (expected FAST_HIT 1)")
    copy = Path(log).with_name(Path(log).name + ".fast0_view")
    copy.write_text(re.sub(r"(COREMARK_STANDARD_PROFILE cfg=\d+ )fast=1 ", r"\1fast=0 ", text, count=1), encoding="utf-8")
    try:
        result = gate.validate_case(copy, uart, profile, cfg, build, max_cycles)
    finally:
        copy.unlink()
    result["cache_fast_hit"] = FAST
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--build-p1", required=True)
    ap.add_argument("--build-p2", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--lanes", type=int, choices=(1, 2, 3, 4, 6), default=6)
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    paths = [Path(args.build_p1).resolve(), Path(args.build_p2).resolve()]
    out = Path(args.output).resolve()
    if any(not p.is_relative_to(ROOT / "results") for p in (*paths, out)):
        ap.error("All evidence must stay inside research results")
    builds = [json.loads(p.read_text()) for p in paths]
    if paths[0] == paths[1] or any(b["status"] != "BUILT_NOT_RUN_NOT_A_SCORE" or b.get("timer_method") != "APB_TIMER_COUNT"
                                   or set(b["profiles"]) != {"performance", "validation"} for b in builds):
        raise RuntimeError("Two independent complete APB firmware builds required")
    if builds[0]["inputs"] != builds[1]["inputs"] or builds[0]["compiler_flags"] != builds[1]["compiler_flags"]:
        raise RuntimeError("Firmware build recipes differ")
    for profile in ("performance", "validation"):
        for name in ("coremark.elf", "coremark.hex"):
            if sha(paths[0].parent / profile / name) != sha(paths[1].parent / profile / name):
                raise RuntimeError("Independent firmware outputs differ")
    manifest = json.loads((ROOT / "results/rtl_manifest.json").read_text())
    frozen = dict(manifest["files"])
    for b in builds:
        frozen.update(b["inputs"])
        for profile in b["profiles"].values():
            frozen.update(profile["artifacts"])
    for p in (*paths, Path(__file__), Path(gate.__file__), Path(native.__file__), HERE / "run_coremark_standard.py",
              HERE / "coremark_crc_gate.py", HERE / "coremark_uart_observer.sv", ROOT / "tb/compile_active_design.do",
              ROOT / "tb/benchmark_snapshot_tb.sv", ROOT / "scripts/snapshot_fields.py"):
        frozen[p.relative_to(ROOT).as_posix()] = sha(p)

    def unchanged():
        changed = [p for p, h in frozen.items() if sha(ROOT / p) != h]
        if changed:
            raise RuntimeError("Frozen source/evidence changed: " + ", ".join(changed))

    unchanged()
    out.mkdir(parents=True, exist_ok=False)
    record = {"status": "PREPARED_NOT_EXECUTED", "inputs": frozen, "ram_bytes": 32768, "clock_hz": 50000000,
              "period_ps": 20000, "minimum_iterate_ticks": 500000000, "cache_fast_hit": FAST,
              "configurations": list(CONFIGS), "profiles": ["performance", "validation"], "passes": [1, 2],
              "lanes": args.lanes, "compile_jobs": 1, "minimum_windows_free_mib": 6000, "minimum_wsl_available_mib": 3000,
              "native_commands": [], "cases": [],
              "method": "simulation-derived CoreMark, RAM32KiB, 50MHz, CACHE_FAST_HIT 1; APB timer equals physical edge/time delta",
              "physical_board_measurement": False, "EEMBC_certification": False}
    receipt = out / "receipt.json"

    def save():
        receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="ascii")

    save()
    if not args.run:
        print(receipt)
        return 0
    record["status"] = "RUNNING_MATRIX_NOT_PAIRED_RESULT"
    save()
    env = dict(os.environ)
    env["VERILATOR_ROOT"] = str(native.VERILATOR.parents[1])

    def available():
        unchanged()
        if (out / "abort_before_next_native").exists():
            raise RuntimeError("Cooperative stop before next tool")
        resources = native.memory()
        if resources["windows_free_mib"] < 6000 or resources["wsl_available_mib"] < 3000:
            record["resource_wait"] = resources
            save()
            return None
        return resources

    def wait_memory():
        while True:
            value = available()
            if value is not None:
                return value
            time.sleep(30)

    def launch(command, directory, log, stage):
        resources = wait_memory()
        item = {"stage": stage, "command": command, "cwd": str(directory), "resources": resources,
                "log": str(log), "started_unix": time.time(), "returncode": None}
        stream = log.open("xb")
        p = subprocess.Popen(command, cwd=directory, stdout=stream, stderr=subprocess.STDOUT, env=env)
        item["pid"] = p.pid
        record["native_commands"].append(item)
        save()
        return p, stream, item

    def complete(job):
        p, stream, item = job
        rc = p.wait()
        stream.close()
        item.update(returncode=rc, finished_unix=time.time(), log_sha256=sha(Path(item["log"])))
        save()
        unchanged()
        if rc:
            raise RuntimeError("Native tool failed: " + item["stage"])

    cases, active = {}, []
    try:
        for number in (1, 2):
            models = {}
            for cfg in CONFIGS:
                directory = out / f"p{number}_c{cfg}_fast_model"
                directory.mkdir()
                observer = directory / "observer.sv"
                observer.write_text(gate.wrapper(), encoding="ascii")
                hdl = re.findall(r"\bhdl/[A-Za-z0-9_/.]+\.(?:v|sv)\b", (ROOT / "tb/compile_active_design.do").read_text())
                if not hdl or len(hdl) != len(set(hdl)) or any(p not in frozen for p in hdl):
                    raise RuntimeError("Unfrozen/unclear RTL membership")
                obj = directory / "obj"
                cmd = [str(native.VERILATOR), "--binary", "--timing", "--assert", "-j", "1", "-Wno-fatal",
                       "--top-module", "tb_coremark_standard", "--Mdir", str(obj),
                       "-GCACHE_CONFIG=" + str(cfg), "-GCACHE_FAST_HIT=" + str(FAST), "-GICACHE_LINE_COUNT=256",
                       "-GDCACHE_LINE_COUNT=256", "-GL0_ENTRIES=8", "-GIMEM_DEPTH=4096", "-GDMEM_DEPTH=4096",
                       '-GMEMFILE="firmware.hex"', *hdl, "tb/benchmark_snapshot_tb.sv", str(observer)]
                log = directory / "compile.log"
                complete(launch(cmd, ROOT, log, f"compile_p{number}_c{cfg}_fast"))
                text = log.read_text(encoding="utf-8", errors="strict")
                kinds = set(re.findall(r"^%Warning-([A-Za-z0-9_]+):", text, re.M))
                if "%Error" in text or kinds - ALLOWED_WARNINGS:
                    raise RuntimeError("Unreviewed Verilator warning/error: " + str(sorted(kinds)))
                exe = obj / "Vtb_coremark_standard"
                if not exe.is_file():
                    raise RuntimeError("Missing compiled executable")
                models[cfg] = exe
                record.setdefault("models", []).append({"pass": number, "cfg": cfg, "cache_fast_hit": FAST,
                                                        "executable": str(exe), "sha256": sha(exe),
                                                        "observer_sha256": sha(observer), "warning_types": sorted(kinds)})
                save()
            pending = []
            for profile in ("performance", "validation"):
                for cfg in CONFIGS:
                    directory = out / f"p{number}_{profile}_c{cfg}_fast"
                    directory.mkdir()
                    shutil.copyfile(paths[number - 1].parent / profile / "coremark.hex", directory / "firmware.hex")
                    uart = directory / "uart.txt"
                    command = [str(models[cfg]), "+benchmark=coremark", "+max_cycles=2000000000", "+coremark_uart=" + str(uart)]
                    pending.append((profile, cfg, directory, command, uart))
            active = []
            while pending or active:
                while pending and len(active) < args.lanes:
                    profile, cfg, directory, command, uart = pending.pop(0)
                    log = directory / "simulation.log"
                    active.append((profile, cfg, directory, uart, log, launch(command, directory, log, f"simulate_p{number}_{profile}_c{cfg}_fast")))
                progressed = False
                for task in list(active):
                    profile, cfg, directory, uart, log, job = task
                    if job[0].poll() is None:
                        continue
                    complete(job)
                    active.remove(task)
                    progressed = True
                    value = validate_fast(log, uart, profile, cfg, builds[number - 1], 2000000000)
                    key = profile, cfg
                    if number == 1:
                        cases[key] = value
                    elif cases.get(key) != value:
                        raise RuntimeError("Paired complete measurement fields differ: " + str(key))
                    record["cases"].append({"pass": number, "profile": profile, "cfg": cfg, "cache_fast_hit": FAST,
                                            "measurement": value, "log": str(log), "log_sha256": sha(log), "uart": str(uart),
                                            "uart_sha256": sha(uart), "firmware_sha256": sha(directory / "firmware.hex"),
                                            "executable_sha256": sha(models[cfg])})
                    save()
                    print(f"[PASS] p{number} {profile} cfg{cfg} fast ticks={value['timer_ticks']} CRC+physical_time", flush=True)
                if not progressed and active:
                    time.sleep(5)
        unchanged()
        if len(record["cases"]) != 12 or len(cases) != 6:
            raise RuntimeError("Incomplete paired FAST matrix")
        record["status"] = "VERIFIED_TWO_INDEPENDENT_STANDARD_COREMARK_SIMULATIONS_RAM32K_50MHZ_FAST_HIT"
        record["summary"] = {f"{p} cfg{c}": {"timer_ticks": v["timer_ticks"], "iterations_per_second_exact": v["iterations_per_second_exact"],
                                            "coremark_per_mhz_exact": v["coremark_per_mhz_exact"]} for (p, c), v in sorted(cases.items())}
        save()
        print(receipt)
        return 0
    except BaseException as exc:
        for _, _, _, _, _, job in active:
            if job[0].poll() is None:
                job[0].wait()
            job[1].close()
        record["status"] = "FAILED_INCOMPLETE_NOT_PAIRED_RESULT"
        record["error"] = str(exc)
        save()
        raise


if __name__ == "__main__":
    raise SystemExit(main())
