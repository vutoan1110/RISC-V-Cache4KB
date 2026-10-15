"""Audit the verified ASIC subset for T6; never run or change a PD flow.

Require identical full metric dictionaries, the existing final sign-off gate,
byte-identical final netlist/DEF and SPEF differing only in *DATE. Power is
included only after two independent raw STA reports and their CSVs agree.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

from verify_activity_power import parse as parse_power

ROOT = Path(__file__).resolve().parents[2]
SA2 = "sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin"
PAIRS = {"DM": ("soc_dm_4kb", "r14F_A", "r14F_B"),
         "SA2": ("soc_sa2_4kb", SA2 + "_r1", SA2 + "_r2")}
CORNERS = [f"{rc}_{pvt}" for pvt in ("tt_025C_1v80", "ff_n40C_1v95", "ss_100C_1v60")
           for rc in ("nom", "min", "max")]


def sha(path, spef=False):
    digest = hashlib.sha256()
    dates = 0
    with path.open("rb") as f:
        if spef:
            for line in f:
                if re.match(br"^\*DATE(?:\s|$)", line):
                    dates += 1
                else:
                    digest.update(line)
        else:
            for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
                digest.update(chunk)
    if spef and dates != 1:
        raise RuntimeError(f"Expected exactly one SPEF DATE line: {path}")
    return digest.hexdigest()


def equal_metrics(first, second):
    a, b = ({k: v for k, v in m.items() if not k.startswith(("runtime", "flow__"))}
            for m in (first, second))
    if a.keys() != b.keys():
        raise RuntimeError(f"Metric keys differ: {sorted(a.keys() ^ b.keys())}")
    differences = [k for k in a if a[k] != b[k]]
    if differences:
        raise RuntimeError(f"Independent metrics differ: {differences[:10]}")
    if not a:
        raise RuntimeError("No measurement metrics")
    return a


def metrics(run):
    merged, eco = {}, []
    steps = sorted((p for p in run.iterdir() if p.is_dir() and re.match(r"^\d+-", p.name)),
                   key=lambda p: int(p.name.split("-", 1)[0]))
    for step in steps:
        state = step / "state_out.json"
        if not state.is_file():
            continue
        values = json.loads(state.read_text())["metrics"]
        merged.update(values)
        if "-openroad-postrouteholdeco" in step.name:
            eco.append({"step": step.name, "inserted_hold_buffers": values["design__instance__count__hold_buffer"]})
    return merged, eco


def equal_eco_sequence(first, second):
    # Resumes allocate new directory numbers; numbers are provenance, not a
    # hardware measurement. Compare step identity and counts in flow order.
    values = lambda seq: [(e["step"].split("-", 1)[1], e["inserted_hold_buffers"]) for e in seq]
    if not first or values(first) != values(second):
        raise RuntimeError("Independent hold ECO sequences differ")


def last(run, suffix):
    candidates = sorted(run.glob("*-" + suffix), key=lambda p: int(p.name.split("-")[0]))
    if not candidates:
        raise RuntimeError(f"Missing {suffix}: {run}")
    return candidates[-1]


def final_gate(run):
    p = subprocess.run([sys.executable, str(ROOT / "asic/fp_tools/gate_check.py"), str(run), "final"],
                       capture_output=True, text=True, check=False)
    if p.returncode or not p.stdout.startswith("PASS final:"):
        raise RuntimeError(f"Final gate failed: {run.name}: {p.stdout.strip()} {p.stderr.strip()}")
    return p.stdout.strip()


def paired_csv(first, second, keys):
    def read(path):
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            header, rows = reader.fieldnames, list(reader)
        data = {tuple(r[k] for k in keys): r for r in rows}
        if len(data) != len(rows) or not rows:
            raise RuntimeError(f"Empty or duplicate CSV keys: {path}")
        return header, data
    a, b = read(first), read(second)
    if a[0] != b[0] or a[1] != b[1]:
        raise RuntimeError(f"Independent CSVs differ: {first}, {second}")
    return a[1]


def activity(tag, run, ref_path, cfg):
    receipt = ROOT / f"results/gls_power_{tag}_power_verification.json"
    if not receipt.is_file():
        return {"status": "NOT_DOUBLE_VERIFIED", "reason": "no two-STA verification receipt"}
    meta = json.loads(receipt.read_text())
    if meta.get("status") != "VERIFIED_TWO_INDEPENDENT_STA_PASSES" or meta.get("corner") != CORNERS[0]:
        raise RuntimeError(f"Invalid power verification receipt: {receipt}")
    paired = paired_csv(ROOT / f"results/gls_power_{tag}_power_p1.csv",
                        ROOT / f"results/gls_power_{tag}_power_p2.csv", ["kernel"])
    if len(paired) != 12:
        raise RuntimeError("Require twelve power kernels")
    with ref_path.open(newline="") as f:
        reference = {r["kernel"]: r for r in csv.DictReader(f) if r["config"] == cfg}
    with (ROOT / f"results/gls_power_{tag}.csv").open(newline="") as f:
        gls = {r["kernel"]: r for r in csv.DictReader(f)}
    kernels = {k[0] for k in paired}
    if kernels != reference.keys() or kernels != gls.keys():
        raise RuntimeError("Power/GLS/RTL reference kernel sets differ")
    folder = ROOT / f"results/gls_power_{tag}"
    flow = parse_power(last(run, "openroad-stapostpnr") / CORNERS[0] / "power.rpt", activity=False)[0]
    for suffix in ("", ".p2"):
        if parse_power(folder / f"vectorless.power{suffix}.rpt", activity=False)[0] != flow:
            raise RuntimeError("Vectorless STA does not reproduce every flow power group")
    rows, evidence = [], {receipt.relative_to(ROOT).as_posix(): sha(receipt)}
    for kernel in sorted(kernels):
        p1, p2 = (folder / f"{kernel}.power{s}.rpt" for s in ("", ".p2"))
        groups, origins = parse_power(p1)
        if (groups, origins) != parse_power(p2):
            raise RuntimeError(f"Raw independent STA power reports differ: {kernel}")
        mc, mi = int(reference[kernel]["mcycle"]), int(reference[kernel]["minstret"])
        g = gls[kernel]
        if (g["status"], g["match"], g["saif"]) != ("PASS", "YES", "YES") or not (
                g["gls_mcycle"] == g["rtl_mcycle"] == g["win_cycles"] == str(mc)):
            raise RuntimeError(f"GLS reference/window gate failed: {kernel}")
        internal, switching, leakage, total = groups["Total"]
        values = {"total_mw": f"{total * 1000:.2f}", "dynamic_mw": f"{(internal+switching)*1000:.2f}",
                  "leakage_mw": f"{leakage*1000:.3f}", "window_cycles": str(mc), "minstret": str(mi),
                  "cpi": f"{mc/mi:.4f}", "epi_pj": f"{total*Decimal(mc)*Decimal('20000')/Decimal(mi):.0f}",
                  "unknown_pct": origins["unknown"][1],
                  **{field: f"{groups[group][3]*1000:.2f}" for field, group in (
                      ("seq_mw", "Sequential"), ("comb_mw", "Combinational"),
                      ("clock_mw", "Clock"), ("macro_mw", "Macro"))}}
        if any(paired[kernel,][k] != v for k, v in values.items()):
            raise RuntimeError(f"Power CSV differs from the raw STA/reference evidence: {kernel}")
        rows.append({"kernel": kernel, "total_mw": float(total*1000),
                     "dynamic_mw": float((internal+switching)*1000), "leakage_mw": float(leakage*1000),
                     "epi_pj": float(total)*mc*20000/mi, "unknown_pct": origins["unknown"][1]})
        evidence.update({p.relative_to(ROOT).as_posix(): sha(p) for p in (p1, p2)})
    return {"status": "VERIFIED_TWO_INDEPENDENT_STA_PASSES", "corner": CORNERS[0], "kernels": rows,
            "evidence": evidence, "method": "GLS -> SAIF -> OpenSTA with sign-off RCX SPEF"}


def audit(label, spec):
    design, a, b = spec
    runs = [ROOT / "asic" / design / "runs" / tag for tag in (a, b)]
    measured = [metrics(p) for p in runs]
    m = equal_metrics(measured[0][0], measured[1][0])
    equal_eco_sequence(measured[0][1], measured[1][1])
    gates = [final_gate(p) for p in runs]
    artifacts = {}
    for suffix, pattern in (
        ("final_netlist", "openroad-fillinsertion"),
        ("final_DEF", "openroad-fillinsertion")):
        name = "soc_asic_top.nl.v" if suffix == "final_netlist" else "soc_asic_top.def"
        paths = [last(run, pattern) / name for run in runs]
        digests = [sha(p) for p in paths]
        if digests[0] != digests[1]:
            raise RuntimeError(f"Independent {suffix} differ")
        artifacts[suffix] = {"paths": [p.relative_to(ROOT).as_posix() for p in paths], "sha256": digests[0]}
    for corner in ("nom", "min", "max"):
        paths = [last(run, "openroad-rcx") / corner / f"soc_asic_top.{corner}.spef" for run in runs]
        digests = [sha(p, spef=True) for p in paths]
        if digests[0] != digests[1]:
            raise RuntimeError(f"Independent {corner} SPEF differ beyond DATE")
        artifacts[f"SPEF_{corner}"] = {"paths": [p.relative_to(ROOT).as_posix() for p in paths],
                                      "sha256_except_DATE": digests[0]}
    flow_power = []
    for run in runs:
        flow_power.append(parse_power(last(run, "openroad-stapostpnr") / CORNERS[0] / "power.rpt", activity=False)[0])
    if flow_power[0] != flow_power[1]:
        raise RuntimeError("Independent vectorless sign-off power groups differ")
    text = (last(runs[0], "openroad-fillinsertion") / "soc_asic_top.def").read_text()
    section = re.search(r"COMPONENTS\s+\d+\s*;(.*?)END COMPONENTS", text, re.S)
    if not section:
        raise RuntimeError("Missing DEF components")
    masters = collections.Counter(cell.split("__")[-1].rsplit("_", 1)[0]
                                  for name, cell in re.findall(r"^\s*-\s+(\S+)\s+(\S+)", section[1], re.M))
    buffer_census = {k: masters[k] for k in ("buf", "clkbuf", "inv", "clkinv", "dlymetal6s2s", "dlymetal6s4s")}
    ref = ROOT / ("results/upstream_asic_r15_p1.csv" if label == "DM" else "results/dse_asic_view_p1.csv")
    power = activity(a, runs[0], ref, label)
    return {"design": design, "runs": [a, b], "signoff": gates, "paired_metrics": len(m),
            "metrics": m, "artifacts": artifacts, "hold_ECO_sequence": measured[0][1],
            "hold_ECO_second_run_provenance": measured[1][1],
            "final_cell_master_census": buffer_census, "vectorless_nom_tt_total_mw": float(flow_power[0]["Total"][3]*1000),
            "activity_power": power}


def render(data, architecture):
    labels = list(data)
    out = ["# T6 verified ASIC subset: DM and SA2", "",
           "This is a partial table, not the final three-configuration PPA result. DM_VC4 has not passed sign-off; "
           "SA2 minimum die is not proved. Activity power is included only where independent second STA evidence is verified.", ""]
    def table(title, rows):
        out.extend(["## " + title, "", "| metric | " + " | ".join(labels) + " |", "|---|" + "---:|"*len(labels)])
        for name, fn in rows:
            out.append("| " + name + " | " + " | ".join(str(fn(label, data[label])) for label in labels) + " |")
        out.append("")
    table("Sign-off and independent execution gate", [
        ("Final sign-off, both runs", lambda l,d: "PASS / PASS"),
        ("All non-runtime metrics, identical full key sets", lambda l,d: d["paired_metrics"]),
        ("Final netlist / DEF", lambda l,d: "byte-identical"),
        ("nom / min / max SPEF", lambda l,d: "identical except DATE"),
        ("Route / Magic / KLayout DRC; all LVS differences; XOR; overlap; critical pins; antenna nets/pins",
         lambda l,d: "all zero"),
        ("Setup every tt/ff; hold all 9 corners", lambda l,d: "PASS")])
    def metric(key, factor=1, precision=3):
        return lambda l,d: f"{float(d['metrics'][key])*factor:.{precision}f}"
    table("Area and routing", [(name, metric(key, factor, precision)) for name,key,factor,precision in (
        ("Die mm2", "design__die__area", 1e-6, 6), ("Core mm2", "design__core__area", 1e-6, 6),
        ("Standard-cell area mm2", "design__instance__area__stdcell", 1e-6, 6),
        ("Standard-cell count", "design__instance__count__stdcell", 1, 0),
        ("Macro area mm2", "design__instance__area__macros", 1e-6, 6),
        ("Total routed wire m", "route__wirelength", 1e-6, 6))])
    table("Timing: STAPostPNR WNS in ns, ss setup reported only", [
        (f"{kind} {corner}", metric(f"timing__{kind}__ws__corner:{corner}"))
        for corner in CORNERS for kind in ("setup", "hold")])
    table("Buffer accounting", [
        ("Flow timing-repair-buffer class", metric("design__instance__count__class:timing_repair_buffer", 1, 0)),
        ("Flow clock-buffer class", metric("design__instance__count__class:clock_buffer", 1, 0)),
        ("Flow macro-pin-buffer count", metric("design__macro_pin_buffer__count", 1, 0)),
        ("Hold buffers inserted per post-route ECO pass", lambda l,d: " + ".join(str(e["inserted_hold_buffers"]) for e in d["hold_ECO_sequence"])),
        ("Final DEF buf + clkbuf masters", lambda l,d: d["final_cell_master_census"]["buf"]+d["final_cell_master_census"]["clkbuf"]),
        ("Final DEF inv + clkinv masters", lambda l,d: d["final_cell_master_census"]["inv"]+d["final_cell_master_census"]["clkinv"])])
    out.extend(["Flow class counters and per-ECO insertions describe different stages and may overlap; do not sum them. "
                "The separate DEF census counts final physical cell masters, without inferring clock-net connectivity.", ""])
    def psummary(d, field):
        p = d["activity_power"]
        if p["status"] != "VERIFIED_TWO_INDEPENDENT_STA_PASSES":
            return "pending independent second STA"
        values = [r[field] for r in p["kernels"]]
        return f"{min(values):.3f}..{max(values):.3f}; mean {sum(values)/len(values):.3f}"
    table("Power: nom_tt_025C_1v80, sign-off RCX SPEF", [
        ("Vectorless OpenSTA default activity, mW", lambda l,d: f"{d['vectorless_nom_tt_total_mw']:.3f}"),
        ("GLS -> SAIF -> OpenSTA total, mW", lambda l,d: psummary(d,"total_mw")),
        ("Activity dynamic, mW", lambda l,d: psummary(d,"dynamic_mw")),
        ("Activity leakage, mW", lambda l,d: psummary(d,"leakage_mw")),
        ("Energy/instruction, pJ", lambda l,d: psummary(d,"epi_pj"))])
    table("Embench on current RTL 6c4ccffd: FPGA view, 12 kernels, both passes identical", [
        (name, lambda l,d, key=key: f"{architecture[l][key]:.4f}")
        for name,key in (("Weighted CPI", "cpi"), ("I-cache hit %", "i_hit_pct"), ("D-cache read hit %", "d_hit_pct"))])
    out.extend(["ASIC power/EPI use ASIC-view cycles; the architectural rows use FPGA-view counters. "
                "SRAM timing models are TT only; ss/ff paths through SRAM retain that limitation.", "",
                "Recipe notes: DM remains locked at config_R14_FINAL.json (density 55, CTS cluster 8, "
                "hold margins 0.03/0.02). SA2 retains cap margin 20, fanout 16, one-site padding, timing-driven "
                "placement, clock trunks on met3..5, resizer tt/ff and max_* then min_* hold ECO. "
                "Their measured rationales remain in NHAT_KY section 8; no new recipe is selected by this table.", "",
                "Evidence and per-kernel unrounded values are in the companion JSON. Architecture source: "
                "results/rfbht_4kb_p{1,2}.csv. DM power second-pass plan: "
                "results/dm_activity_power_second_pass_preparation_20261009.json. "
                "DM_VC4 experiment plan: results/vc4_padding_hypothesis_20261009.md.", ""])
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="results/asic_ppa_verified_subset_20261009.md")
    args = ap.parse_args()
    subprocess.run([sys.executable, str(ROOT / "scripts/rtl_manifest.py"), "--check"], cwd=ROOT, check=True)
    manifest = json.loads((ROOT / "results/rtl_manifest.json").read_text())
    if not manifest["aggregate"].startswith("6c4ccffd"):
        raise RuntimeError("Architectural source RTL differs; review before publishing")
    architecture_rows = paired_csv(ROOT / "results/rfbht_4kb_p1.csv", ROOT / "results/rfbht_4kb_p2.csv", ["config", "kernel"])
    architecture = {}
    for label in PAIRS:
        rows = [r for r in architecture_rows.values() if r["config"] == label]
        if len(rows) != 12 or any(r["result_pass"] != "1" or r["invariant_pass"] != "1" for r in rows):
            raise RuntimeError(f"Invalid architectural measurement subset: {label}")
        total = lambda key: sum(int(r[key]) for r in rows)
        architecture[label] = {"cpi": total("mcycle")/total("minstret"),
                               "i_hit_pct": 100*total("i_hit_ev")/total("i_access"),
                               "d_hit_pct": 100*total("d_rd_hit")/total("d_read")}
    data = {}
    for label, spec in PAIRS.items():
        print(f"[AUDIT] {label}: independent metrics, gate, final artifacts and power evidence", flush=True)
        data[label] = audit(label, spec)
    dest = (ROOT / args.out).resolve()
    dest.relative_to(ROOT)
    dest.write_text(render(data, architecture), encoding="ascii")
    dest.with_suffix(".json").write_text(json.dumps({"status": "VERIFIED_SUBSET_NOT_FINAL_T6", "designs": data,
        "rtl_id": manifest["aggregate"],
        "architecture": architecture, "architecture_sources": {p.relative_to(ROOT).as_posix(): sha(p)
        for p in (ROOT / "results/rfbht_4kb_p1.csv", ROOT / "results/rfbht_4kb_p2.csv")},
        "gaps": (["DM second activity STA not yet verified"]
                 if data['DM']['activity_power']['status'] != 'VERIFIED_TWO_INDEPENDENT_STA_PASSES' else [])
                + ["SA2 minimum die not proved", "DM_VC4 not signed off"]},
        indent=2) + "\n", encoding="ascii")
    print(f"[PASS] DM/SA2 verified PD subset; power gaps explicit; {dest.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
