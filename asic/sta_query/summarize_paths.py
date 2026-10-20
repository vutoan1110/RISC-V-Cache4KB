"""Summarise report_checks paths: per SQ_GROUP block, print the arrival at every
named design net (u_soc.*) plus the first and last cell (NHAT_KY.md 2026-09-26)."""
import re
import sys

txt = open(sys.argv[1], encoding="utf-8", errors="replace").read()
for blk in txt.split("SQ_GROUP ")[1:]:
    name = blk.split()[0]
    rows = []
    for ln in blk.splitlines():
        if "(net)" in ln and rows:
            rows[-1].append(ln.split()[0].lstrip(chr(92)))
            continue
        mm = re.search(r"([\d.]+)\s+([\d.]+)\s+[\^v]\s+(\S+)/(\w+)\s+\((sky130\S+)\)", ln)
        if mm and mm.group(4) in ("X", "Y", "Q", "Q_N"):
            rows.append([float(mm.group(2)), mm.group(3), mm.group(5).replace("sky130_fd_sc_hd__", "")])
    rows = [r for r in rows if not r[1].startswith("clkbuf")]
    sl = re.search(r"(-?[\d.]+)\s+slack", blk)
    print("== %s slack %s cells %d" % (name, sl.group(1) if sl else "?", len(rows)))
    for i, r in enumerate(rows):
        net = r[3] if len(r) > 3 else ""
        if net.startswith("u_soc") or i in (0, len(rows) - 1):
            print("   %7.2f %-12s %s" % (r[0], r[2][:12], net))
