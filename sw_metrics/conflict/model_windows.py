#!/usr/bin/env python3
"""Per-window cross-check of the extended conflict probe against the independent cache model.

Replays the D-cache trace of tb_conflict_probe (+trace=...) through scripts/cache_model.py's Cache (written from the
organizations' specification, not from the RTL; the DM D-cache's L0 modelled for configuration 0), resetting the
counts at every MARK CLEAR, and compares each window's main hits / victim hits / true misses / reads / writes with
the CPROBE_WINDOW line the RTL counters produced. Writes one CSV row per window.

    python sw_metrics/conflict/model_windows.py <sim log> <trace> <config> <lines> <out.csv>
exit 0 only if every window matches exactly.
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from cache_model import CONFIGS, Cache  # noqa: E402

TABLE = [(0, 1, 1, 64), (0, 1, 2, 64), (0, 1, 3, 64), (0, 1, 4, 64), (0, 1, 5, 64), (0, 1, 6, 64), (0, 1, 7, 64),
         (0, 1, 8, 64),
         (0, 2, 2, 32), (0, 3, 2, 32), (0, 4, 2, 32), (0, 5, 2, 32), (0, 6, 2, 32), (0, 8, 2, 32), (0, 16, 2, 32),
         (0, 32, 2, 32),
         (0, 2, 3, 32), (0, 3, 3, 32), (0, 4, 3, 32), (0, 8, 3, 32),
         (0, 2, 4, 16), (0, 4, 4, 16), (0, 8, 4, 16),
         (1, 1, 4, 64), (1, 1, 8, 64), (1, 5, 2, 32), (1, 6, 2, 32), (1, 8, 2, 32), (1, 16, 2, 32),
         (2, 1, 2, 32), (2, 4, 2, 32), (2, 5, 2, 32),
         (3, 1, 2, 32), (3, 8, 2, 32),
         (4, 4, 2, 32)]          # conflict_probe.c table[], id = index + 1
MODES = {0: "cyclic read", 1: "random read", 2: "read-modify-write", 3: "read line 0, write others", 4: "write only"}

log, trace, cfg, lines, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
spec = CONFIGS[cfg]
d = Cache(lines, 16, spec["ways"], spec["victim"], write_allocate=False, dm_l0=(cfg == 0))

model = []
counting = False
for line in open(trace):
    if line.startswith("MARK CLEAR"):
        if counting:
            model.append((d.main_hit, d.victim_hit, d.true_miss, d.reads, d.writes))
        d.reset_counts()
        counting = True
        continue
    p = line.split()
    if p and p[0] == "D":
        d.access(int(p[1], 16), p[2] == "1", counted=(p[3] == "1"))
if counting:
    model.append((d.main_hit, d.victim_hit, d.true_miss, d.reads, d.writes))

rtl = []
for m in re.finditer(r"CPROBE_WINDOW (.*)", open(log, errors="ignore").read()):
    rtl.append(dict(kv.split("=") for kv in m.group(1).split()))
if not re.search(r"\[PASS\] CPROBE", open(log, errors="ignore").read()):
    sys.exit("[FAIL] %s: run did not pass" % log)
if len(rtl) != len(model):
    sys.exit("[FAIL] %d RTL windows, %d model windows" % (len(rtl), len(model)))

bad = 0
rows = []
for r, m in zip(rtl, model):
    i = int(r["id"])
    mode, S, N, P = TABLE[i - 1]
    got = (int(r["d_main"]), int(r["d_victim"]), int(r["d_miss"]), int(r["d_read"]), int(r["d_write"]))
    ok = got == m
    bad += not ok
    acc = got[3] + got[4]
    rows.append(dict(config=spec["name"], lines=lines, id=i, mode=MODES[mode], S=S, N=N, P=P, d_read=got[3],
                     d_write=got[4], d_main=got[0], d_victim=got[1], d_miss=got[2],
                     hit_pct="%.2f" % (100.0 * (got[0] + got[1]) / acc), d_rd_hit=r["d_rd_hit"],
                     d_rd_miss=r["d_rd_miss"], d_wr_hit=r["d_wr_hit"], d_wr_miss=r["d_wr_miss"],
                     axi_read=r["axi_read"], axi_write=r["axi_write"], mcycle=r["mcycle"],
                     cycles_per_access="%.3f" % (int(r["mcycle"]) / acc),
                     model_main=m[0], model_victim=m[1], model_miss=m[2], model_match="EXACT" if ok else "DIFF"))
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print("%s %s lines=%d: %d windows, %d exact, %d differ" % ("[PASS]" if not bad else "[FAIL]", spec["name"], lines,
                                                             len(rows), len(rows) - bad, bad))
sys.exit(1 if bad else 0)
