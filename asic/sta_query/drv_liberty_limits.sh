#!/usr/bin/env bash
# DRV counts of a signed layout at one corner: the flow's SDC limits and the Liberty (PDK) pin limits alone
# (drv_liberty_limits.tcl). Uses the final netlist and SDC of the fill-insertion step (the SDC is written with
# literal values) and the RCX SPEF of the corner's RC case. Read only for the run directory.
#   bash drv_liberty_limits.sh <run dir> <corner, e.g. nom_tt_025C_1v80> <output prefix>
set -euo pipefail
RUN=$(realpath "$1"); CORNER=$2; OUT=$3
FILL=$(ls -d $RUN/*-openroad-fillinsertion | tail -1)
RCX=$(ls -d $RUN/*-openroad-rcx | tail -1)
rc=${CORNER%%_*}                                   # nom / min / max
pv=${CORNER#*_}; pv=${pv%%_*}                      # tt / ss / ff
case $pv in tt) lib=tt_025C_1v80 ;; ss) lib=ss_100C_1v60 ;; ff) lib=ff_n40C_1v95 ;; *) echo "bad corner $CORNER"; exit 2 ;; esac
V=/home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A
L=$V/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__$lib.lib
# the OpenRAM macros have TT Liberty only; the sign-off STA uses the same files at every corner
MD=$(dirname $(dirname $RUN))/macros/lib
[ -d $MD ] || MD=/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/macros/lib   # SA2 / DM_VC4 runs read the DM macro views
MAC=$(ls $MD/*TT_1p8V_25C.lib | tr '\n' ' ')
export SQ_NETLIST=$FILL/soc_asic_top.nl.v SQ_SPEF=$(ls $RCX/$rc/*.spef | head -1) SQ_SDC=$FILL/soc_asic_top.sdc
export SQ_LIBS="$L $MAC" SQ_OUT=$OUT SQ_CORNER=$CORNER
OR=/nix/store/q5ycjmn0d9awbcq05c75z2rmgwjgbc9g-opensta/bin/sta   # standalone OpenSTA: no technology LEF needed
$OR -exit -no_splash "$(dirname "$(realpath "$0")")/drv_liberty_limits.tcl" 2>&1 | grep -E "^DRV|ERROR|Error" | head -20
