# FLOW_JOURNAL Incident 93: the patched Classic flow must still build (variable clash check) and resolve
# config_FINAL3.json with the new step gated off, and config_H1.json with it on.
import sys
from openlane.flows.classic import Classic
from openlane.steps.openroad import PostRouteHoldECO

ids = [s.id for s in Classic.Steps]
i = ids.index("OpenROAD.PostRouteHoldECO")
print("step at", i, "between", ids[i - 1], "and", ids[i + 1])
for cfg in sys.argv[1:]:
    flow = Classic(cfg, design_dir="/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb", pdk="sky130A", scl="sky130_fd_sc_hd", pdk_root="/home/toanl/.volare")
    c = flow.config
    print(cfg, "ECO_DRV", c["POST_ROUTE_ECO_REPAIR_DESIGN"], "PRE", c.get("MACRO_PIN_BUFFER_IN_PRE_CELL"), "RUN_POST_ROUTE_HOLD_ECO =", c["RUN_POST_ROUTE_HOLD_ECO"], "RUN_MACRO_PIN_BUFFERS =", c["RUN_MACRO_PIN_BUFFERS"], c.get("MACRO_PIN_BUFFER_IN_PINS"),
          "margin", c.get("POST_ROUTE_HOLD_ECO_MARGIN"), "corner", c.get("POST_ROUTE_HOLD_ECO_RCX_CORNER"))
