set ::env(DRT_THREADS) 32
set ::env(STEP_ID) OpenROAD.DetailedRouting
set ::env(TECH_LEF) /home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef
set ::env(MACRO_LEFS) "/mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/macros/lef/sky130_sram_2kbyte_1rw1r_32x512_8.lef /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/macros/lef/sky130_sram_1kbyte_1rw1r_32x256_8.lef"
set ::env(STD_CELL_LIBRARY) sky130_fd_sc_hd
set ::env(VDD_PIN) VPWR
set ::env(VDD_PIN_VOLTAGE) 1.80
set ::env(GND_PIN) VGND
set ::env(TECH_LEFS) "\"nom_*\" /home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef \"min_*\" /home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__min.tlef \"max_*\" /home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__max.tlef"
set ::env(GPIO_PADS_LEF) "/home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_io/lef/sky130_fd_io.lef /home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_io/lef/sky130_ef_io.lef"
set ::env(GPIO_PADS_LEF_CORE_SIDE) "/home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.tech/openlane/custom_cells/lef/sky130_fd_io_core.lef /home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.tech/openlane/custom_cells/lef/sky130_ef_io_core.lef"
set ::env(GPIO_PADS_VERILOG) /home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_io/verilog/sky130_ef_io.v
set ::env(GPIO_PAD_CELLS) "\"sky130_fd_io*\" \"sky130_ef_io*\""
set ::env(PRIMARY_GDSII_STREAMOUT_TOOL) klayout
set ::env(DEFAULT_CORNER) nom_tt_025C_1v80
set ::env(STA_CORNERS) "nom_tt_025C_1v80 nom_ss_100C_1v60 nom_ff_n40C_1v95 min_tt_025C_1v80 min_ss_100C_1v60 min_ff_n40C_1v95 max_tt_025C_1v80 max_ss_100C_1v60 max_ff_n40C_1v95"
set ::env(FP_TRACKS_INFO) /home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.tech/openlane/sky130_fd_sc_hd/tracks.info
set ::env(FP_TAPCELL_DIST) 13
set ::env(FP_IO_HLAYER) met3
set ::env(FP_IO_VLAYER) met2
set ::env(RT_MIN_LAYER) met1
set ::env(RT_MAX_LAYER) met5
set ::env(SCL_GROUND_PINS) "VGND VNB"
set ::env(SCL_POWER_PINS) "VPWR VPB"
set ::env(TRISTATE_CELLS) "\"sky130_fd_sc_hd__ebuf*\""
set ::env(FILL_CELL) "\"sky130_fd_sc_hd__fill*\""
set ::env(DECAP_CELL) "sky130_ef_sc_hd__decap_12 sky130_fd_sc_hd__decap_8 sky130_fd_sc_hd__decap_6 sky130_fd_sc_hd__decap_4 sky130_fd_sc_hd__decap_3"
set ::env(LIB) "\"*_tt_025C_1v80\" /home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib \"*_ss_100C_1v60\" /home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ss_100C_1v60.lib \"*_ff_n40C_1v95\" /home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ff_n40C_1v95.lib"
set ::env(CELL_LEFS) "/home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/lef/sky130_ef_sc_hd.lef /home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef"
set ::env(CELL_GDS) /home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/gds/sky130_fd_sc_hd.gds
set ::env(CELL_VERILOG_MODELS) "/home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v /home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v"
set ::env(CELL_BB_VERILOG_MODELS) "/home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd__blackbox.v /home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd__blackbox_pp.v"
set ::env(CELL_SPICE_MODELS) "/home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_ef_sc_hd__decap_12.spice /home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_ef_sc_hd__fill_12.spice /home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_ef_sc_hd__fill_4.spice /home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_ef_sc_hd__fill_8.spice /home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice"
set ::env(SYNTH_EXCLUDED_CELL_FILE) /home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.tech/openlane/sky130_fd_sc_hd/no_synth.cells
set ::env(PNR_EXCLUDED_CELL_FILE) /home/toanl/.volare/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.tech/openlane/sky130_fd_sc_hd/drc_exclude.cells
set ::env(OUTPUT_CAP_LOAD) 33.442
set ::env(MAX_FANOUT_CONSTRAINT) 8
set ::env(MAX_TRANSITION_CONSTRAINT) 0.75
set ::env(MAX_CAPACITANCE_CONSTRAINT) 0.2
set ::env(CLOCK_UNCERTAINTY_CONSTRAINT) 0.25
set ::env(CLOCK_TRANSITION_CONSTRAINT) 0.1499999999999999944488848768742172978818416595458984375
set ::env(TIME_DERATING_CONSTRAINT) 5
set ::env(IO_DELAY_CONSTRAINT) 20
set ::env(SYNTH_DRIVING_CELL) sky130_fd_sc_hd__inv_2/Y
set ::env(SYNTH_TIEHI_CELL) sky130_fd_sc_hd__conb_1/HI
set ::env(SYNTH_TIELO_CELL) sky130_fd_sc_hd__conb_1/LO
set ::env(SYNTH_BUFFER_CELL) sky130_fd_sc_hd__buf_2/A/X
set ::env(WELLTAP_CELL) sky130_fd_sc_hd__tapvpwrvgnd_1
set ::env(ENDCAP_CELL) sky130_fd_sc_hd__decap_3
set ::env(PLACE_SITE) unithd
set ::env(CELL_PAD_EXCLUDE) "\"sky130_fd_sc_hd__tap*\" \"sky130_fd_sc_hd__decap*\" \"sky130_ef_sc_hd__decap*\" \"sky130_fd_sc_hd__fill*\""
set ::env(DIODE_CELL) sky130_fd_sc_hd__diode_2/DIODE
set ::env(DESIGN_NAME) soc_asic_top
set ::env(CLOCK_PERIOD) 20.0
set ::env(CLOCK_PORT) clk
set ::env(DIE_AREA) "0 0 2800 2900"
set ::env(MACROS) "sky130_sram_2kbyte_1rw1r_32x512_8 \"gds /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/macros/gds/sky130_sram_2kbyte_1rw1r_32x512_8.magicsafe.gds lef /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/macros/lef/sky130_sram_2kbyte_1rw1r_32x512_8.lef instances \\\"\\\\\\\"u_soc.u_axi_ram.g_bank\\\\\\\\\\\\\\\[0].u_bank\\\\\\\" \\\\\\\"location \\\\\\\\\\\\\\\"150.0 150.0\\\\\\\\\\\\\\\" orientation N\\\\\\\" \\\\\\\"u_soc.u_axi_ram.g_bank\\\\\\\\\\\\\\\[1].u_bank\\\\\\\" \\\\\\\"location \\\\\\\\\\\\\\\"150.0 650.0\\\\\\\\\\\\\\\" orientation N\\\\\\\" \\\\\\\"u_soc.u_axi_ram.g_bank\\\\\\\\\\\\\\\[2].u_bank\\\\\\\" \\\\\\\"location \\\\\\\\\\\\\\\"150.0 1150.0\\\\\\\\\\\\\\\" orientation N\\\\\\\" \\\\\\\"u_soc.u_axi_ram.g_bank\\\\\\\\\\\\\\\[3].u_bank\\\\\\\" \\\\\\\"location \\\\\\\\\\\\\\\"150.0 1650.0\\\\\\\\\\\\\\\" orientation N\\\\\\\"\\\" vh \\\"\\\" nl /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/macros/verilog/sky130_sram_2kbyte_1rw1r_32x512_8.v pnl \\\"\\\" spef \\\"\\\" lib \\\"\\\\\\\"*\\\\\\\" /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/macros/lib/sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib\\\" spice \\\"\\\" sdf \\\"\\\" json_h None\" sky130_sram_1kbyte_1rw1r_32x256_8 \"gds /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/macros/gds/sky130_sram_1kbyte_1rw1r_32x256_8.magicsafe.gds lef /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/macros/lef/sky130_sram_1kbyte_1rw1r_32x256_8.lef instances \\\"\\\" vh \\\"\\\" nl /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/macros/verilog/sky130_sram_1kbyte_1rw1r_32x256_8.v pnl \\\"\\\" spef \\\"\\\" lib \\\"\\\\\\\"*\\\\\\\" /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/macros/lib/sky130_sram_1kbyte_1rw1r_32x256_8_TT_1p8V_25C.lib\\\" spice \\\"\\\" sdf \\\"\\\" json_h None\""
set ::env(FALLBACK_SDC_FILE) /mnt/e/Projects/RISCV-research/asic/openlane-local/openlane/scripts/base.sdc
set ::env(PDN_CONNECT_MACROS_TO_GRID) 1
set ::env(PDN_MACRO_CONNECTIONS) "\".*u_bank VPWR VGND vccd1 vssd1\""
set ::env(PDN_ENABLE_GLOBAL_CONNECTIONS) 1
set ::env(PNR_SDC_FILE) /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/soc.sdc
set ::env(DRT_OPT_ITERS) 64
set ::env(CURRENT_ODB) /mnt/e/Projects/RISCV-research/asic/soc_dm_4kb/runs/final_A/46-openroad-detailedrouting/soc_asic_top.odb
set ::env(SAVE_ODB) /mnt/e/Projects/RISCV-research/asic/pd_exp/rc_corr/soc_asic_top.odb
set ::env(SAVE_DEF) /mnt/e/Projects/RISCV-research/asic/pd_exp/rc_corr/soc_asic_top.def
set ::env(SAVE_SDC) /mnt/e/Projects/RISCV-research/asic/pd_exp/rc_corr/soc_asic_top.sdc
set ::env(SAVE_NETLIST) /mnt/e/Projects/RISCV-research/asic/pd_exp/rc_corr/soc_asic_top.nl.v
set ::env(SAVE_POWERED_NETLIST) /mnt/e/Projects/RISCV-research/asic/pd_exp/rc_corr/soc_asic_top.pnl.v
set ::env(LAYERS_RC) "li1 1.7536e-04 7.5294e-02,met1 1.6949e-04 8.9286e-04,met2 1.5578e-04 8.9286e-04,met3 1.7138e-04 1.5667e-04,met4 1.5175e-04 1.5667e-04,met5 1.7563e-04 1.7812e-05"
