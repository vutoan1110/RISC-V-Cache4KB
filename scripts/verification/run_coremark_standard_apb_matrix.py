"""Fixed four-cache/two-profile/two-pass CoreMark matrix, RAM32KiB RTL.

One Verilator compilation at a time, then at most eight small native simulators.
Every final iterate interval must physically last >=10s at a 20ns period.
No physical-board or EEMBC registration/certification claim is made.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import run_coremark_standard_verilator as native
import coremark_standard_apb_gate as gate
from run_coremark_standard import sha

ALLOWED_WARNINGS = {"TIMESCALEMOD", "WIDTHEXPAND"}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--build-p1", required=True)
    ap.add_argument("--build-p2", required=True)
    ap.add_argument("--initial-screen", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--lanes", type=int, choices=(1, 2, 3, 4, 8), default=8)
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    paths = [Path(args.build_p1).resolve(), Path(args.build_p2).resolve()]
    initial = Path(args.initial_screen).resolve(); out = Path(args.output).resolve()
    if any(not p.is_relative_to(ROOT / "results") for p in (*paths, initial, out)):
        ap.error("All evidence must stay inside research results")
    builds = [json.loads(p.read_text()) for p in paths]
    if paths[0] == paths[1] or any(b["status"] != "BUILT_NOT_RUN_NOT_A_SCORE" or
        b.get("timer_method") != "APB_TIMER_COUNT" or set(b["profiles"]) != {"performance", "validation"} for b in builds):
        raise RuntimeError("Two independent complete APB firmware builds required")
    if builds[0]["inputs"] != builds[1]["inputs"] or builds[0]["compiler_flags"] != builds[1]["compiler_flags"]:
        raise RuntimeError("Firmware build recipes differ")
    for profile in ("performance", "validation"):
        for name in ("coremark.elf", "coremark.hex"):
            if sha(paths[0].parent / profile / name) != sha(paths[1].parent / profile / name):
                raise RuntimeError("Independent firmware outputs differ")
    screen = json.loads(initial.read_text())
    if screen["status"] != "SINGLE_VALID_TIMED_SCREEN_NOT_PAIRED_RESULT" or screen["config"] != 0 or screen["profile"] != "performance":
        raise RuntimeError("Completed DM performance screen required")
    if len(screen["commands"]) != 3 or any(c["returncode"] != 0 for c in screen["commands"]):
        raise RuntimeError("Screen native commands incomplete or failed")
    if any(sha(Path(c["log"])) != c["log_sha256"] for c in screen["commands"]):
        raise RuntimeError("Screen native logs changed")
    for p, h in screen["inputs"].items():
        if sha(ROOT / p) != h: raise RuntimeError("Screen input changed: " + p)
    screen_value = gate.validate_case(Path(screen["commands"][-1]["log"]), initial.parent / "uart.txt",
                                     "performance", 0, builds[0], 2000000000)
    if screen_value != screen["measurement"]: raise RuntimeError("Fresh raw screen parsing differs")
    existing_model = initial.parent / "obj/Vtb_coremark_standard"
    if sha(existing_model) != screen["executable_sha256"]: raise RuntimeError("Initial executable changed")
    manifest = json.loads((ROOT / "results/rtl_manifest.json").read_text())
    frozen = dict(manifest["files"])
    for b in builds:
        frozen.update(b["inputs"])
        for profile in b["profiles"].values(): frozen.update(profile["artifacts"])
    for p in (*paths, initial, Path(__file__), Path(gate.__file__), Path(native.__file__),
              HERE / "run_coremark_standard.py", HERE / "coremark_crc_gate.py", HERE / "coremark_uart_observer.sv",
              ROOT / "tb/compile_active_design.do", ROOT / "tb/benchmark_snapshot_tb.sv", ROOT / "scripts/snapshot_fields.py"):
        frozen[p.relative_to(ROOT).as_posix()] = sha(p)
    def unchanged():
        changed = [p for p, h in frozen.items() if sha(ROOT / p) != h]
        if changed: raise RuntimeError("Frozen source/evidence changed: " + ", ".join(changed))
    unchanged(); out.mkdir(parents=True, exist_ok=False)
    record = {"status": "PREPARED_NOT_EXECUTED", "inputs": frozen, "ram_bytes": 32768,
              "clock_hz": 50000000, "period_ps": 20000, "minimum_iterate_ticks": 500000000,
              "configurations": [0, 1, 2, 3], "profiles": ["performance", "validation"], "passes": [1, 2],
              "lanes": args.lanes, "compile_jobs": 1, "native_jobs_max": args.lanes,
              "resource_estimate": {"simulator_mib_each_conservative": 64, "compiler_mib_conservative": 512,
                                    "measured_dm_simulator_rss_mib": 4, "measured_dm_compiler_allocated_mib": 39},
              "minimum_windows_free_mib": 6000, "minimum_wsl_available_mib": 3000,
              "initial_screen": str(initial), "native_commands": [], "cases": [],
              "method": "simulation-derived CoreMark, RAM32KiB,50MHz; APB timer equals physical edge/time delta",
              "physical_board_measurement": False, "EEMBC_certification": False}
    receipt = out / "receipt.json"
    def save(): receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="ascii")
    save()
    if not args.run: print(receipt); return 0
    record["status"] = "RUNNING_MATRIX_NOT_PAIRED_RESULT"; save()
    env = dict(os.environ); env["VERILATOR_ROOT"] = str(native.VERILATOR.parents[1])
    def available():
        unchanged()
        if (out / "abort_before_next_native").exists(): raise RuntimeError("Cooperative stop before next tool")
        resources = native.memory()
        if resources["windows_free_mib"] < 6000 or resources["wsl_available_mib"] < 3000:
            record["resource_wait"] = resources; save(); return None
        return resources
    def wait_memory():
        while True:
            value = available()
            if value is not None: return value
            time.sleep(30)
    def launch(command, directory, log, stage):
        resources = wait_memory()
        item = {"stage": stage, "command": command, "cwd": str(directory), "resources": resources,
                "log": str(log), "started_unix": time.time(), "returncode": None}
        stream = log.open("xb")
        p = subprocess.Popen(command, cwd=directory, stdout=stream, stderr=subprocess.STDOUT, env=env)
        item["pid"] = p.pid; record["native_commands"].append(item); save()
        return p, stream, item
    def complete(job):
        p, stream, item = job; rc = p.wait(); stream.close()
        item.update(returncode=rc, finished_unix=time.time(), log_sha256=sha(Path(item["log"]))); save()
        unchanged()
        if rc: raise RuntimeError("Native tool failed: " + item["stage"])
    cases, active = {}, []
    try:
        for number in (1, 2):
            models = {}
            for cfg in range(4):
                if number == 1 and cfg == 0:
                    models[cfg] = existing_model; continue
                directory = out / f"p{number}_c{cfg}_model"; directory.mkdir()
                observer = directory / "observer.sv"; observer.write_text(gate.wrapper(), encoding="ascii")
                hdl = re.findall(r"\bhdl/[A-Za-z0-9_/.]+\.(?:v|sv)\b", (ROOT / "tb/compile_active_design.do").read_text())
                if not hdl or len(hdl) != len(set(hdl)) or any(p not in frozen for p in hdl):
                    raise RuntimeError("Unfrozen/unclear RTL membership")
                obj = directory / "obj"
                cmd = [str(native.VERILATOR), "--binary", "--timing", "--assert", "-j", "1", "-Wno-fatal",
                       "--top-module", "tb_coremark_standard", "--Mdir", str(obj),
                       "-GCACHE_CONFIG=" + str(cfg), "-GCACHE_FAST_HIT=0", "-GICACHE_LINE_COUNT=256",
                       "-GDCACHE_LINE_COUNT=256", "-GL0_ENTRIES=8", "-GIMEM_DEPTH=4096", "-GDMEM_DEPTH=4096",
                       '-GMEMFILE="firmware.hex"', *hdl, "tb/benchmark_snapshot_tb.sv", str(observer)]
                log = directory / "compile.log"; job = launch(cmd, ROOT, log, f"compile_p{number}_c{cfg}")
                complete(job)
                text = log.read_text(encoding="utf-8", errors="strict")
                kinds = set(re.findall(r"^%Warning-([A-Za-z0-9_]+):", text, re.M))
                if "%Error" in text or kinds - ALLOWED_WARNINGS:
                    raise RuntimeError("Unreviewed Verilator warning/error: " + str(sorted(kinds)))
                exe = obj / "Vtb_coremark_standard"
                if not exe.is_file(): raise RuntimeError("Missing compiled executable")
                models[cfg] = exe
                record.setdefault("models", []).append({"pass": number, "cfg": cfg, "executable": str(exe),
                    "sha256": sha(exe), "observer_sha256": sha(observer), "warning_types": sorted(kinds)})
                save()
            pending = []
            for profile in ("performance", "validation"):
                for cfg in range(4):
                    if (number, profile, cfg) == (1, "performance", 0):
                        cases[(profile, cfg)] = screen_value
                        record["cases"].append({"pass": 1, "profile": profile, "cfg": cfg,
                                                "initial_screen": str(initial), "measurement": screen_value}); save(); continue
                    directory = out / f"p{number}_{profile}_c{cfg}"; directory.mkdir()
                    firmware = directory / "firmware.hex"
                    shutil.copyfile(paths[number - 1].parent / profile / "coremark.hex", firmware)
                    uart = directory / "uart.txt"
                    command = [str(models[cfg]), "+benchmark=coremark", "+max_cycles=2000000000", "+coremark_uart=" + str(uart)]
                    pending.append((profile, cfg, directory, command, uart))
            active = []
            while pending or active:
                while pending and len(active) < args.lanes:
                    profile, cfg, directory, command, uart = pending.pop(0)
                    log = directory / "simulation.log"
                    job = launch(command, directory, log, f"simulate_p{number}_{profile}_c{cfg}")
                    active.append((profile, cfg, directory, uart, log, job))
                progressed = False
                for task in list(active):
                    profile, cfg, directory, uart, log, job = task
                    if job[0].poll() is None: continue
                    complete(job); active.remove(task); progressed = True
                    value = gate.validate_case(log, uart, profile, cfg, builds[number - 1], 2000000000)
                    key = profile, cfg
                    if number == 1: cases[key] = value
                    elif cases.get(key) != value: raise RuntimeError("Paired complete measurement fields differ: " + str(key))
                    record["cases"].append({"pass": number, "profile": profile, "cfg": cfg, "measurement": value,
                        "log": str(log), "log_sha256": sha(log), "uart": str(uart), "uart_sha256": sha(uart),
                        "firmware_sha256": sha(directory / "firmware.hex"), "executable_sha256": sha(models[cfg])})
                    save(); print(f"[PASS] p{number} {profile} cfg{cfg} ticks={value['timer_ticks']} CRC+physical_time", flush=True)
                if not progressed and active: time.sleep(5)
        unchanged()
        if len(record["cases"]) != 16 or len(cases) != 8: raise RuntimeError("Incomplete paired fixed matrix")
        record["status"] = "VERIFIED_TWO_INDEPENDENT_STANDARD_COREMARK_SIMULATIONS_RAM32K_50MHZ"
        save(); print(receipt); return 0
    except BaseException as exc:
        # Finish healthy foreground children; no force kill or owner-app changes.
        for _, _, _, _, _, job in active:
            if job[0].poll() is None: job[0].wait()
            job[1].close()
        record["status"] = "FAILED_INCOMPLETE_NOT_PAIRED_RESULT"; record["error"] = str(exc); save(); raise

if __name__ == "__main__": raise SystemExit(main())
