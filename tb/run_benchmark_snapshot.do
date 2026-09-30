transcript on
onerror {quit -code 1 -f}

foreach required {BENCHMARK_HEX BENCHMARK_NAME CACHE_CONFIG} {
    if {![info exists ::env($required)]} {
        echo "[FAIL] missing required environment variable $required"
        quit -code 1 -f
    }
}

set max_cycles 3000000
if {[info exists ::env(BENCHMARK_MAX_CYCLES)]} {
    set max_cycles $::env(BENCHMARK_MAX_CYCLES)
}

set sim_args [list -onfinish stop -voptargs=+acc]
lappend sim_args "-gCACHE_CONFIG=$::env(CACHE_CONFIG)"
lappend sim_args "-gMEMFILE=$::env(BENCHMARK_HEX)"
lappend sim_args work.tb_benchmark_snapshot
lappend sim_args "+benchmark=$::env(BENCHMARK_NAME)"
lappend sim_args "+max_cycles=$max_cycles"
eval vsim $sim_args

if {[info exists ::env(BENCHMARK_FAST_UART)] && $::env(BENCHMARK_FAST_UART) == 1} {
    force -freeze sim:/tb_benchmark_snapshot/dut/u_uart/tx_done_latched 1
}

run -all
quit -sim
