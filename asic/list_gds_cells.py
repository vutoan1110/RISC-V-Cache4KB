# -*- coding: utf-8 -*-
# Are the cells Magic cannot find actually in the macro GDS, or did Magic rename
# them on read? A "_2" suffix on a cell name is what Magic appends when a name
# collides with one already loaded from somewhere else.
import os, pya
ly = pya.Layout(); ly.read(os.environ["MACRO_GDS"])
names = sorted(ly.cell(i).name for i in range(ly.cells()))
print("cells in macro GDS: %d" % len(names))
susp = [n for n in names if n.endswith("_2")]
print("ending in _2: %d" % len(susp))
for n in susp[:12]: print("   ", n)
for probe in ("sky130_fd_bd_sram__openram_dff",
              "sky130_fd_bd_sram__openram_dp_cell",
              "sky130_sram_2kbyte_1rw1r_32x512_8_bitcell_array"):
    print("%-50s present=%s   _2 variant=%s"
          % (probe, probe in names, (probe + "_2") in names))
