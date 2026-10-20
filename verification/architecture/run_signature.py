#!/usr/bin/env python3
"""Run one flat word-hex ACT4/RISCOF-style image and export its signature."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VSIM = Path(r"D:\altera\modelsim\modelsim_ase\win32aloem\vsim.exe")
FAIL_RE = re.compile(
    r"^\s*#?\s*(?:\*\*\s+(?:fatal|error):|\[FAIL\])|"
    r"^\s*#?\s*Errors:\s*[1-9]",
    re.IGNORECASE | re.MULTILINE,
)


def run_checked(command: list[str], *, cwd: Path, env: dict[str, str] | None,
                required_pass: re.Pattern[str]) -> str:
    completed = subprocess.run(
        command, cwd=cwd, env=env, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    transcript = completed.stdout or ""
    print(transcript, end="")
    if completed.returncode != 0:
        raise SystemExit(f"command failed with exit code {completed.returncode}")
    if FAIL_RE.search(transcript):
        raise SystemExit("ModelSim transcript contains a fatal/error/fail marker")
    if required_pass.search(transcript) is None:
        raise SystemExit("required PASS marker is absent from ModelSim transcript")
    return transcript


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hex", type=Path, required=True)
    parser.add_argument("--signature", type=Path, required=True)
    parser.add_argument("--sig-begin", type=lambda value: int(value, 0), required=True)
    parser.add_argument("--sig-end", type=lambda value: int(value, 0), required=True)
    parser.add_argument("--halt-pc", type=lambda value: int(value, 0))
    parser.add_argument("--tohost-addr", type=lambda value: int(value, 0),
                        default=0x81FF0)
    parser.add_argument("--max-cycles", type=int, default=2000000)
    parser.add_argument("--no-compile", action="store_true")
    parser.add_argument("--vsim", type=Path, default=DEFAULT_VSIM)
    args = parser.parse_args()

    hex_path = args.hex.resolve()
    signature_path = args.signature.resolve()
    signature_path.parent.mkdir(parents=True, exist_ok=True)
    if not args.vsim.exists():
        raise SystemExit(f"Questa executable not found: {args.vsim}")
    if not hex_path.exists():
        raise SystemExit(f"word-hex image not found: {hex_path}")
    if args.sig_end <= args.sig_begin or (args.sig_begin | args.sig_end) & 3:
        raise SystemExit("signature addresses must be aligned and end > begin")

    if not args.no_compile:
        run_checked(
            [str(args.vsim), "-c", "-do", "do tb/compile_active_design.do; quit -f"],
            cwd=ROOT, env=None,
            required_pass=re.compile(r"(?im)^\s*#?\s*\[PASS\]\s+Active RTL"),
        )

    env = os.environ.copy()
    env.update({
        "VERIFY_HEX": hex_path.as_posix(),
        "VERIFY_SIGNATURE": signature_path.as_posix(),
        "VERIFY_SIG_BEGIN": f"{args.sig_begin:08x}",
        "VERIFY_SIG_END": f"{args.sig_end:08x}",
        "VERIFY_TOHOST_ADDR": f"{args.tohost_addr:08x}",
        "VERIFY_MAX_CYCLES": str(args.max_cycles),
    })
    if args.halt_pc is not None:
        env["VERIFY_HALT_PC"] = f"{args.halt_pc:08x}"
    run_checked(
        [str(args.vsim), "-c", "-do",
         "do tb/run_architecture_signature.do; quit -f"],
        cwd=ROOT, env=env,
        required_pass=re.compile(r"(?im)^\s*#?\s*\[PASS\]\s+Signature harness"),
    )
    print(f"[PASS] signature written to {signature_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
