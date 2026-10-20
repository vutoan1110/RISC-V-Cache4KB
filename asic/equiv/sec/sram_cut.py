"""FLOW_JOURNAL Incident 86, SEC: cut the 12 SRAM macro instances out of the top module.

Every SRAM input pin (clk, csb, web, wmask, addr, din) becomes a new top-level OUTPUT, so the
miter compares it between gold and gate at every cycle; every SRAM data output (dout0, dout1)
becomes a new top-level INPUT with the same name on both sides, so the miter feeds gold and
gate the SAME read data. Sound: if both sides present identical pin values to the macro at
every cycle, the macro contents and its outputs are identical; proving equivalence for ANY
read-data sequence covers the real one.

usage: python3 sram_cut.py in.il out.il   (prints the pins it cut)
"""
import re
import sys

TOK = re.compile(r"\{|\}|\d+'[01xzm-]+|[\\$]\S+(?: \[\d+(?::\d+)?\])?")
OUT_PINS = ("\\dout0", "\\dout1")

src, dst = sys.argv[1], sys.argv[2]
lines = open(src).read().split("\n")

# locate the top module
start = next(i for i, l in enumerate(lines) if l == "module \\soc_asic_top")
end = next(i for i in range(start + 1, len(lines)) if lines[i] == "end")
body = lines[start + 1:end]

width, port_ids = {}, []
for l in body:
    if l.startswith("  wire "):
        p = l.split()
        width[p[-1]] = int(p[p.index("width") + 1]) if "width" in p else 1
        for kw in ("input", "output", "inout"):
            if kw in p:
                port_ids.append(int(p[p.index(kw) + 1]))


def nbits(sig):
    n = 0
    for t in TOK.findall(sig):
        if t in "{}":
            continue
        if "'" in t and t[0].isdigit():
            n += int(t.split("'")[0])
            continue
        m = re.match(r"^(\S+)(?: \[(\d+)(?::(\d+))?\])?$", t)
        if m.group(2) is None:
            n += width[m.group(1)]
        elif m.group(3) is None:
            n += 1
        else:
            n += int(m.group(2)) - int(m.group(3)) + 1
    return n


# A macro output pin tied only to hidden no-connect nets (the gate netlist's _NC* wires,
# renamed $auto$rename... by EQY's gate front end) and read by nothing else carries no
# information: drop it, as the gold side leaves such pins unconnected. Count, over the whole
# module, how often every $-named signal is referenced in cell/module connections.
refs = {}
for l in body:
    s = l.strip()
    if s.startswith("connect "):
        for t in TOK.findall(s):
            if t.startswith("$"):
                nm = t.split(" ")[0]
                refs[nm] = refs.get(nm, 0) + 1


def unused_nc(sig):
    toks = [t for t in TOK.findall(sig) if t not in "{}"]
    return toks and all(t.startswith("$") and refs.get(t.split(" ")[0], 0) == 1 for t in toks)


new_body, new_wires, new_conns, cut = [], [], [], 0
pid = max(port_ids)
i = 0
pending_attrs = []
while i < len(body):
    l = body[i]
    if l.startswith("  attribute "):
        pending_attrs.append(l)
        i += 1
        continue
    if l.startswith("  cell \\sky130_sram_"):
        inst = l.split()[2]
        base = re.sub(r"[^A-Za-z0-9]", "_", inst.lstrip("\\"))
        i += 1
        while body[i] != "  end":
            s = body[i].strip()
            if s.startswith("connect "):
                _, pin, sig = s.split(None, 2)
                name = "\\%s__%s" % (base, pin.lstrip("\\"))
                w = nbits(sig)
                if w == 0 or (pin in OUT_PINS and unused_nc(sig)):
                    # unconnected pin, or an output tied only to unread no-connect nets
                    print("cut %-70s %-8s unconnected, dropped" % (inst, pin))
                    i += 1
                    continue
                pid += 1
                if pin in OUT_PINS:
                    new_wires.append("  wire width %d input %d %s" % (w, pid, name))
                    new_conns.append("  connect %s %s" % (sig, name))
                else:
                    new_wires.append("  wire width %d output %d %s" % (w, pid, name))
                    new_conns.append("  connect %s %s" % (name, sig))
                print("cut %-70s %-8s %2d bit(s) %s" % (inst, pin, w, "input" if pin in OUT_PINS else "output"))
            i += 1
        i += 1                      # skip "  end"
        pending_attrs = []          # drop the cell's own attributes
        cut += 1
        continue
    new_body.extend(pending_attrs)
    pending_attrs = []
    new_body.append(l)
    i += 1
new_body.extend(pending_attrs)

out = lines[:start + 1] + new_wires + new_body + new_conns + lines[end:]
open(dst, "w", newline="\n").write("\n".join(out))
print("cut %d SRAM instances, added %d ports" % (cut, len(new_wires)))
