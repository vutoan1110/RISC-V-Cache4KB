"""Prepare the T4 die ladder from the signed-off SA2 recipe; never launch a flow.

Only DIE_AREA, CORE_AREA and MACRO_PLACEMENT_CFG change as implementation inputs.
The second-ECO configs retain the signed-off min_* extraction recipe.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESIGN = ROOT / "asic/soc_sa2_4kb"
RECIPE = "f220_capm20_fo16_pad1_tdp_clkm3_rsztf"


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    sizes = {}
    for kb in (1, 2):
        lef = ROOT / f"asic/soc_dm_4kb/macros/lef/sky130_sram_{kb}kbyte_1rw1r_32x{256*kb}_8.lef"
        match = re.search(r"\bSIZE\s+([\d.]+)\s+BY\s+([\d.]+)\s*;", lef.read_text())
        if not match:
            raise RuntimeError(f"Missing macro size: {lef}")
        sizes[kb] = tuple(map(float, match.groups()))
    records = []
    for h in (3250, 3325):
        mp = DESIGN / f"macro_placement_corr3400x{h}_f220.cfg"
        text = mp.read_text()
        if "cache orientation F" not in text or "channel 220" not in text:
            raise RuntimeError(f"Wrong macro orientation or RAM channel: {mp}")
        boxes = []
        names = set()
        for line in text.splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            name, x, y, orient = line.split()
            if name in names or orient not in ("N", "FS"):
                raise RuntimeError(f"Duplicate macro or unexpected orientation: {line}")
            names.add(name)
            w, mh = sizes[2 if "u_axi_ram" in name else 1]
            box = (float(x), float(y), float(x) + w, float(y) + mh)
            if not (12 <= box[0] < box[2] <= 3388 and 12 <= box[1] < box[3] <= h - 12):
                raise RuntimeError(f"Macro outside the candidate core: {name}, {box}")
            for other, b in boxes:
                if min(box[2], b[2]) > max(box[0], b[0]) and min(box[3], b[3]) > max(box[1], b[1]):
                    raise RuntimeError(f"Macro overlap: {name}, {other}")
            boxes.append((name, box))
        if len(names) != 16 or sum("u_axi_ram" in n for n in names) != 8:
            raise RuntimeError("Expected 8 RAM and 8 cache macros")
        for eco in (False, True):
            suffix = "_ecomin" if eco else ""
            source = DESIGN / f"config_corr3400x3400_{RECIPE}{suffix}.json"
            old = json.loads(source.read_text())
            candidate = dict(old)
            candidate.update(DIE_AREA=[0, 0, 3400, h], CORE_AREA=[12, 12, 3388, h - 12],
                             MACRO_PLACEMENT_CFG="dir::" + mp.name)
            candidate["//EXPERIMENT"] = (
                f"T4 minimality candidate {3400*h/1e6:.3f} mm2, UNEXECUTED. Identical signed-off SA2 recipe "
                f"from {source.name}; only die/core and the existing F-oriented, 220 um-gap macro placement change. "
                "Full flow from step 1, then the same max_* -> branch -> min_* hold-ECO procedure; 20 ns unchanged.")
            changed = sorted(k for k in old if not k.startswith("//") and old[k] != candidate[k])
            if changed != ["CORE_AREA", "DIE_AREA", "MACRO_PLACEMENT_CFG"]:
                raise RuntimeError(f"Unexpected implementation changes: {changed}")
            if candidate["CLOCK_PERIOD"] != 20 or candidate["RSZ_CORNERS"] != old["RSZ_CORNERS"]:
                raise RuntimeError("Clock or resizer recipe changed")
            if eco and candidate["POST_ROUTE_HOLD_ECO_RCX_CORNER"] != "min_*":
                raise RuntimeError("Second-ECO extraction differs")
            destination = DESIGN / f"config_corr3400x{h}_{RECIPE}{suffix}.json"
            if destination.exists():
                raise RuntimeError(f"Candidate already exists; inspect instead of overwriting: {destination}")
            record = {"status": "PREPARED_NOT_EXECUTED", "die_mm2": 3400*h/1e6,
                "core_mm2": (3388-12)*(h-24)/1e6, "source": source.relative_to(ROOT).as_posix(),
                "source_sha256": digest(source), "config": destination.relative_to(ROOT).as_posix(),
                "macro_placement": mp.relative_to(ROOT).as_posix(), "macro_sha256": digest(mp),
                "changed_implementation_fields": changed, "macro_count": 16,
                "macro_geometry": "inside core; no overlap", "second_eco": eco}
            if args.write:
                destination.write_text(json.dumps(candidate, indent=4) + "\n", encoding="ascii")
                record["config_sha256"] = digest(destination)
            records.append(record)
    if args.write:
        out = ROOT / "results/sa2_minimality_preparation_20261009.json"
        if out.exists():
            raise RuntimeError("Preparation record exists; inspect before replacing")
        out.write_text(json.dumps({"task": "T4", "order": "3250 first; 3325 only if 3250 fails",
            "not_a_measurement": True, "configs": records}, indent=2) + "\n", encoding="ascii")
    print(f"[{'PREPARED' if args.write else 'PLAN'}] 4 configs; 16 macros fit both cores; only the 3 prescribed implementation fields change; no PD launched")


if __name__ == "__main__":
    main()
