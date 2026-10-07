transcript on
onerror {quit -code 1 -f}

# ASIC-view compile for the SA2 / DM_VC4 ASIC builds (2026-09-30, NHAT_KY.md: SA2 and DM_VC4
# ASIC builds). Same sources and order as tb/compile_asic_view.do, with three differences:
#   1. the RTL comes from the frozen PD snapshot asic/snapshots/rtl_r14, the exact files the
#      OpenLane configs read, not from the live hdl/ tree;
#   2. hdl/cache/cache_dse_data_bank.v is replaced by asic/dse_sram/cache_dse_data_bank_sram.v
#      (32x256 OpenRAM macros, with its simulation-only register-bank shadow);
#   3. its own library, work_asic_dse, so it never collides with the chain's work_asic.
# cache_data_ram_sram4.v stays in, so CACHE_CONFIG 0 runs here too and must reproduce the
# DM ASIC view. ASIC_TOP selects which soc_asic_top is compiled (only the wrapper
# synchroniser bench uses it); default is the SA2 build.
if {![info exists ASIC_TOP]} { set ASIC_TOP asic/soc_sa2_4kb/soc_asic_top.v }
set R asic/snapshots/rtl_r14
if {![info exists L]} { set L work_asic_dse }

if {[file exists $L]} {
    vdel -lib $L -all
}
vlib $L

vlog -work $L -timescale 1ns/1ps \
    asic/soc_dm_4kb/macros/verilog/sky130_sram_1kbyte_1rw1r_32x256_8.v \
    asic/soc_dm_4kb/macros/verilog/sky130_sram_2kbyte_1rw1r_32x512_8.v

# Processor core and native request/response wrapper.
vlog -work $L -sv +define+ASIC_VIEW_SIM \
    $R/hdl/alu.v \
    $R/hdl/aludec.v \
    $R/hdl/branch.v \
    $R/hdl/predictor/bht_2bit.v \
    $R/hdl/controller.v \
    $R/hdl/datapath.v \
    $R/hdl/extend.v \
    $R/hdl/hazard_unit.v \
    $R/hdl/maindec.v \
    $R/hdl/regfile.v \
    $R/hdl/riscv_core.v \
    $R/hdl/riscv_core_native.v

# Cache hierarchy: DM data RAMs and the DSE data bank both on macros.
vlog -work $L -sv +define+ASIC_VIEW_SIM \
    $R/hdl/cache/icache_tag_ram.v \
    $R/asic/soc_dm_4kb/cache_data_ram_sram4.v \
    $R/hdl/cache/icache_controller.v \
    asic/dse_sram/cache_dse_data_bank_sram.v \
    $R/hdl/cache/icache_dse_core.v \
    $R/hdl/cache/icache.v \
    $R/hdl/cache/dcache_tag_ram.v \
    $R/hdl/cache/dcache_controller.v \
    $R/hdl/cache/dcache_dse_core.v \
    $R/hdl/cache/dcache.v

# AXI, APB, performance monitoring, peripherals, and SoC.
vlog -work $L -sv +define+ASIC_VIEW_SIM \
    $R/hdl/axi/cache_axi_master.v \
    $R/asic/soc_dm_4kb/axi_ram_32_asic_macro.v \
    $R/hdl/axi/native_axi_lite_master.v \
    $R/hdl/axi/axi_lite_to_apb.v \
    $R/hdl/bus/soc_address_decoder.v \
    $R/hdl/apb_display_regs.v \
    $R/hdl/apb_timer.v \
    $R/hdl/perf_counters.v \
    $R/hdl/apb_performance_monitor.v \
    $R/hdl/performance_observability.v \
    $R/hdl/hex7seg_decoder.v \
    $R/hdl/lcd_1602_hex.v \
    $R/hdl/fifo.sv \
    $R/hdl/baudrate_gen_block.sv \
    $R/hdl/rx_block.sv \
    $R/hdl/tx_block.sv \
    $R/hdl/uart_core.sv \
    $R/hdl/uart_apb.v \
    $R/hdl/soc_top.v \
    $ASIC_TOP

# Simulation-only assertions and functional coverage.
vlog -work $L -sv +define+ASIC_VIEW_SIM \
    verification/assertions/core_assertions.sv \
    verification/assertions/axi_assertions.sv \
    verification/assertions/cache_assertions.sv \
    verification/coverage/core_coverage.sv

# SoC-level benches used on this library (benchmark snapshot, directed ISA, wrapper
# synchronisers) and their ASIC-view checkers. The directed ISA bench is the DSE copy
# (scripts/metrics/directed_isa_dse_tb.sv, same module name): the original wires one assertion
# input to a DM-only signal and cannot elaborate for CACHE_CONFIG 1 or 2.
vlog -work $L -sv +define+ASIC_VIEW_SIM \
    tb/cache_backend_model.sv \
    scripts/metrics/directed_isa_dse_tb.sv \
    tb/benchmark_snapshot_tb.sv \
    tb/asic_view_checker.sv \
    tb/asic_view_checker_isa.sv \
    tb/top_wrapper_sync_tb.sv

echo {[PASS] ASIC-view RTL and verification sources compiled}
