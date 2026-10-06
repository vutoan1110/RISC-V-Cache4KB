"""FLOW_JOURNAL Incident 96 (2026-10-03): sign-off gates for the gated full flows (run_gated_pd.sh).

    python3 gate_check.py <run dir> p1|p2|final
exit 0 = PASS, 1 = FAIL (one line on stdout says why), 2 = data missing (treated as FAIL by the caller).

  p1    (after OpenROAD.GlobalRouting)  G1: initial global-route overflow <= P1_MAX_OVF (500)
                                         G2: STAMidPNR-2 setup nom_tt >= P1_MIN_SETUP (+0.5 ns), hold nom_tt >= 0
  p2    (after OpenROAD.STAMidPNR-3)    G3: overflow after the post-GRT design repair re-route <= P2_MAX_OVF (2000)
                                         G4: STAMidPNR-3 setup nom_tt >= P2_MIN_SETUP (+0.3 ns), hold nom_tt >= 0
  final (after sign-off)                G6: route / Magic / KLayout DRC 0, LVS 0 (every difference count), XOR 0,
                                         illegal overlap 0, critical disconnected pins 0, antenna nets/pins 0,
                                         setup >= 0 at every tt and ff corner, hold >= 0 at EVERY corner;
                                         the ss setup slacks are printed (known negative for all three designs,
                                         DM signed-off max_ss -7.365 ns) and only fail the gate with FINAL_SS=1.
The mid-PnR gates use only the tt corner: STAMidPNR ss/ff numbers are stale pre-PnR values (memory note).
Thresholds can be overridden with the environment variables named above.
"""
import glob
import json
import os
import re
import sys

run, gate = sys.argv[1], sys.argv[2]
E = os.environ


def thr(name, default):
    return float(E.get(name, default))


def step_dir(pattern):
    c = sorted(glob.glob(os.path.join(run, pattern)), key=lambda p: int(os.path.basename(p).split("-")[0]))
    return c[-1] if c else None


def metrics_of(d):
    try:
        return json.load(open(os.path.join(d, "state_out.json")))["metrics"]
    except Exception:
        return None


def last_total_overflow(log):
    v = None
    for ln in open(log, errors="replace"):
        if ln.startswith("Total "):
            v = int(ln.split()[-1])
    return v


def out(ok, msg):
    print(("PASS " if ok else "FAIL ") + gate + ": " + msg)
    sys.exit(0 if ok else 1)


if gate == "p1":
    g = step_dir("*-openroad-globalrouting")
    s2 = step_dir("*-openroad-stamidpnr-2")
    if not g or not s2 or metrics_of(s2) is None:
        print("MISSING p1 data")
        sys.exit(2)
    ovf = last_total_overflow(os.path.join(g, "openroad-globalrouting.log"))
    m = metrics_of(s2)
    su, ho = m["timing__setup__ws__corner:nom_tt_025C_1v80"], m["timing__hold__ws__corner:nom_tt_025C_1v80"]
    msg = "GRT overflow %s (max %d), STAMidPNR-2 setup nom_tt %.3f (min %.2f), hold nom_tt %.3f" % (
        ovf, thr("P1_MAX_OVF", 500), su, thr("P1_MIN_SETUP", 0.5), ho)
    out(ovf is not None and ovf <= thr("P1_MAX_OVF", 500) and su >= thr("P1_MIN_SETUP", 0.5) and ho >= 0, msg)

if gate == "p2":
    r = step_dir("*-openroad-repairdesignpostgrt")
    s3 = step_dir("*-openroad-stamidpnr-3")
    if not r or not s3 or metrics_of(s3) is None:
        print("MISSING p2 data")
        sys.exit(2)
    ovf = last_total_overflow(os.path.join(r, "openroad-repairdesignpostgrt.log"))
    m = metrics_of(s3)
    su, ho = m["timing__setup__ws__corner:nom_tt_025C_1v80"], m["timing__hold__ws__corner:nom_tt_025C_1v80"]
    msg = "post-GRT-repair overflow %s (max %d), STAMidPNR-3 setup nom_tt %.3f (min %.2f), hold nom_tt %.3f" % (
        ovf, thr("P2_MAX_OVF", 2000), su, thr("P2_MIN_SETUP", 0.3), ho)
    out(ovf is not None and ovf <= thr("P2_MAX_OVF", 2000) and su >= thr("P2_MIN_SETUP", 0.3) and ho >= 0, msg)

if gate == "final":
    m = {}
    for so in sorted(glob.glob(os.path.join(run, "*", "state_out.json")),
                     key=lambda p: int(os.path.basename(os.path.dirname(p)).split("-")[0])):
        try:
            m.update(json.load(open(so)).get("metrics", {}))
        except Exception:
            pass
    need_zero = ["route__drc_errors", "magic__drc_error__count", "klayout__drc_error__count",
                 "design__lvs_error__count", "design__lvs_device_difference__count",
                 "design__lvs_net_difference__count", "design__lvs_property_fail__count",
                 "design__lvs_unmatched_device__count", "design__lvs_unmatched_net__count",
                 "design__lvs_unmatched_pin__count", "design__xor_difference__count",
                 "magic__illegal_overlap__count", "design__critical_disconnected_pin__count",
                 "antenna__violating__nets", "antenna__violating__pins"]
    bad = []
    for k in need_zero:
        if k not in m:
            bad.append(k + "=missing")
        elif m[k] != 0:
            bad.append("%s=%s" % (k, m[k]))
    corners = sorted(k.split(":", 1)[1] for k in m if k.startswith("timing__setup__ws__corner:"))
    ss = []
    for c in corners:
        su, ho = m["timing__setup__ws__corner:" + c], m.get("timing__hold__ws__corner:" + c)
        if ho is None or ho < 0:
            bad.append("hold %s=%s" % (c, ho))
        if "_ss_" in c:
            ss.append("%s %.3f" % (c, su))
            if E.get("FINAL_SS") == "1" and su < 0:
                bad.append("setup %s=%.3f" % (c, su))
        elif su < 0:
            bad.append("setup %s=%.3f" % (c, su))
    if len(corners) < 9:
        bad.append("only %d corners" % len(corners))
    out(not bad, ("clean; " if not bad else "; ".join(bad) + "; ") + "ss setup (reported, not gated): " + ", ".join(ss))

print("unknown gate " + gate)
sys.exit(2)
