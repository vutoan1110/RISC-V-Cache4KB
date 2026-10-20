#!/usr/bin/env bash
# Interrupt latency and context-switch cost (metric expansion, 2026-09-30): sw_metrics/irq on the FPGA-view
# SoC (4 KiB caches, BP on), CACHE_CONFIG 0-3, every run twice. The firmware is rebuilt first; the simulation
# library is work_irq (sw_metrics/irq/compile_irq.do), so nothing collides with a batch in work.
# Output: results/irq_metrics/cfg<k>_p<pass>.log and results/irq_metrics.csv (scripts/metrics/irq_metrics_table.py).
set -uo pipefail
cd "$(dirname "$0")/../.."
V=C:/questasim64_2024.1/win64/vsim.exe
OUT=results/irq_metrics
CONFIGS=${CONFIGS:-"0 1 2 3"}
mkdir -p "$OUT"
wsl.exe -d Ubuntu -e bash -lc 'cd /mnt/e/Projects/RISCV-research/sw_metrics/irq && make clean > /dev/null && make 2>&1 | tail -1' \
    | tee "$OUT/build.log"
grep -q '\[PASS\]' "$OUT/build.log" || { echo "[FAIL] firmware build, see $OUT/build.log"; exit 1; }
"$V" -c -do "do sw_metrics/irq/compile_irq.do; quit -f" > "$OUT/compile.log" 2>&1 \
    || { echo "[FAIL] compile, see $OUT/compile.log"; exit 1; }
for pass in 1 2; do
    for cfg in $CONFIGS; do
        "$V" -c -do "vsim -onfinish stop -gCACHE_CONFIG=$cfg work_irq.tb_irq_metrics; run -all; quit -f" \
            > "$OUT/cfg${cfg}_p$pass.log" 2>&1
        echo "pass $pass cfg $cfg: $(grep -o '\[PASS\] IRQ_METRICS.*' "$OUT/cfg${cfg}_p$pass.log" || echo FAIL)"
    done
done
python scripts/metrics/irq_metrics_table.py --configs "$(echo $CONFIGS | tr ' ' ',')"
