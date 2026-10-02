"""Interrupt latency / context-switch table from the tb_irq_metrics logs (metric expansion, 2026-09-30).

Each IRQ_SAMPLE line is one machine-timer interrupt (sw_metrics/irq/tb_irq_metrics.sv):
  entry   = cycles from the timer line rising to the first handler instruction retiring
  accept  = cycles from the line rising to irq_accept (fetch redirected to mtvec)
  handler = first handler instruction retired -> mret retired
  resume  = mret retired -> first interrupted instruction retired
  total   = line rising -> first interrupted instruction retired (the whole interruption)
Phases (irq_bench.c): 1 irq_min + register work, 2 irq_ctx + register work, 3 irq_min + memory-bound
work (6 KiB walk, misses in a 4 KiB D-cache), 4 irq_ctx + memory-bound work.
The simulation is deterministic, so pass 1 and pass 2 must give identical sample lists; any difference
fails the table. Output: results/irq_metrics.csv (one row per configuration and phase).

    python scripts/metrics/irq_metrics_table.py [--configs 0,1,2,3]
"""
import argparse
import csv
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "results" / "irq_metrics"
NAMES = {0: "DM", 1: "SA2", 2: "DM_VC4", 3: "DM_DSE", 4: "SA4", 5: "SA2N"}
PHASES = {1: ("irq_min", "register"), 2: ("irq_ctx", "register"),
          3: ("irq_min", "memory"), 4: ("irq_ctx", "memory")}
SAMPLE = re.compile(r"IRQ_SAMPLE cfg=(\d+) phase=(\d+) n=(\d+) accept=(-?\d+) entry=(-?\d+) "
                    r"handler=(-?\d+) resume=(-?\d+) total=(-?\d+)")
FIELDS = ("accept", "entry", "handler", "resume", "total")


def load(log):
    txt = log.read_text(errors="replace")
    if "[PASS] IRQ_METRICS" not in txt or "Fatal" in txt:
        return None
    return [tuple(int(x) for x in m.groups()) for m in SAMPLE.finditer(txt)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", default="0,1,2,3")
    args = ap.parse_args()
    rows, bad = [], []
    for cfg in [int(c) for c in args.configs.split(",")]:
        s1 = load(LOGS / ("cfg%d_p1.log" % cfg))
        s2 = load(LOGS / ("cfg%d_p2.log" % cfg))
        if s1 is None or s2 is None:
            bad.append("cfg %d: a pass did not finish with [PASS] IRQ_METRICS" % cfg)
            continue
        if s1 != s2:
            bad.append("cfg %d: pass 1 and pass 2 sample lists differ" % cfg)
        for ph, (handler, work) in PHASES.items():
            smp = [s for s in s1 if s[1] == ph]
            row = {"config": NAMES.get(cfg, str(cfg)), "config_id": cfg, "phase": ph,
                   "handler": handler, "workload": work, "samples": len(smp)}
            for i, f in enumerate(FIELDS):
                vals = [s[3 + i] for s in smp]
                row[f + "_min"] = min(vals)
                row[f + "_median"] = statistics.median(vals)
                row[f + "_max"] = max(vals)
            # the first interrupt of each phase runs a cold handler (I-cache miss); report it apart
            row["entry_first"] = smp[0][4] if smp else ""
            row["total_first"] = smp[0][7] if smp else ""
            rows.append(row)
            print("%-7s phase %d %-7s %-8s n=%3d  entry %3s/%5s/%3s  handler %4s/%6s/%4s  total %4s/%6s/%4s  (min/median/max)"
                  % (row["config"], ph, handler, work, len(smp),
                     row["entry_min"], row["entry_median"], row["entry_max"],
                     row["handler_min"], row["handler_median"], row["handler_max"],
                     row["total_min"], row["total_median"], row["total_max"]))
    out = ROOT / "results" / "irq_metrics.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        cols = list(rows[0].keys()) if rows else ["config"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    for b in bad:
        print("[FAIL] " + b)
    print("[%s] %d row(s) -> %s" % ("PASS" if not bad else "FAIL", len(rows), out))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
