#!/usr/bin/env bash
# FLOW_JOURNAL Incident 93: bisect the x_E3 crash in disconnected_pins.py (copy of the script with a trace print).
D=/mnt/e/Projects/RISCV-research/asic/pd_exp/dcp
V=/home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd
OR=/nix/store/alhgaybdgmv706469rp57ggcyg3750yk-openroad-python3-3.11.9-env/bin/openroad
IN=${1:-/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/x_E3/17-openroad-postrouteholdeco/soc_asic_top.odb}
cd $D
$OR -exit -no_splash -python $D/odbpy/disconnected_pins.py --input-lef $V/techlef/sky130_fd_sc_hd__nom.tlef --input-lef $V/lef/sky130_ef_sc_hd.lef --input-lef $V/lef/sky130_fd_sc_hd.lef --ignore-module sky130_sram_1kbyte_1rw1r_32x256_8 --ignore-module sky130_sram_2kbyte_1rw1r_32x512_8 --write-full-table-to $D/full.txt --output-odb $D/out.odb --output-def $D/out.def $IN > $D/trace.log 2>&1
echo "rc=$?"
