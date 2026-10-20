#!/usr/bin/env python3
"""Extract cache-DSE Quartus Fitter/timing summaries without invented values."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


CONFIGS = {
    "DM": ("results/quartus/experiments/output_files_cache_dm", "soc_top_cache_dm"),
    "SA2": ("results/quartus/experiments/output_files_cache_sa2", "soc_top_cache_sa2"),
    "DM_VC4": ("results/quartus/experiments/output_files_cache_dm_vc4", "soc_top_cache_dm_vc4"),
}


def first_int(pattern: str, text: str) -> int:
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        raise ValueError(f"missing report field: {pattern}")
    return int(match.group(1).replace(",", ""))


def first_float(pattern: str, text: str) -> float:
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        raise ValueError(f"missing report field: {pattern}")
    return float(match.group(1))


def extract(root: Path, name: str, out_dir: str, revision: str) -> dict[str, object]:
    fit_path = root / out_dir / f"{revision}.fit.rpt"
    sta_path = root / out_dir / f"{revision}.sta.rpt"
    if not fit_path.is_file() or not sta_path.is_file():
        return {
            "configuration": name,
            "revision": revision,
            "device": "EP4CE115F29C7",
            "compile_status": "NOT_RUN",
            "logic_elements": "NOT_RUN",
            "registers": "NOT_RUN",
            "m9k": "NOT_RUN",
            "total_memory_bits": "NOT_RUN",
            "dsp_9bit_elements": "NOT_RUN",
            "fmax_mhz_slow_85c": "NOT_RUN",
            "wns_ns_slow_85c": "NOT_RUN",
            "constraint_mhz": 50.0,
            "timing_met": "NOT_RUN",
            "notes": "Quartus reports are absent",
        }

    fit = fit_path.read_text(encoding="utf-8", errors="replace")
    sta = sta_path.read_text(encoding="utf-8", errors="replace")
    fmax_panel = sta.rsplit("Slow 1200mV 85C Model Fmax Summary", 1)[1]
    fmax = first_float(r";\s*([0-9.]+) MHz\s*;", fmax_panel)
    wns = first_float(r"Worst-case setup slack is\s+(-?[0-9.]+)", sta)
    return {
        "configuration": name,
        "revision": revision,
        "device": "EP4CE115F29C7",
        "compile_status": "PASS",
        "logic_elements": first_int(r"^; Total logic elements\s+;\s*([0-9,]+)\s*/", fit),
        "registers": first_int(r"^; Total registers\s+;\s*([0-9,]+)", fit),
        "m9k": first_int(r"^; M9Ks\s+;\s*([0-9,]+)\s*/", fit),
        "total_memory_bits": first_int(r"^; Total memory bits\s+;\s*([0-9,]+)\s*/", fit),
        "dsp_9bit_elements": first_int(
            r"^; Embedded Multiplier 9-bit elements\s+;\s*([0-9,]+)\s*/", fit
        ),
        "fmax_mhz_slow_85c": fmax,
        "wns_ns_slow_85c": wns,
        "constraint_mhz": 50.0,
        "timing_met": "YES" if wns >= 0.0 else "NO",
        "notes": "Design uses the shared 50 MHz SoC timing constraints",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "results" / "quartus_cache_dse_summary.csv",
    )
    args = parser.parse_args()

    rows = [extract(args.root, name, *paths) for name, paths in CONFIGS.items()]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        print(
            f"{row['configuration']}: {row['compile_status']} "
            f"LE={row['logic_elements']} Fmax={row['fmax_mhz_slow_85c']} "
            f"WNS={row['wns_ns_slow_85c']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
