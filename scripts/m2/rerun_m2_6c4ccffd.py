#!/usr/bin/env python3
"""Re-execute the review M1/M2 sweep on RTL 6c4ccffd (owner 2026-10-14: every reported number from ONE RTL).

The original sweep (results/m2, 2026-10-06) ran on R15 / R16. This driver runs the same grid twice on the live hdl/
(manifest 6c4ccffd, checked before the start) into results/m2_6c4ccffd, every pass with freshly compiled libraries
(compile scripts regenerated from the current tb/compile_active_design.do by make_compile_do.py), base and FAST_HIT
chains in parallel (4 workers each), the whole process tree at below-normal priority so the PD flows in WSL keep the
CPU. Afterwards: pass 1 vs pass 2 and 6c4ccffd vs the R15 / R16 results, every snapshot field.

    python scripts/m2/rerun_m2_6c4ccffd.py            (cooperative stop: results/m2_6c4ccffd/.abort)
"""
from __future__ import annotations

import csv
import ctypes
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "m2_6c4ccffd"
PY = sys.executable
LOGF = OUT / "driver.log"
MANIFEST = "6c4ccffd4257c224a537bd8d8e7b724ac8505bb19eb4d9e1361019af77341291"


def log(msg):
    line = "%s %s" % (time.strftime("%Y-%m-%dT%H:%M:%S"), msg)
    print(line, flush=True)
    with LOGF.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(args, tag):
    lf = OUT / ("%s.log" % tag)
    with lf.open("w", encoding="utf-8") as f:
        rc = subprocess.run([PY, str(ROOT / "scripts" / "m2" / "run_m2_sweep.py")] + args, cwd=ROOT,
                            stdout=f, stderr=subprocess.STDOUT).returncode
    log("%s rc=%d (%s)" % (tag, rc, lf.name))
    return rc


def chain(fast):
    extra = ["--fast"] if fast else []
    name = "fast" if fast else "base"
    for p in (1, 2):
        if (OUT / ".abort").exists():
            log("%s: abort flag before pass %d" % (name, p))
            return
        run(["--compile", "--workers", "4", "--pass", str(p), "--out", str(OUT)] + extra, "%s_p%d" % (name, p))
        for cl in OUT.glob("compile_m2%s_[0-9].log" % ("f" if fast else "")):   # keep each pass's fresh compile
            cl.replace(cl.with_name(cl.stem + "_p%d.log" % p))


def rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {(r["point"], r["workload"]): r for r in csv.DictReader(f)}


def compare(a, b, skip=("point", "org", "cfg", "cap_bytes", "line_bytes", "lines", "vc", "workload")):
    ra, rb = rows(a), rows(b)
    keys = sorted(set(ra) | set(rb))
    only_a = [k for k in keys if k not in rb]
    only_b = [k for k in keys if k not in ra]
    diff = []
    for k in keys:
        if k in ra and k in rb:
            for f in ra[k]:
                if f not in skip and ra[k].get(f) != rb[k].get(f):
                    diff.append((k, f, ra[k].get(f), rb[k].get(f)))
    return {"a": str(a.relative_to(ROOT)), "b": str(b.relative_to(ROOT)), "rows_a": len(ra), "rows_b": len(rb),
            "only_a": [list(k) for k in only_a][:20], "only_b": [list(k) for k in only_b][:20],
            "n_only_a": len(only_a), "n_only_b": len(only_b), "n_field_diffs": len(diff),
            "first_diffs": [[list(k), f, x, y] for k, f, x, y in diff[:20]]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)  # BELOW_NORMAL
    chk = subprocess.run([PY, str(ROOT / "scripts" / "rtl_manifest.py"), "--check"], cwd=ROOT,
                         capture_output=True, text=True)
    if "IDENTICAL" not in chk.stdout or MANIFEST[:8] not in chk.stdout:
        log("manifest check failed, not starting:\n" + chk.stdout + chk.stderr)
        return 1
    log("start: live tree = manifest %s (IDENTICAL); base and FAST chains, 2 passes each" % MANIFEST[:8])
    th = [threading.Thread(target=chain, args=(f,)) for f in (False, True)]
    for t in th:
        t.start()
    for t in th:
        t.join()
    res = {}
    for kind in ("", "fast_"):
        p1, p2 = OUT / ("sweep_%sp1.csv" % kind), OUT / ("sweep_%sp2.csv" % kind)
        old = ROOT / "results" / "m2" / ("sweep_%sp1.csv" % kind)
        if p1.is_file() and p2.is_file():
            res[(kind or "base_") + "p1_vs_p2"] = compare(p1, p2)
        if p1.is_file() and old.is_file():
            res[(kind or "base_") + "6c4ccffd_vs_old"] = compare(old, p1)
    (OUT / "comparison.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    for k, v in res.items():
        log("%s: rows %d / %d, only-old %d, only-new %d, field differences %d"
            % (k, v["rows_a"], v["rows_b"], v["n_only_a"], v["n_only_b"], v["n_field_diffs"]))
    log("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
