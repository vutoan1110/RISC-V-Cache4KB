"""Print the first (worst) path of an OpenSTA max.rpt/min.rpt: arrival, pin, cell, driven net.
    python first_path.py <report> [all]   (default: only named design nets u_soc.* + ends)"""
import re
import sys

t = open(sys.argv[1], errors="replace").read()
blocks = re.split(r"\n(?=Startpoint: )", t)
blk = next(b for b in blocks if b.startswith("Startpoint"))
rows = []
lines = blk.splitlines()
for i, ln in enumerate(lines):
    m = re.search(r"([-\d.]+)\s+([-\d.]+)\s+[\^v]\s+(\S+)\s+\((\S+)\)\s*$", ln)
    if m:
        net = ""
        if i + 1 < len(lines) and "(net)" in lines[i + 1]:
            net = lines[i + 1].split()[0].lstrip("\\")
        rows.append((float(m.group(2)), m.group(3), m.group(4).replace("sky130_fd_sc_hd__", ""), net))
    if "slack" in ln:
        rows.append((0, ln.strip(), "", ""))
print(blk.splitlines()[0]); print([l for l in blk.splitlines() if l.startswith("Endpoint")][0])
show_all = len(sys.argv) > 2
for k, (tm, pin, cell, net) in enumerate(rows):
    if show_all or net.startswith("u_soc") or "slack" in pin or k in (0, len(rows) - 2) or "dout" in pin:
        if pin.startswith("clk") or "clkbuf" in pin:
            continue
        print("  %8.3f %-40s %-16s %s" % (tm, pin[:40], cell[:16], net))
