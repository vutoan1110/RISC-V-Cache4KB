"""FLOW_JOURNAL Incident 93: print the timeline (arrival, driving cell, net) of the worst VIOLATED path in a
q_whatif report, so the next cut point can be chosen.  usage: python worst.py w1.rpt"""
import re
import sys

txt = open(sys.argv[1], encoding="utf-8", errors="replace").read()
blocks = txt.split("Startpoint:")[1:]
for b in blocks:
    if "VIOLATED" not in b.split("slack")[-2] + b[-400:]:
        continue
    print("Startpoint:" + b.split("\n")[0])
    print(b.split("\n")[1])
    t = None
    ref = ""
    for line in b.split("\n"):
        m = re.match(r"\s*(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+[\^v]\s+(\S+)\s+\((\S+)\)", line)
        if m:
            t, ref = float(m.group(2)), m.group(4).replace("sky130_fd_sc_hd__", "")
        m2 = re.match(r"\s+(\S+) \(net\)", line)
        if m2 and t is not None:
            print("%8.3f  %-16s %s" % (t, ref, m2.group(1)))
        if "slack" in line:
            print(line.strip())
            break
    break
