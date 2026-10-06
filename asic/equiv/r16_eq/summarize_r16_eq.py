"""R16 formal checks: verdicts re-derived from the equiv_status evidence (*.status) of every check.

The first runners (run_r16_eq_mod.sh as generated before 2026-10-03 09:40) looked for 'Found [0-9]+ unproven',
which never matches equiv_status's "Found a total of M unproven $equiv cells.", so their summary line reads
unproven=0 / FAIL for every negative control. The yosys runs themselves are unaffected; this script reads the
status files they wrote and decides:
  expect-equivalent  PASS iff yosys rc = 0 (equiv_status -assert) AND "M are unproven" with M = 0
  negative-control   PASS iff M > 0 (the method sees the FAST_HIT=1 change), and lists the unproven signals.
                     That list is NOT the full set of differing signals: equiv_induct assumes EVERY $equiv cell of
                     its workset (the failing ones included) in the earlier time steps, so with rsp_valid assumed
                     equal it "proves" e.g. state[1], which equiv_simple correctly failed (FAST_HIT=1 skips
                     ST_HIT_RESP). Per-signal results of equiv_induct are sound only when the whole workset is proven,
                     i.e. for the expect-equivalent checks with M = 0.

    python asic/equiv/r16_eq/summarize_r16_eq.py [r16_eq_summary_mod.txt ...]   -> r16_eq_verdict.txt
"""
import re
import sys
from pathlib import Path

D = Path(__file__).resolve().parent
# Runs stopped on purpose and replaced; reported as SUPERSEDED (not PASS, not counted as FAIL) with the reason.
SUPERSEDED = {"soc_sa2_4kb_soc_fast1": "stopped 2026-10-06 in equiv_induct at 14 GB (after equiv_simple: 1,824 of "
                                      "36,741 cells unproven); replaced by soc_sa2_4kb_soc_fast1s, the same check "
                                      "ending at the stage where the FAST_HIT 0 proof was already complete"}
summaries = [Path(a) for a in sys.argv[1:]] or sorted(D.glob("r16_eq_summary_*.txt"))
out, bad = [], 0
for sfile in summaries:
    sfile = sfile if sfile.is_absolute() else D / sfile.name
    for line in sfile.read_text(encoding="utf-8").splitlines():
        m = re.match(r"(\S+) (expect-equivalent|negative-control) rc=(\d+) ", line)
        if not m:
            continue
        name, kind, rc = m.group(1), m.group(2), int(m.group(3))
        if name in SUPERSEDED:
            out.append("%-26s %-17s rc=%d  SUPERSEDED: %s" % (name, kind, rc, SUPERSEDED[name]))
            continue
        st = D / (name + ".status")
        txt = st.read_text(encoding="utf-8", errors="replace") if st.is_file() else ""
        mm = re.search(r"Of those cells (\d+) are proven and (\d+) are unproven", txt)
        if not mm:
            out.append("%-26s %-17s rc=%d  no equiv_status result  FAIL" % (name, kind, rc))
            bad += 1
            continue
        proven, unproven = int(mm.group(1)), int(mm.group(2))
        if kind == "expect-equivalent":
            ok = rc == 0 and unproven == 0 and "Equivalence successfully proven" in txt
            extra = ""
        else:
            ok = unproven > 0
            sigs = sorted({re.sub(r"_(gold|gate)$", "", s) for s in
                           re.findall(r"Unproven \$equiv \S+: \\(\S+?)(?: \[\d+\])? \\", txt)})
            extra = "  unproven (a lower bound of what differs): " + ", ".join(sigs)
        bad += 0 if ok else 1
        out.append("%-26s %-17s rc=%d  proven=%d unproven=%d  %s%s" % (name, kind, rc, proven, unproven,
                                                                     "PASS" if ok else "FAIL", extra))
out.append("%d checks, %d FAIL" % (len(out), bad))
(D / "r16_eq_verdict.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("\n".join(out))
sys.exit(1 if bad else 0)
