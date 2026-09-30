"""Side-by-side signoff metrics of PD runs (STAPostPNR state_out.json), FLOW_JOURNAL Incident 76.
    python compare_runs.py <runs dir> run1 run2 ..."""
import glob
import json
import os
import sys

base = sys.argv[1]
runs = sys.argv[2:]
keys = [("timing__setup__ws__corner:nom_tt_025C_1v80", "tt setup WS"), ("timing__setup__ws__corner:max_tt_025C_1v80", "max_tt setup"),
        ("timing__setup__ws__corner:nom_ss_100C_1v60", "nom_ss setup"), ("timing__setup__ws__corner:max_ss_100C_1v60", "max_ss setup"),
        ("timing__setup__ws__corner:min_ss_100C_1v60", "min_ss setup"), ("timing__setup_vio__count__corner:max_ss_100C_1v60", "max_ss setup vio"),
        ("timing__setup__tns__corner:max_ss_100C_1v60", "max_ss TNS"), ("timing__setup__ws__corner:min_ff_n40C_1v95", "ff setup"),
        ("timing__hold__ws", "hold WS (all)"), ("timing__hold_vio__count", "hold vio"),
        ("design__instance__area__stdcell", "stdcell area"), ("design__instance__count__stdcell", "stdcell count"),
        ("route__wirelength", "wirelength"), ("route__drc_errors", "route DRC"),
        ("design__max_slew_violation__count", "slew vio"), ("design__max_cap_violation__count", "cap vio"),
        ("design__max_fanout_violation__count", "fanout vio"), ("antenna__violating__nets", "antenna nets"),
        ("antenna__violating__pins", "antenna pins"), ("power__total", "power flow W (max_ff corner!)"),
        # FLOW_JOURNAL Incident 91: per-corner DRV at nom_tt, antenna cells, hold/setup TNS at tt
        ("design__max_slew_violation__count__corner:nom_tt_025C_1v80", "nom_tt slew vio"),
        ("design__max_cap_violation__count__corner:nom_tt_025C_1v80", "nom_tt cap vio"),
        ("design__max_fanout_violation__count__corner:nom_tt_025C_1v80", "nom_tt fanout vio"),
        ("design__instance__count__class:antenna_cell", "antenna cells"),
        ("timing__setup__ws__corner:max_ff_n40C_1v95", "max_ff setup"),
        ("timing__hold__ws__corner:max_ff_n40C_1v95", "max_ff hold"),
        ("timing__hold__ws__corner:nom_tt_025C_1v80", "nom_tt hold")]
m = {}
for r in runs:
    d = sorted(glob.glob(os.path.join(base, r, "*-openroad-stapostpnr")))
    m[r] = json.load(open(os.path.join(d[-1], "state_out.json")))["metrics"] if d else {}
fmt = "%-20s" + " %13s" * len(runs)
print(fmt % ("", *runs))
for k, l in keys:
    vals = []
    for r in runs:
        v = m[r].get(k)
        vals.append(("%.4g" % v) if isinstance(v, (int, float)) else str(v))
    print(fmt % (l, *vals))
