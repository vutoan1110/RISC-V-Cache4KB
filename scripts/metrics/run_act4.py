#!/usr/bin/env python3
"""ACT4 architectural tests on the active RTL, twice (review item A7: "ACT4 logs were not archived").

Suite: riscv-arch-test (ACT4 framework) built for I + Zmmul, unprivileged, by
verification/architecture/act4_rv32i_zmmul (config files used from an LF copy: the repo copies are CRLF),
reference model Spike -> 43 self-checking ELFs under verification/results/act4/work/rv32i-zmmul/elfs.
Procedure and PASS criterion are those of verification/architecture/act4_rv32i_zmmul/run_act4_dut.py and
verification/architecture/run_signature.py: ELF -> flat binary -> word hex at rvtest_entry_point, run on
tb_architecture_signature; the test checks its own results and stores the verdict to tohost, where the bench
finishes on the pass code and $fatal's on a failure code; the signature region is dumped. Two differences:
the library is work_act4 (scripts/metrics/compile_act4.do), so the run never collides with a batch in work,
and the installed Questa is used. Every test runs twice; the two signature sets must be byte-identical.

    python scripts/metrics/run_act4.py   -> verification/results/act4/dut_p{1,2}/, results/act4_summary.json
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "verification/results/act4/work/rv32i-zmmul/elfs"
OUT = ROOT / "verification/results/act4"
VSIM = r"C:/questasim64_2024.1/win64/vsim.exe"
BIN_TO_HEX = ROOT / "verification/scripts/bin_to_word_hex.py"
TOOLS = "/home/toanl/tools/riscv-gcc16/bin/riscv64-unknown-elf-"
FAIL_RE = re.compile(r"^\s*#?\s*(?:\*\*\s+(?:fatal|error):|\[FAIL\])|^\s*#?\s*Errors:\s*[1-9]",
                     re.IGNORECASE | re.MULTILINE)


def wsl_path(p: Path) -> str:
    p = p.resolve()
    return "/mnt/%s%s" % (p.drive[0].lower(), p.as_posix()[2:])


def wsl(*args: str) -> str:
    return subprocess.run(["wsl.exe", "-d", "Ubuntu", "--", *args], text=True, check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout


def symbols(elf: Path) -> dict[str, int]:
    want = {"rvtest_entry_point", "begin_signature", "end_signature", "tohost"}
    got = {}
    for line in wsl(TOOLS + "nm", "-n", wsl_path(elf)).splitlines():
        f = line.split()
        if len(f) >= 3 and f[-1] in want:
            got[f[-1]] = int(f[0], 16)
    if want - got.keys():
        raise RuntimeError("missing symbols %s" % sorted(want - got.keys()))
    return got


def vsim(do: str, log: Path) -> str:
    r = subprocess.run([VSIM, "-c", "-do", do], cwd=ROOT, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    t = r.stdout or ""
    log.write_text(t, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError("vsim exit %d" % r.returncode)
    return t


def run_pass(n: int, elfs: list[Path], images: Path) -> dict:
    out = OUT / ("dut_p%d" % n)
    (out / "logs").mkdir(parents=True, exist_ok=True)
    (out / "signatures").mkdir(parents=True, exist_ok=True)
    t = vsim("do scripts/metrics/compile_act4.do; quit -f", out / "compile.log")
    if FAIL_RE.search(t) or "[PASS] Active RTL" not in t:
        raise SystemExit("[FAIL] compile, see %s" % (out / "compile.log"))
    results = []
    for i, elf in enumerate(elfs, 1):
        rel = elf.relative_to(SUITE)
        tid = "__".join(rel.with_suffix("").parts)
        rec = {"test": rel.as_posix(), "extension": rel.parts[-2], "status": "FAIL"}
        t0 = time.time()
        try:
            hexf = images / (tid + ".hex")
            if not hexf.exists():
                sym = symbols(elf)
                binf = images / (tid + ".bin")
                wsl(TOOLS + "objcopy", "-O", "binary", wsl_path(elf), wsl_path(binf))
                subprocess.run([sys.executable, str(BIN_TO_HEX), str(binf), str(hexf),
                                "--base-address", hex(sym["rvtest_entry_point"])],
                               cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                (images / (tid + ".sym.json")).write_text(json.dumps(sym))
            sym = json.loads((images / (tid + ".sym.json")).read_text())
            sig = out / "signatures" / (tid + ".signature")
            do = ("vsim -onfinish stop -voptargs=+acc work_act4.tb_architecture_signature "
                  "+HEX=%s +SIGNATURE=%s +SIG_BEGIN=%08x +SIG_END=%08x +TOHOST_ADDR=%08x +MAX_CYCLES=2000000; "
                  "run -all; quit -f" % (hexf.as_posix(), sig.as_posix(), sym["begin_signature"],
                                         sym["end_signature"], sym["tohost"]))
            t = vsim(do, out / "logs" / (tid + ".log"))
            if FAIL_RE.search(t):
                raise RuntimeError("fatal/error/fail marker in transcript")
            m = re.search(r"\[PASS\] Signature harness\s+(\S+)\s+retirements=(\d+)\s+cycles=(\d+)", t)
            if not m:
                raise RuntimeError("PASS marker absent")
            rec.update(status="PASS", finish=m.group(1), retirements=int(m.group(2)), cycles=int(m.group(3)))
        except Exception as exc:   # keep going: the whole failing set is the result
            rec["error"] = str(exc)
        rec["seconds"] = round(time.time() - t0, 2)
        results.append(rec)
        print("[%s] p%d %02d/%02d %s %s" % (rec["status"], n, i, len(elfs), rec["test"],
                                           rec.get("finish", rec.get("error", ""))), flush=True)
    passed = sum(r["status"] == "PASS" for r in results)
    summary = {"pass": n, "total": len(results), "passed": passed, "failed": len(results) - passed,
               "results": results}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    elfs = sorted(SUITE.rglob("*.elf"))
    if not elfs:
        raise SystemExit("no ELF below %s" % SUITE)
    images = OUT / "images"
    images.mkdir(parents=True, exist_ok=True)
    s1 = run_pass(1, elfs, images)
    s2 = run_pass(2, elfs, images)
    same = []
    for r in s1["results"]:
        tid = "__".join(Path(r["test"]).with_suffix("").parts)
        a = OUT / "dut_p1" / "signatures" / (tid + ".signature")
        b = OUT / "dut_p2" / "signatures" / (tid + ".signature")
        same.append(a.is_file() and b.is_file() and a.read_bytes() == b.read_bytes())
    by_ext = {}
    for r in s1["results"]:
        e = by_ext.setdefault(r["extension"], {"total": 0, "passed": 0})
        e["total"] += 1
        e["passed"] += r["status"] == "PASS"
    summary = {"suite": "riscv-arch-test ACT4, I + Zmmul, unprivileged, reference Spike",
               "elfs": len(elfs), "pass1": s1["passed"], "pass2": s2["passed"],
               "signatures_identical_p1_p2": sum(same), "by_extension": by_ext}
    (ROOT / "results" / "act4_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    ok = s1["passed"] == s2["passed"] == len(elfs) and all(same)
    print("[%s] ACT4 %d/%d pass 1, %d/%d pass 2, signatures identical %d/%d"
          % ("PASS" if ok else "FAIL", s1["passed"], len(elfs), s2["passed"], len(elfs), sum(same), len(elfs)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
