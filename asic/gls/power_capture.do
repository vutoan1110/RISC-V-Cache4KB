# Toggle capture over one kernel's measured region (FLOW_JOURNAL Incident 69).
# tb_gls_soc raises win_on at the kernel's sysmon_clear_start() and win_done at
# its sysmon_freeze_snapshot(); counting starts at the first and the SAIF is
# written at the second. Every net of the flat netlist is added (-internal:
# the nets at the dut scope; -in -out: its ports). A second win_on (not
# expected: the firmware clears once) restarts the count.
#
# Questa keeps the file header's DURATION at the total simulated time even
# after "power reset"/a late "power add"; saif_to_pins.py rewrites it from the
# nets' own T0+T1+TX (all equal to the window length) and checks they agree.
#   set SAIF <out>; do asic/gls/power_capture.do   (after vsim has loaded)
set ::pw_added 0
when -label pw_start {/tb_gls_soc/win_on == 1} {
    if {$::pw_added} {
        power reset -all
    } else {
        power add -in -out -internal /tb_gls_soc/dut/*
        set ::pw_added 1
    }
    echo "PW_WIN_START $now"
}
when -label pw_end {/tb_gls_soc/win_done == 1} {
    power report -all -bsaif $::SAIF
    echo "PW_WIN_END $now"
}
run -all
