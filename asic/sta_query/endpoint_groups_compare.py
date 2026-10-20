#!/usr/bin/env python3
"""Compare violating setup endpoints of two or more layouts per RTL register group (2026-10-15 ss study).

    python endpoint_groups_compare.py LABEL=<dir with endgroups_<corner>.tsv> [LABEL=...] [--corner max_ss_100C_1v60]
                                      [--top 40] [--out file.md]

Input: the TSV written by q_endgroups.tcl (endpoint, qnet, slack, startpoint, startnet). A register endpoint is
grouped by the RTL name of its Q net without the bit index (u_soc.mcause_dbg[31] -> u_soc.mcause_dbg); a macro
input pin by instance and pin name without index (.../u_bank/din0[5] -> .../u_bank/din0). Per group: number of
violating endpoints, worst slack, and the start group of the worst path. Groups are ordered by the worst slack of the
last layout; a group missing in a layout had no violating endpoint there ("-").
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def base(name: str) -> str:
    return re.sub(r"\[\d+\]$", "", name.strip().lstrip("\\")).replace("\\", "")


def load(path: Path) -> dict:
    groups: dict[str, list] = {}
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines()[1:]:
        f = ln.split("\t")
        if len(f) < 5:
            continue
        endpoint, qnet, slack, _sp, startnet = f[:5]
        try:
            s = float(slack)
        except ValueError:
            continue
        g = base(qnet) if qnet else base(endpoint.replace("\\", ""))
        start = base(startnet) if startnet else "?"
        cur = groups.setdefault(g, [0, None, ""])
        cur[0] += 1
        if cur[1] is None or s < cur[1]:
            cur[1], cur[2] = s, start
    return groups


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--corner", default="max_ss_100C_1v60")
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--out")
    a = ap.parse_args()
    labels, data = [], []
    for item in a.runs:
        lab, _, d = item.partition("=")
        f = Path(d) / ("endgroups_%s.tsv" % a.corner)
        if not f.is_file():
            print("missing %s" % f, file=sys.stderr)
            return 2
        labels.append(lab)
        data.append(load(f))
    last = data[-1]
    names = sorted(set().union(*data), key=lambda g: (last[g][1] if g in last else 0.0, g))
    L = ["Violating setup endpoints per register group at %s (slack ns; n = violating endpoints)" % a.corner, ""]
    L.append("| group | " + " | ".join("%s worst / n" % lab for lab in labels) + " | worst path starts in (%s) |" % labels[-1])
    L.append("|---|" + "---:|" * len(labels) + "---|")
    for g in names[: a.top]:
        cells = []
        for d in data:
            cells.append("%+.3f / %d" % (d[g][1], d[g][0]) if g in d else "-")
        L.append("| %s | %s | %s |" % (g, " | ".join(cells), last[g][2] if g in last else "-"))
    L.append("")
    for lab, d in zip(labels, data):
        n = sum(v[0] for v in d.values())
        w = min((v[1] for v in d.values()), default=0.0)
        L.append("%s: %d violating endpoints in %d groups, worst %+.3f" % (lab, n, len(d), w))
    text = "\n".join(L) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
