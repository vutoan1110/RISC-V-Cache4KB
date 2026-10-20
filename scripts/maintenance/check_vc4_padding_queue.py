#!/usr/bin/env python3
"""Focused VC4 queue controls. Synthetic tools/memory only; never starts WSL."""
from __future__ import annotations

import contextlib
import argparse
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/vc4_padding_queue_controls_20261010"
SPEC = importlib.util.spec_from_file_location("queue_vc4_padding", ROOT / "scripts/maintenance/queue_vc4_padding.py")
q = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(q)


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(OUT.relative_to(ROOT)))
    args = parser.parse_args()
    OUT = q.path_in(ROOT, args.output)
    q.require(OUT.is_relative_to(ROOT / "results/vc4_padding_queue_controls_20261010"), "controls output outside owned folder")
    OUT.mkdir(parents=True, exist_ok=True)
    require_new = OUT / "verification.json"
    if require_new.exists():
        raise RuntimeError("controls receipt already exists; keep the previous evidence")
    controls = []
    def check(name, fn):
        fn()
        controls.append({"name": name, "status": "PASS"})
    def rejected(fn, marker):
        try:
            fn()
        except q.Rejected as exc:
            assert marker in str(exc), (marker, str(exc))
        else:
            raise AssertionError("negative control accepted: " + marker)

    preparation = q.read_json(ROOT / q.PREPARATION)
    old = q.read_json(ROOT / preparation["configs"][0]["source"])
    new = q.read_json(ROOT / preparation["configs"][0]["config"])
    check("real_recipe_padding_only", lambda: q.check_pair(old, new))
    check("real_recipe_20ns_and_geometry", lambda: q.check_geometry(new))
    for name, key, value in [
        ("changed_clock", "CLOCK_PERIOD", 21),
        ("changed_geometry", "DIE_AREA", [0, 0, 3700, 3400]),
        ("changed_sdc", "PNR_SDC_FILE", "dir::relaxed.sdc"),
        ("changed_corners", "RSZ_CORNERS", ["tt"]),
        ("changed_clock_layer", "RT_CLOCK_MIN_LAYER", "met3"),
        ("extra_hypothesis", "MAX_FANOUT_CONSTRAINT", 16),
        ("changed_rtl_order", "VERILOG_FILES", list(reversed(new["VERILOG_FILES"]))),
        ("changed_macro", "MACROS", {}),
        ("incorrect_padding", "GPL_CELL_PADDING", 4),
    ]:
        changed = copy.deepcopy(new)
        changed[key] = value
        check(name + "_rejected", lambda changed=changed: rejected(lambda: q.check_pair(old, changed),
              "padding must" if name == "incorrect_padding" else
              "config key set" if key not in old else "exceed padding"))
    check("secondary_clock_override_rejected", lambda: rejected(
        lambda: q.check_geometry({**new, "pdk::sky130A": {"scl::sky130_fd_sc_hd": {"CLOCK_PERIOD": 25}}}), "20 ns"))
    with tempfile.TemporaryDirectory(prefix="queue_hash_control_", dir=OUT) as name:
        root = Path(name)
        (root / "x").write_text("baseline", encoding="utf-8")
        baseline = {"x": q.sha(root / "x")}
        check("frozen_hash_positive", lambda: q.assert_hashes(root, baseline))
        (root / "x").write_text("mutated", encoding="utf-8")
        check("frozen_hash_mutation_rejected", lambda: rejected(lambda: q.assert_hashes(root, baseline), "changed input"))
        check("missing_frozen_input_rejected", lambda: rejected(lambda: q.assert_hashes(root, {"absent": "0" * 64}), "missing input"))
        check("empty_frozen_set_rejected", lambda: rejected(lambda: q.assert_hashes(root, {}), "empty frozen"))
        check("workspace_escape_rejected", lambda: rejected(lambda: q.path_in(root, "../escape"), "outside research"))

    # No real process/memory/manifest tools are called by these queue cases.
    plan = {"frozen_local_input_sha256": {"synthetic": "0" * 64},
            "completion_meaning": "Synthetic process completion; no gate result"}
    case_count = 0
    def queue_case(name, memory, *, rc=0, pre_abort=False, abort_sleep=False,
                   abort_started=False, plan_fail=False, idle_fail=False,
                   plan_fail_on_final=False, create_run=False, interrupt_once=False,
                   fail_started_receipt=False):
        nonlocal case_count
        case_count += 1
        root = OUT / ("synthetic_" + name)
        assert not root.exists(), root
        (root / "asic").mkdir(parents=True)
        (root / "results").mkdir()
        if pre_abort:
            (root / q.ABORT).touch()
        calls = {"launch": 0, "wait": 0, "sleep": [], "plan": 0, "idle": 0, "commands": []}
        observations = iter(memory)
        def mem():
            return next(observations)
        def check_plan(_root, _plan):
            calls["plan"] += 1
            if plan_fail or (plan_fail_on_final and calls["plan"] > 1):
                raise q.Rejected("synthetic changed frozen input")
            return {"returncode": 0, "stdout": "synthetic manifest --check IDENTICAL"}
        def idle(_root):
            calls["idle"] += 1
            if idle_fail:
                raise q.Rejected("synthetic active PD process")
            return {"active_blockers": []}
        class Child:
            pid = 987654
            def wait(self):
                calls["wait"] += 1
                if interrupt_once and calls["wait"] == 1:
                    raise KeyboardInterrupt()
                if abort_started:
                    (root / q.ABORT).touch()
                if create_run:
                    (root / q.DESIGN / "runs" / q.TAG).mkdir(parents=True)
                return rc
        def launch(command, _root, log):
            assert command == q.COMMAND
            calls["launch"] += 1
            calls["commands"].append(command)
            log.write("SYNTHETIC TOOL ONLY: child output is not PD evidence\n")
            return Child()
        def sleep(seconds):
            assert seconds == 30
            calls["sleep"].append(seconds)
            if abort_sleep:
                (root / q.ABORT).touch()
        receipt_path = root / "receipt.json"
        original_save = q.save_json
        def save(path, value, **kwargs):
            if fail_started_receipt and value.get("status") == "STARTED":
                raise OSError("synthetic STARTED receipt write failure")
            original_save(path, value, **kwargs)
        try:
            q.save_json = save
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                exitcode = q.run_queue(root, plan, "0" * 64, receipt_path,
                                      memory_probe=mem, check_idle=idle, check_plan=check_plan,
                                      launch=launch, sleep=sleep)
        finally:
            q.save_json = original_save
        receipt = json.loads(receipt_path.read_text())
        (root / "calls.json").write_text(json.dumps({"calls": calls, "exitcode": exitcode,
            "synthetic_only": True}, indent=2) + "\n", encoding="utf-8")
        (root / "stdout.txt").write_text(stdout.getvalue(), encoding="utf-8")
        assert "gatePASS" not in json.dumps(receipt)
        assert receipt.get("signed_off", False) is False
        return exitcode, receipt, calls

    def assert_finish(name, memory, **kwargs):
        exitcode, receipt, calls = queue_case(name, memory, **kwargs)
        assert calls["launch"] == 1 and calls["wait"] >= 1
        assert receipt["status"] == "P1P2_FINISHED_REQUIRES_GATES_INSPECTION"
        assert receipt["gates_inspected"] is False and receipt["signed_off"] is False
        assert receipt["child_returncode"] == kwargs.get("rc", 0)
        assert exitcode == kwargs.get("rc", 0)
        return receipt, calls
    def assert_reject(name, memory, **kwargs):
        exitcode, receipt, calls = queue_case(name, memory, **kwargs)
        assert exitcode != 0 and calls["launch"] == 0
        assert receipt["status"] in ("ABORTED_BEFORE_START", "REJECTED_BEFORE_START")
    check("exact_10000mb_starts_once_foreground_wait", lambda: assert_finish("threshold", [10000, 10000], create_run=True))
    def wait_control():
        receipt, calls = assert_finish("wait_then_start", [9999, 3500, 10000, 10000])
        assert calls["sleep"] == [30, 30]
        assert [e["status"] for e in receipt["events"]] == ["WAITING_FOR_MEMORY", "WAITING_FOR_MEMORY", "STARTED", "P1P2_FINISHED_REQUIRES_GATES_INSPECTION"]
    check("waits_30sec_below_guard_then_starts", wait_control)
    def falling_control():
        receipt, calls = assert_finish("final_memory_fall", [10000, 9999, 10001, 10000])
        assert calls["sleep"] == [30] and calls["plan"] == 3
    check("ram_falls_during_validation_requeues", falling_control)
    check("preexisting_queue_abort_no_launch", lambda: assert_reject("abort_initial", [], pre_abort=True))
    check("abort_while_waiting_no_launch", lambda: assert_reject("abort_waiting", [9999], abort_sleep=True))
    check("frozen_input_changed_no_launch", lambda: assert_reject("hash_initial", [], plan_fail=True))
    check("frozen_input_changed_after_wait_no_launch", lambda: assert_reject("hash_final", [9999, 10000], plan_fail_on_final=True))
    check("live_pd_no_launch", lambda: assert_reject("live_pd", [], idle_fail=True))
    check("invalid_memory_no_launch", lambda: assert_reject("invalid_memory", [-1]))
    def after_start_control():
        receipt, calls = assert_finish("abort_after_started", [10000, 10000], abort_started=True)
        assert receipt["queue_abort_seen_after_start"] is True and calls["wait"] == 1
    check("abort_after_started_never_kills_flow", after_start_control)
    check("child_failure_retained_requires_gate_inspection", lambda: assert_finish("child_rc_failure", [10000, 10000], rc=7))
    def no_run_control():
        receipt, _ = assert_finish("exit_zero_no_run", [10000, 10000])
        assert receipt["run_directory_exists"] is False and receipt["gates_inspected"] is False
    check("exit_zero_without_run_never_gate_pass", no_run_control)
    def interrupt_control():
        _, calls = assert_finish("interrupt_monitored", [10000, 10000], interrupt_once=True)
        assert calls["wait"] == 2
    check("monitor_interrupt_retains_child_wait", interrupt_control)
    def write_failure_control():
        exitcode, receipt, calls = queue_case("started_receipt_error", [10000, 10000], fail_started_receipt=True)
        assert calls["launch"] == 1 and calls["wait"] == 1 and exitcode != 0
        assert receipt["status"] == "QUEUE_MONITOR_ERROR_REQUIRES_INSPECTION"
    check("started_receipt_error_retains_foreground_child", write_failure_control)
    def existing_receipt():
        root = OUT / "synthetic_threshold"
        rejected(lambda: q.run_queue(root, plan, "0" * 64, root / "receipt.json"), "receipt already exists")
    check("existing_receipt_never_overwritten", existing_receipt)

    # Check command/guard tampering before any local input or tool call.
    skeleton = {"schema": 1, "status": "PREPARED_NOT_EXECUTED", "not_a_measurement": True,
        "run_tag": q.TAG, "command": q.COMMAND, "stop_after": "p2",
        "windows_free_min_mb": 10000, "poll_seconds": 30, "queue_abort_file": q.ABORT}
    for key, value in [("command", ["wsl.exe", "unsafe"]), ("stop_after", "final"),
                       ("windows_free_min_mb", 6000), ("poll_seconds", 1),
                       ("queue_abort_file", "asic/.abort_gated_pd"), ("run_tag", "old_run")]:
        altered = {**skeleton, key: value}
        check("plan_" + key + "_tampering_rejected", lambda altered=altered: rejected(
            lambda: q.verify_plan(ROOT, altered), "queue command, scope or resource guard changed"))
    receipt = {"status": "VERIFIED_CONTROLS_ONLY", "not_a_measurement": True,
        "no_wsl_started": True, "memory_and_child_mocked": True, "total": len(controls),
        "passed": len(controls), "synthetic_queue_cases": case_count,
        "sources": {str(Path(__file__).relative_to(ROOT)).replace("\\", "/"): q.sha(Path(__file__)),
                    "scripts/maintenance/queue_vc4_padding.py": q.sha(ROOT / "scripts/maintenance/queue_vc4_padding.py")},
        "controls": controls}
    require_new.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "passed": len(controls), "total": len(controls),
                      "synthetic_queue_cases": case_count, "no_wsl_started": True}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
