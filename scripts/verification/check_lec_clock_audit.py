#!/usr/bin/env python3
"""Synthetic positive/negative controls for the streaming clock audit."""
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/dm_lec_clock_audit_20261010/controls"
spec = importlib.util.spec_from_file_location("clock_audit", ROOT / "scripts/verification/lec_clock_audit.py")
clock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clock)

BASE = """module \\soc_asic_top
  wire input 1 \\clk
  wire input 2 \\d
  wire output 3 \\q
  cell $dff \\f
    parameter \\WIDTH 1
    parameter \\CLK_POLARITY 1
    connect \\CLK \\clk
    connect \\D \\d
    connect \\Q \\q
  end
end
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "verification.json"
    assert not out.exists(), "Preserve the previous controls receipt"
    cases = {
        "positive_dff": (BASE, "VERIFIED_CLOCK_EDGE_DOMAIN_AUDIT"),
        "positive_binary_parameter": (BASE.replace("POLARITY 1", "POLARITY 1'1"), "VERIFIED_CLOCK_EDGE_DOMAIN_AUDIT"),
        "positive_fine_dff": (BASE.replace("cell $dff", "cell $_DFF_P_").replace("connect \\CLK", "connect \\C"), "VERIFIED_CLOCK_EDGE_DOMAIN_AUDIT"),
        "negative_polarity": (BASE.replace("POLARITY 1", "POLARITY 0"), "FAIL"),
        "negative_fine_primitive": (BASE.replace("cell $dff", "cell $_DFF_N_"), "FAIL"),
        "missing_clock_connection": (BASE.replace("    connect \\CLK \\clk\n", ""), "FAIL"),
        "clock_disconnected": (BASE.replace("connect \\CLK \\clk", "connect \\CLK 1'0"), "MISSING_CLOCK_PROOF"),
        "clock_x": (BASE.replace("connect \\CLK \\clk", "connect \\CLK 1'x"), "MISSING_CLOCK_PROOF"),
        "other_clock_domain": (BASE.replace("connect \\CLK \\clk", "connect \\CLK \\another_clock"), "MISSING_CLOCK_PROOF"),
        "inverted_clock": (BASE.replace("connect \\CLK \\clk", "connect \\CLK \\inverted")
            .replace("\nend\n", "\n  cell $_NOT_ \\clock_inverter\n    connect \\A \\clk\n    connect \\Y \\inverted\n  end\nend\n", 1), "MISSING_CLOCK_PROOF"),
        "unproved_buffer_alias": (BASE.replace("connect \\CLK \\clk", "connect \\CLK \\clock_alias")
            .replace("\nend\n", "\n  connect \\clock_alias \\clk\nend\n", 1), "MISSING_CLOCK_PROOF"),
        "primary_clock_port_missing": (BASE.replace("  wire input 1 \\clk\n", ""), "FAIL"),
        "primary_clock_port_wrong_direction": (BASE.replace("wire input 1 \\clk", "wire output 1 \\clk"), "FAIL"),
        "primary_clock_bus": (BASE.replace("wire input 1 \\clk", "wire width 2 input 1 \\clk"), "FAIL"),
        "primary_clock_driven": (BASE.replace("\nend\n", "\n  connect \\clk \\d\nend\n", 1), "FAIL"),
        "internal_clock_driver": (BASE.replace("\nend\n", "\n  cell $_NOT_ \\bad_driver\n    connect \\A \\d\n    connect \\Y \\clk\n  end\nend\n", 1), "FAIL"),
        "missing_polarity": (BASE.replace("    parameter \\CLK_POLARITY 1\n", ""), "FAIL"),
        "duplicate_clock_port": (BASE.replace("    connect \\CLK \\clk\n", "    connect \\CLK \\clk\n    connect \\CLK \\d\n"), "FAIL"),
        "missing_flop_d": (BASE.replace("    connect \\D \\d\n", ""), "FAIL"),
        "missing_flop_q": (BASE.replace("    connect \\Q \\q\n", ""), "FAIL"),
        "unsupported_latch": (BASE.replace("cell $dff", "cell $dlatch"), "FAIL"),
        "empty_sequential_audit": ("module \\soc_asic_top\n  wire input 1 \\clk\nend\n", "FAIL"),
        "truncated_module": (BASE.rsplit("end", 1)[0], "FAIL"),
        "duplicate_module": (BASE + BASE, "FAIL"),
    }
    results = []
    for name, (text, expected) in cases.items():
        path = OUT / (name + ".il")
        assert not path.exists(), path
        path.write_text(text, encoding="utf-8")
        got = clock.audit(path)
        assert got["status"] == expected, (name, expected, got)
        result = {"case": name, "expected": expected, "status": "PASS", "audit": got}
        results.append(result)
    value = {"status": "VERIFIED_SYNTHETIC_CLOCK_CONTROLS", "tools_launched": 0,
        "wsl_started": False, "total": len(results), "passed": len(results),
        "sources": {"scripts/verification/lec_clock_audit.py": clock.digest(ROOT / "scripts/verification/lec_clock_audit.py"),
                    "scripts/verification/check_lec_clock_audit.py": clock.digest(Path(__file__))},
        "cases": results}
    out.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": value["status"], "passed": len(results), "total": len(results)}))


if __name__ == "__main__":
    main()
