// RTL needed by the riscv_core_native DUT, in the order used by
// tb/compile_active_design.do. No file under tb/ is compiled here: the UVM
// environment is parallel to the directed testbenches, not a replacement.
hdl/alu.v
hdl/aludec.v
hdl/branch.v
hdl/predictor/bht_2bit.v
hdl/controller.v
hdl/datapath.v
hdl/extend.v
hdl/hazard_unit.v
hdl/maindec.v
hdl/regfile.v
hdl/riscv_core.v
hdl/riscv_core_native.v

// AXI master, the DUT of the phase 4 environment.
hdl/axi/cache_axi_master.v

// Full SoC, the DUT of the phase 5 environment, in the order of
// tb/compile_active_design.do.
hdl/cache/icache_tag_ram.v
hdl/cache/icache_data_ram.v
hdl/cache/icache_controller.v
hdl/cache/cache_dse_data_bank.v
hdl/cache/icache_dse_core.v
hdl/cache/icache.v
hdl/cache/dcache_tag_ram.v
hdl/cache/dcache_data_ram.v
hdl/cache/dcache_controller.v
hdl/cache/dcache_dse_core.v
hdl/cache/dcache.v
hdl/axi/axi_ram_32.v
hdl/axi/native_axi_lite_master.v
hdl/axi/axi_lite_to_apb.v
hdl/bus/soc_address_decoder.v
hdl/apb_display_regs.v
hdl/apb_timer.v
hdl/perf_counters.v
hdl/apb_performance_monitor.v
hdl/performance_observability.v
hdl/hex7seg_decoder.v
hdl/lcd_1602_hex.v
hdl/fifo.sv
hdl/baudrate_gen_block.sv
hdl/rx_block.sv
hdl/tx_block.sv
hdl/uart_core.sv
hdl/uart_apb.v
hdl/soc_top.v

// Simulation-only checkers, reused as is by all three environments.
verification/assertions/core_assertions.sv
verification/assertions/axi_assertions.sv
verification/assertions/cache_assertions.sv
verification/coverage/core_coverage.sv
