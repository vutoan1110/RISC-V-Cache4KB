"""DM_VC4 placement-density variants on the wide floorplan (2026-10-03, FLOW_JOURNAL Incident 96).
vc4F_A (config_wide.json, density 42) overflows global routing by 34,086 even with GRT_ALLOW_CONGESTION. The
block-traffic analysis (scratchpad block_traffic.py) puts the extra wire inside the two tag-array clusters
(nets >= 500 um: I$+D$ tag 1,516 mm vs DM 231 mm). Lowering the global-placement density spreads those clusters,
which lowers wire demand per area roughly as 1/sqrt(area). These configs are config_wide.json with only
PL_TARGET_DENSITY_PCT changed; they are run from the post-synthesis state of vc4F_A (step 12) to detailed
placement, then ranked with route_proxy.py against SA2-wide (routes) and VC4-wide (fails)."""
import json

A = "E:/Projects/RISCV-research/asic/soc_vc4_4kb/"
base = json.load(open(A + "config_wide.json", encoding="utf-8"))
for d in (36, 32, 28):
    c = dict(base)
    c["//EXPLORATION"] = ("2026-10-03 DM_VC4 density sweep on the wide floorplan: config_wide.json with "
                          "PL_TARGET_DENSITY_PCT %d instead of 42 (vc4F_A at 42: GRT overflow 34,086). "
                          "Exploration only (run from vc4F_A step 12 state to detailed placement)." % d)
    c["PL_TARGET_DENSITY_PCT"] = d
    c["//PL_TARGET_DENSITY_PCT"] = "%d for the density sweep (see //EXPLORATION)." % d
    open(A + "config_xd%d.json" % d, "w", encoding="utf-8", newline="\n").write(
        json.dumps(c, indent=4, ensure_ascii=True) + "\n")
    print("wrote config_xd%d.json" % d)
