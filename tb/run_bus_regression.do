transcript on
onerror {quit -code 1 -f}
do tb/compile_active_design.do

foreach test {
    tb_mmio_bypass
    tb_axi_memory
    tb_axi_mmio
    tb_soc_integration
    tb_performance_counters
    tb_predictor_axi
} {
    echo "===== BUS/SOC REGRESSION $test ====="
    vsim -onfinish stop -voptargs=+acc work.$test
    run -all
    quit -sim
}

echo {[PASS] AXI, APB, SoC, performance-monitor, and predictor-stall regression}
