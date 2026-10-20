transcript on
onerror {quit -code 1 -f}

foreach required {VERIFY_HEX VERIFY_TRACE_OFF VERIFY_TRACE_ON VERIFY_SEED} {
    if {![info exists ::env($required)]} {
        echo "[FAIL] missing required environment variable $required"
        quit -code 1 -f
    }
}

set sim_args [list -onfinish stop -voptargs=+acc work.tb_random_trace]
lappend sim_args "+HEX=$::env(VERIFY_HEX)"
lappend sim_args "+TRACE_OFF=$::env(VERIFY_TRACE_OFF)"
lappend sim_args "+TRACE_ON=$::env(VERIFY_TRACE_ON)"
lappend sim_args "+SEED=$::env(VERIFY_SEED)"
lappend sim_args "+MAX_CYCLES=50000"
eval vsim $sim_args
run -all
quit -sim
