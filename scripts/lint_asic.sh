#!/usr/bin/env bash
# Strict static analysis of the ASIC elaboration scope.
#
# lint_rtl.sh lints the FPGA scope: de2_115_top down through soc_top. The ASIC
# flow has a different top -- soc_asic_top, with soc_top_asic under it and the
# SRAM macro wrapper in place of the FPGA block RAM -- and those three files are
# not in the FPGA file list at all. That gap hid a real defect: the chip select
# in axi_ram_32_asic_macro.v was declared two bits wide against a one-bit macro
# port, so every instance connection truncated silently. OpenLane's own lint
# step found it; this script exists so the project finds it without having to
# run a synthesis.
#
# The vendor SRAM behavioural model under macros/verilog/ is included, because
# without it the design does not elaborate. Warnings raised inside that file are
# counted separately: it is a third-party model this project neither authors nor
# ships, which is a different thing from waiving a warning on our own code.
# Nothing is suppressed with -Wno or a lint_off.
#
#   bash lint_asic.sh [DESIGN_DIR]     default is soc_dm_control
set -uo pipefail
cd "$(dirname "$0")/.."

VROOT=${VROOT:-$HOME/tools/src/verilator}
VERILATOR="$VROOT/bin/verilator"
DES=${1:-soc_dm_control}

if [ ! -x "$VERILATOR" ]; then
    echo "[FAIL] verilator not found at $VERILATOR" >&2
    exit 2
fi
if [ ! -d "asic/$DES" ]; then
    echo "[FAIL] no such design directory: asic/$DES" >&2
    exit 2
fi
export VERILATOR_ROOT="$VROOT"

# Lint exactly the files OpenLane synthesises -- the design's VERILOG_FILES --
# not a glob. The glob loaded hdl/cache/icache_data_ram.v and
# cache_data_ram_sram4.v together, two modules of one name (MODDUP x3 on
# soc_dm_4kb), and still printed PASS: it linted whichever copy Verilator kept.
FILES=$(python3 - "asic/$DES" <<'PY'
import json, os, sys
d = sys.argv[1]
c = json.load(open(os.path.join(d, 'config.json')))
for f in c['VERILOG_FILES']:
    print(os.path.normpath(os.path.join(d, f[5:])) if f.startswith('dir::') else f)
PY
)
FILES="$FILES $(ls "asic/$DES"/macros/verilog/*.v 2>/dev/null)"
VENDOR='macros/verilog/'

OUT="results/verilator_lint_asic_${DES}.txt"

"$VERILATOR" --lint-only -Wall --timing --top-module soc_asic_top $FILES \
    > "$OUT" 2>&1
cat "$OUT"

CORRECTNESS='WIDTH|WIDTHTRUNC|WIDTHEXPAND|WIDTHCONCAT|LATCH|COMBDLY|BLKSEQ|UNDRIVEN|MULTIDRIVEN|UNOPTFLAT|IMPLICIT|CASEINCOMPLETE|CASEOVERLAP|CASEX|SYNCASYNCNET|ALWCOMBORDER|LATCHOUT|SELRANGE|EOFNEWLINE|REALCVT|INFINITELOOP|MODDUP'

echo ""
echo "  === $DES: summary by warning class ==="
grep -oE '%Warning-[A-Z0-9]+' "$OUT" | sort | uniq -c | sort -rn

N_CORRECT=$(grep -E "^%Warning-($CORRECTNESS):" "$OUT" | grep -vc "$VENDOR")
N_VENDOR=$(grep -cE "^%Warning-[A-Z0-9]+: [^ ]*$VENDOR" "$OUT")
N_REAL_ERR=$(grep -c '^%Error[^:]' "$OUT")

echo ""
echo "  correctness warnings : $N_CORRECT   (must be 0)"
echo "  vendor SRAM model    : $N_VENDOR   (third-party, not authored here)"
echo "  elaboration errors   : $N_REAL_ERR"

if [ "$N_CORRECT" -eq 0 ] && [ "$N_REAL_ERR" -eq 0 ]; then
    echo "  [PASS] no correctness-class lint warnings in the ASIC scope"
    exit 0
fi
echo "  [FAIL] correctness-class lint warnings present"
exit 1
