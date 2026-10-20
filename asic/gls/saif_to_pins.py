#!/usr/bin/env python3
"""Questa net-level SAIF of the flat netlist -> driver-pin SAIF for OpenSTA.

    python3 saif_to_pins.py <raw.saif> <netlist.nl.v> <out.saif> <lib> [<lib> ...]

FLOW_JOURNAL Incident 69. Measured on OpenSTA 2.6.0 (the build OpenLane runs),
with small netlists before any real number was trusted:
* read_saif looks a NET entry up as a PIN of the enclosing instance. At the
  flat top level that matches the ports only; the ~200k internal nets of the
  netlist are silently ignored. Activity must be given as
  (INSTANCE <leaf cell> (NET (<pin> ...))).
* Instance and pin names must escape '[' and ']' but NOT '.': "u_x.inv\\[0\\]"
  matches instance u_x.inv[0]; "u_x\\.inv\\[0\\]" (Questa's style) does not.
* A pin in a feedback loop that nothing seeds stays "unknown" (zero activity)
  unless it is annotated itself, so every net is attached to its DRIVER pin
  (cell output, macro output bit or input port); loads take it from there.

Checks, any failure -> exit 1:
* all net entries span the same window W = T0+T1+TX; the header DURATION
  (Questa leaves it at the total simulated time) is rewritten to W;
* coverage: nets that have a driver in the netlist and an entry in the SAIF,
  over all driven nets, is printed; nets with an entry but no driver found
  are counted and listed (first 20).
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict

ENTRY = re.compile(r"^\s*\((\S+) \(T0 (\d+)\) \(T1 (\d+)\) \(TX (\d+)\) \(TC (\d+)\) \(IG (\d+)\)\)\s*$")


def unescape(name: str) -> str:
    return re.sub(r"\\(.)", r"\1", name)


def saif_name(name: str) -> str:
    return name.replace("[", "\\[").replace("]", "\\]").replace("/", "\\/")


def read_raw(path: str):
    head, nets = {}, {}
    depth_inst = []
    for ln in open(path, errors="replace"):
        s = ln.strip()
        m = re.match(r"^\((TIMESCALE|DURATION) (.*)\)$", s)
        if m:
            head[m.group(1)] = m.group(2)
            continue
        m = re.match(r"^\(INSTANCE (\S+)$", s)
        if m:
            depth_inst.append(m.group(1))
            continue
        m = ENTRY.match(ln)
        if m:
            if depth_inst != ["tb_gls_soc", "dut"]:
                raise SystemExit("[FAIL] entry outside tb_gls_soc/dut: %s in %s" % (s, depth_inst))
            nets[unescape(m.group(1))] = tuple(int(x) for x in m.groups()[1:])
    return head, nets


def block(txt: str, i: int) -> tuple[str, int]:
    """txt[i] is '{'; return the text inside the matching braces and the end."""
    depth, j = 0, i
    while True:
        c = txt[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return txt[i + 1: j], j + 1
        j += 1


def top_level(body: str) -> str:
    """Drop every nested {...} group, keeping this block's own attributes."""
    out, depth = [], 0
    for c in body:
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif depth == 0:
            out.append(c)
    return "".join(out)


def read_libs(paths):
    """cell -> {output pin: None, or (bit_from, bit_to) for a bus}."""
    outs: dict[str, dict[str, tuple | None]] = {}
    for p in paths:
        txt = open(p, errors="replace").read()
        types = {}
        for m in re.finditer(r"\btype\s*\(\s*\"?(\w+)\"?\s*\)\s*\{", txt):
            body, _ = block(txt, m.end() - 1)
            f = re.search(r"bit_from\s*:\s*(\d+)", body)
            t = re.search(r"bit_to\s*:\s*(\d+)", body)
            if f and t:
                types[m.group(1)] = (int(f.group(1)), int(t.group(1)))
        for cm in re.finditer(r"\bcell\s*\(\s*\"?([\w$]+)\"?\s*\)\s*\{", txt):
            cbody, _ = block(txt, cm.end() - 1)
            pins = {}
            for pm in re.finditer(r"\b(pin|bus)\s*\(\s*\"?([\w\[\]]+)\"?\s*\)\s*\{", cbody):
                pbody, _ = block(cbody, pm.end() - 1)
                own = top_level(pbody)
                d = re.search(r"direction\s*:\s*\"?(\w+)\"?", own)
                if not d or d.group(1) != "output":
                    continue
                if pm.group(1) == "bus":
                    bt = re.search(r"bus_type\s*:\s*\"?(\w+)\"?", own)
                    pins[pm.group(2)] = types[bt.group(1)]
                elif "[" not in pm.group(2):
                    pins[pm.group(2)] = None
            outs[cm.group(1)] = pins
    return outs


def split_conn(conn: str) -> list[str]:
    conn = conn.strip()
    if conn.startswith("{"):
        conn = conn[1:conn.rindex("}")]
    toks, cur, esc = [], "", False
    for ch in conn:
        if esc:
            cur += ch
            if ch.isspace():
                esc = False
            continue
        if ch == "\\":
            esc = True
            cur += ch
        elif ch == ",":
            toks.append(cur)
            cur = ""
        else:
            cur += ch
    toks.append(cur)
    out = []
    for t in toks:
        t = t.strip()
        out.append(t[1:].strip() if t.startswith("\\") else t)
    return out


def read_netlist(path: str, outs):
    """net -> (instance, pin) of its driver; also the set of input ports."""
    txt = open(path, errors="replace").read()
    drivers: dict[str, tuple[str, str]] = {}
    inputs, outputs, unknown_cells = set(), set(), defaultdict(int)
    for st in txt.split(";"):
        s = st.strip()
        if not s or s.startswith(("module", "endmodule", "wire", "inout", "assign")):
            continue
        if s.startswith(("input", "output")):
            kind = "input" if s.startswith("input") else "output"
            for m in re.finditer(r"(\[\d+:\d+\]\s*)?(\\\S+|\w+)", s[len(kind):]):
                (inputs if kind == "input" else outputs).add(m.group(2).lstrip("\\"))
            continue
        m = re.match(r"^([\w$]+)\s+(\\\S+|[\w$]+)\s*\((.*)\)\s*$", s, re.S)
        if not m:
            continue
        cell, inst, body = m.group(1), m.group(2).lstrip("\\"), m.group(3)
        if cell not in outs:
            unknown_cells[cell] += 1
            continue
        opins = outs[cell]
        for pm in re.finditer(r"\.(\w+)\s*\(", body):
            pin = pm.group(1)
            if pin not in opins:
                continue
            i, depth = pm.end(), 1
            while depth:
                c = body[i]
                if c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
                i += 1
            nets = split_conn(body[pm.end(): i - 1])
            rng = opins[pin]
            if rng is None:
                pairs = [(pin, nets[0])]
            else:
                hi, lo = rng
                step = -1 if hi >= lo else 1
                bits = list(range(hi, lo + step, step))
                if len(bits) != len(nets):
                    raise SystemExit("[FAIL] %s.%s: %d nets for %d bits" % (inst, pin, len(nets), len(bits)))
                pairs = [("%s[%d]" % (pin, b), n) for b, n in zip(bits, nets)]
            for p, n in pairs:
                if not n or n.startswith(("1'b", "0'b")):
                    continue
                if n in drivers:
                    raise SystemExit("[FAIL] net %s driven by %s and %s/%s" % (n, drivers[n], inst, p))
                drivers[n] = (inst, p)
    return drivers, inputs, outputs, unknown_cells


def main() -> int:
    raw, nl, out, libs = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
    head, nets = read_raw(raw)
    spans = {t0 + t1 + tx for (t0, t1, tx, tc, ig) in nets.values()}
    if len(spans) != 1:
        print("[FAIL] net entries do not share one window: %s" % sorted(spans)[:10])
        return 1
    W = spans.pop()
    outs = read_libs(libs)
    drivers, inputs, outputs, unknown_cells = read_netlist(nl, outs)
    ignore = {c for c in unknown_cells if re.match(r"sky130_(fd|ef)_sc_hd__(tapvpwrvgnd|decap|fill)", c)}
    real_unknown = {c: n for c, n in unknown_cells.items() if c not in ignore}
    if real_unknown:
        print("[FAIL] cells without liberty output data: %s" % real_unknown)
        return 1
    by_inst: dict[str, list] = defaultdict(list)
    ports, no_driver, out_ports = [], [], 0
    for n, v in nets.items():
        if n in drivers:
            inst, pin = drivers[n]
            by_inst[inst].append((pin, v))
        elif n in inputs or re.sub(r"\[\d+\]$", "", n) in inputs:
            ports.append((n, v))
        elif re.sub(r"\[\d+\]$", "", n) in outputs:
            out_ports += 1
        else:
            no_driver.append(n)
    covered = sum(1 for n in drivers if n in nets)
    print("PW_SAIF window %d (%s units); entries %d; driven nets %d; covered %d (%.2f %%); "
          "input-port entries %d; output-port entries %d (activity propagates); entries without driver %d" % (
              W, head.get("TIMESCALE", "?"), len(nets), len(drivers), covered,
              100.0 * covered / max(1, len(drivers)), len(ports), out_ports, len(no_driver)))
    if no_driver:
        print("PW_SAIF no-driver sample: %s" % no_driver[:20])
    missing = [n for n in drivers if n not in nets]
    if missing:
        print("PW_SAIF driven nets with no entry, sample: %s" % missing[:20])
    with open(out, "w", newline="\n") as f:
        f.write('(SAIFILE\n(SAIFVERSION "2.0")\n(DIRECTION "backward")\n(DESIGN )\n'
                '(PROGRAM_NAME "saif_to_pins.py")\n(DIVIDER /)\n(TIMESCALE %s)\n(DURATION %d)\n'
                % (head["TIMESCALE"], W))
        f.write("(INSTANCE tb_gls_soc\n\t(INSTANCE dut\n")
        fmt = "(%s (T0 %d) (T1 %d) (TX %d) (TC %d) (IG %d))\n"
        if ports:
            f.write("\t\t(NET\n")
            for n, v in ports:
                f.write("\t\t\t" + fmt % ((saif_name(n),) + v))
            f.write("\t\t)\n")
        for inst in sorted(by_inst):
            f.write("\t\t(INSTANCE %s\n\t\t\t(NET\n" % saif_name(inst))
            for pin, v in by_inst[inst]:
                f.write("\t\t\t\t" + fmt % ((saif_name(pin),) + v))
            f.write("\t\t\t)\n\t\t)\n")
        f.write("\t)\n)\n)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
