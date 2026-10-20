"""Execute one isolated standard CoreMark RTL screen with existing Verilator.

One compilation thread and one foreground simulator. This is a single screen,
not a paired result, certification, or physical 16KiB-chip measurement.
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
from run_coremark_standard import sha, wrapper, validate_case

VERILATOR = Path("/home/toanl/tools/src/verilator/bin/verilator")
POWERSHELL = "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"

def memory():
    data = dict(re.findall(r"^(\w+):\s+(\d+)", Path("/proc/meminfo").read_text(), re.M))
    w = subprocess.run([POWERSHELL, "-NoProfile", "-NonInteractive", "-Command",
        "[int]((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1024)"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if w.returncode or not re.fullmatch(r"\s*\d+\s*", w.stdout):
        raise RuntimeError("Cannot prove Windows free memory")
    return {"windows_free_mib": int(w.stdout), "wsl_available_mib": int(data["MemAvailable"]) // 1024}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--build", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--config", type=int, choices=range(4), default=0)
    ap.add_argument("--profile", choices=("performance", "validation"), default="performance")
    ap.add_argument("--max-cycles", type=int, default=2000000000)
    args = ap.parse_args()
    bp = Path(args.build).resolve(); out = Path(args.output).resolve()
    if not bp.is_relative_to(ROOT / "results") or not out.is_relative_to(ROOT / "results"):
        ap.error("Research results paths required")
    if not 500000000 < args.max_cycles < 2**31: ap.error("Invalid bounded simulation cycles")
    b = json.loads(bp.read_text())
    if b["status"] != "BUILT_NOT_RUN_NOT_A_SCORE" or args.profile not in b["profiles"]:
        raise RuntimeError("Incomplete firmware build")
    manifest = json.loads((ROOT / "results/rtl_manifest.json").read_text())
    frozen = dict(manifest["files"]); frozen.update(b["inputs"])
    frozen.update(b["profiles"][args.profile]["artifacts"])
    for p in (Path(__file__), HERE / "run_coremark_standard.py", HERE / "coremark_uart_observer.sv",
              HERE / "coremark_crc_gate.py", ROOT / "scripts/snapshot_fields.py", bp,
              ROOT / "tb/compile_active_design.do", ROOT / "tb/benchmark_snapshot_tb.sv"):
        frozen[p.relative_to(ROOT).as_posix()] = sha(p)
    def unchanged():
        bad = [p for p, h in frozen.items() if sha(ROOT / p) != h]
        if bad: raise RuntimeError("Inputs changed: " + ", ".join(bad))
    unchanged()
    resource = memory()
    if resource["windows_free_mib"] < 6000 or resource["wsl_available_mib"] < 3000:
        raise RuntimeError("Insufficient memory; no compilation launched")
    out.mkdir(parents=True, exist_ok=False)
    observer = out / "observer.sv"; observer.write_text(wrapper(), encoding="ascii")
    firmware = out / "firmware.hex"
    shutil.copyfile(bp.parent / args.profile / "coremark.hex", firmware)
    record = {"status": "COMPILING_SINGLE_SCREEN_NOT_RESULT", "inputs": frozen,
              "build": str(bp), "config": args.config, "profile": args.profile,
              "timer": "mcycle_32bit_CSR_0xB00", "clock_hz": 50000000,
              "ram_bytes": 32768, "cache_bytes_each": 4096, "fast_uart": False,
              "fast_hit": False, "compiler_threads": 1, "simulation_threads": 1,
              "resource_before_compile": resource, "max_cycles": args.max_cycles,
              "commands": [], "observer_sha256": sha(observer), "firmware_sha256": sha(firmware),
              "paired": False, "certified": False, "physical_chip_execution": False}
    receipt = out / "receipt.json"
    def save(): receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="ascii")
    save()
    def native(command, name, cwd):
        unchanged()
        r = memory()
        if r["windows_free_mib"] < 6000 or r["wsl_available_mib"] < 3000:
            raise RuntimeError("Insufficient memory; next native tool not launched")
        if (out / "abort_before_next_native").exists(): raise RuntimeError("Cooperative stop before next tool")
        log = out / (name + ".log")
        item = {"command": command, "cwd": str(cwd), "memory_before": r, "returncode": None,
                "log": str(log), "started_unix": time.time()}
        record["commands"].append(item); save()
        env = dict(os.environ); env["VERILATOR_ROOT"] = str(VERILATOR.parents[1])
        with log.open("xb") as f:
            p = subprocess.Popen(command, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, env=env)
            item["pid"] = p.pid; save()
            rc = p.wait()
        item.update(returncode=rc, finished_unix=time.time(), log_sha256=sha(log)); save()
        if rc: raise RuntimeError("Native failure: " + name + " rc=" + str(rc))
        unchanged(); return log
    try:
        compile_do = (ROOT / "tb/compile_active_design.do").read_text()
        hdl = re.findall(r"\bhdl/[A-Za-z0-9_/.]+\.(?:v|sv)\b", compile_do)
        if len(set(hdl)) != len(hdl) or not hdl: raise RuntimeError("Unclear RTL compile membership")
        for path in hdl:
            if path not in frozen: raise RuntimeError("Unfrozen RTL source: " + path)
        version = native([str(VERILATOR), "--version"], "verilator_version", ROOT)
        record["verilator_version"] = version.read_text().strip(); save()
        obj = out / "obj"
        command = [str(VERILATOR), "--binary", "--timing", "--assert", "-j", "1", "-Wno-fatal",
                   "--top-module", "tb_coremark_standard", "--Mdir", str(obj),
                   "-GCACHE_CONFIG=" + str(args.config), "-GCACHE_FAST_HIT=0", "-GICACHE_LINE_COUNT=256",
                   "-GDCACHE_LINE_COUNT=256", "-GL0_ENTRIES=8", "-GIMEM_DEPTH=4096", "-GDMEM_DEPTH=4096",
                   '-GMEMFILE="firmware.hex"', *hdl, "tb/benchmark_snapshot_tb.sv", str(observer)]
        compiled = native(command, "compile", ROOT)
        if re.search(r"%Error", compiled.read_text(errors="strict")): raise RuntimeError("Verilator compile error")
        record["compile_warnings"] = re.findall(r"^%Warning[^\n]+", compiled.read_text(), re.M)
        exe = obj / "Vtb_coremark_standard"
        if not exe.is_file(): raise RuntimeError("Executable missing after native compile")
        record["executable_sha256"] = sha(exe)
        record["status"] = "RUNNING_SINGLE_SCREEN_NOT_RESULT"; save()
        uart = out / "uart.txt"
        log = native([str(exe), "+benchmark=coremark", "+max_cycles=" + str(args.max_cycles),
                      "+coremark_uart=" + str(uart)], "simulation", out)
        value = validate_case(log, uart, args.profile, args.config, b, args.max_cycles)
        record["measurement"] = value; record["uart_sha256"] = sha(uart)
        record["status"] = "SINGLE_VALID_TIMED_SCREEN_NOT_PAIRED_RESULT"; save(); print(receipt); return 0
    except BaseException as exc:
        record["status"] = "FAILED_SINGLE_SCREEN_NOT_RESULT"; record["error"] = str(exc); save(); raise

if __name__ == "__main__": raise SystemExit(main())
