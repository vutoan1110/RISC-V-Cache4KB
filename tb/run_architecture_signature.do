transcript on
onerror {quit -code 1 -f}

foreach required {VERIFY_HEX VERIFY_SIGNATURE VERIFY_SIG_BEGIN VERIFY_SIG_END} {
    if {![info exists ::env($required)]} {
        echo "[FAIL] missing required environment variable $required"
        quit -code 1 -f
    }
}

set sim_args [list -onfinish stop -voptargs=+acc work.tb_architecture_signature]
lappend sim_args "+HEX=$::env(VERIFY_HEX)"
lappend sim_args "+SIGNATURE=$::env(VERIFY_SIGNATURE)"
lappend sim_args "+SIG_BEGIN=$::env(VERIFY_SIG_BEGIN)"
lappend sim_args "+SIG_END=$::env(VERIFY_SIG_END)"

foreach optional {VERIFY_HALT_PC VERIFY_TOHOST_ADDR VERIFY_MAX_CYCLES} {
    if {[info exists ::env($optional)]} {
        set plusarg [string range $optional 7 end]
        lappend sim_args "+$plusarg=$::env($optional)"
    }
}

eval vsim $sim_args
run -all
quit -sim
