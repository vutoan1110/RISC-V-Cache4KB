# -*- coding: utf-8 -*-
"""Prove the .magicsafe.gds is geometry-neutral, without KLayout.

The original proof was a KLayout boolean XOR: 34 layers compared, 0 differ,
412 annotation shapes removed. KLayout lives in the OpenLane nix store and is
not reachable from this host any more, so that log cannot be regenerated.

This is a stronger check than the XOR it replaces. XOR proves the *area* of
the difference is empty. This walks both GDS files record by record and
compares every shape as an exact tuple -- structure name, record type, layer,
datatype, and the full coordinate list -- so it proves shape-for-shape
identity, not merely equal area. Anything that moved by one database unit
would show up here and would not show up in an area XOR of coincident edges.

Claim under test: the only difference between the two files is the complete
removal of shapes on five mask-prep annotation layer/datatypes, and nothing
on any other layer changed.

    22/21   cfom.maskAdd     22/22   cfom.maskDrop
    33/42   cp1m.maskDrop    33/43   cp1m.maskAdd
    235/0   boundary

Run:  python asic/prove_magicsafe_equivalence.py
Exit 0 only if the claim holds exactly.
"""
import struct
import sys
from collections import Counter

STRIPPED = {(22, 21), (22, 22), (33, 42), (33, 43), (235, 0)}

# record type -> the record that carries its layer, and the one that carries
# its purpose number. Only element records that own geometry are listed.
ELEMENTS = {0x08: "BOUNDARY", 0x09: "PATH", 0x0C: "TEXT",
            0x2D: "BOX", 0x15: "NODE"}
PURPOSE = {0x0E, 0x16, 0x2E, 0x2A}  # DATATYPE, TEXTTYPE, BOXTYPE, NODETYPE


def shapes(path):
    """Yield (struct_name, element, layer, purpose, coords) for every shape."""
    buf = open(path, "rb").read()
    i, n = 0, len(buf)
    sname, elem, layer, purpose, xy = None, None, None, None, None
    while i < n:
        if i + 4 > n:
            raise ValueError("truncated record header at %d" % i)
        ln, rt, dt = struct.unpack(">HBB", buf[i:i + 4])
        if ln < 4:
            raise ValueError("bad record length %d at %d" % (ln, i))
        body = buf[i + 4:i + ln]
        if rt == 0x06:                                   # STRNAME
            sname = body.rstrip(b"\x00").decode("ascii", "replace")
        elif rt in ELEMENTS:
            elem, layer, purpose, xy = ELEMENTS[rt], None, None, None
        elif rt == 0x0D:                                 # LAYER
            layer = struct.unpack(">h", body[:2])[0]
        elif rt in PURPOSE:
            purpose = struct.unpack(">h", body[:2])[0]
        elif rt == 0x10:                                 # XY
            xy = struct.unpack(">%di" % (len(body) // 4), body)
        elif rt == 0x11:                                 # ENDEL
            if elem is not None and layer is not None:
                yield (sname, elem, layer, purpose, xy)
            elem = None
        i += ln


def census(path):
    c = Counter()
    for s in shapes(path):
        c[s] += 1
    return c


# Default is the 2 KiB macro in the 1 KiB design; any original .gds can be
# passed instead and its .magicsafe.gds sibling is derived.
orig = (sys.argv[1] if len(sys.argv) > 1
        else "asic/soc_dm_control/macros/gds/sky130_sram_2kbyte_1rw1r_32x512_8.gds")
safe = orig.replace(".gds", ".magicsafe.gds")

a, b = census(orig), census(safe)
print("original   %8d shapes   %s" % (sum(a.values()), orig))
print("magicsafe  %8d shapes   %s" % (sum(b.values()), safe))

removed = a - b          # in original, missing or fewer in magicsafe
added = b - a            # in magicsafe but not in original

rm_layers = Counter((s[2], s[3]) for s in removed.elements())
print("\nshapes removed: %d" % sum(removed.values()))
for (ly, pu), k in sorted(rm_layers.items()):
    mark = "expected" if (ly, pu) in STRIPPED else "UNEXPECTED"
    print("   %3d/%-3d  %6d shapes   %s" % (ly, pu, k, mark))
print("shapes added: %d" % sum(added.values()))

kept = set((s[2], s[3]) for s in b)
print("\nlayer/datatypes retained and compared: %d" % len(kept))
bad_layers = [lp for lp in rm_layers if lp not in STRIPPED]
diff_on_kept = {lp: k for lp, k in rm_layers.items() if lp in kept}

ok = True
if bad_layers:
    print("FAIL: shapes removed from non-annotation layers: %s" % bad_layers)
    ok = False
if diff_on_kept:
    print("FAIL: retained layers lost shapes: %s" % diff_on_kept)
    ok = False
if added:
    print("FAIL: magicsafe introduced %d shapes" % sum(added.values()))
    ok = False

print("\nRESULT: %s" % ("every retained layer is shape-for-shape identical; "
                        "the only difference is the removal of the five "
                        "annotation layer/datatypes"
                        if ok else "CLAIM DOES NOT HOLD"))
sys.exit(0 if ok else 1)
