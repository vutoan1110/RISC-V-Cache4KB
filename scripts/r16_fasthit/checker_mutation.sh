#!/usr/bin/env bash
# R16 sim-only checker liveness (rule D.3): the per-cycle checker in each FAST_HIT core reports nothing when it
# agrees, so a clean log alone cannot tell "checked and fine" from "not compiled / never evaluated". Each run here
# forces the checker's recorded answer (r16_word) to a wrong constant in one core, FAST_HIT=1, up_crc32; the run
# PASSES only if that checker stops the simulation with its own message. Four cores: I$ / D$ x DSE (cfg 1) / N-way (cfg 4).
#   bash scripts/r16_fasthit/checker_mutation.sh [library, default work]  -> results/r16_checker_mutation_*.log
set -uo pipefail
cd "$(dirname "$0")/../.."
V=C:/questasim64_2024.1/win64/vsim.exe
LIB=${1:-work}
ok=0
for spec in "1 u_icache g_dse" "1 u_dcache g_dse" "4 u_icache g_nway" "4 u_dcache g_nway"; do
  set -- $spec; cfg=$1; cache=$2; blk=$3
  log=results/r16_checker_mutation_${cache}_${blk}.log
  "$V" -c -do "vsim -onfinish stop -voptargs=+acc -gCACHE_FAST_HIT=1 -gCACHE_CONFIG=$cfg -gMEMFILE=fw/up_crc32.hex -gICACHE_LINE_COUNT=256 -gDCACHE_LINE_COUNT=256 $LIB.tb_benchmark_snapshot +benchmark=up_crc32 +max_cycles=40000000; force -freeze sim:/tb_benchmark_snapshot/dut/$cache/$blk/u_core/r16_word 32'hdeadbeef; run -all; quit -f" > "$log" 2>&1
  if grep -q "R16 FAST_HIT: ST_LOOKUP answer deadbeef" "$log"; then
    ok=$((ok+1)); echo "  [OK]   $cache/$blk (cfg $cfg): checker fired on the forced wrong answer"
  else
    echo "  [FAIL] $cache/$blk (cfg $cfg): checker did not fire, see $log"
  fi
done
echo "checker mutation: $ok/4 fired"
[ "$ok" -eq 4 ]
