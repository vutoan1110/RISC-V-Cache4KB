"""Classify the max slew / max capacitance / max fanout violators of a signed layout by cell kind.
    python drv_classify.py <run dir> [corner ...]
Reads <run>/<NN>-openroad-stapostpnr/<corner>/checks.rpt (OpenSTA report_check_types -violators) and the final DEF
(<NN>-openroad-fillinsertion/*.def) to find, for every violating pin, its instance, cell and net, and whether the
net carries antenna diodes inserted by the antenna repair. Prints counts per class and the worst entries."""
import collections
import re
import sys
from pathlib import Path

run = Path(sys.argv[1])
corners = sys.argv[2:] or ["nom_tt_025C_1v80", "max_ss_100C_1v60", "max_ff_n40C_1v95"]
sta = sorted(run.glob("*-openroad-stapostpnr"))[-1]
fill = sorted(run.glob("*-openroad-fillinsertion"))[-1]
defp = next(fill.glob("*.def"))

# ---- DEF: instance -> cell, pin -> net, net -> diode count
inst_cell, pin_net, net_diodes, net_pins = {}, {}, collections.Counter(), collections.Counter()
section = None
buf = ""
with open(defp, encoding="utf-8", errors="replace") as f:
    for line in f:
        s = line.strip()
        if s.startswith("COMPONENTS "):
            section = "C"
            continue
        if s.startswith("END COMPONENTS"):
            section = None
            continue
        if s.startswith("NETS ") or s.startswith("SPECIALNETS "):
            section = "N" if s.startswith("NETS ") else "S"
            buf = ""
            continue
        if s.startswith("END NETS") or s.startswith("END SPECIALNETS"):
            section = None
            continue
        if section == "C" and s.startswith("- "):
            p = s.split()
            inst_cell[p[1]] = p[2]
        elif section == "N":
            buf += " " + s
            if s.endswith(";"):
                m = re.match(r"\s*-\s+(\S+)(.*)", buf)
                if m:
                    net = m.group(1)
                    body = m.group(2).split("+ ROUTED")[0].split("+ USE")[0]
                    for inst, pin in re.findall(r"\(\s*(\S+)\s+(\S+)\s*\)", body):
                        pin_net[(inst, pin)] = net
                        net_pins[net] += 1
                        if inst.startswith("ANTENNA"):
                            net_diodes[net] += 1
                buf = ""


def kind(inst, cell):
    if inst.startswith("ANTENNA"):
        return "antenna diode pin"
    if cell.startswith("sky130_sram"):
        return "SRAM macro pin"
    if re.match(r"(clkbuf|clkload|clkinv|delaybuf)", inst) or "clkbuf" in cell and inst.startswith("clk"):
        return "clock tree"
    if re.match(r"(wire|max_cap|max_length|split|rebuffer|buffer|load_slew|fanout|place|hold|input|output|rsz)\d*", inst):
        return "resizer buffer (" + re.match(r"[a-z_]+", inst).group(0) + ")"
    if inst.startswith("macro_pin"):
        return "macro pin buffer"
    if re.match(r"_\d+_$", inst):
        return "synthesized cell"
    return "other (" + inst[:20] + ")"


for corner in corners:
    rpt = sta / corner / "checks.rpt"
    if not rpt.is_file():
        print("missing", rpt)
        continue
    text = rpt.read_text(encoding="utf-8", errors="replace")
    print(f"=== {run.name} {corner}")
    for title, unit in (("max slew", "ns"), ("max capacitance", "pF"), ("max fanout", "")):
        m = re.search(rf"^{title}\n\n.*?\n-+\n(.*?)(?:\n\n|\Z)", text, flags=re.S | re.M)
        if not m:
            print(f"  {title}: none")
            continue
        rows = []
        for line in m.group(1).splitlines():
            p = line.split()
            if len(p) < 4 or "VIOLATED" not in line:
                continue
            pin = p[0]
            inst, _, pname = pin.rpartition("/")
            cell = inst_cell.get(inst, "?")
            net = pin_net.get((inst, pname), "?")
            rows.append((float(p[-2]), pin, kind(inst, cell), cell, net, net_diodes.get(net, 0), net_pins.get(net, 0)))
        cls = collections.Counter(r[2] for r in rows)
        with_diode = sum(1 for r in rows if r[5] > 0)
        nets = {r[4] for r in rows}
        print(f"  {title}: {len(rows)} violating pins on {len(nets)} nets; pins on nets with antenna diodes: {with_diode}")
        for k, v in cls.most_common():
            print(f"    {v:6d}  {k}")
        for r in sorted(rows)[:4]:
            print(f"    worst: slack {r[0]:.3f} pin {r[1]} ({r[3]}) net {r[4]} diodes {r[5]} pins {r[6]}")
