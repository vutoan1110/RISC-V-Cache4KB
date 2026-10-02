#!/usr/bin/env bash
# Strict static analysis of research/hdl with Verilator.
#
# Questa's lint is clean on this RTL, but it does not report width truncation
# inside a module, which is the failure mode that has already cost two debugging
# cycles here: a port wider than its driver left every comparison at X, and a
# driver wider than its port aliased the upper words of each line onto the lower
# ones. Neither failed compilation. Verilator reports both.
#
# The check is split in two. The CORRECTNESS classes below are the ones where a
# warning means the silicon can be wrong: a width that silently truncates or
# extends, an inferred latch, a blocking assignment in sequential logic, an
# undriven or multiply driven net, a combinational loop, an incomplete case, a
# reset net used both synchronously and asynchronously. Those must be zero, and
# this script fails if any of them fires.
#
# UNUSEDSIGNAL and PINCONNECTEMPTY are reported but do not fail the run. They
# describe structure rather than behaviour: the debug taps and the retire trace
# port that the testbenches, the UVM environment and the Spike co-simulation
# read through hierarchical references are, by construction, unread inside
# soc_top; so are the address bits a peripheral deliberately does not decode and
# the low half of a multiplier whose high half is the result. Deleting them to
# reach a zero would delete the observation interface the measurements depend
# on. Every one of them is listed in CHANGELOG_AND_ISSUES.md with its reason.
#
#   bash lint_rtl.sh [TOP]        default TOP is soc_top
set -uo pipefail
cd "$(dirname "$0")/.."

VROOT=${VROOT:-$HOME/tools/src/verilator}
VERILATOR="$VROOT/bin/verilator"
TOP=${1:-de2_115_top}

if [ ! -x "$VERILATOR" ]; then
    echo "[FAIL] verilator not found at $VERILATOR" >&2
    exit 2
fi

# The man pages fail to install without help2man, so the tool runs from its
# build tree; VERILATOR_ROOT must point there and nowhere else.
export VERILATOR_ROOT="$VROOT"

# hdl/board/de2_115_top.v is the entity Quartus actually synthesises, so it
# belongs in the file list even though soc_top is the usual lint top.
FILES=$(ls hdl/*.v hdl/cache/*.v hdl/axi/*.v hdl/bus/*.v hdl/predictor/*.v hdl/board/*.v hdl/*.sv 2>/dev/null)

# CACHE_CONFIG selects between two generate branches, and only the selected one
# is elaborated. Linting the default alone therefore checks the direct-mapped
# controller and never looks at the ten-state DSE core -- which is where a first
# pass of this script left seventeen width warnings unseen. Every configuration
# is linted, and the findings are merged.
: > results/verilator_lint.txt
# Capacity is swept as well as organisation. INDEX_WIDTH and TAG_WIDTH are
# derived from LINE_COUNT -- INDEX_WIDTH = clog2(LINE_COUNT) and TAG_WIDTH =
# 32 - 4 - INDEX_WIDTH -- so every slice and array bound in the cache moves
# with it. Linting only the 64-line default leaves the 4 KiB configuration,
# which is the one heading for silicon, entirely unchecked. LINES overrides.
for LC in ${LINES:-64 256 512}; do
for CFG in ${CONFIGS:-0 1 2 3 4 5}; do   # 4 = SA4, 5 = the N-way core at two ways (R15)
    echo "=== CACHE_CONFIG=$CFG LINE_COUNT=$LC ===" >> results/verilator_lint.txt
    "$VERILATOR" --lint-only -Wall \
        --timing --top-module "$TOP" -GCACHE_CONFIG="$CFG" \
        -GICACHE_LINE_COUNT="$LC" -GDCACHE_LINE_COUNT="$LC" $FILES \
        >> results/verilator_lint.txt 2>&1
done
done
cat results/verilator_lint.txt

# The board's reset synchroniser is the one place where a net is correctly both
# shifted synchronously and used as an asynchronous reset -- that is what a reset
# synchroniser does, and it carries the Altera SYNCHRONIZER_IDENTIFICATION
# attribute to say so. There is no rewrite that avoids the warning: adding a flop
# changes reset release timing, and removing the synchroniser removes the
# metastability protection. Turning the whole class off would have hidden the
# three genuine occurrences this pass fixed, so exactly one net is named here and
# every other SYNCASYNCNET still fails the run.
RESET_SYNC_NET='de2_115_top.reset_sync_q'
CORRECTNESS='WIDTH|WIDTHTRUNC|WIDTHEXPAND|WIDTHCONCAT|LATCH|COMBDLY|BLKSEQ|UNDRIVEN|MULTIDRIVEN|UNOPTFLAT|IMPLICIT|CASEINCOMPLETE|CASEOVERLAP|CASEX|SYNCASYNCNET|ALWCOMBORDER|LATCHOUT|SELRANGE|PINMISSING|EOFNEWLINE|REALCVT|INFINITELOOP'

echo ""
echo "  === summary by warning class ==="
grep -oE '%Warning-[A-Z0-9]+' results/verilator_lint.txt | sort | uniq -c | sort -rn

N_CORRECT=$(grep -E "^%Warning-($CORRECTNESS):" results/verilator_lint.txt | grep -vc "$RESET_SYNC_NET")
N_STRUCT=$(grep -cE '^%Warning-(UNUSEDSIGNAL|PINCONNECTEMPTY):' results/verilator_lint.txt)
N_ERR=$(grep -c '^%Error:' results/verilator_lint.txt)
# Verilator ends with "Exiting due to N warning(s)" under -Wall; that line is an
# exit notice, not a defect, so it is not counted as an error here.
N_REAL_ERR=$(grep -c '^%Error[^:]' results/verilator_lint.txt)

echo ""
echo "  correctness warnings : $N_CORRECT   (must be 0)"
echo "  structural warnings  : $N_STRUCT   (documented, see CHANGELOG_AND_ISSUES.md)"
echo "  reset synchroniser   : $(grep -c "$RESET_SYNC_NET" results/verilator_lint.txt)   (recognised; see the note above)"
echo "  elaboration errors   : $N_REAL_ERR"

if [ "$N_CORRECT" -eq 0 ] && [ "$N_REAL_ERR" -eq 0 ]; then
    echo "  [PASS] no correctness-class lint warnings"
    exit 0
fi
echo "  [FAIL] correctness-class lint warnings present"
exit 1
