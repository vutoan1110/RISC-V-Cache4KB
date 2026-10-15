transcript on
onerror {quit -code 1 -f}
do tb/compile_active_design.do

foreach test {
    tb_branch_predictor_core
    tb_valid_irq
    tb_native_interface
    tb_bht
    tb_regfile
    tb_branch_predictor
    tb_alu_zmmul
} {
    echo "===== CORE REGRESSION $test ====="
    vsim -onfinish stop -voptargs=+acc work.$test
    run -all
    quit -sim
}

echo {[PASS] Core, interrupt, native-interface, predictor, and ALU regression}
