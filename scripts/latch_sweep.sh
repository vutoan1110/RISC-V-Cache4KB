#!/usr/bin/env bash
# Latch sweep with Yosys, the synthesis tool itself.
#
# Verilator's LATCH class only fires on always_comb blocks, so an incomplete
# assignment inside always @(*) goes unreported: rx_block.sv carried two latches
# through every lint pass while the ASIC netlist held two dlxtn_1 cells. Yosys
# infers latches the same way whether the block is always @(*) or always_comb,
# and proc_dlatch prints every one it creates, so this is the authoritative
# count. Every CACHE_CONFIG x LINE_COUNT combination is elaborated, because
# generate branches that are not selected are never checked.
set -uo pipefail
cd "$(dirname "$0")/.."
YOSYS=${YOSYS:-/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys}
TOP=${1:-de2_115_top}
OUT=results/latch_sweep.txt
FILES=$(ls hdl/*.v hdl/cache/*.v hdl/axi/*.v hdl/bus/*.v hdl/predictor/*.v hdl/board/*.v 2>/dev/null | tr '\n' ' ')
SVFILES=$(ls hdl/*.sv 2>/dev/null | tr '\n' ' ')
: > "$OUT"
total=0
for LC in ${LINES:-64 256}; do
for CFG in 0 1 2 3; do
  log=$(mktemp)
  "$YOSYS" -q -l "$log" -p "
    read_verilog -DSYNTHESIS $FILES
    read_verilog -sv -DSYNTHESIS $SVFILES
    hierarchy -check -top $TOP -chparam CACHE_CONFIG $CFG -chparam ICACHE_LINE_COUNT $LC -chparam DCACHE_LINE_COUNT $LC
    proc
    tee -o /dev/stdout select -count t:\$dlatch t:\$adlatch t:\$dlatchsr
  " > /dev/null 2>&1
  rc=$?
  n=$(grep -c "Latch inferred for signal" "$log")
  total=$((total+n))
  echo "=== CACHE_CONFIG=$CFG LINE_COUNT=$LC  rc=$rc  latches=$n" | tee -a "$OUT"
  grep "Latch inferred for signal" "$log" | sed 's/^/    /' | tee -a "$OUT"
  grep -E "^ERROR|^Error" "$log" | head -3 | sed 's/^/    /' | tee -a "$OUT"
  rm -f "$log"
done
done
echo "TOTAL latch inferences across all combinations: $total" | tee -a "$OUT"
[ "$total" -eq 0 ]
