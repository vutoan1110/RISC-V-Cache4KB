#!/usr/bin/env bash
# FLOW_JOURNAL Incident 91: post-DRT antenna repair exploration (reads final_A, writes only here)
D=/mnt/e/Projects/RISCV-research/asic/pd_exp/hold_eco
export SCRIPTS_DIR=/mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts
export _TCL_ENV_IN=$D/env.tcl STEP_DIR=$D
export _SDC_IN=/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/x_E1/15-openroad-detailedrouting/soc_asic_top.sdc
V=/home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A
M=/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/macros/lib
export _MACRO_LIBS="$M/sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib $M/sky130_sram_1kbyte_1rw1r_32x256_8_TT_1p8V_25C.lib"
export _PNR_LIBS="$V/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib $_MACRO_LIBS"
export _PNR_EXCLUDED_CELLS="$(grep -v '^[[:space:]]*#' $V/libs.tech/openlane/sky130_fd_sc_hd/drc_exclude.cells | tr -s '[:space:]' ' ')"
OR=/nix/store/alhgaybdgmv706469rp57ggcyg3750yk-openroad-python3-3.11.9-env/bin/openroad
cd $D
echo "$(date -Is) start" > status.txt
/usr/bin/time -f "%e s %M kB" $OR -exit -no_splash $D/hold_eco_test.tcl > hold_eco_test.log 2>&1
echo "$(date -Is) end rc=$?" >> status.txt
grep -a -E "HOLDECO|worst slack|RSZ-|ERROR|rror" hold_eco_test.log | head -40
