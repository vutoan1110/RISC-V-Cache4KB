"""Show the connections, cell placements and guide bounding boxes of the given nets (read-only).
usage: python net_probe.py <def> <guide> net1 net2 ..."""
import sys, re
deff, guide, nets = sys.argv[1], sys.argv[2], set(sys.argv[3:])
comps, conns, sect, cur = {}, {}, None, None
with open(deff) as f:
    for ln in f:
        s = ln.strip()
        if s.startswith("COMPONENTS"):
            sect = "C"; continue
        if s.startswith("END COMPONENTS"):
            sect = None; continue
        if s.startswith("NETS") or s.startswith("SPECIALNETS"):
            sect = "N" if s.startswith("NETS") else None; continue
        if s.startswith("END NETS"):
            break
        if sect == "C" and s.startswith("- "):
            m = re.match(r"- (\S+) (\S+) .*?(?:PLACED|FIXED) \( (-?\d+) (-?\d+) \) (\S+)", s)
            if m:
                comps[m.group(1)] = (m.group(2), int(m.group(3)) / 1000, int(m.group(4)) / 1000, m.group(5))
        elif sect == "N":
            if s.startswith("- "):
                name = s.split()[1]
                cur = name if name in nets else None
                if cur:
                    conns[cur] = []
            if cur:
                conns[cur] += re.findall(r"\( (\S+) (\S+) \)", s)
                if s.endswith(";"):
                    cur = None
bbox = {}
with open(guide) as f:
    net = None
    for ln in f:
        s = ln.split()
        if len(s) == 1 and s[0] not in "()":
            net = s[0] if s[0] in nets else None
        elif net and len(s) == 5:
            x1, y1, x2, y2 = (int(v) / 1000 for v in s[:4])
            b = bbox.get(net, [1e9, 1e9, -1e9, -1e9])
            bbox[net] = [min(b[0], x1), min(b[1], y1), max(b[2], x2), max(b[3], y2)]
for n in sys.argv[3:]:
    print("==", n, "guide bbox", ["%.0f" % v for v in bbox.get(n, [])])
    for inst, pin in conns.get(n, []):
        c = comps.get(inst)
        print("   %-70s %-6s %s" % (inst, pin, "%s @ (%.0f, %.0f) %s" % c if c else "PIN"))
