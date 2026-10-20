transcript on
onerror {quit -code 1 -f}
do tb/compile_active_design.do

foreach cfg {0 1 2} {
    foreach pat {2 3} {
        vsim -onfinish stop -voptargs=+acc -gCACHE_CONFIG=$cfg \
            work.tb_cache_conflict_experiment +pattern=$pat +repetitions=16
        run -all
        quit -sim
    }
}

echo {[PASS] DM/SA2/DM_VC4 deterministic A/B and A/B/C experiments}
