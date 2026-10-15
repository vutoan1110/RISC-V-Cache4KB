"""Validate CoreMark's numerical CRCs, separately from its snapshot completion.

The frozen firmware runs one iteration in a 32 KiB simulation. The duration
warning is expected and the run is never an official CoreMark score. Reference
CRCs are extracted from the unmodified suite, not learned from DUT output.
"""
from __future__ import annotations

import re
from pathlib import Path

DURATION_ERROR = "ERROR! Must execute for at least 10 secs for a valid result!"


def known_crcs(source: Path) -> dict[int, dict[str, int]]:
    text = source.read_text(encoding="utf-8")
    arrays = {}
    for algorithm in ("list", "matrix", "state"):
        match = re.search(r"\b" + algorithm + r"_known_crc\s*\[\s*\]\s*=\s*\{([^}]+)\}", text)
        if not match:
            raise ValueError(f"Missing suite {algorithm} reference array")
        arrays[algorithm] = [int(x, 16) for x in re.findall(r"0x([0-9a-fA-F]+)", match[1])]
    result = {}
    for seed, index in re.findall(r"case\s+(0x[0-9a-fA-F]+)\s*:\s*(?:/\*.*?\*/\s*)?known_id\s*=\s*(\d+)\s*;", text, re.S):
        key, i = int(seed, 16), int(index)
        if key in result or any(i >= len(values) for values in arrays.values()):
            raise ValueError("Ambiguous suite seed/CRC table")
        result[key] = {"crc" + name: values[i] for name, values in arrays.items()}
    if len(result) != 5:
        raise ValueError("Expected all five suite seed profiles")
    return result


def once(text: str, pattern: str, label: str) -> str:
    matches = re.findall(pattern, text, re.M)
    if len(matches) != 1:
        raise ValueError(f"Expected one complete {label}, found {len(matches)}")
    return matches[0]


def validate_uart(text: str, reference: dict[int, dict[str, int]]) -> dict[str, int | str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    seed = int(once(text, r"^seedcrc\s*:\s*0x([0-9a-fA-F]{4})\s*$", "seedcrc"), 16)
    if seed not in reference:
        raise ValueError(f"Unknown suite seedcrc 0x{seed:04x}; no numeric reference")
    # The canonical, frozen image is the 2K performance profile, one iteration.
    if seed != 0xe9f5:
        raise ValueError(f"Unexpected canonical firmware profile 0x{seed:04x}")
    size = int(once(text, r"^CoreMark Size\s*:\s*(\d+)\s*$", "CoreMark Size"))
    iterations = int(once(text, r"^Iterations\s*:\s*(\d+)\s*$", "Iterations"))
    seconds = int(once(text, r"^Total time \(secs\)\s*:\s*(\d+)\s*$", "duration"))
    if (size, iterations, seconds) != (666, 1, 0):
        raise ValueError(f"Unexpected short-simulation profile {(size, iterations, seconds)}")
    crcs = {}
    for field in ("crclist", "crcmatrix", "crcstate", "crcfinal"):
        pattern = r"^\[0\]" + field + r"\s*:\s*0x([0-9a-fA-F]{4})\s*$"
        crcs[field] = int(once(text, pattern, field), 16)
    if re.search(r"^\[[1-9][0-9]*\]crc", text, re.M):
        raise ValueError("Unexpected extra CoreMark context")
    for field, expected in reference[seed].items():
        if crcs[field] != expected:
            raise ValueError(f"{field}=0x{crcs[field]:04x}, expected 0x{expected:04x}")
    if crcs["crcfinal"] != crcs["crclist"]:
        raise ValueError("One-iteration crcfinal must equal crclist")
    errors = [line.strip() for line in text.splitlines() if "ERROR" in line.upper()]
    if errors != [DURATION_ERROR, "Errors detected"]:
        raise ValueError(f"Unexpected firmware errors: {errors}")
    if "Cannot validate operation" in text or "Correct operation validated" in text:
        raise ValueError("Unexpected validation conclusion for the short performance run")
    if "2K performance run parameters for coremark." not in text:
        raise ValueError("Missing suite parameter recognition")
    return {"seedcrc": seed, **crcs, "size_per_algorithm": size,
            "iterations": iterations, "duration_seconds": seconds,
            "crc_pass": 1, "official_score": 0,
            "validation": "suite_numeric_crc_short_simulation"}


def validate_case(log: Path, uart: Path, reference, expected_config: int, parse_snapshot, invariants):
    txt = log.read_text(encoding="utf-8", errors="replace")
    lines = re.findall(r"BENCHMARK_SNAPSHOT ([^\r\n]+)", txt)
    if len(lines) != 1:
        raise ValueError(f"Expected one snapshot, found {len(lines)}")
    words = [part.split("=", 1) for part in lines[0].split() if "=" in part]
    if len({key for key, _ in words}) != len(words):
        raise ValueError("Duplicate snapshot field")
    context = dict(words)
    if context.get("benchmark") != "coremark" or context.get("config") != str(expected_config):
        raise ValueError("Snapshot benchmark/configuration differs")
    snapshot, reason = parse_snapshot(log)
    if snapshot is None:
        raise ValueError(reason)
    bad = invariants(snapshot)
    if bad:
        raise ValueError("; ".join(bad))
    captures = re.findall(r"COREMARK_UART_CAPTURE bytes=(\d+) method=accepted_apb_txdata_writes", txt)
    if len(captures) != 1 or int(captures[0]) != len(uart.read_bytes()):
        raise ValueError("Missing or incomplete passive UART capture receipt")
    numeric = validate_uart(uart.read_text(encoding="ascii"), reference)
    return snapshot, numeric
