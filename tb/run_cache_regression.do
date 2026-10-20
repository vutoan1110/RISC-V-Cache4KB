transcript on
onerror {quit -code 1 -f}
do tb/compile_active_design.do

foreach test {
    tb_icache
    tb_dcache
    tb_cache_event_accounting
    tb_set_associative_cache
    tb_victim_cache
} {
    echo "===== CACHE REGRESSION $test ====="
    vsim -onfinish stop -voptargs=+acc work.$test
    run -all
    quit -sim
}

foreach cfg {0 1 2} {
    echo "===== CACHE CONFIGURATION $cfg ====="
    vsim -onfinish stop -voptargs=+acc -gCACHE_CONFIG=$cfg work.tb_cache_configuration
    run -all
    quit -sim
}

vsim -onfinish stop -voptargs=+acc work.tb_cache_architecture_equivalence
run -all
quit -sim

echo {[PASS] Cache unit, configuration, and architecture-equivalence regression}
