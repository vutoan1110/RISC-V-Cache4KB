"""Floorplan screening table (FLOW_JOURNAL Incident 96) from asic/dse_pd.log + the configs.

For every screening run (explore_fp2.sh "end <tag> ... midPnR-2 nom_tt setup S hold H; GRT usage U overflow O") and
every full-iteration GRT check (explore_grt50.sh "end <tag>G50: GRT (50 iterations) usage U overflow O"), prints:
design, floorplan, die, area, corridor / logic band (from the macro_placement header), post-CTS-repair setup/hold
nom_tt, 15-iteration overflow, 50-iteration overflow. The LAST line of a tag wins (reruns after a crash).

    python asic/fp_tools/fp_summary.py [--md out.md]
"""
import argparse
import json
import re
from pathlib import Path

A = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument("--md", default="")
a = ap.parse_args()
DES = {"vc4": "soc_vc4_4kb", "sa2": "soc_sa2_4kb", "dm": "soc_dm_4kb"}
scr, g50 = {}, {}
for line in (A / "dse_pd.log").read_text(encoding="utf-8", errors="replace").splitlines():
    m = re.search(r" end (\w+?)G50: GRT \(50 iterations\) usage (\S+) overflow (\d+)", line)
    if m:
        g50[m.group(1)] = (m.group(2), int(m.group(3)))
        continue
    m = re.search(r" end (\w+) last step \S+: midPnR-2 nom_tt setup (\S+) hold (\S+); GRT(50)? usage (\S+) overflow (\d+)", line)
    if m:
        if m.group(4):          # explore_fp3.sh: the screening itself ran the default 50 iterations
            scr[m.group(1)] = (float(m.group(2)), float(m.group(3)), "-", -1)
            g50[m.group(1)] = (m.group(5), int(m.group(6)))
        else:
            scr[m.group(1)] = (float(m.group(2)), float(m.group(3)), m.group(5), int(m.group(6)))
rows = []
for tag, (su, ho, us, ov) in scr.items():
    m = re.match(r"(vc4|sa2|dm)(U2\w+|R\d+\w*|S\d+)$", tag)
    if not m or not m.group(2).startswith("U2"):
        continue
    des, fp = DES[m.group(1)], m.group(2).lower()
    cfg = A / des / ("config_%s.json" % fp)
    if not cfg.is_file():
        continue
    die = json.load(open(cfg, encoding="utf-8"))["DIE_AREA"]
    hdr = (A / des / ("macro_placement_%s.cfg" % fp)).read_text(encoding="utf-8").splitlines()[:3]
    cor = re.search(r"corridor (\d+)", " ".join(hdr))
    band = re.search(r"logic band (\d+)", " ".join(hdr))
    orients = {ln.split()[-1] for ln in (A / des / ("macro_placement_%s.cfg" % fp)).read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")}
    rot = "rotated E/W" if orients & {"E", "W", "FE", "FW"} else ("upper row FS" if "FS" in {ln.split()[-1] for ln in (A / des / ("macro_placement_%s.cfg" % fp)).read_text(encoding="utf-8").splitlines() if "cache" in ln and not ln.startswith("#")} else "")
    g = g50.get(tag)
    rows.append(({"soc_vc4_4kb": "DM_VC4", "soc_sa2_4kb": "SA2", "soc_dm_4kb": "DM"}[des], fp, "%g x %g" % (die[2], die[3]), die[2] * die[3] / 1e6, cor.group(1) if cor else "?",
                 band.group(1) if band else "?", rot, su, ho, ov, g[1] if g else None))
rows.sort(key=lambda r: (r[0], r[3]))
H = "| design | fp | die (um) | area mm2 | corridor um | logic band um | macros | setup nom_tt | hold nom_tt | overflow @15 it | overflow @50 it |"
out = [H, "|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|"]
for r in rows:
    out.append("| %s | %s | %s | %.2f | %s | %s | %s | %+.3f | %+.3f | %s | %s |" % (
        r[0], r[1], r[2], r[3], r[4], r[5], r[6] or "N", r[7], r[8], "-" if r[9] < 0 else r[9], "-" if r[10] is None else r[10]))
print("\n".join(out))
if a.md:
    Path(a.md).write_text("\n".join(out) + "\n", encoding="utf-8")
