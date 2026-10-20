## Diagnostic for the 8-byte-line hang.
## Runs the parameterised caches at LINE_WORDS given by the LW env var and
## samples the two cache FSMs and their access counters, to tell a stuck
## controller apart from a machine that is simply running wrong code.

set lw $::env(LW)
set lines [expr {1024 / (4 * $lw)}]

vsim -onfinish stop -voptargs="+acc" -gCACHE_CONFIG=1 -gCACHE_LINE_WORDS=$lw \
     -gICACHE_LINE_COUNT=$lines -gDCACHE_LINE_COUNT=$lines \
     -gMEMFILE=fw/crc32.hex work.tb_benchmark_snapshot \
     +benchmark=crc32 +max_cycles=5000000

set ip sim:/tb_benchmark_snapshot/dut/u_icache/g_dse/u_core
set dp sim:/tb_benchmark_snapshot/dut/u_dcache/g_dse/u_core

echo "LINE_WORDS=$lw  lines=$lines"
echo "   time      i.state i.addr      i.access   d.state d.access   retire_pc"
for {set k 1} {$k <= 8} {incr k} {
    run 50 us
    set istate  [examine -radix unsigned $ip/state]
    set iaddr   [examine -radix hex      $ip/request_addr]
    set iacc    [examine -radix unsigned $ip/access_count]
    set dstate  [examine -radix unsigned $dp/state]
    set dacc    [examine -radix unsigned $dp/access_count]
    set pc      [examine -radix hex \
                    sim:/tb_benchmark_snapshot/dut/u_core/retire_pc]
    echo "  [format %6d [expr {$k * 50}]]us  $istate  $iaddr  $iacc   $dstate  $dacc   $pc"
}
quit -f
