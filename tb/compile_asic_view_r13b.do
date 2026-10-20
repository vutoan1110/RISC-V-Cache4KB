transcript on
onerror {quit -code 1 -f}

if {[file exists work_r13b]} {
    vdel -lib work_r13b -all
}
vlib work_r13b

# FLOW_JOURNAL Incident 93: copy of compile_asic_view.do for the experimental RTL asic/snapshots/rtl_r13b
# (library work_r13b). ASIC-view compile: the same RTL and testbenches as compile_active_design.do,
# with the memories the ASIC actually builds -- the Sky130 SRAM macro models,
# cache_data_ram_sram4.v in place of icache_data_ram.v / dcache_data_ram.v, and
# axi_ram_32_asic_macro.v in place of hdl/axi/axi_ram_32.v. These wrappers had
# never been simulated before; every ASIC number was produced from them.
#
# Only SoC-level benches are meaningful here. Unit benches that drive
# axi_ram_32's test hooks (stalls, injected errors) compile, but the macro
# wrapper ignores those hooks by design.
vlog -work work_r13b -timescale 1ns/1ps \
    asic/soc_dm_4kb/macros/verilog/sky130_sram_1kbyte_1rw1r_32x256_8.v \
    asic/soc_dm_4kb/macros/verilog/sky130_sram_2kbyte_1rw1r_32x512_8.v

# Processor core and native request/response wrapper.
vlog -work work_r13b -sv +define+ASIC_VIEW_SIM \
    asic/snapshots/rtl_r13b/hdl/alu.v \
    asic/snapshots/rtl_r13b/hdl/aludec.v \
    asic/snapshots/rtl_r13b/hdl/branch.v \
    asic/snapshots/rtl_r13b/hdl/predictor/bht_2bit.v \
    asic/snapshots/rtl_r13b/hdl/controller.v \
    asic/snapshots/rtl_r13b/hdl/datapath.v \
    asic/snapshots/rtl_r13b/hdl/extend.v \
    asic/snapshots/rtl_r13b/hdl/hazard_unit.v \
    asic/snapshots/rtl_r13b/hdl/maindec.v \
    asic/snapshots/rtl_r13b/hdl/regfile.v \
    asic/snapshots/rtl_r13b/hdl/riscv_core.v \
    asic/snapshots/rtl_r13b/hdl/riscv_core_native.v

# Active cache hierarchy.
vlog -work work_r13b -sv +define+ASIC_VIEW_SIM \
    asic/snapshots/rtl_r13b/hdl/cache/icache_tag_ram.v \
    asic/snapshots/rtl_r13b/asic/soc_dm_4kb/cache_data_ram_sram4.v \
    asic/snapshots/rtl_r13b/hdl/cache/icache_controller.v \
    asic/snapshots/rtl_r13b/hdl/cache/cache_dse_data_bank.v \
    asic/snapshots/rtl_r13b/hdl/cache/icache_dse_core.v \
    asic/snapshots/rtl_r13b/hdl/cache/icache.v \
    asic/snapshots/rtl_r13b/hdl/cache/dcache_tag_ram.v \
    asic/snapshots/rtl_r13b/hdl/cache/dcache_controller.v \
    asic/snapshots/rtl_r13b/hdl/cache/dcache_dse_core.v \
    asic/snapshots/rtl_r13b/hdl/cache/dcache.v

# AXI, APB, performance monitoring, peripherals, and active SoC.
vlog -work work_r13b -sv +define+ASIC_VIEW_SIM \
    asic/snapshots/rtl_r13b/hdl/axi/cache_axi_master.v \
    asic/snapshots/rtl_r13b/asic/soc_dm_4kb/axi_ram_32_asic_macro.v \
    asic/snapshots/rtl_r13b/hdl/axi/native_axi_lite_master.v \
    asic/snapshots/rtl_r13b/hdl/axi/axi_lite_to_apb.v \
    asic/snapshots/rtl_r13b/hdl/bus/soc_address_decoder.v \
    asic/snapshots/rtl_r13b/hdl/apb_display_regs.v \
    asic/snapshots/rtl_r13b/hdl/apb_timer.v \
    asic/snapshots/rtl_r13b/hdl/perf_counters.v \
    asic/snapshots/rtl_r13b/hdl/apb_performance_monitor.v \
    asic/snapshots/rtl_r13b/hdl/performance_observability.v \
    asic/snapshots/rtl_r13b/hdl/hex7seg_decoder.v \
    asic/snapshots/rtl_r13b/hdl/lcd_1602_hex.v \
    asic/snapshots/rtl_r13b/hdl/fifo.sv \
    asic/snapshots/rtl_r13b/hdl/baudrate_gen_block.sv \
    asic/snapshots/rtl_r13b/hdl/rx_block.sv \
    asic/snapshots/rtl_r13b/hdl/tx_block.sv \
    asic/snapshots/rtl_r13b/hdl/uart_core.sv \
    asic/snapshots/rtl_r13b/hdl/uart_apb.v \
    asic/snapshots/rtl_r13b/hdl/soc_top.v \
    asic/snapshots/rtl_r13b/asic/soc_dm_4kb/soc_asic_top.v

# Simulation-only assertions and functional coverage.
vlog -work work_r13b -sv +define+ASIC_VIEW_SIM \
    verification/assertions/core_assertions.sv \
    verification/assertions/axi_assertions.sv \
    verification/assertions/cache_assertions.sv \
    verification/coverage/core_coverage.sv

# Active self-checking testbenches and reusable backend model.
vlog -work work_r13b -sv +define+ASIC_VIEW_SIM \
    tb/cache_backend_model.sv \
    tb/branch_predictor_core_tb.sv \
    tb/valid_irq_tb.sv \
    tb/native_interface_tb.sv \
    tb/icache_tb.sv \
    tb/dcache_tb.sv \
    tb/mmio_bypass_tb.sv \
    tb/axi_memory_tb.sv \
    tb/axi_mmio_tb.sv \
    tb/soc_integration_tb.sv \
    tb/cache_event_accounting_tb.sv \
    tb/performance_counters_tb.sv \
    tb/uart_apb_tb.sv \
    tb/bht_tb.sv \
    tb/branch_predictor_tb.sv \
    tb/predictor_axi_tb.sv \
    tb/alu_zmmul_tb.sv \
    tb/directed_isa_tb.sv \
    tb/random_trace_tb.sv \
    tb/architecture_signature_tb.sv \
    tb/set_associative_cache_tb.sv \
    tb/victim_cache_tb.sv \
    tb/cache_configuration_tb.sv \
    tb/cache_architecture_equivalence_tb.sv \
    tb/benchmark_snapshot_tb.sv \
    tb/asic_view_checker.sv \
    tb/asic_view_checker_isa.sv \
    tb/top_wrapper_sync_tb.sv \
    tb/cache_conflict_experiment_tb.sv

echo {[PASS] ASIC-view RTL and verification sources compiled}
