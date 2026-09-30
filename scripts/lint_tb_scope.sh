#!/usr/bin/env bash
# Lint the RTL at its real integration scope: the SoC plus the harness that
# consumes it.
#
# lint_rtl.sh takes soc_top as the top module. That is the synthesis scope, and
# it is the right scope for width, reset and latch checks. It is the wrong scope
# for UNUSEDSIGNAL: the debug taps and the retire trace port are read by the
# testbenches through hierarchical references, which do not exist when soc_top
# is elaborated alone. Elaborating the testbench instead puts the consumers back
# in the picture, so a signal still reported here is one that truly nothing
# reads.
#
#   bash lint_tb_scope.sh [TB_TOP] [TB_FILE]
set -uo pipefail
cd "$(dirname "$0")/.."

VROOT=${VROOT:-$HOME/tools/src/verilator}
VERILATOR="$VROOT/bin/verilator"
TOP=${1:-tb_benchmark_snapshot}
TBF=${2:-tb/benchmark_snapshot_tb.sv}
export VERILATOR_ROOT="$VROOT"

FILES=$(ls hdl/*.v hdl/cache/*.v hdl/axi/*.v hdl/bus/*.v hdl/predictor/*.v hdl/*.sv 2>/dev/null)
OUT=results/verilator_lint_${TOP}.txt

"$VERILATOR" --lint-only -Wall -Wno-DECLFILENAME -Wno-VARHIDDEN \
    --timing --top-module "$TOP" $FILES "$TBF" 2>&1 | tee "$OUT"

echo ""
echo "  === $TOP: summary by warning class ==="
grep -oE '%Warning-[A-Z0-9]+' "$OUT" | sort | uniq -c | sort -rn
echo "  warnings: $(grep -c '^%Warning' "$OUT")"
