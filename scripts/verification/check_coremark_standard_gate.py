"""Synthetic rejection controls only; this never produces a benchmark score."""
import csv
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from run_coremark_standard import validate_case, known_crcs, sha
from snapshot_fields import FIELDS

def main():
    out = ROOT / "results/coremark_standard_gate_checked_20261011"
    out.mkdir(exist_ok=False)
    buildpath = ROOT / "results/coremark_standard_integer_os_20261011/build.json"
    build = json.loads(buildpath.read_text())
    with (ROOT / "results/coremark_rfbht_4kb_p1.csv").open() as f:
        row = next(r for r in csv.DictReader(f) if r["config_id"] == "0")
    snapshot = "BENCHMARK_SNAPSHOT benchmark=coremark config=0 " + " ".join(k + "=" + row[k] for k in FIELDS)
    crcs = known_crcs(ROOT / "sw/coremark/core_main.c")[0xe9f5]
    serial = ("COREMARK_STANDARD_BEGIN\n2K performance run parameters for coremark.\n"
              "CoreMark Size    : 666\nTotal ticks      : 500000000\nTotal time (secs): 10\n"
              "Iterations/Sec   : 200\nIterations       : 2000\n"
              "Compiler version : GCC" + build["compiler_macro_version"] + "\nCompiler flags   : " +
              " ".join(build["compiler_flags"]) + "\nMemory location  : STATIC\nseedcrc          : 0xe9f5\n" +
              "".join("[0]" + k + " : 0x%04x\n" % v for k, v in crcs.items()) +
              "[0]crcfinal : 0x1234\nCorrect operation validated. See README.md for run and reporting rules.\n"
              "COREMARK_TIMER clock_hz=50000000 bits=32 samples=1 error=0 open=0\n"
              "COREMARK_INTERVAL index=0 start=0x00000064 stop=0x1dcd6564 ticks=500000000\n"
              "BENCH=coremark\nRESULT=PASS\n")
    def logfile(uart):
        return ("COREMARK_STANDARD_PROFILE cfg=0 fast=0 i_lines=256 d_lines=256 line_words=4 l0=8 predictor=1 imem=4096 dmem=4096\n" +
                snapshot + "\n[PASS] Atomic benchmark snapshot\n" +
                "COREMARK_STANDARD_FINISH cycles=600000000 uart_bytes=%d\n" % len(uart.encode("ascii")))
    cases = [("valid_synthetic_not_measurement", serial, logfile(serial), False),
             ("short_iteration", serial.replace("500000000", "499999999"), None, True),
             ("wrong_crc", serial.replace("0xe714", "0xe715"), None, True),
             ("wrong_ram", serial, logfile(serial).replace("imem=4096", "imem=2048"), True),
             ("wrong_configuration", serial, logfile(serial).replace("PROFILE cfg=0", "PROFILE cfg=1"), True),
             ("missing_upstream_validation", serial.replace("Correct operation validated.", "Not validated."), None, True),
             ("bad_timer_subtraction", serial.replace("stop=0x1dcd6564", "stop=0x1dcd6565"), None, True),
             ("forged_integer_seconds", serial.replace("(secs): 10", "(secs): 11"), None, True),
             ("native_fatal", serial, logfile(serial) + "** Fatal: wrong result\n", True),
             ("incomplete_uart_bytes", serial, logfile(serial).replace("uart_bytes=", "uart_bytes=1"), True),
             ("wrap_ambiguity_timeout", serial, logfile(serial).replace("cycles=600000000", "cycles=2147483648"), True)]
    outcomes = []
    for name, uart_text, log_text, reject in cases:
        uart = out / (name + ".uart.txt"); log = out / (name + ".log")
        uart.write_bytes(uart_text.encode("ascii")); log.write_text(log_text or logfile(uart_text), encoding="ascii")
        error = None
        try: validate_case(log, uart, "performance", 0, build, 2000000000)
        except (ValueError, KeyError) as exc: error = str(exc)
        if bool(error) != reject: raise RuntimeError("Rejection control failed: " + name + " " + str(error))
        outcomes.append({"case": name, "expected_rejection": reject, "actual_rejection": bool(error), "reason": error})
    result = {"status": "PASS_SYNTHETIC_CONTROLS_NOT_MEASUREMENTS", "simulator_executions": 0,
              "controls": outcomes, "runner_sha256": sha(ROOT / "scripts/verification/run_coremark_standard.py"),
              "build_sha256": sha(buildpath)}
    (out / "receipt.json").write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(out / "receipt.json")

if __name__ == "__main__": main()
