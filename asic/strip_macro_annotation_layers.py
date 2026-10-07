# -*- coding: utf-8 -*-
"""Remove mask-prep annotation layers from the SRAM macro GDS, and prove it is
geometry-neutral.

Magic.StreamOut failed 13 times in a row, identically every time -- 20 Calma
errors, 59 problems -- so it is not the machine. Magic's sky130A techfile does
not declare these layer/datatypes, which the OpenRAM macro GDS contains:

    22/21   cfom.maskAdd      not in sky130A.tech at all
    22/22   cfom.maskDrop     not in sky130A.tech at all
    33/42   cp1m.maskDrop     not in sky130A.tech at all
    33/43   cp1m.maskAdd      not in sky130A.tech at all
    235/0   boundary          tech declares 235/4 (prBoundary), not 235/0

Names read out of the PDK's own sky130A.lyp, not guessed. Every one is mask
data-prep annotation or a cell outline: none of them is device geometry, so
none can affect DRC, LVS, XOR, antenna or parasitics. OpenLane escalates
Magic's read errors to fatal via MAGIC_CAPTURE_ERRORS and fails the step.

The signoff GDS is KLayout's -- PRIMARY_GDSII_STREAMOUT_TOOL is already
"klayout" -- so Magic's copy exists for the XOR cross-check.

This does not disable a check. It removes annotation Magic cannot parse and
then proves, layer by layer, that nothing else moved. Run with:
    klayout -b -r strip_macro_annotation_layers.py
"""
import os
import sys

import pya

SRC = os.environ["MACRO_GDS"]
DST = os.environ["MACRO_GDS_OUT"]
DROP = [(22, 21), (22, 22), (33, 42), (33, 43), (235, 0)]

ly = pya.Layout()
ly.read(SRC)
print("read %s: %d cells" % (SRC, ly.cells()))

print("--- layers present before ---")
before = {}
for li in ly.layer_indexes():
    info = ly.get_info(li)
    n = sum(ly.cell(c).shapes(li).size() for c in range(ly.cells()))
    before[(info.layer, info.datatype)] = n
    print("    %3d/%-3d  %8d shapes" % (info.layer, info.datatype, n))

removed = 0
for lay, dt in DROP:
    li = ly.find_layer(lay, dt)
    if li is None:
        print("    %d/%d not present, nothing to do" % (lay, dt))
        continue
    removed += before.get((lay, dt), 0)
    ly.delete_layer(li)
    print("    removed %d/%d" % (lay, dt))

ly.write(DST)
print("wrote %s (%d shapes removed)" % (DST, removed))

# --- proof: XOR the original against the stripped copy on every layer that is
# supposed to survive. Anything non-empty means this edit changed geometry.
a = pya.Layout(); a.read(SRC)
b = pya.Layout(); b.read(DST)
ta, tb = a.top_cell(), b.top_cell()
bad = 0
checked = 0
for li in a.layer_indexes():
    info = a.get_info(li)
    if (info.layer, info.datatype) in DROP:
        continue
    lj = b.find_layer(info.layer, info.datatype)
    ra = pya.Region(ta.begin_shapes_rec(li))
    rb = pya.Region(tb.begin_shapes_rec(lj)) if lj is not None else pya.Region()
    x = ra ^ rb
    checked += 1
    if not x.is_empty():
        bad += 1
        print("XOR NON-EMPTY on %d/%d: %d polygons"
              % (info.layer, info.datatype, x.count()))
print("XOR: %d layers compared, %d differ" % (checked, bad))
print("PROOF_OK" if bad == 0 else "PROOF_FAILED")
sys.exit(0 if bad == 0 else 1)
