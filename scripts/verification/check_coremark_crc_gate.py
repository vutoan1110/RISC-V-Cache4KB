"""Positive fixture and strict negative controls for the supplemental CRC gate.

Fixtures exercise the result parser only. They are never measured RTL results.
"""
from __future__ import annotations

import csv
import hashlib
import json
import tempfile
from pathlib import Path

from coremark_crc_gate import known_crcs, validate_case, validate_uart
from run_coremark_crc import ROOT, FIELDS, invariants, parse_snapshot, validate_compile_script

HERE = Path(__file__).resolve().parent
PREPARATION = ROOT / "results/completion_preparation_20261009"
GOOD = """2K performance run parameters for coremark.
CoreMark Size    : 666
Total time (secs): 0
ERROR! Must execute for at least 10 secs for a valid result!
Iterations       : 1
seedcrc          : 0xe9f5
[0]crclist       : 0xe714
[0]crcmatrix     : 0x1fd7
[0]crcstate      : 0x8e3a
[0]crcfinal      : 0xe714
Errors detected
"""


def main():
    source = ROOT / "sw/coremark/core_main.c"
    reference = known_crcs(source)
    assert validate_uart(GOOD, reference)["crc_pass"] == 1
    controls = {
        "wrong_list_crc": GOOD.replace("crclist       : 0xe714", "crclist       : 0xe715"),
        "wrong_matrix_crc": GOOD.replace("0x1fd7", "0x1fd6"),
        "wrong_state_crc": GOOD.replace("0x8e3a", "0x8e3b"),
        "wrong_final_crc": GOOD.replace("crcfinal      : 0xe714", "crcfinal      : 0xe715"),
        "missing_crc": GOOD.replace("[0]crcstate      : 0x8e3a\n", ""),
        "truncated_crc": GOOD.replace("[0]crcstate      : 0x8e3a", "[0]crcstate      : 0x8e3"),
        "duplicate_crc": GOOD + "[0]crclist       : 0xe714\n",
        "unknown_seed": GOOD.replace("0xe9f5", "0xffff"),
        "different_known_profile": GOOD.replace("0xe9f5", "0x4eaf"),
        "extra_firmware_error": GOOD + "ERROR! list failed\n",
        "unexpected_context": GOOD + "[1]crclist       : 0xe714\n",
        "missing_duration_warning": GOOD.replace("ERROR! Must execute for at least 10 secs for a valid result!\n", ""),
        "missing_error_conclusion": GOOD.replace("Errors detected\n", ""),
        "misleading_success": GOOD + "Correct operation validated.\n",
        "different_iteration": GOOD.replace("Iterations       : 1", "Iterations       : 2"),
        "different_data_size": GOOD.replace("Size    : 666", "Size    : 400"),
    }
    results = []
    libdir = PREPARATION / "fixture_private_library"
    private_compile = (f"# default work is untouched; vlog -work is a tool option\n"
                       f"vlib {{{libdir.as_posix()}}}\n"
                       "vlog -work private_fixture -sv hdl/alu.v\n"
                       "vlog -work private_fixture -sv fixture.sv\n")
    validate_compile_script(private_compile, "private_fixture", libdir)
    for name, text in {
        "compile_default_work_target": private_compile.replace("-work private_fixture", "-work work", 1),
        "compile_unqualified_vlog": private_compile.replace("vlog -work private_fixture", "vlog", 1),
        "compile_default_vlib": private_compile.replace(f"vlib {{{libdir.as_posix()}}}", "vlib work"),
        "compile_forbidden_delete": private_compile + "vdel -lib work -all\n",
        "compile_forbidden_mapping": private_compile + "vmap work work\n",
    }.items():
        try:
            validate_compile_script(text, "private_fixture", libdir)
        except RuntimeError as exc:
            results.append({"name": name, "caught": True, "reason": str(exc)})
        else:
            raise AssertionError("Compile negative control accepted: " + name)
    for name, text in controls.items():
        try:
            validate_uart(text, reference)
        except ValueError as exc:
            results.append({"name": name, "caught": True, "reason": str(exc)})
        else:
            raise AssertionError("Negative control accepted: " + name)
    with (ROOT / "results/coremark_rfbht_4kb_p1.csv").open(newline="", encoding="utf-8") as f:
        row = next(csv.DictReader(f))
    frame = "BENCHMARK_SNAPSHOT benchmark=coremark config=0 " + " ".join(f"{field}={row[field]}" for field in FIELDS)
    capture = f"COREMARK_UART_CAPTURE bytes={len(GOOD.encode('ascii'))} method=accepted_apb_txdata_writes"
    goodlog = frame + "\n[PASS] Atomic benchmark snapshot\n" + capture + "\n"
    PREPARATION.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=PREPARATION, prefix="gate_fixtures_") as temp:
        log, uart = Path(temp) / "sim.log", Path(temp) / "uart.txt"
        uart.write_bytes(GOOD.encode("ascii"))
        log.write_text(goodlog, encoding="ascii")
        snapshot, numeric = validate_case(log, uart, reference, 0, parse_snapshot, invariants)
        assert snapshot["mcycle"] == int(row["mcycle"]) and numeric["crc_pass"] == 1
        for name, text in {
            "missing_snapshot": goodlog.replace(frame, ""),
            "duplicate_snapshot": goodlog + frame + "\n",
            "wrong_configuration": goodlog.replace("config=0", "config=1"),
            "wrong_benchmark": goodlog.replace("benchmark=coremark", "benchmark=other"),
            "missing_snapshot_pass": goodlog.replace("[PASS] Atomic benchmark snapshot", ""),
            "simulator_fatal": goodlog + "** Fatal: fixture\n",
            "wrong_capture_bytes": goodlog.replace(f"bytes={len(GOOD.encode('ascii'))}", "bytes=1"),
            "missing_capture_receipt": goodlog.replace(capture, ""),
            "missing_counter": goodlog.replace("minstret=" + row["minstret"], ""),
            "broken_counter_invariant": goodlog.replace("mcycle=" + row["mcycle"], "mcycle=1"),
            "duplicate_counter": goodlog.replace(frame, frame + " mcycle=1"),
        }.items():
            log.write_text(text, encoding="ascii")
            try:
                validate_case(log, uart, reference, 0, parse_snapshot, invariants)
            except ValueError as exc:
                results.append({"name": name, "caught": True, "reason": str(exc)})
            else:
                raise AssertionError("Negative control accepted: " + name)
    receipt = {"status": "PARSER_FIXTURES_VERIFIED_ONLY_NOT_RTL_MEASUREMENT",
               "positive_fixtures": 3, "negative_controls": results,
               "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
               "gate_sha256": hashlib.sha256((HERE / "coremark_crc_gate.py").read_bytes()).hexdigest()}
    (PREPARATION / "coremark_crc_gate_checks.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="ascii")
    print(f"[PASS] 3 positive fixtures and {len(results)} negative controls; no RTL simulation performed")


if __name__ == "__main__":
    main()
