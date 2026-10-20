"""Verify two independent OpenSTA power passes and the vectorless reproduction.

Compare every reported power group and activity-origin count, not rounded CSV
totals. Generate a _p1/_p2 CSV pair only after all twelve kernels agree.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORNER = "nom_tt_025C_1v80"
GROUPS = {"Sequential", "Combinational", "Clock", "Macro", "Pad", "Total"}


def parse(path, activity=True):
    text = path.read_text(encoding="utf-8", errors="replace")
    groups = {}
    for m in re.finditer(r"^(Sequential|Combinational|Clock|Macro|Pad|Total)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", text, re.M):
        if m[1] in groups:
            raise RuntimeError(f"Repeated power group: {path}: {m[1]}")
        groups[m[1]] = tuple(Decimal(m[i]) for i in range(2, 6))
    if set(groups) != GROUPS or any(not v.is_finite() or v < 0 for values in groups.values() for v in values):
        raise RuntimeError(f"Missing or invalid power fields: {path}")
    origins = {m[1]: (int(m[2]), m[3] or "") for m in re.finditer(
        r"^PW_ORIGIN\s+(\S+)\s+(\d+)(?:\s+([\d.]+) %)?\s*$", text, re.M)}
    if activity:
        if not {"clock", "constant", "saif", "unknown", "total_output_pins"}.issubset(origins):
            raise RuntimeError(f"Missing activity-origin fields: {path}")
        info = re.search(r"^PW_INFO sta=(\S+) corner=(\S+) spef=(\S+)", text, re.M)
        if not info or info[2] != CORNER:
            raise RuntimeError(f"Wrong or missing power corner: {path}")
    return groups, origins


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--design", required=True)
    ap.add_argument("--step", required=True)
    ap.add_argument("--ref-csv", required=True)
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    folder = ROOT / f"results/gls_power_{args.tag}"
    with (ROOT / f"results/gls_power_{args.tag}.csv").open(newline="") as f:
        gls_rows = list(csv.DictReader(f))
    with (ROOT / args.ref_csv).open(newline="") as f:
        ref_rows = [r for r in csv.DictReader(f) if r["config"] == args.config]
    gls = {r["kernel"]: r for r in gls_rows}
    ref = {r["kernel"]: r for r in ref_rows}
    if len(gls) != 12 or len(gls_rows) != 12 or len(ref_rows) != 12 or ref.keys() != gls.keys():
        raise RuntimeError("Require exactly twelve unique, matching GLS/reference kernels")
    original = ROOT / f"asic/{args.design}/runs/{args.tag}/{args.step}/{CORNER}/power.rpt"
    flow, _ = parse(original, activity=False)
    for suffix in ("", ".p2"):
        vectorless, _ = parse(folder / f"vectorless.power{suffix}.rpt", activity=False)
        if vectorless != flow:
            raise RuntimeError(f"Vectorless pass {suffix or '1'} does not reproduce all six flow power groups")
    rows = []
    for kernel in sorted(gls):
        g, r = gls[kernel], ref[kernel]
        if g["status"] != "PASS" or g["match"] != "YES" or g["saif"] != "YES":
            raise RuntimeError(f"GLS gate failed: {kernel}")
        if not (g["gls_mcycle"] == g["rtl_mcycle"] == g["win_cycles"] == r["mcycle"]):
            raise RuntimeError(f"Cycle/window mismatch: {kernel}")
        first = parse(folder / f"{kernel}.power.rpt")
        second = parse(folder / f"{kernel}.power.p2.rpt")
        if first != second:
            raise RuntimeError(f"Independent power passes differ: {kernel}")
        groups, origins = first
        internal, switching, leakage, total = groups["Total"]
        mc, mi = int(r["mcycle"]), int(r["minstret"])
        rows.append({"kernel": kernel, "total_mw": f"{total * 1000:.2f}",
            "dynamic_mw": f"{(internal + switching) * 1000:.2f}", "leakage_mw": f"{leakage * 1000:.3f}",
            "seq_mw": f"{groups['Sequential'][3] * 1000:.2f}",
            "comb_mw": f"{groups['Combinational'][3] * 1000:.2f}",
            "clock_mw": f"{groups['Clock'][3] * 1000:.2f}", "macro_mw": f"{groups['Macro'][3] * 1000:.2f}",
            "window_cycles": mc, "minstret": mi, "cpi": f"{mc / mi:.4f}",
            "epi_pj": f"{total * Decimal(mc) * Decimal('20000') / Decimal(mi):.0f}",
            "unknown_pct": origins["unknown"][1]})
    for pass_no in (1, 2):
        dst = ROOT / f"results/gls_power_{args.tag}_power_p{pass_no}.csv"
        with dst.open("w", newline="", encoding="ascii") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    summary = {"status": "VERIFIED_TWO_INDEPENDENT_STA_PASSES", "corner": CORNER,
        "method": "GLS SAIF -> driver-pin SAIF -> OpenSTA with signoff RCX SPEF",
        "kernels": 12, "vectorless_reproduces_flow": True,
        "compared": "all six power groups (internal, switching, leakage, total) and all activity-origin counts/shares",
        "minimum_total_mw": min(float(r['total_mw']) for r in rows),
        "maximum_total_mw": max(float(r['total_mw']) for r in rows),
        "mean_total_mw": sum(float(r['total_mw']) for r in rows) / len(rows),
        "gm_epi_pj": math.exp(sum(math.log(float(r['epi_pj'])) for r in rows) / len(rows)),
        "unknown_pct": sorted({r['unknown_pct'] for r in rows})}
    dst = ROOT / f"results/gls_power_{args.tag}_power_verification.json"
    dst.write_text(json.dumps(summary, indent=2) + "\n", encoding="ascii")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
