"""Read-only evidence audit of the first 3400x3250 SA2 minimality screen."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
TAG = "sa2_corr3400x3250_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def first_path(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    end = next(i for i, line in enumerate(lines) if "slack (" in line)
    text = "\n".join(lines[:end+1])
    corner = re.search(r"=+\s+(\S+) Corner", text).group(1)
    start = re.search(r"Startpoint: (.*)", text).group(1)
    endpoint = re.search(r"Endpoint: (\S+)", text).group(1)
    arrival = float(re.search(r"([-\d.]+)\s+data arrival time", text).group(1))
    required = float(re.search(r"([-\d.]+)\s+data required time", text).group(1))
    slack = float(re.search(r"([-\d.]+)\s+slack \(", text).group(1))
    return {"corner": corner, "startpoint": start, "endpoint": endpoint,
            "data_arrival_ns": arrival, "data_required_ns": required, "slack_ns": slack,
            "report_first_path": text, "report_first_path_end_line": end+1}


def main():
    design = ROOT / "asic/soc_sa2_4kb"
    run = design / "runs" / TAG
    step = run / "45-openroad-stamidpnr-3"
    basepath = design / "config_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf.json"
    base = json.loads(basepath.read_text(encoding="utf-8"))
    diffs = {}
    inputs = [basepath]
    for height in (3100, 3250, 3325):
        path = design / f"config_corr3400x{height}_f220_capm20_fo16_pad1_tdp_clkm3_rsztf.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        changed = {key: {"signed_recipe": base.get(key), "candidate": value.get(key)} for key in set(base) | set(value)
                   if not key.startswith("//") and base.get(key) != value.get(key)}
        if set(changed) != {"DIE_AREA", "CORE_AREA", "MACRO_PLACEMENT_CFG"}:
            raise ValueError("Candidate changes more than geometry")
        diffs[str(height)] = changed
        inputs.extend((path, design / value["MACRO_PLACEMENT_CFG"].removeprefix("dir::")))
    metrics = json.loads((step / "or_metrics_out.json").read_text(encoding="utf-8"))
    fresh_corners = sorted({key.split("__corner:", 1)[1] for key in metrics if "__corner:" in key})
    if fresh_corners != ["nom_tt_025C_1v80"]:
        raise ValueError("Unexpected fresh STA corner scope")
    setup, hold = first_path(step / "max.rpt"), first_path(step / "min.rpt")
    if setup["slack_ns"] >= 0 or hold["slack_ns"] >= 0:
        raise ValueError("Screen no longer matches the captured failure")
    nl = run / "44-openroad-resizertimingpostgrt/soc_asic_top.nl.v"
    mapped = {}
    target_cells = {setup["endpoint"], hold["endpoint"], "_115980_"}
    pending = []
    start = 0
    with nl.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not pending:
                if not any(re.search(r"\s" + re.escape(cell) + r"\s*\(", line) for cell in target_cells):
                    continue
                start = number
            pending.append(line)
            if ";" in line:
                text = "".join(pending)
                cell = next(cell for cell in target_cells if re.search(r"\s" + re.escape(cell) + r"\s*\(", text))
                mapped[cell] = {"line": start, "statement": text.rstrip(),
                                "pins": {pin: net.strip().lstrip("\\") for pin, net in re.findall(r"\.(\w+)\(([^()]*)\)", text)}}
                pending = []
    if set(mapped) != target_cells:
        raise ValueError("Missing exact timing endpoint/source flop")
    inputs.extend(step / name for name in ("max.rpt", "min.rpt", "or_metrics_out.json", "runtime.txt", "state_in.json", "state_out.json", "_env.tcl", "skew.max.rpt", "skew.min.rpt"))
    inputs.extend((nl, run / "resolved.json", ROOT / "asic/soc_dm_4kb/soc.sdc"))
    record = {"status": "READ_ONLY_SINGLE_EXECUTION_P2_FAILURE_AUDIT", "run": TAG,
              "die_mm2": 11.05, "corner": "nom_tt_025C_1v80", "setup": setup, "hold": hold,
              "fresh_metrics": metrics, "fresh_corners": fresh_corners,
              "other_eight_signoff_corners": "NOT_EXECUTED_AT_THIS_STEP; inherited pre-PnR values are stale and not routed sign-off evidence",
              "setup_endpoint_mapping": mapped[setup["endpoint"]],
              "hold_endpoint_mapping": mapped[hold["endpoint"]], "hold_source_mapping": mapped["_115980_"],
              "geometry_only_config_differences": diffs,
              "config_3150": "No such current candidate file exists; 3100 exists and is audited explicitly",
              "diagnosis": [
                  "Worst setup is a half-cycle I-cache SRAM port1 output bit25 to the actual PC/request-address bit31 flop, not a generic clock-skew-only diagnosis.",
                  "Setup report arrival23.654978ns exceeds required23.323046ns by0.331932ns; ten setup endpoints violate nom_tt.",
                  "Worst hold starts at D-cache way0 bank0 hold_a_q[9] and ends at hot_line1[9], through mux2,o21ai,nor2,a211o; four hold endpoints violate nom_tt.",
                  "Small hold is intended to be repairable by extracted-RC ECO, but negative nom_tt setup blocks this screening gate. No threshold or clock relaxation.",
                  "Only one full-flow execution exists here and it stopped at P2. This is neither a signed result nor proof of minimum routable area."],
              "next_hypothesis": {
                  "statement": "Repeat the same3400x3250 geometry-only full flow fromstep1 with identical signed SA2 recipe to test reproducibility of this nom_tt setup failure; no knob change.",
                  "next_run": "sa2_corr3400x3250_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r2",
                  "acceptance": "Inspect actual fresh P1/P2 timing and paths. If the same recipe again fails setup, preserve both results; do not continue an unexplained failed gate.",
                  "conditional_next": "Then test3400x3325 using the prepared same-recipe geometry config as the next separate experiment, fullstep1 and max_*thenmin_*ECO procedure if all gates permit.",
                  "launched_by_this_audit": False},
              "input_sha256": {p.relative_to(ROOT).as_posix(): sha(p) for p in inputs},
              "audit_source_sha256": sha(Path(__file__))}
    folder = ROOT / "results/sa2_minimality_screen_20261010"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "first_execution_audit.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": record["status"], "setup_ns": setup["slack_ns"], "hold_ns": hold["slack_ns"],
                      "actual_corners": fresh_corners, "out": str(folder / "first_execution_audit.json")}))


if __name__ == "__main__":
    main()
