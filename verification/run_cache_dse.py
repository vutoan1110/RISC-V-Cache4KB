#!/usr/bin/env python3
"""Unified cache-DSE ModelSim/Quartus entry point."""
from __future__ import annotations
import argparse, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VSIM=Path(r"D:\altera\modelsim\modelsim_ase\win32aloem\vsim.exe")
QUARTUS=Path(r"D:\altera\quartus\bin64\quartus_sh.exe")

def run(cmd:list[str])->None:
    print("+"," ".join(cmd));subprocess.run(cmd,cwd=ROOT,check=True)

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--all",action="store_true")
    ap.add_argument("--unit",action="store_true");ap.add_argument("--equivalence",action="store_true")
    ap.add_argument("--legacy",action="store_true");ap.add_argument("--quartus",action="store_true")
    args=ap.parse_args()
    if not any(vars(args).values()):ap.error("select --unit, --equivalence, --legacy, --quartus, or --all")
    if args.all or args.unit or args.equivalence:
        if not VSIM.exists():raise SystemExit(f"ModelSim not found: {VSIM}")
        run([str(VSIM),"-c","-do","do tb/run_cache_regression.do; quit -f"])
    if args.all or args.legacy:
        run([str(VSIM),"-c","-do","do tb/run_full_regression.do; quit -f"])
    if args.all or args.quartus:
        if not QUARTUS.exists():raise SystemExit(f"Quartus not found: {QUARTUS}")
        for project in (
            "quartus/experiments/cache_dse/soc_top_cache_dm",
            "quartus/experiments/cache_dse/soc_top_cache_sa2",
            "quartus/experiments/cache_dse/soc_top_cache_dm_vc4",
        ):
            run([str(QUARTUS),"--flow","compile",project])
    print("[PASS] Requested cache-DSE regression layers completed")
    return 0
if __name__=="__main__":raise SystemExit(main())
