"""Shared input checks and tool execution for current-RTL board preparation."""
from __future__ import annotations

import ctypes
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POINTS = {"dm_4kb": "DM", "sa2_4kb": "SA2", "vc4_4kb": "DM_VC4", "dse_4kb": "DM_DSE"}
UP = "aha-mont64 crc32 depthconv edn huffbench matmult-int md5sum nettle-sha256 slre statemate tarfind ud".split()
MIFS = [ROOT / "hdl" / f"riscv_full_byte{i}.mif" for i in range(4)]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def stamp():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def manifest():
    p = ROOT / "results/rtl_manifest.json"
    m = json.loads(p.read_text(encoding="utf-8"))
    bad = [rel for rel, digest in m["files"].items() if sha(ROOT / rel) != digest]
    if bad:
        raise RuntimeError("Frozen manifest differs: " + ", ".join(bad))
    return m


def free_mb():
    class Status(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
            (n, ctypes.c_ulonglong) for n in
            ("total", "avail", "page_total", "page_avail", "virtual_total", "virtual_avail", "ext")]
    s = Status()
    s.length = ctypes.sizeof(s)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s)):
        raise RuntimeError("Cannot read Windows free memory")
    return s.avail // (1024 * 1024)


def check_idle():
    p = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True, check=True)
    if re.search(r'"quartus_(?:map|fit|sta|asm|cdb|pow|sh)\.exe"', p.stdout, re.I):
        raise RuntimeError("Another Quartus job is running; database use must be sequential")


def checked_tool(cmd, log, retries=3):
    """Retry only independently recognisable native crashes; stop on other failures."""
    log = Path(log)
    log.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, retries + 1):
        with log.open("wb") as f:
            p = subprocess.run(cmd, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT, timeout=7200)
        if p.returncode == 0:
            return
        kept = log.with_name(f"{log.stem}.attempt{attempt}.failed{log.suffix}")
        shutil.copy2(log, kept)
        txt = kept.read_text(encoding="utf-8", errors="replace")
        crash = (p.returncode & 0xffffffff) in (0xc0000005, 0xc000001d, 0xc0000409)
        crash = crash or bool(re.search(r"EXCEPTION_ACCESS_VIOLATION|Segmentation fault|signal 11", txt, re.I))
        if not crash or attempt == retries:
            raise RuntimeError(f"Tool failed rc={p.returncode}; inspect {kept}; no automatic deterministic retry")
        with (ROOT / "asic/gated_pd.log").open("a", encoding="ascii") as f:
            f.write(f"{stamp()} NOTE board_prepare {Path(cmd[0]).name} native crash rc={p.returncode}; "
                    f"evidence {kept.relative_to(ROOT).as_posix()}; retry same inputs\n")
        print(f"[NOTE] native crash; retry same inputs: {kept.name}", flush=True)
        time.sleep(5)


def validate_pair(a, b, keys, ignore=("seconds",)):
    import csv
    def load(p):
        with Path(p).open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        out = {tuple(r[k] for k in keys): r for r in rows}
        if not rows or len(out) != len(rows):
            raise RuntimeError(f"Empty or duplicate keys: {p}")
        return out
    x, y = load(a), load(b)
    if x.keys() != y.keys():
        raise RuntimeError(f"Unpaired rows: {a}, {b}")
    for k in x:
        if x[k].keys() != y[k].keys():
            raise RuntimeError(f"Column mismatch: {k}")
        diff = [c for c in x[k] if c not in ignore and x[k][c] != y[k][c]]
        if diff:
            raise RuntimeError(f"Mismatch {k}: {diff}")
    return x
