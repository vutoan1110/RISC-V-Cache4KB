"""R16 ASIC snapshot + synthesis config (rule D.6 for the DM chip; the SA2 / DM_VC4 PD file lists are covered by
asic/equiv/r16_eq/run_r16_eq_soc.sh).

asic/snapshots/rtl_r16 = asic/snapshots/rtl_r15 with the seven R16 files of hdl/ (soc_top.v and the six cache files)
taken from the frozen R16 tree (manifest ea3ef852). Every other snapshot file must still equal the working tree
byte for byte, or the script stops: the snapshot may differ from R15 by exactly the R16 change.
asic/soc_dm_4kb/config_R16_synth.json = config_R15_synth.json with rtl_r15 -> rtl_r16 in VERILOG_FILES.

    python scripts/r16_fasthit/make_r16_snapshot.py
"""
import filecmp
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
S15 = ROOT / "asic" / "snapshots" / "rtl_r15"
S16 = ROOT / "asic" / "snapshots" / "rtl_r16"
R16 = {"hdl/soc_top.v", "hdl/cache/icache.v", "hdl/cache/dcache.v", "hdl/cache/icache_dse_core.v",
       "hdl/cache/dcache_dse_core.v", "hdl/cache/icache_nway_core.v", "hdl/cache/dcache_nway_core.v"}

assert not S16.exists(), "%s exists already" % S16
files = sorted(p.relative_to(S15).as_posix() for p in S15.rglob("*") if p.is_file() and p.name != "SNAPSHOT_ID.txt")
changed = [f for f in files if not filecmp.cmp(S15 / f, ROOT / f, shallow=False)]
assert set(changed) == R16, ("snapshot vs tree differs in", sorted(set(changed) ^ R16))
for f in files:
    (S16 / f).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / f, S16 / f)
(S16 / "SNAPSHOT_ID.txt").write_text(
    "R16 (2026-10-03, review M1): rtl_r15 + the R16 FAST_HIT files from the working tree (manifest ea3ef852):\n"
    + "".join("  %s\n" % f for f in sorted(R16))
    + "The other %d files are byte-identical to rtl_r15. FAST_HIT defaults to 0; CACHE_CONFIG 0 (this chip) never\n"
      "elaborates the FAST_HIT logic.\n" % (len(files) - len(R16)), encoding="utf-8", newline="\n")

D = ROOT / "asic" / "soc_dm_4kb"
c = json.load(open(D / "config_R15_synth.json", encoding="utf-8"))
vf = [f.replace("/snapshots/rtl_r15/", "/snapshots/rtl_r16/") for f in c["VERILOG_FILES"]]
assert sum(1 for f in vf if "/rtl_r16/" in f) == len(vf) == len(files), (len(vf), len(files))
out = {}
for k, v in c.items():
    if k == "//EXPERIMENT":
        out[k] = ("R16 synthesis + OpenLane lint gate (2026-10-03): config_R15_synth with the R16 RTL snapshot "
                  "(rtl_r16 = rtl_r15 + the seven FAST_HIT files). Not a PD configuration.")
    elif k == "VERILOG_FILES":
        out[k] = vf
    else:
        out[k] = v
(D / "config_R16_synth.json").write_text(json.dumps(out, indent=4) + "\n", encoding="utf-8", newline="\n")
print("rtl_r16: %d files (%d from R16), config_R16_synth.json: %d VERILOG_FILES" % (len(files), len(R16), len(vf)))
