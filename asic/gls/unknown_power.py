#!/usr/bin/env python3
"""Switching power of the nets OpenSTA left at "unknown" activity.

    python3 unknown_power.py <unknown_pins.txt> <pins.saif> <design.spef> [vdd]

FLOW_JOURNAL Incident 69. OpenSTA 2.6 never visits the SRAM macro outputs
(their liberty has a clk->dout arc and no function) nor the buffers hanging
off them, so those pins keep zero activity even though the SAIF annotates
them. This puts a number on what that leaves out: for every such driver pin,
P = 1/2 * C_net * VDD^2 * TC / T, with C_net the total net capacitance from
the SPEF (*D_NET) and TC, T the toggle count and window from the SAIF.
Internal power of the buffers involved is NOT included; it is reported as a
separate caveat, not guessed.
"""
from __future__ import annotations

import re
import sys


def saif_pins(path):
    """(instance, pin) -> (TC, duration) from the driver-pin SAIF."""
    out, inst, dur, scale = {}, None, None, 1.0
    for ln in open(path):
        s = ln.strip()
        m = re.match(r"\(TIMESCALE (\d+) (\w+)\)", s)
        if m:
            scale = int(m.group(1)) * {"s": 1.0, "ms": 1e-3, "us": 1e-6, "ns": 1e-9, "ps": 1e-12, "fs": 1e-15}[m.group(2)]
            continue
        m = re.match(r"\(DURATION (\d+)\)", s)
        if m:
            dur = int(m.group(1)) * scale
            continue
        m = re.match(r"\(INSTANCE (\S+)$", s)
        if m:
            inst = m.group(1).replace("\\", "")
            continue
        m = re.match(r"\((\S+) \(T0 \d+\) \(T1 \d+\) \(TX \d+\) \(TC (\d+)\)", s)
        if m and inst not in (None, "tb_gls_soc", "dut"):
            out[(inst, m.group(1).replace("\\", ""))] = int(m.group(2))
    return out, dur


def spef_caps(path, wanted):
    """net name -> total capacitance (F) for the nets in `wanted`."""
    names, caps, unit = {}, {}, 1e-12
    in_map = False
    with open(path, errors="replace") as fh:
        for ln in fh:
            if ln.startswith("*C_UNIT"):
                v, u = ln.split()[1:3]
                unit = float(v) * {"PF": 1e-12, "FF": 1e-15, "NF": 1e-9}[u.upper()]
            elif ln.startswith("*NAME_MAP"):
                in_map = True
            elif in_map and ln.startswith("*") and not ln.startswith("*D_NET") and re.match(r"^\*\d+ ", ln):
                idx, name = ln.split(None, 1)
                name = name.strip().replace("\\", "")
                if name in wanted:
                    names[idx] = name
            elif ln.startswith("*D_NET"):
                in_map = False
                _, ref, cap = ln.split()[:3]
                n = names.get(ref, ref.replace("\\", ""))
                if n in wanted:
                    caps[n] = float(cap) * unit
    return caps


def main():
    unk, saif, spef = sys.argv[1:4]
    vdd = float(sys.argv[4]) if len(sys.argv) > 4 else 1.8
    toggles, dur = saif_pins(saif)
    pins = [ln.split()[0] for ln in open(unk) if ln.strip()]
    # driver pin -> net: the netlist net on that pin is what the SPEF names;
    # read it from the SAIF key and the netlist connectivity already resolved
    # by saif_to_pins.py (instance/pin). Here the SPEF *D_NET names are nets,
    # so map pin -> net through the SPEF *CONN section instead.
    want_pins = {p for p in pins}
    pin_net = {}
    cur = None
    with open(spef, errors="replace") as fh:
        idx_name = {}
        for ln in fh:
            if re.match(r"^\*\d+ ", ln) and cur is None:
                idx, name = ln.split(None, 1)
                idx_name[idx] = name.strip().replace("\\", "")
            elif ln.startswith("*D_NET"):
                ref = ln.split()[1]
                cur = idx_name.get(ref, ref.replace("\\", ""))
            elif ln.startswith("*I ") and cur is not None:
                tok = ln.split()[1]
                if ":" in tok:
                    i, p = tok.rsplit(":", 1)
                    i = idx_name.get(i, i.replace("\\", ""))
                    full = "%s/%s" % (i, p.replace("\\", ""))
                    if full in want_pins and " O" in ln[len(tok) + 3:]:
                        pin_net[full] = cur
    caps = spef_caps(spef, set(pin_net.values()))
    total, n_ok, missing = 0.0, 0, []
    for p in pins:
        inst, pin = p.rsplit("/", 1)
        tc = toggles.get((inst, pin))
        net = pin_net.get(p)
        c = caps.get(net) if net else None
        if tc is None or c is None:
            missing.append(p)
            continue
        total += 0.5 * c * vdd * vdd * tc / dur
        n_ok += 1
    print("UNKNOWN_POWER pins %d, with TC and C %d, switching %.4f mW over %.3f us (vdd %.2f)"
          % (len(pins), n_ok, total * 1e3, dur * 1e6, vdd))
    if missing:
        print("UNKNOWN_POWER no TC/C for %d pins, e.g. %s" % (len(missing), missing[:5]))


if __name__ == "__main__":
    main()
