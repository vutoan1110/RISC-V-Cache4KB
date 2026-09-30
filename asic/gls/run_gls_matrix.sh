#!/usr/bin/env bash
# Run every Embench kernel on the gate-level netlist and compare with the
# ASIC-view RTL run (FLOW_JOURNAL: functional substitute for Yosys.EQY).
#
#   bash asic/gls/run_gls_matrix.sh <netlist> <tag> [kernels...]
#
# A kernel passes only if (a) the firmware's own self-check passes on the
# netlist (LEDR = 0xA5), (b) all eight HEX digits decode, and (c) the decoded
# mcycle equals the ASIC-view RTL mcycle in results/asic_view_4kb_p1.csv
# exactly. Output: results/gls_<tag>.csv and results/gls_<tag>/<kernel>.log.
set -uo pipefail
# R14 (RAM16K_CHANGES.md): GLS_DEFINES="+define+GLS_RAM16K" for the 16 KiB netlist; GLS_REF = the ASIC-view
# RTL csv the mcycle is compared with (default: the 8 KiB design's results/asic_view_4kb_p1.csv).
cd "$(dirname "$0")/../.."
NET=$1; TAG=$2; shift 2
KERNELS=${*:-"crc32 depthconv edn fdct huffbench insertsort matmult md5sum mont64 sha256 tarfind wikisort"}
V=C:/questasim64_2024.1/win64/vsim.exe
OUT=results/gls_$TAG; mkdir -p "$OUT"
CSV=results/gls_$TAG.csv
echo "kernel,status,gls_mcycle,rtl_mcycle,match,cycles_to_done" > "$CSV"
"$V" -c -do "set NETLIST $NET; set TB_DEFINES {${GLS_DEFINES:-}}; do asic/gls/compile_gls.do; quit -f" > "$OUT/compile.log" 2>&1 \
  || { echo "[FAIL] compile, see $OUT/compile.log"; exit 1; }
fail=0
for k in $KERNELS; do
  "$V" -c -do "vsim -onfinish stop -gMEMFILE=fw/$k.hex -gMAX_CYCLES=8000000 work_gls.tb_gls_soc; run -all; quit -f" > "$OUT/$k.log" 2>&1
  line=$(grep -o 'GLS_RESULT.*' "$OUT/$k.log" | head -1)
  st=$(echo "$line" | grep -o 'status=[A-Z]*' | cut -d= -f2)
  gm=$(echo "$line" | grep -o 'mcycle=[0-9]*' | cut -d= -f2)
  hx=$(echo "$line" | grep -o 'hex_decoded=[0-9]' | cut -d= -f2)
  cd_=$(echo "$line" | grep -o 'cycles_to_done=[0-9]*' | cut -d= -f2)
  rm_=$(awk -F, -v k="$k" '$1==k && $2=="DM"{print $4}' ${GLS_REF:-results/asic_view_4kb_p1.csv})
  m=NO; [ "$st" = PASS ] && [ "$hx" = 1 ] && [ -n "$gm" ] && [ "$gm" = "$rm_" ] && m=YES
  [ "$m" = YES ] || fail=$((fail+1))
  echo "$k,${st:-NONE},${gm:-},${rm_:-},$m,${cd_:-}" | tee -a "$CSV"
done
echo "[$([ $fail = 0 ] && echo PASS || echo FAIL)] $TAG: $fail kernel(s) not matching"
exit $fail
