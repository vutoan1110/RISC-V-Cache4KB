"""Prepare one VC4 cell-spacing hypothesis from the stopped 12.24 mm2 run.

No flow is launched. The two padding fields implement one site on each side
throughout placement. Every other implementation input retains the old recipe.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESIGN = ROOT / "asic/soc_vc4_4kb"
OLD = "corr3600x3400_f220_capm20_antoff_nogrtt_nogrtd"
NEW = "corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    folder = ROOT / "results/vc4_padding_preparation_20261009"
    receipt = folder / "inputs.json"
    sources = [DESIGN / f"config_{OLD}{s}.json" for s in ("", "_ecomin")]
    outputs = [DESIGN / f"config_{NEW}{s}.json" for s in ("", "_ecomin")]
    if receipt.exists() or any(p.exists() for p in outputs):
        raise RuntimeError("Preparation already exists; inspect instead of overwriting")
    diagnostics = ROOT / "results/vc4_corr3600x3400_drt_diagnosis_20261009.json"
    d = json.loads(diagnostics.read_text())
    if (d["watchdog_iteration"], d["parsed_report_markers"]) != (10, 5689):
        raise RuntimeError("Stopped-run diagnostic changed; review the hypothesis")
    scripts = ROOT / "asic/openlane-local/openlane/scripts/openroad"
    gpl = scripts / "gpl.tcl"
    dpl = scripts / "common/dpl_cell_pad.tcl"
    if '$::env(GPL_CELL_PADDING) / 2' not in gpl.read_text() or '$cell_pad_value / 2' not in dpl.read_text():
        raise RuntimeError("Padding-unit interpretation changed")
    records, prepared = [], []
    for source, output in zip(sources, outputs):
        old = json.loads(source.read_text())
        new = dict(old, GPL_CELL_PADDING=2, DPL_CELL_PADDING=2)
        new["//EXPERIMENT"] = (
            "UNEXECUTED single hypothesis: one placement site per side reduces the concentrated "
            "met1/met2 pin-access shorts and spacing errors in the stopped 12.24 mm2 run. "
            "Only GPL_CELL_PADDING and DPL_CELL_PADDING change; both are 2 total sites. "
            "Die, macros, default resizer corners and clock layers remain those of " + source.name + ". "
            "A fresh full flow is required; the clock routing may change, so diagnose GRT/p2 before DRT."
        )
        changes = sorted(k for k in old.keys() | new.keys() if not k.startswith("//") and old.get(k) != new.get(k))
        if changes != ["DPL_CELL_PADDING", "GPL_CELL_PADDING"]:
            raise RuntimeError(f"Unexpected changes: {changes}")
        if old["GPL_CELL_PADDING"] != 0 or old["DPL_CELL_PADDING"] != 0:
            raise RuntimeError("Expected unpadded baseline")
        if old["CLOCK_PERIOD"] != 20 or old["DIE_AREA"] != [0, 0, 3600, 3400]:
            raise RuntimeError("Baseline clock or die differs")
        if old["RUN_POST_GRT_DESIGN_REPAIR"] is not False or "RSZ_CORNERS" in old:
            raise RuntimeError("Keep disabled post-GRT repair and default resizer corners")
        if source.name.endswith("_ecomin.json") and new["POST_ROUTE_HOLD_ECO_RCX_CORNER"] != "min_*":
            raise RuntimeError("Second hold ECO must retain min_* extraction")
        records.append({"source": source.relative_to(ROOT).as_posix(), "source_sha256": sha(source),
            "config": output.relative_to(ROOT).as_posix(), "changes": {k: {"old": old[k], "new": new[k]} for k in changes}})
        prepared.append(new)
    if args.write:
        folder.mkdir(parents=True, exist_ok=False)
        for output, config, record in zip(outputs, prepared, records):
            output.write_text(json.dumps(config, indent=4) + "\n", encoding="ascii")
            record["config_sha256"] = sha(output)
        inputs = {p.relative_to(ROOT).as_posix(): sha(p) for p in (diagnostics, gpl, dpl)}
        receipt.write_text(json.dumps({"status": "PREPARED_NOT_EXECUTED", "not_a_measurement": True,
            "hypothesis": "one site per cell side at unchanged 12.24 mm2 die",
            "padding_sites_each_side": 1, "configs": records, "evidence": inputs,
            "launch_prerequisites": "owner WSL terminal open; memory scheduling; fresh run from step 1"}, indent=2) + "\n",
            encoding="ascii")
    print(f"[{'PREPARED' if args.write else 'PLAN'}] one hypothesis, two padding fields, unchanged die/RTL/clock/SDC/other recipe; no PD launched")


if __name__ == "__main__":
    main()
