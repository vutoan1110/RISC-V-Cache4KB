"""Compile one new sampler, run once as the ordinary WSL user, and preserve its verdict."""
from __future__ import annotations

from datetime import datetime, timezone
import bisect
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
REL = "results/vc4_cpu_sampling_20261010"
OUT = ROOT / REL
SOURCE = ROOT / "scripts/metrics/read_only_perf_sampler.c"
EXEC = "/nix/store/zzypcxbrgw1qink1l7fwgwpbk7fvdwpg-openroad/bin/.openroad-wrapped"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def native(*argv, timeout=20):
    begin = time.monotonic()
    p = subprocess.run(["wsl.exe", "-d", "Ubuntu", "-e", *argv],
                       capture_output=True, text=True, timeout=timeout)
    return {"argv": list(argv), "rc": p.returncode, "wall_seconds": time.monotonic()-begin,
            "stdout": p.stdout, "stderr": p.stderr}


def main():
    OUT.mkdir(exist_ok=False)
    record = {"capture_start_utc": datetime.now(timezone.utc).isoformat(),
              "status": "PREPARING", "sampler_source_sha256": sha(SOURCE),
              "runner_source_sha256": sha(Path(__file__)),
              "owner_approved_scope": "One user-only perf_event_open software CPU-clock sample of exact TID669,20Hz,at most5s,no permissions changes/no ptrace/no pause/no target signals/no target memory reads; denial stops without retry or alternate privilege.",
              "source_provenance_receipt": "results/vc4_postdrt_antenna_comparison_20261010.json",
              "process_control_operations": "No ptrace, debugger attach, pause, target signal, install, privilege/kernel change, flow launch or running input mutation"}
    try:
        maps = native("cat", "/proc/669/maps")
        record["maps_before"] = maps
        if maps["rc"] or EXEC not in maps["stdout"]:
            raise RuntimeError("Exact native executable identity absent from target maps")
        compile_cmd = native("cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2",
                             "/mnt/e/Projects/RISCV-research/scripts/metrics/read_only_perf_sampler.c",
                             "-o", f"/mnt/e/Projects/RISCV-research/{REL}/read_only_perf_sampler")
        record["compile"] = compile_cmd
        if compile_cmd["rc"]:
            raise RuntimeError("Existing compiler failed; no install or alternate compiler")
        record["compiled_binary_sha256"] = sha(OUT / "read_only_perf_sampler")
        argument_control = native(f"/mnt/e/Projects/RISCV-research/{REL}/read_only_perf_sampler", "reject")
        record["argument_rejection_control"] = argument_control
        ctl = json.loads(argument_control["stdout"])
        if argument_control["rc"] != 2 or ctl["status"] != "REJECTED" or ctl["stage"] != "unexpected_arguments" or ctl["event_was_enabled"]:
            raise RuntimeError("Argument guard control failed")
        sampled = native(f"/mnt/e/Projects/RISCV-research/{REL}/read_only_perf_sampler", timeout=15)
        record["native_sample"] = sampled
        receipt = json.loads(sampled["stdout"])
        record["sampling_receipt"] = receipt
        if sampled["rc"]:
            record["status"] = "NO_VALID_SAMPLE_NATIVE_DENIAL_OR_FAILURE_PRESERVED"
            return
        if receipt["status"] != "COMPLETED_BOUNDED_USER_PC_SAMPLING" or receipt["target_tid"] != 669 or receipt["elapsed_seconds"] > 5:
            raise RuntimeError("Native sampling completion/identity/bound guard failed")
        record["maps_after"] = native("cat", "/proc/669/maps")
        parsed_maps = []
        for line in maps["stdout"].splitlines():
            fields = line.split(maxsplit=5)
            low, high = (int(x,16) for x in fields[0].split("-"))
            parsed_maps.append({"low":low,"high":high,"permissions":fields[1],
                                "file_offset":int(fields[2],16),"module":fields[5] if len(fields)>5 else ""})
        biases = {x["low"]-x["file_offset"] for x in parsed_maps if x["module"] == EXEC and "x" in x["permissions"]}
        if len(biases) != 1:
            raise RuntimeError("PIE executable load bias is ambiguous")
        bias = biases.pop()
        symbols_run = native("nm", "-S", "-n", "--defined-only", "-C", EXEC)
        if symbols_run["rc"]:
            raise RuntimeError("Pinned actual executable symtab could not be read")
        symbols = []
        for line in symbols_run["stdout"].splitlines():
            m = re.match(r"^([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+([tTwW])\s+(.+)$", line)
            if m:
                symbols.append({"address":int(m[1],16),"size":int(m[2],16),"type":m[3],"name":m[4]})
        symbols.sort(key=lambda x:x["address"])
        addresses = [x["address"] for x in symbols]
        resolved = []
        for sample in receipt["samples"]:
            pc = int(sample["ip"],16)
            modules = [x for x in parsed_maps if x["low"] <= pc < x["high"]]
            actual = [x for x in modules if x["module"] == EXEC]
            linked = pc-bias if actual else None
            candidates = []
            if linked is not None:
                index = bisect.bisect_right(addresses,linked)-1
                while index >= 0 and symbols[index]["address"] == symbols[bisect.bisect_right(addresses,linked)-1]["address"]:
                    symbol=symbols[index]
                    if symbol["address"] <= linked < symbol["address"]+symbol["size"]:
                        candidates.append({**symbol,"offset":linked-symbol["address"]})
                    index -= 1
            resolved.append({**sample,"modules":modules,"load_bias":hex(bias) if actual else None,
                             "linked_address":hex(linked) if linked is not None else None,
                             "actual_pinned_executable_symbol_candidates":candidates})
        record["symbol_resolution"] = resolved
        record["symtab_command"] = {k:v for k,v in symbols_run.items() if k != "stdout"}
        record["symtab_stdout_sha256"] = hashlib.sha256(symbols_run["stdout"].encode()).hexdigest()
        record["actual_executable_sha256"] = sha(Path(r"\\wsl.localhost\Ubuntu") / EXEC.lstrip("/"))
        counts = {}
        for sample in resolved:
            names = [x["name"] for x in sample["actual_pinned_executable_symbol_candidates"]]
            key = " | ".join(names) if names else "UNRESOLVED_PINNED_SYMBOL"
            counts[key] = counts.get(key,0)+1
        record["statistical_function_sample_counts"] = counts
        record["status"] = "COMPLETED_STATISTICAL_USER_PC_DIAGNOSTIC_NOT_PROGRESS_OR_NET_PROOF"
    except Exception as exc:
        record["status"] = "DIAGNOSTIC_STOPPED_ERROR_PRESERVED_NO_ALTERNATE_PROBE"
        record["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        record["capture_end_utc"] = datetime.now(timezone.utc).isoformat()
        record["sampler_source_unchanged"] = sha(SOURCE) == record["sampler_source_sha256"]
        record["conclusion_limit"] = "Instruction samples identify only statistical user-space locations. They do not identify the active net, prove termination/algorithm progress, or establish a machine fault/hang. No alternate privilege/profiler is attempted."
        (OUT / "receipt.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"status":record["status"],"out":str(OUT / "receipt.json"),
                          "errno":record.get("sampling_receipt",{}).get("errno"),
                          "sample_counts":record.get("statistical_function_sample_counts",{})}))


if __name__ == "__main__":
    main()
