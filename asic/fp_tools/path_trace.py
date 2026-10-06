# FLOW_JOURNAL Incident 96: where does a timing path physically go? Reads the FIRST path of an OpenSTA max.rpt,
# looks up every instance on the data path (from the startpoint's data pin on) in the step's ODB and prints its
# location, the stage delay, the fanout of the net it drives, and the Manhattan distance from the previous stage.
# Run: openroad -python -exit path_trace.py <odb> <max.rpt> [path index, 1-based]
import re
import sys

import odb

path_odb, rpt = sys.argv[1], sys.argv[2]
which = int(sys.argv[3]) if len(sys.argv) > 3 else 1
db = odb.dbDatabase.create()
odb.read_db(db, path_odb)
block = db.getChip().getBlock()
dbu = block.getDefUnits()
lines = open(rpt).read().split("\n")
starts = [i for i, l in enumerate(lines) if l.startswith("Startpoint")]
s = starts[which - 1]
e = next(i for i in range(s, len(lines)) if "data arrival time" in lines[i])
print(lines[s].strip())
print(lines[s + 2].strip())
started = False
prev = None
tot = 0.0
for l in lines[s:e]:
    m = re.match(r"^\s+((?:[-\d.]+\s+){2,4})([-\d.]+)\s+([v^])\s+(\S+)\s+\((\S+)\)", l)
    if not m:
        continue
    nums = m.group(1).split()
    pin, cell = m.group(4), m.group(5)
    sp_inst = lines[s].split(":", 1)[1].strip().split()[0]
    if pin.rsplit("/", 1)[0] == sp_inst and len(nums) >= 3:
        started = True          # the startpoint's own output (CLK->Q or macro dout) begins the data path
    if not started or len(nums) < 3:      # output-pin rows only (one per stage)
        continue
    inst_name = pin.rsplit("/", 1)[0]
    inst = block.findInst(inst_name)
    if inst is None:
        inst = block.findInst(inst_name.replace("\\", ""))
    if inst is None:
        print("   ?", inst_name)
        continue
    bb = inst.getBBox()
    x, y = (bb.xMin() + bb.xMax()) / 2 / dbu, (bb.yMin() + bb.yMax()) / 2 / dbu
    d = float(nums[-1])
    tot += d
    step = abs(x - prev[0]) + abs(y - prev[1]) if prev else 0.0
    prev = (x, y)
    print("   %-58s %-22s fo %3s  (%6.0f,%6.0f)  +%5.0f um  %.3f ns  cum %.2f" % (
        inst_name[-58:], cell.replace("sky130_fd_sc_hd__", "")[:22], nums[0], x, y, step, d, tot))
