"""FLOW_JOURNAL Incident 96 (2026-10-03): sign-off gates for the gated full flows (run_gated_pd.sh).

    python3 gate_check.py <run dir> p1|p2|final
exit 0 = PASS, 1 = FAIL (one line on stdout says why), 2 = data missing (treated as FAIL by the caller).

  p1    (after OpenROAD.GlobalRouting)  G1: initial global-route overflow <= P1_MAX_OVF (500)
                                         G2: STAMidPNR-2 setup nom_tt >= P1_MIN_SETUP (+0.5 ns), hold nom_tt >= 0
  p2    (after OpenROAD.STAMidPNR-3)    G3: overflow after the post-GRT design repair re-route <= P2_MAX_OVF (2000)
                                         G4: STAMidPNR-3 setup nom_tt >= P2_MIN_SETUP (+0.3 ns), hold nom_tt >= P2_MIN_HOLD (0)
  final (after sign-off)                G6: route / Magic / KLayout DRC 0, LVS 0 (every difference count), XOR 0,
                                         illegal overlap 0, critical disconnected pins 0, antenna nets/pins 0,
                                         setup >= 0 at every tt and ff corner, hold >= 0 at EVERY corner;
                                         the ss setup slacks are printed (known negative for all three designs,
                                         DM signed-off max_ss -7.365 ns) and only fail the gate with FINAL_SS=1.
The mid-PnR gates use only the tt corner: STAMidPNR ss/ff numbers are stale pre-PnR values (memory note).
Thresholds can be overridden with the environment variables named above.
P2_INITIAL_GRT_FALLBACK=1 enables the T9 reader fix when resolved.json explicitly
disables RUN_POST_GRT_DESIGN_REPAIR. The last post-GRT reroute is still used when
present, otherwise the initial GlobalRouting overflow is read. Off by default;
no setup, hold, overflow or final sign-off threshold changes.
P2_MIN_HOLD (2026-10-13, default 0 = unchanged): for recipes whose hold is repaired after routing
(RUN_POST_ROUTE_HOLD_ECO, SA2 / DM_VC4), the p2 hold bound is declared at launch instead of logging a
CONTINUE after a p2 FAIL, because a run may not be continued after a failed gate. The final gate is unchanged.
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

def post_grt_overflows():
    """Every global-route 'Total' overflow written after OpenROAD.GlobalRouting and before STAMidPNR-3, in flow
    order (RepairDesignPostGRT, the RepairAntennas sub-steps, ResizerTimingPostGRT ...). The last one is the routing
    detailed routing starts from. 2026-10-06: G3 first read only RepairDesignPostGRT, whose INCREMENTAL re-route
    said 68 / 6 for the two DM_VC4 runs, while the from-scratch re-route inside RepairAntennas said 19,114 / 11,485."""
    g = step_dir("*-openroad-globalrouting")
    s3 = step_dir("*-openroad-stamidpnr-3")
    lo = int(os.path.basename(g).split("-")[0]) if g else 0
    hi = int(os.path.basename(s3).split("-")[0]) if s3 else 10 ** 6
    steps = sorted((d for d in glob.glob(os.path.join(run, "[0-9]*-*")) if os.path.isdir(d)
                    and lo < int(os.path.basename(d).split("-")[0]) < hi),
                   key=lambda p: int(os.path.basename(p).split("-")[0]))
    vals = []
    for d in steps:
        logs = sorted(glob.glob(os.path.join(d, "*.log")) + glob.glob(os.path.join(d, "[0-9]*-*", "*.log")),
                      key=lambda p: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", os.path.relpath(p, d))])
        for lg in logs:
            for ln in open(lg, errors="replace"):
                if ln.startswith("Total "):
                    try:
                        vals.append(int(ln.split()[-1]))
                    except ValueError:
                        pass
    return vals


if gate == "p2":
    r = step_dir("*-openroad-repairdesignpostgrt")
    s3 = step_dir("*-openroad-stamidpnr-3")
    fallback = False
    if not r and E.get("P2_INITIAL_GRT_FALLBACK") == "1":
        try:
            config = json.load(open(os.path.join(run, "resolved.json")))
            fallback = config.get("RUN_POST_GRT_DESIGN_REPAIR") is False
        except (OSError, ValueError):
            pass
    if (not r and not fallback) or not s3 or metrics_of(s3) is None:
        print("MISSING p2 data")
        sys.exit(2)
    g = step_dir("*-openroad-globalrouting") if fallback else None
    if fallback and (not g or metrics_of(g) is None or
                     int(os.path.basename(g).split("-")[0]) >= int(os.path.basename(s3).split("-")[0])):
        print("MISSING p2 data (no completed GlobalRouting before STAMidPNR-3)")
        sys.exit(2)
    allv = post_grt_overflows()
    if fallback:
        log = os.path.join(g, "openroad-globalrouting.log")
        if not allv and not os.path.isfile(log):
            print("MISSING p2 data (initial GlobalRouting overflow log)")
            sys.exit(2)
        ovf = allv[-1] if allv else last_total_overflow(log)
        source = "last post-GRT reroute" if allv else "initial GlobalRouting"
        label = "%s overflow (RUN_POST_GRT_DESIGN_REPAIR=false)" % source
    else:
        ovf = allv[-1] if allv else last_total_overflow(os.path.join(r, "openroad-repairdesignpostgrt.log"))
        label = "post-GRT-repair overflow"
    m = metrics_of(s3)
    su, ho = m["timing__setup__ws__corner:nom_tt_025C_1v80"], m["timing__hold__ws__corner:nom_tt_025C_1v80"]
    msg = ("%s %s (last global route before DRT; max %d; all post-GRT reports %s), "
           "STAMidPNR-3 setup nom_tt %.3f (min %.2f), hold nom_tt %.3f (min %.2f)" % (
               label, ovf, thr("P2_MAX_OVF", 2000), allv, su, thr("P2_MIN_SETUP", 0.3), ho, thr("P2_MIN_HOLD", 0)))
    out(ovf is not None and ovf <= thr("P2_MAX_OVF", 2000) and su >= thr("P2_MIN_SETUP", 0.3)
        and ho >= thr("P2_MIN_HOLD", 0), msg)

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
