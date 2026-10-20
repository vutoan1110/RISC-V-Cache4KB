# sw_metrics/irq/compile_irq.do -- the active FPGA-view design (same sources and order as
# tb/compile_active_design.do) plus tb_irq_metrics.sv, into its own library work_irq, so the
# interrupt measurement never collides with a batch in work (vsim-1962). Run from the repo root.
transcript on
onerror {quit -code 1 -f}

if {[file exists work_irq]} {
    vdel -lib work_irq -all
}
vlib work_irq

vlog -work work_irq -sv \
    hdl/alu.v \
    hdl/aludec.v \
    hdl/branch.v \
    hdl/predictor/bht_2bit.v \
    hdl/controller.v \
    hdl/datapath.v \
    hdl/extend.v \
    hdl/hazard_unit.v \
    hdl/maindec.v \
    hdl/regfile.v \
    hdl/riscv_core.v \
    hdl/riscv_core_native.v

vlog -work work_irq -sv \
    hdl/cache/icache_tag_ram.v \
    hdl/cache/icache_data_ram.v \
    hdl/cache/icache_controller.v \
    hdl/cache/cache_dse_data_bank.v \
    hdl/cache/icache_dse_core.v \
    hdl/cache/icache_nway_core.v \
    hdl/cache/icache.v \
    hdl/cache/dcache_tag_ram.v \
    hdl/cache/dcache_data_ram.v \
    hdl/cache/dcache_controller.v \
    hdl/cache/dcache_dse_core.v \
    hdl/cache/dcache_nway_core.v \
    hdl/cache/dcache.v

vlog -work work_irq -sv \
    hdl/axi/cache_axi_master.v \
    hdl/axi/axi_ram_32.v \
    hdl/axi/native_axi_lite_master.v \
    hdl/axi/axi_lite_to_apb.v \
    hdl/bus/soc_address_decoder.v \
    hdl/apb_display_regs.v \
    hdl/apb_timer.v \
    hdl/perf_counters.v \
    hdl/apb_performance_monitor.v \
    hdl/performance_observability.v \
    hdl/hex7seg_decoder.v \
    hdl/lcd_1602_hex.v \
    hdl/fifo.sv \
    hdl/baudrate_gen_block.sv \
    hdl/rx_block.sv \
    hdl/tx_block.sv \
    hdl/uart_core.sv \
    hdl/uart_apb.v \
    hdl/soc_top.v

vlog -work work_irq -sv sw_metrics/irq/tb_irq_metrics.sv

echo {[PASS] interrupt-metric library compiled}
