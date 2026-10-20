#!/usr/bin/env python3
"""R12b (NHAT_KY.md 2026-09-26): keep R12's encoded selects for the FPGA, restore
R9b's one-hot selects for the ASIC netlist only.

Measured (NHAT_KY.md 2026-09-26): OpenLane synthesis of the R12 RTL does not
finish. ABC (AREA_0 script) stalls in `fraig_restore` on the 136k-node AIG
(>12 min in a step-timed replay, >70 min inside r12_d40), while the pre-R12
RTL synthesises in 2 min 14 s end to end. The two forms are proven equal in
every reachable state (asic/equiv/r12_fv: rsel_w == 1 << result_src_w and
ld_lane_w == 1 << load_byte_offset_w, k-induction), so each tool gets the form
it handles well:
  __openlane__ defined (OpenLane lint/synthesis/EQY): R9b one-hot AND-OR, text
      identical to d030ad12 after preprocessing -> the synthesised netlist must
      be byte-identical to the one r10A..r10E were built from (checked);
  otherwise (Quartus, Questa, lint_rtl): R12 encoded muxes (-145 LE on vc4_4kb).

    python scripts/apply_r12b.py [root]
"""
import os
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
path = os.path.join(ROOT, "hdl/datapath.v")
s = open(path, newline="").read()
if "\r\n" in s:
    sys.exit("[FAIL] datapath.v is CRLF")

ONEHOT_RESULT = ("assign result_w = ({32{rsel_w[3]}} & upper_w)       |\n"
                 "                  ({32{rsel_w[2]}} & pc_plus4_w)    |\n"
                 "                  ({32{rsel_w[1]}} & rd_data_final) |\n"
                 "                  ({32{rsel_w[0]}} & alu_result_w)  ;\n")
ONEHOT_BYTE = ("    load_byte = ({8{ld_lane_w[0]}} & rd_data_w[7:0])   |\n"
               "                ({8{ld_lane_w[1]}} & rd_data_w[15:8])  |\n"
               "                ({8{ld_lane_w[2]}} & rd_data_w[23:16]) |\n"
               "                ({8{ld_lane_w[3]}} & rd_data_w[31:24]);\n")
edits = [
    ("reg  [3:0]  ld_kind_w;\n",
     "reg  [3:0]  ld_kind_w;\n"
     "`ifdef __openlane__\n"
     "// R12b: the ASIC keeps R9b's one-hot copies (see the result_w note below)\n"
     "reg  [3:0]  ld_lane_w;        // one-hot byte offset, reset = lane 0\n"
     "reg  [3:0]  rsel_w;           // one-hot {upper, pc+4, load, alu}, reset = alu\n"
     "`endif\n"),
    ("        ld_kind_w <= 4'b0000;\n    end\n",
     "        ld_kind_w <= 4'b0000;\n"
     "`ifdef __openlane__\n"
     "        ld_lane_w <= 4'b0001;\n"
     "        rsel_w    <= 4'b0001;\n"
     "`endif\n"
     "    end\n"),
    ("                      r9_is_load_m && (instr_m[14:12] == 3'b000)};\n    end\nend\n",
     "                      r9_is_load_m && (instr_m[14:12] == 3'b000)};\n"
     "`ifdef __openlane__\n"
     "        ld_lane_w <= 4'b0001 << mem_byte_offset_m;\n"
     "        rsel_w    <= {result_src_m == 2'b11, result_src_m == 2'b10,\n"
     "                      result_src_m == 2'b01, result_src_m == 2'b00};\n"
     "`endif\n"
     "    end\nend\n"),
    ("assign result_w = (result_src_w == 2'b11) ? upper_w       :\n"
     "                  (result_src_w == 2'b10) ? pc_plus4_w    :\n"
     "                  (result_src_w == 2'b01) ? rd_data_final :\n"
     "                                            alu_result_w;\n",
     "// R12b: the ASIC netlist keeps R9b's one-hot AND-OR. On the encoded form above\n"
     "// OpenLane's ABC stalls in fraig_restore (NHAT_KY.md 2026-09-26); the two\n"
     "// forms are proven equal (asic/equiv/r12_fv, k-induction).\n"
     "`ifdef __openlane__\n" + ONEHOT_RESULT + "`else\n"
     "assign result_w = (result_src_w == 2'b11) ? upper_w       :\n"
     "                  (result_src_w == 2'b10) ? pc_plus4_w    :\n"
     "                  (result_src_w == 2'b01) ? rd_data_final :\n"
     "                                            alu_result_w;\n"
     "`endif\n"),
    ("    case(load_byte_offset_w)\n"
     "        2'b00:   load_byte = rd_data_w[7:0];\n"
     "        2'b01:   load_byte = rd_data_w[15:8];\n"
     "        2'b10:   load_byte = rd_data_w[23:16];\n"
     "        default: load_byte = rd_data_w[31:24];\n"
     "    endcase\n",
     "`ifdef __openlane__\n" + ONEHOT_BYTE + "`else\n"
     "    case(load_byte_offset_w)\n"
     "        2'b00:   load_byte = rd_data_w[7:0];\n"
     "        2'b01:   load_byte = rd_data_w[15:8];\n"
     "        2'b10:   load_byte = rd_data_w[23:16];\n"
     "        default: load_byte = rd_data_w[31:24];\n"
     "    endcase\n"
     "`endif\n"),
]
for old, new in edits:
    if s.count(old) != 1:
        sys.exit("[FAIL] datapath.v anchor x%d:\n%s" % (s.count(old), old[:200]))
    s = s.replace(old, new)
open(path, "w", newline="").write(s)
print("[OK] %s: R12b applied (ASIC one-hot under __openlane__, FPGA encoded otherwise)" % path)
