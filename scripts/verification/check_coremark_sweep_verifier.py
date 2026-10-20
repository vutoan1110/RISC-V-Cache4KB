"""Synthetic acceptance/rejection controls for the independent sweep auditor.

The fixture contains fake compiler/simulator evidence, explicitly marked
NOT_A_MEASUREMENT. No simulator, WSL tool, RTL edit or real result rewrite.
"""
from __future__ import annotations

import copy
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_coremark_sweep_crc as audit


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode("ascii"))


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="ascii") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def log(body):
    return ("Reading pref.tcl\n\n# 2024.1\n# onerror {quit -code 1 -f}\n"
            "# Start time: SYNTHETIC_NOT_A_MEASUREMENT\n" + body +
            "# quit -f\n# End time: SYNTHETIC_NOT_A_MEASUREMENT\n# Errors: 0, Warnings: 0\n")


def uart(r, crcs):
    txt = ("2K performance run parameters for coremark.\nCoreMark Size : 666\n"
           "Iterations : 1\nTotal time (secs): 0\n"
           "ERROR! Must execute for at least 10 secs for a valid result!\nseedcrc : 0xe9f5\n")
    for field in ("crclist", "crcmatrix", "crcstate", "crcfinal"):
        txt += f"[0]{field} : 0x{crcs[field]:04x}\n"
    txt += "Errors detected\nRESULT=PASS\nVERIFY_CODE=0x00000000\n"
    mapping = dict(MCYCLE="mcycle", MINSTRET="minstret", I_ACCESS="i_access", I_MAIN_HIT="i_main",
        I_VICTIM_HIT="i_victim", I_TRUE_MISS="i_miss", D_MAIN_HIT="d_main", D_VICTIM_HIT="d_victim",
        D_TRUE_MISS="d_miss", I_WAIT="i_wait", D_WAIT="d_wait", LOAD_USE="load_use", CONTROL_REDIRECT="control",
        TRAP_REDIRECT="trap", MMIO_WAIT="mmio", PIPE_FILL_DRAIN="fill_drain", OTHER="other", BRANCH="branches",
        BRANCH_TAKEN="taken", BRANCH_NOT_TAKEN="not_taken", PRED="predictions", CORRECT="correct",
        MISPRED="mispredict", AXI_READ="axi_read", AXI_WRITE="axi_write")
    for key, field in mapping.items():
        txt += f"{key}=0x{r[field]:08X}\n"
    return txt + f"D_ACCESS=0x{r['d_read'] + r['d_write']:08X}\nDONE\n"


def fixture(root):
    output = root / "results/synthetic_sweep"
    output.mkdir(parents=True)
    actual = json.loads((audit.ROOT / "results/rtl_manifest.json").read_text())
    special = {"sw/coremark/core_main.c", "scripts/verification/coremark_uart_observer.sv", "tb/compile_active_design.do", *audit.REFERENCE_PATHS}
    for relative in set(actual["files"]) | set(audit.EXTRAS):
        if relative == "results/rtl_manifest.json":
            continue
        content = (audit.ROOT / relative).read_text() if relative in special else "SYNTHETIC_NOT_A_MEASUREMENT\n"
        write(root / relative, content)
    files = {relative: audit.sha(root / relative) for relative in actual["files"]}
    aggregate = hashlib.sha256("".join(k + files[k] for k in sorted(files)).encode()).hexdigest()
    manifest = dict(count=227, aggregate=aggregate, files=files, generated="SYNTHETIC_NOT_A_MEASUREMENT")
    write(root / "results/rtl_manifest.json", json.dumps(manifest, indent=2) + "\n")
    inputs = {k: audit.sha(root / k) for k in set(files) | set(audit.EXTRAS)}
    generated = output / "coremark_sweep_observer.sv"
    write(generated, audit.expected_wrapper((root / "scripts/verification/coremark_uart_observer.sv").read_text()))
    points = audit.grid()
    expected = audit.baseline(root, points)
    crcs = {"seedcrc": 0xe9f5, **audit.source_crcs((root / "sw/coremark/core_main.c").read_text())}
    crcs.update(crcfinal=crcs["crclist"], size_per_algorithm=666, iterations=1,
                duration_seconds=0, crc_pass=1, official_score=0, validation="suite_numeric_crc_short_simulation")
    state = dict(status=audit.STATUS, started="2026-10-10T00:00:00+07:00", completed="2026-10-10T01:00:00+07:00",
        rtl_id=aggregate, cases_per_pass=92, ram_bytes=32768, window="complete_coremark_main", official_score=False,
        method="fresh_single_lane_simulations_passive_apb_uart_source_numeric_crc", excluded_point={"point": "SA4_256B_L16"},
        inputs=inputs, artifacts={}, generated_observer_sha256=audit.sha(generated), cases=[], compilations=[])
    artifacts = [generated]
    for number in (1, 2):
        lib = f"coremark_crc_p{number}"
        libdir = output / lib
        write(libdir / "NOT_A_REAL_COMPILED_LIBRARY.txt", "SYNTHETIC_NOT_A_MEASUREMENT\n")
        ini = output / f"modelsim_p{number}.ini"
        script = output / f"compile_p{number}.do"
        base_log = output / f"compile_p{number}.log"
        wrapper_log = output / f"compile_sweep_p{number}.log"
        write(ini, f"[Library]\n{lib} = {libdir.as_posix()}\nothers = {audit.SYSTEM_INI.as_posix()}\n")
        original = (root / "tb/compile_active_design.do").read_text()
        block = "if {[file exists work]} {\n    vdel -lib work -all\n}\nvlib work"
        generated_do = original.replace(block, f"vlib {{{libdir.as_posix()}}}").replace("vlog -sv", f"vlog -work {lib} -sv")
        generated_do += f"\nvlog -work {lib} -sv {{{(root / 'scripts/verification/coremark_uart_observer.sv').as_posix()}}}\necho {{[PASS] Passive CoreMark UART observer compiled}}\n"
        write(script, generated_do)
        compile_body = f"# do {{{script.as_posix()}}}\n# vlib {{{libdir.as_posix()}}}\n"
        compile_body += "".join(f"# {invocation}\n# Errors: 0, Warnings: 0\n" for invocation in audit.compile_commands(generated_do))
        write(base_log, log(compile_body + "# [PASS] Passive CoreMark UART observer compiled\n"))
        command = f"onerror {{quit -code 1 -f}}; vlog -work {lib} -sv {{{generated.as_posix()}}}; echo {{[PASS] Sweep passive observer compiled}}; quit -f"
        write(wrapper_log, log(f"#  vlog -work {lib} -sv {{{generated.as_posix()}}}\n# -- Compiling module tb_coremark_sweep_crc_audit\n# [PASS] Sweep passive observer compiled\n"))
        state["compilations"].append(dict(pass_=number))
        state["compilations"][-1] = {"pass": number, "library": lib, "modelsim_ini": str(ini),
            "generated_wrapper_command": [str(audit.VSIM), "-c", "-modelsimini", str(ini), "-do", command],
            "generated_wrapper_returncode": 0}
        artifacts.extend((ini, script, base_log, wrapper_log))
        rows = []
        for (name, fast), p in points.items():
            suffix = f"p{number}_{name.lower()}_fast{fast}"
            case_log = output / f"{suffix}.log"
            case_uart = output / f"{suffix}.uart.txt"
            invocation = (f"vsim -onfinish stop -gCACHE_CONFIG={p['cfg']} -gCACHE_FAST_HIT={fast} -gICACHE_LINE_COUNT={p['lines']} "
                f"-gDCACHE_LINE_COUNT={p['lines']} -gCACHE_LINE_WORDS={p['line_words']} -gVICTIM_ENTRIES={p['victim_entries']} "
                f"{lib}.tb_coremark_sweep_crc_audit +benchmark=coremark +max_cycles=40000000 +coremark_uart={case_uart.as_posix()}")
            command = f"onerror {{quit -code 1 -f}}; {invocation}; run -all; quit -f"
            r = expected[(name, fast)]
            content = uart(r, crcs)
            write(case_uart, content)
            profile = {k: p[k] for k in audit.PARAMETERS}
            profile.update(d_lines=p["lines"], imem_words=4096, dmem_words=4096, l0_entries=8, predictor=1)
            body = f"# {invocation}\n# COREMARK_SWEEP_PROFILE " + " ".join(f"{k}={profile[k]}" for k in audit.PROFILE) + "\n"
            body += f"# BENCHMARK_SNAPSHOT benchmark=coremark config={p['cfg']} " + " ".join(f"{k}={r[k]}" for k in audit.FIELDS) + "\n"
            body += f"# [PASS] Atomic benchmark snapshot\n# COREMARK_UART_CAPTURE bytes={len(content.encode('ascii'))} method=accepted_apb_txdata_writes\n"
            write(case_log, log(body))
            state["cases"].append({"pass": number, "point": name, "fast_hit": fast, "crc_pass": True,
                "all_counters_equal_reference": True, "elapsed_seconds": 1.0, "returncode": 0,
                "command": [str(audit.VSIM), "-c", "-modelsimini", str(ini), "-do", command],
                "log": case_log.relative_to(root).as_posix(), "uart": case_uart.relative_to(root).as_posix()})
            artifacts.extend((case_log, case_uart))
            rows.append({k: p[k] for k in audit.RESULT_HEADER[:7]} | r | crcs)
        result = output / f"results_p{number}.csv"
        write_csv(result, rows, audit.RESULT_HEADER)
        artifacts.append(result)
    state["artifacts"] = {p.relative_to(root).as_posix(): audit.sha(p) for p in artifacts}
    write(output / "verification.json", json.dumps(state, indent=2) + "\n")
    write(root / "NOT_A_MEASUREMENT.txt", "Synthetic corruption controls. These files are not project measurement evidence.\n")
    return output, state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("results/coremark_sweep_verifier_controls_20261010/checked_controls"))
    args = parser.parse_args()
    destination = args.out if args.out.is_absolute() else audit.ROOT / args.out
    audit.require(destination.resolve().is_relative_to((audit.ROOT / "results").resolve()) and not destination.exists(), "Controls require a new directory under results")
    destination.mkdir(parents=True, exist_ok=False)
    root = destination / "synthetic_workspace_NOT_A_MEASUREMENT"
    output, pristine = fixture(root)
    checks = []
    receipt = output / "verification.json"

    def control(label, mutate=None, accept=False):
        state = copy.deepcopy(pristine)
        changed = {}
        def patch(relative, transform):
            path = root / relative
            changed[path] = path.read_bytes()
            path.write_bytes(transform(changed[path]))
            if relative in state["artifacts"]:
                state["artifacts"][relative] = audit.sha(path)
        if mutate:
            mutate(state, patch)
        write(receipt, json.dumps(state, indent=2) + "\n")
        try:
            audit.verify(root, output)
            rejected = False
            reason = ""
        except (ValueError, TypeError, KeyError, OSError) as exc:
            rejected = True
            reason = str(exc)
        finally:
            for path, content in changed.items():
                path.write_bytes(content)
        if rejected == accept:
            raise AssertionError("Unexpected control verdict: " + label + " " + reason)
        checks.append(dict(label=label, expected="ACCEPT" if accept else "REJECT", pass_=True, reason=reason))

    first = pristine["cases"][0]
    control("complete_184_case_fixture_not_a_measurement", accept=True)
    control("in_progress_cannot_be_promoted", lambda s, p: s.update(status="IN_PROGRESS"))
    control("tampered_success_status", lambda s, p: s.update(status="PASS"))
    control("missing_independent_case_pair", lambda s, p: s["cases"].pop())
    control("duplicate_receipt_case", lambda s, p: s["cases"].__setitem__(-1, copy.deepcopy(s["cases"][0])))
    control("wrong_input_sha", lambda s, p: s["inputs"].__setitem__("fw/coremark.hex", "0" * 64))
    control("missing_input_sha", lambda s, p: s["inputs"].pop("scripts/verification/coremark_crc_gate.py"))
    control("nonzero_case_process", lambda s, p: s["cases"][0].update(returncode=1))
    control("boolean_zero_is_not_native_returncode", lambda s, p: s["cases"][0].update(returncode=False))
    control("nonzero_wrapper_process", lambda s, p: s["compilations"][0].update(generated_wrapper_returncode=1))
    control("reused_private_library", lambda s, p: s["compilations"][1].update(library="coremark_crc_p1"))
    control("wrong_case_raw_suffix", lambda s, p: s["cases"][0].update(log=s["cases"][1]["log"]))
    control("missing_actual_compilation_with_forged_pass_and_refreshed_sha", lambda s, p: p((output / "compile_p1.log").relative_to(root).as_posix(), lambda b: re.sub(rb"^# vlog[^\n]+\n", b"", b, flags=re.M)))
    control("wrong_command_parameter", lambda s, p: s["cases"][0]["command"].__setitem__(5, s["cases"][0]["command"][5].replace("-gCACHE_CONFIG=0", "-gCACHE_CONFIG=1")))
    control("missing_output_sha", lambda s, p: s["artifacts"].pop(first["uart"]))
    control("wrong_output_sha", lambda s, p: s["artifacts"].__setitem__(first["log"], "0" * 64))
    control("fatal_with_valid_snapshot_and_refreshed_sha", lambda s, p: p(first["log"], lambda b: b + b"# ** Fatal: synthetic corruption\n"))
    control("wrong_actual_elaborated_parameter_with_refreshed_sha", lambda s, p: p(first["log"], lambda b: b.replace(b"imem_words=4096", b"imem_words=2048")))
    control("corrupt_numeric_crc_with_refreshed_sha", lambda s, p: p(first["uart"], lambda b: b.replace(b"0x1fd7", b"0x1fd6")))
    control("missing_numeric_crc_with_refreshed_sha", lambda s, p: p(first["uart"], lambda b: b.replace(b"[0]crcmatrix", b"[0]crcmissing")))
    def changed_counter(s, patch):
        original = (root / first["log"]).read_bytes()
        number = int(re.search(rb"axi_read=(\d+)", original)[1])
        patch(first["log"], lambda b: re.sub(rb"axi_read=(\d+)", lambda m: b"axi_read=" + str(int(m[1]) + 1).encode(), b))
        patch(first["uart"], lambda b: b.replace(f"AXI_READ=0x{number:08X}".encode(), f"AXI_READ=0x{number + 1:08X}".encode()))
    control("valid_invariants_but_counter_differs_reference", changed_counter)
    control("truncated_log_with_refreshed_sha", lambda s, p: p(first["log"], lambda b: b.split(b"# End time:")[0]))
    control("truncated_uart_with_refreshed_sha", lambda s, p: p(first["uart"], lambda b: b[:-5]))
    def duplicate_row(s, patch):
        rel = (output / "results_p1.csv").relative_to(root).as_posix()
        patch(rel, lambda b: b + b.splitlines(keepends=True)[1])
    control("duplicate_csv_row_with_refreshed_sha", duplicate_row)
    def tamper_csv(s, patch):
        rel = (output / "results_p1.csv").relative_to(root).as_posix()
        patch(rel, lambda b: b.replace(b"suite_numeric_crc_short_simulation", b"unchecked_crc", 1))
    control("csv_field_differs_raw_with_refreshed_sha", tamper_csv)
    control("missing_counter_csv_header_with_refreshed_sha", lambda s, p: p((output / "results_p1.csv").relative_to(root).as_posix(), lambda b: b.replace(b"trap_ev,", b"", 1)))
    # Leave only the explicitly labelled pristine synthetic fixture on disk.
    write(receipt, json.dumps(pristine, indent=2) + "\n")
    verification = dict(status="PASS", not_a_measurement=True, no_simulator_or_wsl_invoked=True,
        checks=checks, verifier_sha256=audit.sha(Path(audit.__file__)), checker_sha256=audit.sha(Path(__file__)),
        fixture_case_count=184, fixture_label="SYNTHETIC_NOT_A_MEASUREMENT")
    write(destination / "verification.json", json.dumps(verification, indent=2) + "\n")
    print(f"[PASS] {len(checks)} independent sweep verifier controls; synthetic evidence only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
