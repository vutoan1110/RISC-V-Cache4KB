"""The BENCHMARK_SNAPSHOT line printed by tb/benchmark_snapshot_tb.sv.

One definition shared by run_ablation.py (Embench), run_coremark.py and the
ASIC-view runs, so no runner records a subset of what the harness measured.
Until 2026-09-25 the runners kept 27 of the 29 numbers the line carried and the
harness printed 28 of the 37 counters the sysmon snapshot holds; the missing
ones (axi_write, the raw hit/miss events, the event counts, mcause) are here
now and a run that lacks any of them is a failed run, not a blank cell.
"""
from __future__ import annotations

import re
from pathlib import Path

# In the order the harness prints them. Every one is a sysmon snapshot register
# (apb_performance_monitor.v) except the three bookkeeping fields at the end.
FIELDS = (
    # cycle accounting: mcycle is the sum of the next ten (the harness checks)
    "mcycle", "minstret", "cycle_retire", "load_use", "i_wait", "d_wait",
    "control", "trap", "mmio", "fill_drain", "other",
    # I-cache: access = main + victim + true miss (checked by the harness)
    "i_access", "i_main", "i_victim", "i_miss",
    # D-cache: read + write = main + victim + true miss (checked)
    "d_read", "d_write", "d_main", "d_victim", "d_miss",
    # branch unit
    "branches", "taken", "not_taken", "predictions", "correct", "mispredict",
    # bus
    "axi_read", "axi_write",
    # raw hit / miss events and event counts
    "i_hit_ev", "i_miss_ev", "d_rd_hit", "d_rd_miss", "d_wr_hit", "d_wr_miss",
    "control_ev", "trap_ev", "mcause", "snap_seq",
    # set by the harness only when firmware and invariants passed
    "result_pass", "invariant_pass",
)

# Fields that count cycles, and so legitimately differ between the FPGA view
# and the ASIC view (the macro wrapper ignores the MISS_PENALTY hooks).
# Everything else is architectural or a cache/bus event and must match.
CYCLE_FIELDS = ("mcycle", "cycle_retire", "load_use", "i_wait", "d_wait",
                "control", "trap", "mmio", "fill_drain", "other")


def parse(log: Path) -> tuple[dict | None, str]:
    """Return (row, "") or (None, reason)."""
    txt = Path(log).read_bytes().decode("utf-8", "replace")
    if re.search(r"\*\* (Fatal|Error)", txt):
        return None, "simulator reported Fatal/Error"
    m = re.search(r"BENCHMARK_SNAPSHOT (.*)", txt)
    if not m:
        return None, "no BENCHMARK_SNAPSHOT line"
    if "[PASS] Atomic benchmark snapshot" not in txt:
        return None, "no [PASS] line"
    pairs = dict(kv.split("=", 1) for kv in m.group(1).split() if "=" in kv)
    missing = [f for f in FIELDS if f not in pairs]
    if missing:
        return None, "snapshot lacks %s" % ", ".join(missing)
    row = {f: int(pairs[f]) for f in FIELDS}
    if row["result_pass"] != 1 or row["invariant_pass"] != 1:
        return None, "result_pass/invariant_pass not 1"
    return row, ""


def invariants(row: dict) -> list[str]:
    """Identities the counters must satisfy; returns the ones that fail.

    The harness already checks the cycle sum and the two cache access sums.
    These add the raw hit/miss events and the branch unit, which nothing
    checked before.
    """
    bad = []
    def eq(name, a, b):
        if a != b:
            bad.append("%s: %d != %d" % (name, a, b))
    r = row
    eq("mcycle = sum of cycle classes", r["mcycle"],
       sum(r[k] for k in CYCLE_FIELDS[1:]))
    eq("i_access = i_main + i_victim + i_miss", r["i_access"],
       r["i_main"] + r["i_victim"] + r["i_miss"])
    eq("d_read + d_write = d_main + d_victim + d_miss", r["d_read"] + r["d_write"],
       r["d_main"] + r["d_victim"] + r["d_miss"])
    eq("i_access = i_hit_ev + i_miss_ev", r["i_access"],
       r["i_hit_ev"] + r["i_miss_ev"])
    eq("d_read = d_rd_hit + d_rd_miss", r["d_read"], r["d_rd_hit"] + r["d_rd_miss"])
    eq("d_write = d_wr_hit + d_wr_miss", r["d_write"], r["d_wr_hit"] + r["d_wr_miss"])
    eq("branches = taken + not_taken", r["branches"], r["taken"] + r["not_taken"])
    eq("predictions = correct + mispredict", r["predictions"],
       r["correct"] + r["mispredict"])
    return bad
