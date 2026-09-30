#!/usr/bin/env bash
cd $(dirname $0)
export LIB_SS=$(ls /home/toanl/.volare/volare/sky130/versions/*/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ss_100C_1v60.lib | head -1)
/nix/store/q5ycjmn0d9awbcq05c75z2rmgwjgbc9g-opensta/bin/sta -no_splash -exit sta.tcl 2>&1 | grep -v "^Warning"
for m in cnt_a cnt_b; do echo "-- $m path cells:"; grep -cE "\(sky130" /tmp/r10k_$m.txt; grep -E "data arrival|slack" /tmp/r10k_$m.txt; done
