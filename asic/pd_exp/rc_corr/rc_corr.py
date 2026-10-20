"""FLOW_JOURNAL Incident 91: compare the resizer's wire-capacitance estimate (est.txt, report_net after
estimate_parasitics -placement with the flow's set_rc.tcl) with the signed-off RCX SPEF (spef.txt) on
the same nets.  Prints the ratio spef/est (total over nets, median, by net-size bins).
usage: python rc_corr.py est.txt spef.txt"""
import re
import sys


def load(p):
    d = {}
    cur = None
    for line in open(p):
        m = re.match(r"Net (\S+)", line)
        if m:
            cur = m.group(1)
            continue
        m = re.match(r"\s*Wire capacitance:\s+([0-9.]+(?:[eE][+-]?\d+)?)(?:-([0-9.]+(?:[eE][+-]?\d+)?))?", line)
        if m and cur:
            d[cur] = float(m.group(2) or m.group(1))
        m = re.match(r"\s*Pin capacitance:\s+([0-9.]+(?:[eE][+-]?\d+)?)(?:-([0-9.]+(?:[eE][+-]?\d+)?))?", line)
        if m and cur:
            d[cur + "#pin"] = float(m.group(2) or m.group(1))
    return d


e, s = load(sys.argv[1]), load(sys.argv[2])
nets = [n for n in e if not n.endswith("#pin") and n in s and e[n] > 0]
print("nets compared:", len(nets))
te, ts = sum(e[n] for n in nets), sum(s[n] for n in nets)
tp = sum(e.get(n + "#pin", 0) for n in nets)
r = sorted(s[n] / e[n] for n in nets)
print("total wire cap: est %.4f pF, spef %.4f pF, ratio %.3f; pin cap %.4f pF" % (te, ts, ts / te, tp))
print("per-net ratio: p10 %.2f  median %.2f  p90 %.2f" % (r[len(r) // 10], r[len(r) // 2], r[9 * len(r) // 10]))
print("total (wire+pin) load: est %.4f, spef %.4f, ratio %.3f" % (te + tp, ts + tp, (ts + tp) / (te + tp)))
for lo, hi in ((0, 0.002), (0.002, 0.01), (0.01, 0.05), (0.05, 10)):
    b = [n for n in nets if lo <= e[n] < hi]
    if b:
        print("  est wire cap in [%.3f, %.3f) pF: %5d nets, spef/est total %.3f" % (
            lo, hi, len(b), sum(s[n] for n in b) / sum(e[n] for n in b)))
