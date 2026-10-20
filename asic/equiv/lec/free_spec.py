"""Base spec for a step-B LEC pair (2026-10-13; the inline one-liner of run_lec_r14.ps1 -Step B as a file, so it can run
pinned): no constants, no duplicates, every flop that exists only on the first side left free.
usage: python free_spec.py pairs.json spec.json"""
import json
import sys

P = json.load(open(sys.argv[1]))
json.dump({"const": {}, "dup": {}, "free": list(range(len(P["gold_only"])))}, open(sys.argv[2], "w"))
print("free spec: %d first-side-only flops left free" % len(P["gold_only"]))
