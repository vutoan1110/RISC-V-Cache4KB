#!/usr/bin/env python3
"""Queue the prepared VC4 padding hypothesis through P1/P2 only.

--prepare freezes local inputs without starting WSL. --run requires that plan's
SHA256, waits for Windows free RAM, and owns the foreground wsl.exe until it
finishes. The child exit code never establishes that a PD gate passed. After
completion inspect the gate log and first-GRT skew before further PD work.
The separate queue abort flag only prevents a launch; it never kills a child.
External WSL binaries/PDK libraries remain a runtime prerequisite for the owner.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
OUT = "results/vc4_padding_queue_controls_20261010/prepared_queue"
PREPARATION = "results/vc4_padding_preparation_20261009/inputs.json"
SA2_INPUTS = "results/completion_preparation_20261009/sa2_lec_20261009/inputs_and_acceptance.json"
MANIFEST = "results/rtl_manifest.json"
RTL_ID = "6c4ccffd4257c224a537bd8d8e7b724ac8505bb19eb4d9e1361019af77341291"
TAG = "vc4_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_r1"
DESIGN = "asic/soc_vc4_4kb"
CONFIG = "config_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd.json"
SDC = "asic/soc_dm_4kb/soc.sdc"
SDC_HASH = "bd91f10e1173bb707a9f544d0e5b7656de5b5bebe5b416e24471a15194d82ce9"
ABORT = "results/.abort_vc4_padding_queue"
MEMORY_MB = 10000
POLL_SECONDS = 30
BASH_COMMAND = (
    "cd /mnt/e/Projects/RISCV-research/asic && "
    "G5_UNLIMITED_LATE_PHASE=1 P2_INITIAL_GRT_FALLBACK=1 P2_MIN_SETUP=0 "
    "STOP_AFTER=p2 ITEMS='soc_vc4_4kb:" + TAG + ":" + CONFIG + "' bash run_gated_pd.sh"
)
COMMAND = ["wsl.exe", "-d", "Ubuntu", "-e", "bash", "-c", BASH_COMMAND]
PREPARED_HASHES = {
    "asic/soc_vc4_4kb/config_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd.json": "2e663945491c1b361ee8f4166046455eea8cb6c5252e9276df0be6152ed8fcd7",
    DESIGN + "/" + CONFIG: "ef697fd746297aba4d71ffea370de3748f1ca53e30da247fe2de64f722b34594",
    "asic/soc_vc4_4kb/config_corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd_ecomin.json": "64357e1f62dfd85f560400277289b8de357acb784955bac3327dc1ec29bcc3c6",
    "asic/soc_vc4_4kb/config_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_ecomin.json": "502d35dfbd20be8581033354a7d9410891c7b50fbc075c4f8d2ec47d70a11049",
    "results/vc4_corr3600x3400_drt_diagnosis_20261009.json": "c9f15682e76fdbb8267a2b72b5eb86b8efbfcb99ec95be0bb349ab04061df035",
    "asic/openlane-local/openlane/scripts/openroad/gpl.tcl": "3a44c6b1ab658274e3fac1a0db42ce855d96b3ceeea7c2bc4ece76bcf302fcd3",
    "asic/openlane-local/openlane/scripts/openroad/common/dpl_cell_pad.tcl": "29656e8fcbb5fb2dd952242be3c4c0b05bf5192cce0959c08dda9f063b684314",
}
FLOW_FILES = (
    "asic/run_gated_pd.sh", "asic/run_pd_mk.sh", "asic/run_gated_resume.sh",
    "asic/run_gated_branch.sh", "asic/branch_run.sh", "asic/drt_watch.sh",
    "asic/fp_tools/gate_check.py", "asic/fp_tools/grt_skew_screen.sh",
    "scripts/rtl_manifest.py", "scripts/maintenance/queue_vc4_padding.py",
)


class Rejected(RuntimeError):
    pass


def require(condition, reason):
    if not condition:
        raise Rejected(reason)


def stamp():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def path_in(root, name):
    path = (root / name).resolve()
    require(path.is_relative_to(root.resolve()), "input/output outside research workspace: " + name)
    return path


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def assert_hashes(root, expected):
    require(bool(expected), "empty frozen input set")
    for name, digest in expected.items():
        path = path_in(root, name)
        require(path.is_file(), "missing input: " + name)
        require(sha(path) == digest, "changed input: " + name)


def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if not k.startswith("//")}
    if isinstance(value, list):
        return [clean(v) for v in value]
    return value


def check_pair(old, new):
    old, new = clean(old), clean(new)
    require(set(old) == set(new), "config key set changed")
    changed = {k for k in old if old[k] != new[k]}
    require(changed == {"GPL_CELL_PADDING", "DPL_CELL_PADDING"}, "config changes exceed padding hypothesis")
    for key in changed:
        require(type(old[key]) is int and old[key] == 0 and type(new[key]) is int and new[key] == 2,
                "padding must change from 0 to 2 total sites: " + key)


def check_geometry(cfg):
    require(cfg.get("CLOCK_PERIOD") == 20 and
            cfg.get("pdk::sky130A", {}).get("scl::sky130_fd_sc_hd", {}).get("CLOCK_PERIOD") == 20,
            "clock is not explicitly 20 ns at both configuration levels")
    require(cfg.get("DIE_AREA") == [0, 0, 3600, 3400] and
            cfg.get("CORE_AREA") == [12, 12, 3588, 3388], "die/core geometry changed")
    require(cfg.get("PNR_SDC_FILE") == "dir::../soc_dm_4kb/soc.sdc" and
            cfg.get("SIGNOFF_SDC_FILE") == "dir::../soc_dm_4kb/soc.sdc", "SDC path changed")
    require(cfg.get("RUN_POST_GRT_DESIGN_REPAIR") is False and
            cfg.get("RUN_POST_GRT_RESIZER_TIMING") is False and
            cfg.get("RUN_ANTENNA_REPAIR") is False, "prepared VC4 recipe changed")
    require("RSZ_CORNERS" not in cfg and "RT_CLOCK_MIN_LAYER" not in cfg and
            "RT_CLOCK_MAX_LAYER" not in cfg, "default resizer/clock-layer recipe changed")


def referenced_paths(root, value):
    paths = []
    if isinstance(value, dict):
        for k, v in value.items():
            if not k.startswith("//"):
                paths.extend(referenced_paths(root, v))
    elif isinstance(value, list):
        for v in value:
            paths.extend(referenced_paths(root, v))
    elif isinstance(value, str) and value.startswith("dir::"):
        path = path_in(root, DESIGN + "/" + value[5:])
        require(path.is_file(), "missing config-referenced file: " + str(path))
        paths.append(path.relative_to(root).as_posix())
    return paths


def manifest_check(root):
    manifest = read_json(path_in(root, MANIFEST))
    require(manifest.get("count") == 227 and len(manifest.get("files", {})) == 227 and
            manifest.get("aggregate") == RTL_ID, "unexpected current RTL manifest identity/count")
    proc = subprocess.run([sys.executable, "scripts/rtl_manifest.py", "--check"],
                          cwd=root, text=True, capture_output=True)
    require(proc.returncode == 0 and "IDENTICAL" in proc.stdout,
            "rtl_manifest.py --check failed: " + proc.stdout + proc.stderr)
    return {"command": [sys.executable, "scripts/rtl_manifest.py", "--check"],
            "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def collect_plan(root):
    assert_hashes(root, PREPARED_HASHES)
    preparation = read_json(path_in(root, PREPARATION))
    require(preparation.get("status") == "PREPARED_NOT_EXECUTED" and
            preparation.get("not_a_measurement") is True and
            preparation.get("padding_sites_each_side") == 1, "invalid preparation receipt")
    declared = dict(preparation["evidence"])
    configs = []
    for pair in preparation["configs"]:
        declared[pair["source"]] = pair["source_sha256"]
        declared[pair["config"]] = pair["config_sha256"]
        old = read_json(path_in(root, pair["source"]))
        cfg = read_json(path_in(root, pair["config"]))
        check_pair(old, cfg)
        check_geometry(cfg)
        configs.append(cfg)
    require(declared == PREPARED_HASHES and len(configs) == 2, "preparation's seven hashes/configs changed")
    require(configs[0].get("POST_ROUTE_HOLD_ECO_RCX_CORNER", "max_*") == "max_*" and
            configs[1].get("POST_ROUTE_HOLD_ECO_RCX_CORNER") == "min_*", "ECO max/min recipe changed")
    require(configs[0]["VERILOG_FILES"] == configs[1]["VERILOG_FILES"] and
            len(configs[0]["VERILOG_FILES"]) == 42, "expected 42 ordered frozen RTL inputs")
    rtl = referenced_paths(root, configs[0]["VERILOG_FILES"])
    require(len(set(rtl)) == 42, "duplicate RTL inputs")
    for name in rtl:
        require(name.startswith("asic/snapshots/rtl_r14/") or name in
                ("asic/dse_sram/cache_dse_data_bank_sram.v", DESIGN + "/soc_asic_top.v"),
                "PD reads active/unexpected RTL: " + name)
    shared = read_json(path_in(root, SA2_INPUTS))["local_input_sha256"]
    common = {name: shared[name] for name in rtl if name in shared}
    require(len(common) == 41, "expected 41 shared RTL inputs in the frozen SA2 preparation")
    assert_hashes(root, common)
    require(configs[0]["MACROS"] == configs[1]["MACROS"] and len(configs[0]["MACROS"]) == 2,
            "macro configuration changed")
    macros = sorted(set(referenced_paths(root, configs[0]["MACROS"])))
    require(len(macros) == 8, "expected 8 local GDS/LEF/netlist/Liberty macro files")
    assert_hashes(root, {SDC: SDC_HASH})
    check = manifest_check(root)
    local = set(PREPARED_HASHES) | {PREPARATION, SA2_INPUTS, MANIFEST, SDC,
                                  "results/vc4_padding_hypothesis_20261009.md"} | set(FLOW_FILES)
    for cfg in configs:
        local.update(referenced_paths(root, cfg))
    # Freeze the local OpenLane Python/Tcl implementations, not generated caches.
    for path in path_in(root, "asic/openlane-local/openlane").rglob("*"):
        if path.is_file() and path.suffix in (".py", ".tcl") and "__pycache__" not in path.parts:
            local.add(path.relative_to(root).as_posix())
    frozen = {name: sha(path_in(root, name)) for name in sorted(local)}
    return {
        "schema": 1, "status": "PREPARED_NOT_EXECUTED", "not_a_measurement": True,
        "created": stamp(), "hypothesis": preparation["hypothesis"], "run_tag": TAG,
        "design": DESIGN, "config": CONFIG, "command": COMMAND,
        "stop_after": "p2", "windows_free_min_mb": MEMORY_MB, "poll_seconds": POLL_SECONDS,
        "queue_abort_file": ABORT, "rtl_manifest": RTL_ID, "rtl_manifest_file_count": 227,
        "ordered_rtl_inputs": rtl, "shared_frozen_sa2_rtl_count": len(common),
        "macro_files": macros, "sdc_sha256": SDC_HASH, "prepared_hash_count": 7,
        "frozen_local_input_sha256": frozen, "manifest_check": check,
        "external_runtime_prerequisites": "Check WSL flow binaries, external nix shell and sky130 libraries before the flow. No external equivalence proof or sign-off is claimed.",
        "completion_meaning": "Process finished only; inspect P1/P2 gates and first-GRT skew. No detailed route/sign-off proof.",
    }


def verify_plan(root, plan):
    require(plan.get("schema") == 1 and plan.get("status") == "PREPARED_NOT_EXECUTED" and
            plan.get("not_a_measurement") is True, "invalid prepared queue plan")
    require(plan.get("run_tag") == TAG and plan.get("command") == COMMAND and
            plan.get("stop_after") == "p2" and plan.get("windows_free_min_mb") == MEMORY_MB and
            plan.get("poll_seconds") == POLL_SECONDS and plan.get("queue_abort_file") == ABORT,
            "queue command, scope or resource guard changed")
    assert_hashes(root, plan.get("frozen_local_input_sha256", {}))
    current = collect_plan(root)
    for key in ("frozen_local_input_sha256", "ordered_rtl_inputs", "macro_files", "rtl_manifest",
                "rtl_manifest_file_count", "shared_frozen_sa2_rtl_count", "sdc_sha256", "prepared_hash_count"):
        require(plan.get(key) == current[key], "prepared input set changed: " + key)
    return current["manifest_check"]


def windows_free_mb():
    require(os.name == "nt", "the queue is a Windows runner")
    class Memory(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
            (name, ctypes.c_ulonglong) for name in
            ("total", "avail", "page_total", "page_avail", "virtual_total", "virtual_avail", "ext")]
    state = Memory()
    state.length = ctypes.sizeof(state)
    require(ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(state)), "Windows memory probe failed")
    return state.avail // (1024 * 1024)


def idle_check(root):
    # A read-only Windows inventory does not start a WSL client/VM.
    script = "Get-CimInstance Win32_Process | Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"
    proc = subprocess.run(["pwsh", "-NoProfile", "-Command", script], capture_output=True, text=True)
    require(proc.returncode == 0, "Windows process probe failed: " + proc.stderr)
    rows = json.loads(proc.stdout or "[]")
    if isinstance(rows, dict):
        rows = [rows]
    blockers = []
    for row in rows:
        name = str(row.get("Name", "")).lower()
        line = str(row.get("CommandLine") or "").lower()
        pid = row.get("ProcessId")
        if pid == os.getpid():
            continue
        if name in ("openroad.exe", "yosys.exe", "quartus_fit.exe", "vsim.exe") or (
                name == "wsl.exe" and (not line or any(token in line for token in
                ("run_gated", "run_pd", "--run-tag", "openlane", "run_lec", "sta_power")))) or (
                name in ("python.exe", "pythonw.exe", "py.exe") and
                "queue_vc4_padding.py" in line and "--run" in line):
            blockers.append(row)
    require(not blockers, "active measurement/queue process: " + json.dumps(blockers))
    # Existing gate locks can indicate native jobs invisible to Windows process inventory.
    require(not list(path_in(root, "asic").glob(".gated_drt_gate.lock*")), "gate lock exists; inspect it before launch")
    require(not path_in(root, "asic/.abort_gated_pd").exists(), "global PD cooperative abort flag exists")
    require(not path_in(root, DESIGN + "/runs/" + TAG).exists(), "fresh base run already exists")
    return {"windows_processes_checked": len(rows), "active_blockers": []}


def save_json(path, value, fresh=False):
    require(not fresh or not path.exists(), "output already exists: " + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def note(root, reason):
    require("\n" not in reason and "\r" not in reason, "multiline gate note rejected")
    with path_in(root, "asic/gated_pd.log").open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(stamp() + " NOTE " + TAG + " " + reason + "\n")


def foreground_child(command, root, log):
    # No detached flags, services, scheduler, nohup or process termination.
    return subprocess.Popen(command, cwd=root, stdout=log, stderr=subprocess.STDOUT)


def run_queue(root, plan, plan_digest, receipt_path, *, memory_probe=windows_free_mb,
              check_idle=idle_check, check_plan=verify_plan, launch=foreground_child, sleep=time.sleep):
    require(not receipt_path.exists(), "queue receipt already exists; inspect preserved receipt")
    require(not receipt_path.with_suffix(".log").exists(), "queue stdout log already exists")
    receipt = {"schema": 1, "not_a_measurement": True, "run_tag": TAG, "command": COMMAND,
               "plan_sha256": plan_digest, "wrapper_pid": os.getpid(), "child_pid": None,
               "frozen_local_input_sha256": plan["frozen_local_input_sha256"], "events": [],
               "completion_meaning": plan["completion_meaning"]}
    aborted = path_in(root, ABORT)
    def update(status, **fields):
        receipt.update(status=status, updated=stamp(), **fields)
        receipt["events"].append({"time": receipt["updated"], "status": status, **fields})
        save_json(receipt_path, receipt)
        print(status + " " + json.dumps(fields), flush=True)
    try:
        require(not aborted.exists(), "queue abort flag exists before validation")
        check_plan(root, plan)
        check_idle(root)
        note(root, "queue requested; Windows free >=10000 MB required; foreground P1/P2 only; exit code is not a gate result")
        first_wait = True
        while True:
            if aborted.exists():
                update("ABORTED_BEFORE_START", reason="separate queue abort flag; no child started")
                note(root, "queue stopped before launch by cooperative queue abort flag; no running flow killed")
                return 2
            check_idle(root)
            free = memory_probe()
            require(type(free) is int and free >= 0, "invalid Windows memory observation")
            resources = {"windows_free_mb": free, "required_mb": MEMORY_MB, "poll_seconds": POLL_SECONDS}
            if free >= MEMORY_MB:
                # Validate again immediately before launch; memory can fall while
                # hashing/manifest checking. Re-enter the same queue if it does.
                manifest_result = check_plan(root, plan)
                idle = check_idle(root)
                require(not aborted.exists(), "queue abort flag arrived before launch")
                free = memory_probe()
                require(type(free) is int and free >= 0, "invalid final Windows memory observation")
                resources["windows_free_mb"] = free
                if free >= MEMORY_MB:
                    break
            update("WAITING_FOR_MEMORY", resources=resources)
            if first_wait:
                note(root, "queue waiting for Windows RAM; free_mb=" + str(free) + "; threshold_mb=10000; poll_seconds=30; no applications stopped")
                first_wait = False
            sleep(POLL_SECONDS)
        require(not aborted.exists(), "queue abort flag arrived immediately before launch")
        note(root, "queue launching frozen padding-only hypothesis from step 1; STOP_AFTER=p2; Windows free_mb=" + str(free))
        log_path = receipt_path.with_suffix(".log")
        with log_path.open("x", encoding="utf-8") as log:
            child = launch(COMMAND, root, log)
            receipt["child_pid"] = child.pid
            try:
                update("STARTED", child_pid=child.pid, resources={"windows_free_mb": free, "required_mb": MEMORY_MB},
                       manifest_check=manifest_result, idle_check=idle, stdout_log=str(log_path))
            finally:
                # Even a receipt/disk error after Popen must not orphan a healthy
                # child or return from the queue while the foreground client runs.
                # The queue abort file has no effect after launch.
                while True:
                    try:
                        rc = child.wait()
                        break
                    except KeyboardInterrupt:
                        try:
                            note(root, "queue interrupt observed after launch; foreground child retained until natural completion; use existing PD cooperative abort for future phases")
                        except OSError:
                            print("Receipt/log unavailable; retaining foreground child until completion", file=sys.stderr, flush=True)
        update("P1P2_FINISHED_REQUIRES_GATES_INSPECTION", child_returncode=rc,
               queue_abort_seen_after_start=aborted.exists(),
               run_directory_exists=path_in(root, DESIGN + "/runs/" + TAG).exists(),
               gates_inspected=False, signed_off=False,
               required_next_action="Inspect gated_pd.log, P1/P2 state and first-global-route skew before deciding whether to continue")
        note(root, "foreground queue child finished rc=" + str(rc) + "; P1/P2 gate inspection required; no sign-off claim")
        return 0 if rc == 0 else rc
    except (Rejected, OSError, ValueError, KeyError) as exc:
        update("REJECTED_BEFORE_START" if receipt["child_pid"] is None else "QUEUE_MONITOR_ERROR_REQUIRES_INSPECTION",
               reason=str(exc), gates_inspected=False, signed_off=False)
        note(root, "queue rejected/monitor error: " + str(exc).replace("\n", " ").replace("\r", " ") + "; no child termination requested")
        return 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument("--plan", default=OUT + "/plan.json")
    parser.add_argument("--receipt", default=OUT + "/receipt.json")
    parser.add_argument("--plan-sha256", help="Required for --run; SHA256 printed by --prepare")
    args = parser.parse_args()
    try:
        plan_path = path_in(ROOT, args.plan)
        receipt_path = path_in(ROOT, args.receipt)
        if args.run:
            require(args.plan_sha256 and re.fullmatch(r"[0-9a-f]{64}", args.plan_sha256), "--run requires --plan-sha256")
            require(sha(plan_path) == args.plan_sha256, "plan bytes changed since review")
            return run_queue(ROOT, read_json(plan_path), args.plan_sha256, receipt_path)
        require(not path_in(ROOT, ABORT).exists(), "queue abort flag exists")
        idle_check(ROOT)
        plan = collect_plan(ROOT)
        if args.prepare:
            save_json(plan_path, plan, fresh=True)
            print(json.dumps({"status": plan["status"], "plan": str(plan_path), "plan_sha256": sha(plan_path),
                              "local_inputs": len(plan["frozen_local_input_sha256"]), "rtl_inputs": 42,
                              "macro_files": 8, "command": COMMAND}, indent=2))
        else:
            print(json.dumps(plan, indent=2))
        return 0
    except (Rejected, OSError, ValueError, KeyError) as exc:
        print("REJECTED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
