#!/usr/bin/env bash
# 2026-10-21 (FPGA paper, note N08): current-RTL Quartus fits of the FAST_HIT and SA4 points, so that their cost is
# measured on the same RTL as the four base points (register file and BHT in M9K) and with the same protocol:
# ten common placement seeds 1..10, two independent passes, fits strictly one at a time.
# Points: dse_4kb_fast, sa2_4kb_fast, vc4_4kb_fast (CACHE_FAST_HIT 1) and sa4_4kb, sa4_4kb_fast (N-way core).
# Output: results/fpga_points_fast_sa4_20261021_p1.csv / _p2.csv, reports under results/fpga_points/fast_sa4_20261021_p*/.
# A failed fit is retried once (Quartus on this host crashes at random in about 8 % of fits); a second failure is
# recorded and the loop continues. Cooperative stop: touch results/.abort_fpga_sweep.
#   bash scripts/fpga/run_fast_sa4_refits_20261021.sh
set -u
R=/e/Projects/RISCV-research
PY=/c/Users/toanl/AppData/Local/Programs/Python/Python311/python.exe
POINTS="dse_4kb_fast sa2_4kb_fast vc4_4kb_fast sa4_4kb sa4_4kb_fast"
LOG=$R/results/fpga_points_fast_sa4_20261021.log
cd $R || exit 1
say () { echo "$(date -Is) $*" | tee -a $LOG; }
say "start: points $POINTS, seeds 1..10, passes 1 2; RTL manifest $(grep -o -m1 -E '"aggregate": *"[0-9a-f]{8}' results/rtl_manifest.json)"
for pass in 1 2; do
    for seed in 1 2 3 4 5 6 7 8 9 10; do
        for p in $POINTS; do
            [ -e results/.abort_fpga_sweep ] && { say "ABORT before $p seed $seed pass $pass"; exit 3; }
            ok=0
            for attempt in 1 2; do
                if $PY scripts/run_fpga_points.py --points $p --seed $seed --out results/fpga_points_fast_sa4_20261021_p$pass.csv --tag fast_sa4_20261021_p$pass >> $LOG 2>&1; then
                    ok=1; break
                fi
                say "FAIL $p seed $seed pass $pass attempt $attempt"
            done
            [ $ok = 1 ] && say "OK $p seed $seed pass $pass" || say "GIVE UP $p seed $seed pass $pass"
        done
    done
done
say "done"
