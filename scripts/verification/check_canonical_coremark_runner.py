"""Exercise the maintained CoreMark runner with a synthetic simulator boundary.

No RTL simulations or source changes are performed. Snapshot counters are a
retained valid frame, while UART CRCs are generated from suite source tables.
"""
from __future__ import annotations

from contextlib import redirect_stdout
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/coremark_canonical_runner_controls_20261009"
spec = importlib.util.spec_from_file_location("canonical_coremark", ROOT / "scripts/run_coremark.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=True)
    fixture = Path(tempfile.mkdtemp(prefix="controls_", dir=OUT))
    with (ROOT / "results/coremark_rfbht_4kb_p1_c0.csv").open(newline="") as f:
        snapshot = {key: int(value) for key, value in next(csv.DictReader(f)).items()
                    if key in runner.FIELDS}
    assert not runner.invariants(snapshot)
    reference = runner.known_crcs(ROOT / "sw/coremark/core_main.c")[0xe9f5]
    uart_good = ("2K performance run parameters for coremark.\nCoreMark Size : 666\n"
                 "Total time (secs): 0\n"
                 "ERROR! Must execute for at least 10 secs for a valid result!\n"
                 "Iterations : 1\nseedcrc : 0xe9f5\n" +
                 "".join(f"[0]{key} : 0x{value:04x}\n" for key, value in reference.items()) +
                 f"[0]crcfinal : 0x{reference['crclist']:04x}\nErrors detected\n")
    checks = []
    scenarios = ["good", "all_params", "wrong_crc", "missing_crc", "missing_uart",
                 "wrong_capture_length", "fatal", "nonzero_sim", "missing_snapshot",
                 "duplicate_snapshot", "wrong_config", "broken_invariant",
                 "missing_compile_pass", "fatal_compile", "nonzero_compile"]
    original_run = runner.subprocess.run
    for mode in scenarios:
        target = fixture / (mode + ".csv")
        seen = []
        options = ["--out", str(target), "--lines", "256", "--configs", "0"]
        if mode == "all_params":
            options = ["--out", str(target), "--lines", "128", "--l0", "16",
                       "--imem", "8192", "--dmem", "8192", "--configs", "2",
                       "--max-cycles", "54321", "--lib", "chosen_fixture_lib", "--fast"]

        def fake_vsim(command, cwd, stdout, stderr):
            assert command[0] == runner.VSIM and command[1:3] == ["-c", "-do"]
            script = command[3]
            seen.append(script)
            if "vlog -work" in script:
                text = "# [PASS] Passive CoreMark UART observer compiled\n# Errors: 0, Warnings: 0\n"
                if mode == "missing_compile_pass": text = "# Errors: 0, Warnings: 0\n"
                if mode == "fatal_compile": text += "# ** Fatal: synthetic compiler failure\n"
                stdout.write(text.encode("ascii"))
                return subprocess.CompletedProcess(command, 3 if mode == "nonzero_compile" else 0)
            cfg = int(re.search(r"-gCACHE_CONFIG=(\d+)", script).group(1))
            path = Path(re.search(r"\{\+coremark_uart=([^}]+)\}", script).group(1))
            text = uart_good
            if mode == "wrong_crc": text = text.replace("0xe714", "0xe715")
            if mode == "missing_crc": text = "\n".join(line for line in text.splitlines()
                                                      if not line.startswith("[0]crcstate")) + "\n"
            if mode != "missing_uart": path.write_text(text, encoding="ascii", newline="\n")
            measured = dict(snapshot)
            if mode == "broken_invariant": measured["d_read"] += 1
            one = ("# BENCHMARK_SNAPSHOT benchmark=coremark config=%d " % (cfg+1 if mode == "wrong_config" else cfg) +
                   " ".join(f"{key}={value}" for key, value in measured.items()) + "\n")
            log = one + "# [PASS] Atomic benchmark snapshot\n"
            if mode == "missing_snapshot": log = "# [PASS] Atomic benchmark snapshot\n"
            if mode == "duplicate_snapshot": log += one
            n = len(text.encode("ascii")) + int(mode == "wrong_capture_length")
            log += f"# COREMARK_UART_CAPTURE bytes={n} method=accepted_apb_txdata_writes\n"
            if mode == "fatal": log += "# ** Fatal: synthetic simulation failure\n"
            stdout.write(log.encode("ascii"))
            return subprocess.CompletedProcess(command, 4 if mode == "nonzero_sim" else 0)

        runner.subprocess.run = fake_vsim
        buf = io.StringIO()
        try:
            with redirect_stdout(buf): rc = runner.main(options)
        finally:
            runner.subprocess.run = original_run
        (fixture / (mode + ".log")).write_text(buf.getvalue(), encoding="ascii")
        positive = mode in ("good", "all_params")
        ok = (rc == 0) == positive and target.exists() == positive
        if positive:
            with target.open(newline="") as f:
                reader = csv.DictReader(f); data = list(reader)
                ok = ok and reader.fieldnames == ["kernel", "config", "config_id"] + list(runner.FIELDS)
                ok = ok and len(reader.fieldnames) == 43 and len(data) == 1
                ok = ok and all(int(data[0][field]) == snapshot[field] for field in runner.FIELDS)
        else:
            ok = ok and "[PASS]" not in buf.getvalue()
        if mode == "all_params":
            required = ["-gCACHE_CONFIG=2", "-gCACHE_FAST_HIT=1", "-gICACHE_LINE_COUNT=128",
                        "-gDCACHE_LINE_COUNT=128", "-gL0_ENTRIES=16", "-gIMEM_DEPTH=8192",
                        "-gDMEM_DEPTH=8192", "chosen_fixture_lib.tb_coremark_crc_audit",
                        "+benchmark=coremark", "+max_cycles=54321"]
            ok = ok and all(item in seen[-1] for item in required) and "vlog -work chosen_fixture_lib" in seen[0]
        checks.append({"name": mode, "pass": bool(ok), "runner_returncode": rc,
                       "csv_created": target.exists(), "commands": seen})
        print(f"[{'PASS' if ok else 'FAIL'}] {mode}")
    report = {"status": "PASS" if all(c["pass"] for c in checks) else "FAIL",
              "controls": len(checks), "passed": sum(c["pass"] for c in checks),
              "method": "synthetic simulator boundary; no new RTL measurements",
              "fixture": str(fixture.relative_to(ROOT)), "checks": checks,
              "input_sha256": {p: sha(ROOT / p) for p in
                ("scripts/run_coremark.py", "scripts/verification/coremark_uart_observer.sv",
                 "scripts/verification/coremark_crc_gate.py", "sw/coremark/core_main.c",
                 "results/coremark_rfbht_4kb_p1_c0.csv")}}
    (fixture / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    (OUT / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="ascii")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
