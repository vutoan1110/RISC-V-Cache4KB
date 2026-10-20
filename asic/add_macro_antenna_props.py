# -*- coding: utf-8 -*-
"""Add the missing antenna properties to the SRAM macro's LEF.

OpenROAD's antenna checker segfaults on this design (Signal 11 inside
ant::AntennaChecker::checkAntennas). The cause is not the design: the macro LEF
that ships with this OpenLane template declares **no antenna properties at all**
-- zero ANTENNAGATEAREA, zero ANTENNADIFFAREA -- and the flow says so itself:

    [Odb.CheckMacroAntennaProperties] Cell 'sky130_sram_2kbyte_1rw1r_32x512_8'
    has (59) input pin(s) without antenna gate information.

The antenna ratio is metal area divided by gate area. With no gate area on a
pin, the checker has nothing to divide by.

The values here come from the PDK's own standard-cell library,
sky130_fd_sc_hd.lef:

  * inputs  ANTENNAGATEAREA 0.126 um^2 -- the library's most common input gate
    area (180 of its pins use exactly this), i.e. a minimum-size input gate.
    This is the conservative choice: a *smaller* gate area yields a *larger*
    antenna ratio, so this flags more violations and inserts more diodes rather
    than fewer.
  * outputs ANTENNADIFFAREA 0.4455 um^2 -- the value sky130_fd_sc_hd__inv_2
    declares on its Y pin. Output diffusion provides antenna protection.

This is a normal thing to have to do when a memory compiler omits antenna data,
and it is not a bypass: the check still runs, on real numbers, and any violation
it finds is still repaired. What must be reported is that these values were
supplied rather than characterised from the macro's own layout.

    python3 add_macro_antenna_props.py <file.lef> [--revert]
"""
import re
import shutil
import sys
import os

GATE_AREA = "0.126000"
DIFF_AREA = "0.445500"

path = sys.argv[1] if len(sys.argv) > 1 else None
if not path or not os.path.isfile(path):
    sys.exit("usage: add_macro_antenna_props.py <file.lef> [--revert]")
backup = path + ".noantenna"

if "--revert" in sys.argv:
    if os.path.isfile(backup):
        shutil.copyfile(backup, path)
        print("reverted to the LEF as shipped")
    else:
        print("no backup to revert to")
    sys.exit(0)

text = open(path, encoding="utf-8", errors="replace").read()
if "ANTENNAGATEAREA" in text or "ANTENNADIFFAREA" in text:
    sys.exit("this LEF already declares antenna properties; nothing to do")

if not os.path.isfile(backup):
    shutil.copyfile(path, backup)
    print("kept the original as %s" % os.path.basename(backup))

# Each pin block looks like:
#    PIN <name>
#       DIRECTION INPUT ;
#       PORT
# The property goes immediately after DIRECTION, which is where the standard
# cell library puts it.
pat = re.compile(r"^(?P<ind>\s*)DIRECTION\s+(?P<dir>INPUT|OUTPUT|INOUT)\s*;",
                 re.M)
counts = {"INPUT": 0, "OUTPUT": 0, "INOUT": 0}


def add(m):
    d = m.group("dir")
    counts[d] += 1
    if d == "INPUT":
        extra = "%sANTENNAGATEAREA %s ;" % (m.group("ind"), GATE_AREA)
    elif d == "OUTPUT":
        extra = "%sANTENNADIFFAREA %s ;" % (m.group("ind"), DIFF_AREA)
    else:
        return m.group(0)          # power/ground pins get nothing
    return m.group(0) + "\n" + extra


out = pat.sub(add, text)
open(path, "w", encoding="utf-8", newline="\n").write(out)
print("input pins  : %d  (ANTENNAGATEAREA %s)" % (counts["INPUT"], GATE_AREA))
print("output pins : %d  (ANTENNADIFFAREA %s)" % (counts["OUTPUT"], DIFF_AREA))
print("inout pins  : %d  (left alone)" % counts["INOUT"])
