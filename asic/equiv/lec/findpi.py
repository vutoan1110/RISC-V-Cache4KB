"""FLOW_JOURNAL Incident 89: find the LEC input (lec_q_pNNNNN) of registers by RTL-name suffix.
usage: python findpi.py pairs.json suffix [suffix ...]"""
import json
import sys

P = json.load(open(sys.argv[1]))
for s in sys.argv[2:]:
    for k, (i, j) in enumerate(P["pairs"]):
        if any(n.endswith(s) for n in P["gold"][i]["names"]):
            print("%-34s lec_q_p%05d  %s" % (s, k, P["gold"][i]["names"][0]))
