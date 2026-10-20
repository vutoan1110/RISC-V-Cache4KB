#!/usr/bin/env python3
"""R12 (NHAT_KY.md 2026-09-26): give back the FPGA logic R9b cost, same function.

Measured (Quartus 20.1, vc4_4kb, NHAT_KY.md 2026-09-26): after R9 the DM+VC4
4 KiB point is 20,002-20,077 LE over four seeds, above the specification's
20,000 LE ("LE over 20,000 ... is still a FAIL against the specification",
docs/en/guides/01_RTL_QUARTUS_QPF_QSF_SOF.md). A map-only A/B of the old and
new RTL puts the whole increase in datapath's own logic (+216 LUTs; hazard
unit -21, controller -8). The one-hot AND-OR selects R9b introduced cannot be
packed into LUT4s the way a mux on an encoded select can (Quartus does not
know the select is one-hot): result_w (4 sources x 32 bits) and load_byte
(4 lanes x 8 bits). Rewriting only those two as muxes on the 2-bit registered
selects that already exist maps to 22,599 LE (22,744 before) and fits at
19,855 LE, +1.194 ns Slow-85C setup (seed 2).

Same function, register by register:
  rsel_w    : reset 4'b0001; if(!stall_pipe) <= onehot(result_src_m)
  result_src_w (controller): reset 2'b00; if(!stall_pipe) <= result_src_m
    => rsel_w == onehot(result_src_w) in every cycle (no flush on either).
  ld_lane_w : reset 4'b0001; if(!stall_pipe) <= 1 << mem_byte_offset_m
  load_byte_offset_w: reset 2'b00; if(!stall_pipe) <= mem_byte_offset_m
    => ld_lane_w == 1 << load_byte_offset_w in every cycle.
So result_w / load_byte computed from the encoded selects equal the one-hot
forms, and rsel_w / ld_lane_w become dead and are removed. ld_kind_w (the
one-hot load kind that took the opcode/funct3 decode off the W path) stays.
The R9 checker's reference already uses exactly these encoded forms.

    python scripts/apply_r12.py [root]
"""
import os
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
path = os.path.join(ROOT, "hdl/datapath.v")
s = open(path, newline="").read()
if "\r\n" in s:
    sys.exit("[FAIL] datapath.v is CRLF")

edits = [
    # result_w: AND-OR on rsel_w -> mux on result_src_w
    ("// R9b: one-hot result select registered at M->W (was decoded from result_src_w)\n"
     "assign result_w = ({32{rsel_w[3]}} & upper_w)       |\n"
     "                  ({32{rsel_w[2]}} & pc_plus4_w)    |\n"
     "                  ({32{rsel_w[1]}} & rd_data_final) |\n"
     "                  ({32{rsel_w[0]}} & alu_result_w)  ;\n",
     "// R12: mux on the registered 2-bit result_src_w. R9b used a one-hot AND-OR on\n"
     "// rsel_w (always == onehot(result_src_w)); Quartus cannot pack that into LUT4s\n"
     "// and the DM+VC4 4 KiB point went over the 20,000 LE budget.\n"
     "assign result_w = (result_src_w == 2'b11) ? upper_w       :\n"
     "                  (result_src_w == 2'b10) ? pc_plus4_w    :\n"
     "                  (result_src_w == 2'b01) ? rd_data_final :\n"
     "                                            alu_result_w;\n"),
    # load_byte: AND-OR on ld_lane_w -> case on load_byte_offset_w
    ("    // R9b: byte lane and load kind come from registered one-hot selects\n"
     "    load_byte = ({8{ld_lane_w[0]}} & rd_data_w[7:0])   |\n"
     "                ({8{ld_lane_w[1]}} & rd_data_w[15:8])  |\n"
     "                ({8{ld_lane_w[2]}} & rd_data_w[23:16]) |\n"
     "                ({8{ld_lane_w[3]}} & rd_data_w[31:24]);\n",
     "    // R9b: load kind from the registered one-hot ld_kind_w; R12: byte lane from\n"
     "    // the registered 2-bit load_byte_offset_w (ld_lane_w was its one-hot copy)\n"
     "    case(load_byte_offset_w)\n"
     "        2'b00:   load_byte = rd_data_w[7:0];\n"
     "        2'b01:   load_byte = rd_data_w[15:8];\n"
     "        2'b10:   load_byte = rd_data_w[23:16];\n"
     "        default: load_byte = rd_data_w[31:24];\n"
     "    endcase\n"),
    # the two dead registers
    ("reg  [3:0]  ld_lane_w;        // one-hot byte offset, reset = lane 0\n"
     "reg  [3:0]  rsel_w;           // one-hot {upper, pc+4, load, alu}, reset = alu\n", ""),
    ("        ld_kind_w <= 4'b0000;\n"
     "        ld_lane_w <= 4'b0001;\n"
     "        rsel_w    <= 4'b0001;\n",
     "        ld_kind_w <= 4'b0000;\n"),
    ("        ld_lane_w <= 4'b0001 << mem_byte_offset_m;\n"
     "        rsel_w    <= {result_src_m == 2'b11, result_src_m == 2'b10,\n"
     "                      result_src_m == 2'b01, result_src_m == 2'b00};\n", ""),
]
for old, new in edits:
    if s.count(old) != 1:
        sys.exit("[FAIL] datapath.v anchor x%d:\n%s" % (s.count(old), old[:160]))
    s = s.replace(old, new)
code = "\n".join(l.split("//")[0] for l in s.split("\n"))   # comments may name them
for dead in ("rsel_w", "ld_lane_w"):
    if dead in code:
        sys.exit("[FAIL] %s still referenced" % dead)
open(path, "w", newline="").write(s)
print("[OK] %s: R12 applied (result_w / load_byte on encoded selects, 2 dead registers removed)" % path)
