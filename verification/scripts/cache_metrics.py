#!/usr/bin/env python3
"""Derive paper metrics from a raw benchmark CSV without hardware dividers."""
from __future__ import annotations
import argparse, csv
from pathlib import Path

REQUIRED = ["config","benchmark","mcycle","minstret","I_access","I_main_hit",
            "I_victim_hit","I_true_miss","D_access","D_main_hit","D_victim_hit",
            "D_true_miss","I_wait_cycles","D_wait_cycles","branch_count","mispredict_count"]

def ratio(n: int, d: int, scale: float=1.0) -> str:
    return "NA" if d == 0 else f"{n*scale/d:.6f}"

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("input",type=Path);ap.add_argument("output",type=Path)
    args=ap.parse_args()
    with args.input.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    if not rows: raise SystemExit("input CSV has no rows")
    missing=[c for c in REQUIRED if c not in rows[0]]
    if missing: raise SystemExit("missing columns: "+", ".join(missing))
    out=[]
    for row in rows:
        v={k:int(row[k],0) for k in REQUIRED if k not in ("config","benchmark")}
        row.update({
            "CPI":ratio(v["mcycle"],v["minstret"]),
            "I_MPKI":ratio(v["I_true_miss"],v["minstret"],1000.0),
            "D_MPKI":ratio(v["D_true_miss"],v["minstret"],1000.0),
            "I_victim_rescue_rate":ratio(v["I_victim_hit"],v["I_victim_hit"]+v["I_true_miss"]),
            "D_victim_rescue_rate":ratio(v["D_victim_hit"],v["D_victim_hit"]+v["D_true_miss"]),
        });out.append(row)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    fields=list(out[0]);
    with args.output.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
    print(f"[PASS] wrote {args.output}")
    return 0
if __name__=="__main__": raise SystemExit(main())
