#!/usr/bin/env python3
"""Side-by-side sign-off and PPA numbers of finished OpenLane runs, e.g. SA2 E1 against the signed ecomaxmin recipe,
or the DM acceptance run against r14F_A.

    python scripts/metrics/compare_signoff_runs.py LABEL=asic/<design>/runs/<tag> [LABEL=...] [--out file.md]

Every value is read from the run (final/metrics.json, and the nom_tt power report of its last post-PNR STA step);
a value the run did not produce prints as "n/a", it is never filled in. With two or more runs the last column is
the difference of the last run against the first. Power: power__total is the flow's estimate at max_ff; the nom_tt
groups are OpenSTA vectorless (default activity), not the activity-based (GLS / SAIF) numbers.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pd_metrics import CORNERS, power_rpt, step_dirs  # noqa: E402

SIGNOFF = [("Magic DRC", "magic__drc_error__count"), ("KLayout DRC", "klayout__drc_error__count"),
           ("Route DRC", "route__drc_errors"), ("LVS errors", "design__lvs_error__count"),
           ("XOR differences", "design__xor_difference__count"), ("Antenna nets", "antenna__violating__nets"),
           ("Antenna pins", "antenna__violating__pins")]
AREA = [("Die area, um2", "design__die__area"), ("Core area, um2", "design__core__area"),
        ("Std-cell area, um2", "design__instance__area__stdcell"), ("Std cells", "design__instance__count__stdcell"),
        ("Std-cell utilisation", "design__instance__utilization__stdcell")]
CELLS = [("Timing-repair buffers", "timing_repair_buffer"), ("Clock buffers", "clock_buffer"),
         ("Clock inverters", "clock_inverter"), ("Other buffers", "buffer"), ("Inverters", "inverter"),
         ("Sequential cells", "sequential_cell"), ("Multi-input combinational", "multi_input_combinational_cell"),
         ("Antenna diodes", "antenna_cell")]
DRV = [("Max slew violations", "design__max_slew_violation__count"),
       ("Max cap violations", "design__max_cap_violation__count"),
       ("Max fanout violations", "design__max_fanout_violation__count")]
GROUPS = ("Sequential", "Combinational", "Clock", "Macro", "Total")


def load(run: Path) -> tuple[dict, dict, str]:
    """Metrics, nom_tt power groups, and where the metrics came from. A run that ended in a step after sign-off
    without writing final/ (e.g. r14F_A, which stopped in Yosys.EQY) is read from the state_out.json of its last
    completed step; OpenLane's state metrics are cumulative, so that file carries every earlier step's metrics."""
    f = run / "final" / "metrics.json"
    if f.is_file():
        m, src = json.loads(f.read_text()), "final/metrics.json"
    else:
        done = sorted((d for d in run.iterdir() if d.is_dir() and d.name[:1].isdigit()
                       and (d / "state_out.json").is_file()), key=lambda d: int(d.name.split("-")[0]))
        m = json.loads((done[-1] / "state_out.json").read_text()).get("metrics", {}) if done else {}
        src = (done[-1].name + "/state_out.json") if done else "none"
    sta = step_dirs(run, "openroad-stapostpnr")
    p = power_rpt(sta[-1] / "nom_tt_025C_1v80" / "power.rpt") if sta else {}
    return m, p, src


def fmt(v, kind: str) -> str:
    if v is None:
        return "n/a"
    if kind == "ns":
        return "%+.3f" % v
    if kind == "frac":
        return "%.4f" % v
    if kind == "mW":
        return "%.2f" % v
    if isinstance(v, float) and not v.is_integer():
        return "%.3f" % v
    return "{:,}".format(int(v))


def diff(a, b, kind: str) -> str:
    if a is None or b is None:
        return "n/a"
    d = b - a
    if kind == "ns":
        return "%+.3f" % d
    if kind == "mW":
        s = "%+.2f" % d
    elif kind == "frac":
        s = "%+.4f" % d
    else:
        s = "{:+,}".format(int(round(d))) if float(d).is_integer() else "%+.3f" % d
    return s + (" (%+.1f %%)" % (100.0 * d / a) if a else "")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("runs", nargs="+", help="LABEL=run directory")
    ap.add_argument("--out")
    a = ap.parse_args()
    labels, data = [], []
    for item in a.runs:
        lab, _, path = item.partition("=")
        run = Path(path)
        if not run.is_dir():
            print("no run directory %s" % run, file=sys.stderr)
            return 2
        labels.append(lab)
        data.append(load(run))
    two = len(data) >= 2
    head = "| item | " + " | ".join(labels) + (" | last - first |" if two else " |")
    sep = "|---|" + "---:|" * (len(labels) + (1 if two else 0))
    L = ["Runs (metrics source): " + ", ".join("%s = `%s` (%s)" % (lab, it.partition("=")[2], d[2])
                                               for lab, it, d in zip(labels, a.runs, data)), ""]

    def table(title, rows):
        L.extend(["", "### " + title, "", head, sep])
        for name, vals, kind in rows:
            line = "| %s | " % name + " | ".join(fmt(v, kind) for v in vals)
            if two:
                line += " | " + diff(vals[0], vals[-1], kind)
            L.append(line + " |")

    def col(key):
        return [m.get(key) for m, _, _ in data]

    table("Sign-off checks (all must be 0)", [(n, col(k), "int") for n, k in SIGNOFF])
    table("Setup worst slack, ns", [(c, col("timing__setup__ws__corner:" + c), "ns") for c in CORNERS])
    table("Hold worst slack, ns", [(c, col("timing__hold__ws__corner:" + c), "ns") for c in CORNERS])
    table("Area", [(n, col(k), "frac" if "utilisation" in n else "int") for n, k in AREA])
    table("Cells by class", [(n, col("design__instance__count__class:" + k), "int") for n, k in CELLS])
    table("Wire and DRV (DRV reported, not gated)",
          [("Routed wire, um", col("route__wirelength"), "int")] + [(n, col(k), "int") for n, k in DRV])
    prow = [("Flow power__total (max_ff estimate), mW",
             [None if m.get("power__total") is None else 1000.0 * m["power__total"] for m, _, _ in data], "mW")]
    for g in GROUPS:
        prow.append(("nom_tt vectorless %s, mW" % g,
                     [None if g not in p else 1000.0 * p[g][3] for _, p, _ in data], "mW"))
    table("Power", prow)
    text = "\n".join(L) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
