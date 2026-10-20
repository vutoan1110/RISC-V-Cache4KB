#!/usr/bin/env python3
"""Every number an OpenLane 2 run produced, in one place.

    python scripts/pd_metrics.py asic/soc_dm_4kb/runs/<tag> --out results/pd/<tag>

Writes
  metrics_final.csv    every key of final/metrics.json (nothing filtered)
  metrics_stages.csv   post-synthesis, pre-PNR STA and post-PNR STA metrics
                       side by side, from those steps' state_out.json
  corners.csv          per corner (all nine), pre-PNR and post-PNR: setup and
                       hold WS/TNS/violations, max slew/cap/fanout violations,
                       clock skew, and internal/switching/leakage/total power
                       from each corner's power.rpt
  summary.md           Area / Performance / Power / Signoff, with a list of
                       everything that was NOT measured and why

A step that did not run is reported as not measured; it is never filled in from
another step. Exit code 1 when final/metrics.json is missing.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

CORNERS = ("nom_tt_025C_1v80", "nom_ss_100C_1v60", "nom_ff_n40C_1v95",
           "min_tt_025C_1v80", "min_ss_100C_1v60", "min_ff_n40C_1v95",
           "max_tt_025C_1v80", "max_ss_100C_1v60", "max_ff_n40C_1v95")
PER_CORNER = (
    ("setup_ws_ns", "timing__setup__ws"), ("setup_tns_ns", "timing__setup__tns"),
    ("setup_vio", "timing__setup_vio__count"),
    ("setup_r2r_ws_ns", "timing__setup_r2r__ws"),
    ("hold_ws_ns", "timing__hold__ws"), ("hold_tns_ns", "timing__hold__tns"),
    ("hold_vio", "timing__hold_vio__count"),
    ("hold_r2r_ws_ns", "timing__hold_r2r__ws"),
    ("max_slew_vio", "design__max_slew_violation__count"),
    ("max_cap_vio", "design__max_cap_violation__count"),
    ("max_fanout_vio", "design__max_fanout_violation__count"),
    ("skew_setup_ns", "clock__skew__worst_setup"),
    ("skew_hold_ns", "clock__skew__worst_hold"),
    ("unannotated_nets", "timing__unannotated_net__count"),
)
POWER_GROUPS = ("Sequential", "Combinational", "Clock", "Macro", "Pad", "Total")


def step_dirs(run: Path, slug: str) -> list[Path]:
    """Completed step directories whose name ends with -<slug>[-N], in order."""
    out = []
    for d in sorted(run.iterdir(), key=lambda p: p.name):
        m = re.match(r"^(\d+)-(.+?)(?:-(\d+))?$", d.name)
        if d.is_dir() and m and m.group(2) == slug \
                and (d / "state_out.json").is_file():
            out.append(d)
    return sorted(out, key=lambda p: int(p.name.split("-")[0]))


def metrics_of(step: Path | None) -> dict:
    if step is None:
        return {}
    return json.loads((step / "state_out.json").read_text()).get("metrics", {})


def power_rpt(path: Path) -> dict:
    """Group -> (internal, switching, leakage, total) in watts."""
    out = {}
    if not path.is_file():
        return out
    for line in path.read_text(errors="replace").splitlines():
        parts = line.split()
        if parts and parts[0] in POWER_GROUPS and len(parts) >= 5:
            try:
                out[parts[0]] = tuple(float(x) for x in parts[1:5])
            except ValueError:
                pass
    return out


def corner_rows(stage: str, step: Path | None, m: dict, period: float | None):
    rows = []
    for c in CORNERS:
        r = {"stage": stage, "corner": c}
        # state_out.json metrics are cumulative: a corner this step did not
        # analyse still carries the value of whichever earlier step did.
        # STAMidPNR analyses nom_tt only, and on rtlfix_c235 its state_out
        # still showed the pre-PnR -108.402 ns at nom_ss. Only a corner with
        # its own report directory in this step is taken.
        analysed = step is not None and (step / c).is_dir()
        for col, key in PER_CORNER:
            r[col] = m.get("%s__corner:%s" % (key, c)) if analysed else None
        if period and r["setup_ws_ns"] is not None:
            # Achievable frequency at this corner: the period minus the
            # worst setup slack. Negative slack lengthens the period.
            r["fmax_mhz"] = round(1000.0 / (period - r["setup_ws_ns"]), 3)
        p = power_rpt(step / c / "power.rpt") if step else {}
        for g in POWER_GROUPS:
            v = p.get(g)
            for i, kind in enumerate(("internal", "switching", "leakage", "total")):
                r["pwr_%s_%s_mw" % (g.lower(), kind)] = \
                    round(v[i] * 1000, 6) if v else None
        rows.append(r)
    return rows


def fmt(v, nd=3):
    if v is None:
        return "not measured"
    if isinstance(v, float):
        return ("%%.%df" % nd) % v
    return str(v)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--out", required=True)
    ap.add_argument("--partial", action="store_true",
                    help="run without final/: use the newest completed step, "
                         "flagged as INCOMPLETE in every output")
    args = ap.parse_args()
    run, out = Path(args.run), Path(args.out)
    final = run / "final" / "metrics.json"
    partial_from = None
    if final.is_file():
        fm = json.loads(final.read_text())
    elif args.partial:
        # The run stopped before OpenLane wrote final/ (on this host: Yosys.EQY
        # dying, NHAT_KY.md 2026-09-25). Take the newest completed step's
        # cumulative metrics and say so at the top of every output.
        done = [d for d in run.iterdir() if d.is_dir() and re.match(r"^\d+-", d.name)
                and (d / "state_out.json").is_file()]
        if not done:
            sys.exit("[FAIL] no completed step in %s" % run)
        last = max(done, key=lambda d: int(d.name.split("-")[0]))
        fm = metrics_of(last)
        partial_from = last.name
    else:
        sys.exit("[FAIL] %s not found: the run did not finish (use --partial)" % final)
    out.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((run / "resolved.json").read_text()) \
        if (run / "resolved.json").is_file() else {}
    period = cfg.get("CLOCK_PERIOD")

    with (out / "metrics_final.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["key", "value"])
        for k in sorted(fm):
            w.writerow([k, fm[k]])

    synth = (step_dirs(run, "yosys-synthesis") or [None])[-1]
    pre = (step_dirs(run, "openroad-staprepnr") or [None])[-1]
    post = (step_dirs(run, "openroad-stapostpnr") or [None])[-1]
    ir = (step_dirs(run, "openroad-irdropreport") or [None])[-1]
    eqy = (step_dirs(run, "yosys-eqy") or [None])[-1]
    stages = {"post_synth": metrics_of(synth), "pre_pnr_sta": metrics_of(pre),
              "post_pnr_sta": metrics_of(post), "final": fm}
    keys = sorted(set().union(*[set(v) for v in stages.values()]))
    with (out / "metrics_stages.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["key"] + list(stages))
        for k in keys:
            w.writerow([k] + [stages[s].get(k, "") for s in stages])

    rows = corner_rows("pre_pnr", pre, stages["pre_pnr_sta"], period) + \
        corner_rows("post_pnr", post, stages["post_pnr_sta"], period)
    cols = list(rows[0])
    for r in rows:
        cols += [c for c in r if c not in cols]
    with (out / "corners.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    # ---- summary -----------------------------------------------------------
    g = fm.get
    missing = []
    for name, step in (("post-synthesis metrics (Yosys.Synthesis)", synth),
                       ("pre-PNR STA (OpenROAD.STAPrePNR)", pre),
                       ("post-PNR STA (OpenROAD.STAPostPNR)", post),
                       ("IR drop (OpenROAD.IRDropReport)", ir),
                       ("equivalence (Yosys.EQY)", eqy)):
        if step is None:
            missing.append(name + ": step did not run or did not finish")
    post_rows = [r for r in rows if r["stage"] == "post_pnr"]
    if post_rows and all(r["pwr_total_total_mw"] is None for r in post_rows):
        missing.append("per-corner power: no power.rpt in the post-PNR STA step")
    L = []
    L.append("# PD metrics: %s\n" % run.name)
    if partial_from:
        L.append("**INCOMPLETE RUN: final/ was never written. Every 'final' number "
                 "below is the cumulative metrics of `%s`, the newest completed "
                 "step; steps after it did not run.**\n" % partial_from)
        missing.append("final/metrics.json: run stopped after %s" % partial_from)
    L.append("Clock period %s ns. Source: `%s`.\n" % (
        period, (run / partial_from / "state_out.json") if partial_from else final))
    L.append("## Area\n")
    L.append("| | Post-synthesis | Final |\n|---|---:|---:|")
    sm = stages["post_synth"]
    for label, key in (("Cell instances", "design__instance__count"),
                       ("Cell area (um^2)", "design__instance__area")):
        L.append("| %s | %s | %s |" % (label, fmt(sm.get(key)), fmt(g(key))))
    for label, key in (("Die area (um^2)", "design__die__area"),
                       ("Core area (um^2)", "design__core__area"),
                       ("Std-cell area (um^2)", "design__instance__area__stdcell"),
                       ("Macro area (um^2)", "design__instance__area__macros"),
                       ("Macros", "design__instance__count__macros"),
                       ("Std cells", "design__instance__count__stdcell"),
                       ("Utilization", "design__instance__utilization"),
                       ("Std-cell utilization", "design__instance__utilization__stdcell"),
                       ("Sequential cells", "design__instance__count__class:sequential_cell"),
                       ("Timing-repair buffers", "design__instance__count__class:timing_repair_buffer"),
                       ("Clock buffers", "design__instance__count__class:clock_buffer"),
                       ("Antenna diodes", "antenna_diodes_count"),
                       ("Wirelength (um)", "route__wirelength"),
                       ("Vias", "route__vias")):
        L.append("| %s | | %s |" % (label, fmt(g(key))))
    L.append("\n## Performance and power, every corner (post-PNR)\n")
    L.append("| Corner | Setup WS | Setup TNS | Setup vio | Hold WS | Hold TNS | "
             "Hold vio | Fmax MHz | Slew vio | Cap vio | Fanout vio | "
             "Power total mW | internal | switching | leakage |")
    L.append("|---|" + "---:|" * 14)
    for r in post_rows:
        L.append("| %s |" % r["corner"] + " %s |" * 14 % tuple(
            fmt(r.get(k)) for k in (
                "setup_ws_ns", "setup_tns_ns", "setup_vio", "hold_ws_ns",
                "hold_tns_ns", "hold_vio", "fmax_mhz", "max_slew_vio",
                "max_cap_vio", "max_fanout_vio", "pwr_total_total_mw",
                "pwr_total_internal_mw", "pwr_total_switching_mw",
                "pwr_total_leakage_mw")))
    L.append("\n## Post-synthesis (pre-PNR STA: ideal clocks, no placement)\n")
    L.append("| Corner | Setup WS | Setup TNS | Setup vio | Hold WS | Hold vio | "
             "Power total mW | internal | switching | leakage |")
    L.append("|---|" + "---:|" * 9)
    for r in rows:
        if r["stage"] != "pre_pnr" or r["setup_ws_ns"] is None:
            continue
        L.append("| %s |" % r["corner"] + " %s |" * 9 % tuple(
            fmt(r.get(k)) for k in (
                "setup_ws_ns", "setup_tns_ns", "setup_vio", "hold_ws_ns",
                "hold_vio", "pwr_total_total_mw", "pwr_total_internal_mw",
                "pwr_total_switching_mw", "pwr_total_leakage_mw")))
    L.append("\nPower is OpenSTA's vectorless estimate (default switching "
             "activity), not a simulation-driven measurement. Pre-PNR STA "
             "analyses the three nominal corners only.\n")
    L.append("## Signoff\n")
    L.append("| Check | Value |\n|---|---:|")
    for label, key in (("Magic DRC errors", "magic__drc_error__count"),
                       ("KLayout DRC errors", "klayout__drc_error__count"),
                       ("Illegal overlaps", "magic__illegal_overlap__count"),
                       ("LVS errors", "design__lvs_error__count"),
                       ("LVS unmatched nets", "design__lvs_unmatched_net__count"),
                       ("LVS unmatched pins", "design__lvs_unmatched_pin__count"),
                       ("Antenna violating nets", "antenna__violating__nets"),
                       ("Antenna violating pins", "antenna__violating__pins"),
                       ("Route DRC errors", "route__drc_errors"),
                       ("Power-grid violations", "design__power_grid_violation__count"),
                       ("Floating nets", "timing__drv__floating__nets"),
                       ("Lint errors", "design__lint_error__count"),
                       ("Lint warnings", "design__lint_warning__count"),
                       ("Inferred latches (Verilator; unreliable, see NHAT_KY.md 2026-09-24)",
                        "design__inferred_latch__count"),
                       ("Flow errors", "flow__errors__count"),
                       ("Flow warnings", "flow__warnings__count")):
        L.append("| %s | %s |" % (label, fmt(g(key))))
    irm = metrics_of(ir)
    for k in sorted(irm):
        if k.startswith(("ir__", "design__power")):
            L.append("| %s | %s |" % (k, fmt(irm[k], 6)))
    L.append("\n## Not measured\n")
    L.extend("- " + x for x in missing) if missing else L.append("- nothing")
    (out / "summary.md").write_text("\n".join(L) + "\n")
    print("[OK] %d final keys, %d stage keys, %d corner rows -> %s"
          % (len(fm), len(keys), len(rows), out))
    for x in missing:
        print("   not measured: %s" % x)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
