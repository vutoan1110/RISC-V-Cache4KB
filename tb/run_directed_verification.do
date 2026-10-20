transcript on
onerror {quit -code 1 -f}
do tb/compile_active_design.do

foreach test {tb_alu_zmmul tb_directed_isa} {
    echo "===== DIRECTED VERIFICATION $test ====="
    vsim -onfinish stop -voptargs=+acc work.$test
    run -all
    quit -sim
}

echo {[PASS] Directed ISA, retirement, assertion, and coverage regression}
