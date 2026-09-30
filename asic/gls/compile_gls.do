# Gate-level simulation library for tb_gls_soc (asic/gls/tb_gls_soc.sv).
#   vsim -c -do "set NETLIST <path>; do asic/gls/compile_gls.do; quit -f"
# Run from the research root. FUNCTIONAL selects the sky130 cells' zero-delay
# functional models (no specify blocks); the SRAM macro models are the same
# OpenRAM behavioural models the ASIC-view RTL simulation uses.
onerror {quit -code 1 -f}
if {![info exists NETLIST]} { echo {[FAIL] set NETLIST first}; quit -code 1 -f }
if {[file exists work_gls]} { vdel -lib work_gls -all }
vlib work_gls
vlog -work work_gls -timescale 1ns/1ps +define+FUNCTIONAL +define+UNIT_DELAY=#0 -suppress 2892,2902 \
    asic/gls/lib/primitives.v asic/gls/lib/sky130_fd_sc_hd.v
vlog -work work_gls -timescale 1ns/1ps \
    asic/soc_dm_4kb/macros/verilog/sky130_sram_2kbyte_1rw1r_32x512_8.v \
    asic/soc_dm_4kb/macros/verilog/sky130_sram_1kbyte_1rw1r_32x256_8.v
vlog -work work_gls -timescale 1ns/1ps -suppress 2892 $NETLIST
# R14 (RAM16K_CHANGES.md): set TB_DEFINES "+define+GLS_RAM16K" for the 16 KiB (8-bank) netlist.
if {![info exists TB_DEFINES]} { set TB_DEFINES "" }
vlog -work work_gls -sv {*}$TB_DEFINES asic/gls/tb_gls_soc.sv
echo "\[PASS\] gate-level library compiled from $NETLIST"
