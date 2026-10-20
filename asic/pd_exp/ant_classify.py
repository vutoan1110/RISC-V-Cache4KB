"""FLOW_JOURNAL Incident 91: classify the post-route antenna violations of a run (antenna.rpt of
OpenROAD check_antennas -verbose): per violating (net, pin): layer, PAR / required, gate cell type,
whether the pin is a diode (net already protected), and the kind of net (resizer buffer net
netNNNN / wire / fanout / synthesis net / named RTL net).
usage: python ant_classify.py antenna.rpt"""
import collections
import re
import sys

net = pin = cell = layer = None
viol = []
side = None
for line in open(sys.argv[1], encoding="utf-8", errors="replace"):
    s = line.strip()
    if s.startswith("Net:"):
        net = s.split(None, 1)[1]
    elif s.startswith("Pin:"):
        m = re.match(r"Pin:\s+(\S+)\s+\((\S+)\)", s)
        pin, cell = m.group(1), m.group(2)
    elif s.startswith("Layer:"):
        layer = s.split()[1]
    elif s.startswith("Partial area ratio:"):
        side = float(s.split(":")[1])
    elif s.startswith("Required ratio:") and "VIOLATED" in s:
        req = float(s.split(":")[1].split()[0])
        kind = s.split("(")[1].split(")")[0]
        viol.append((net, pin, cell, layer, side, req, kind))

nets = {v[0] for v in viol}
print("violations (pin x layer): %d on %d nets" % (len(viol), len(nets)))
print("by layer      :", dict(collections.Counter(v[3] for v in viol)))
print("by rule       :", dict(collections.Counter(v[6] for v in viol)))
print("by gate cell  :", collections.Counter(v[2].replace("sky130_fd_sc_hd__", "") for v in viol).most_common(12))


def nkind(n):
    if re.fullmatch(r"net\d+", n):
        return "resizer net (netNNNN)"
    if re.fullmatch(r"_\d+_", n):
        return "synthesis net (_NNN_)"
    return "named RTL net"


print("by net kind   :", dict(collections.Counter(nkind(n) for n in nets)))
pk = collections.Counter()
for v in viol:
    inst = v[1].split("/")[0]
    k = "diode (ANTENNA_*)" if inst.startswith("ANTENNA") else re.sub(r"\d+$", "", inst) if re.match(r"^(wire|fanout|rebuffer|split|max_length|load_slew|hold)", inst) else "logic cell"
    pk[k] += 1
print("by pin owner  :", dict(pk))
r = sorted(v[4] / v[5] for v in viol)
print("PAR/required  : max %.2f, median %.2f, share <= 1.5: %.0f %%, <= 2: %.0f %%"
      % (r[-1], r[len(r) // 2], 100 * sum(x <= 1.5 for x in r) / len(r), 100 * sum(x <= 2 for x in r) / len(r)))
