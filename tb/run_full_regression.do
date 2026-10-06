transcript on
onerror {quit -code 1 -f}
do tb/compile_active_design.do

foreach test {
    tb_branch_predictor_core
    tb_valid_irq
    tb_native_interface
    tb_bht
    tb_branch_predictor
    tb_alu_zmmul
    tb_icache
    tb_dcache
    tb_cache_event_accounting
    tb_set_associative_cache
    tb_victim_cache
    tb_mmio_bypass
    tb_axi_memory
    tb_axi_mmio
    tb_soc_integration
    tb_performance_counters
    tb_uart_apb
    tb_de2_115_top_sync
    tb_predictor_axi
    tb_directed_isa
} {
    echo "===== FULL REGRESSION $test ====="
    vsim -onfinish stop -voptargs=+acc work.$test
    run -all
    quit -sim
}

foreach cfg {0 1 2 3} {
    vsim -onfinish stop -voptargs=+acc -gCACHE_CONFIG=$cfg work.tb_cache_configuration
    run -all
    quit -sim
}

# Capacity is the other axis, and until now the directed suite only ever saw
# 1 KiB. The 48-run matrix measures 4 KiB, so the unit tests have to cover it
# too -- a firmware self-check is weaker evidence than a directed test, and
# this project has already paid for that lesson once.
foreach lc {128 256} {
    foreach cfg {0 1 2 3} {
        echo "===== CAPACITY $lc lines (cfg $cfg) ====="
        vsim -onfinish stop -voptargs=+acc -gCACHE_CONFIG=$cfg -gLINE_COUNT=$lc work.tb_cache_configuration
        run -all
        quit -sim
    }
}

# Line size is a parameter of the design, so it belongs in the directed suite
# and not only in the full-SoC sweeps. LINE_COUNT is scaled to hold capacity at
# 1 KiB, so only the mapping changes between these points.
foreach {lw lc} {2 128 8 32 16 16} {
    foreach cfg {1 3} {
        echo "===== LINE_WORDS $lw (cfg $cfg) ====="
        vsim -onfinish stop -voptargs=+acc -gCACHE_CONFIG=$cfg              -gLINE_WORDS=$lw -gLINE_COUNT=$lc work.tb_cache_configuration
        run -all
        quit -sim
    }
}

vsim -onfinish stop -voptargs=+acc work.tb_cache_architecture_equivalence
run -all
quit -sim

# R16 (review M1): FAST_HIT=1 answers a main-array hit in ST_LOOKUP (DSE / N-way cores). The configuration,
# capacity and line-size checks above must hold unchanged, the SA2 main hit must come one cycle earlier, and
# SA2 / DM_VC4 built with FAST_HIT must retire exactly what DM retires.
foreach lc {64 128 256} {
    foreach cfg {1 2 3} {
        echo "===== FAST_HIT 1, $lc lines (cfg $cfg) ====="
        vsim -onfinish stop -voptargs=+acc -gCACHE_CONFIG=$cfg -gLINE_COUNT=$lc -gFAST_HIT=1 work.tb_cache_configuration
        run -all
        quit -sim
    }
}
foreach {lw lc} {2 128 8 32 16 16} {
    foreach cfg {1 3} {
        echo "===== FAST_HIT 1, LINE_WORDS $lw (cfg $cfg) ====="
        vsim -onfinish stop -voptargs=+acc -gCACHE_CONFIG=$cfg -gLINE_WORDS=$lw -gLINE_COUNT=$lc -gFAST_HIT=1 work.tb_cache_configuration
        run -all
        quit -sim
    }
}
vsim -onfinish stop -voptargs=+acc -gFAST_HIT=1 work.tb_cache_architecture_equivalence
run -all
quit -sim

echo {[PASS] Complete active RTL regression}
