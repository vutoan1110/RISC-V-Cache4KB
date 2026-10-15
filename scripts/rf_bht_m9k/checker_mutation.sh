#!/usr/bin/env bash
# Register file / BHT in M9K (2026-10-08, review A1): liveness of the two sim-only checkers (rule D.3). A silent log
# cannot tell "checked and equal" from "never evaluated", so each run forces one registered RAM read of the FPGA view
# to a wrong constant (regfile q1, bht_2bit qf) in the DM core running up_crc32; the run PASSES only if that module's
# checker stops the simulation with its own message.
#   bash scripts/rf_bht_m9k/checker_mutation.sh [library, default work]  -> results/rf_bht_m9k_checker_mutation_*.log
set -uo pipefail
cd "$(dirname "$0")/../.."
V=C:/questasim64_2024.1/win64/vsim.exe
LIB=${1:-work}
P=sim:/tb_benchmark_snapshot/dut/u_core/u_pipeline/datapath
ok=0
for spec in "regfile regfile/q1 32'hdeadbeef" "bht g_bp_on/u_bht/qf 2'b10"; do
  set -- $spec; name=$1; sig=$2; val=$3
  log=results/rf_bht_m9k_checker_mutation_$name.log
  "$V" -c -do "vsim -onfinish stop -voptargs=+acc -gCACHE_CONFIG=0 -gMEMFILE=fw/up_crc32.hex -gICACHE_LINE_COUNT=256 -gDCACHE_LINE_COUNT=256 $LIB.tb_benchmark_snapshot +benchmark=up_crc32 +max_cycles=40000000; force -freeze $P/$sig $val; run -all; quit -f" > "$log" 2>&1
  if grep -q "$name.* M9K checker" "$log" || grep -q "${name}_2bit M9K checker" "$log"; then
    ok=$((ok+1)); echo "  [OK]   $name: checker fired on the forced wrong read ($sig = $val)"
  else
    echo "  [FAIL] $name: checker did not fire, see $log"
  fi
done
echo "checker mutation: $ok/2 fired"
[ "$ok" -eq 2 ]
