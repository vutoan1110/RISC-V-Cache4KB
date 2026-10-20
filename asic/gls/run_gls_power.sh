#!/usr/bin/env bash
# Gate-level toggle capture for activity-based power (FLOW_JOURNAL Incident 69).
#
#   bash asic/gls/run_gls_power.sh <netlist> <tag> [kernels...]
#   JOBS=4 bash asic/gls/run_gls_power.sh ...    # kernels in parallel
#
# Same harness and pass/fail rules as run_gls_matrix_lib.sh (self-check PASS,
# all HEX digits decode, mcycle = ASIC-view RTL), plus: the tb's measured
# window must span exactly the decoded mcycle, and a SAIF of that window is
# written to results/gls_power_<tag>/<kernel>.raw.saif.
# Own library work_glsp_<tag>, compiled once; with JOBS > 1 each kernel is its
# own vsim process reading that library (read-only), results collected after.
set -uo pipefail
cd "$(dirname "$0")/../.."
NET=$1; TAG=$2; shift 2
KERNELS=${*:-"up_aha-mont64 up_crc32 up_depthconv up_edn up_huffbench up_matmult-int up_md5sum up_nettle-sha256 up_slre up_statemate up_tarfind up_ud"}
JOBS=${JOBS:-1}
V=C:/questasim64_2024.1/win64/vsim.exe
LIB=work_glsp_$TAG
OUT=results/gls_power_$TAG; mkdir -p "$OUT"
CSV=results/gls_power_$TAG.csv
"$V" -c -do "set NETLIST $NET; set LIB $LIB; do asic/gls/compile_gls_lib.do; quit -f" > "$OUT/compile.log" 2>&1 \
  || { echo "[FAIL] compile, see $OUT/compile.log"; exit 1; }

run_kernel () {
  local k=$1 SAIF=$OUT/$1.raw.saif
  rm -f "$SAIF"
  "$V" -c -do "vsim -onfinish stop -voptargs={+acc=rn+tb_gls_soc +acc=n+soc_asic_top} -gMEMFILE=fw/$k.hex -gMAX_CYCLES=8000000 $LIB.tb_gls_soc; set SAIF $SAIF; do asic/gls/power_capture.do; quit -f" > "$OUT/$k.log" 2>&1
}

running=0
for k in $KERNELS; do
  run_kernel "$k" &
  running=$((running+1))
  if [ "$running" -ge "$JOBS" ]; then wait -n; running=$((running-1)); fi
done
wait

echo "kernel,status,gls_mcycle,rtl_mcycle,match,win_cycles,win_t0_ns,win_t1_ns,saif" > "$CSV"
fail=0
for k in $KERNELS; do
  SAIF=$OUT/$k.raw.saif
  line=$(grep -o 'GLS_RESULT.*' "$OUT/$k.log" | head -1)
  st=$(echo "$line" | grep -o 'status=[A-Z]*' | cut -d= -f2)
  gm=$(echo "$line" | grep -o ' mcycle=[0-9]*' | cut -d= -f2)
  hx=$(echo "$line" | grep -o 'hex_decoded=[0-9]' | cut -d= -f2)
  wc_=$(echo "$line" | grep -o 'win_cycles=[0-9]*' | cut -d= -f2)
  t0=$(echo "$line" | grep -o 'win_t0=[0-9]*' | cut -d= -f2)
  t1=$(echo "$line" | grep -o 'win_t1=[0-9]*' | cut -d= -f2)
  rm_=$(awk -F, -v k="$k" '$1==k && $2=="DM"{print $4}' results/asic_view_4kb_p1.csv)
  m=NO; [ "$st" = PASS ] && [ "$hx" = 1 ] && [ -n "$gm" ] && [ "$gm" = "$rm_" ] && m=YES
  sf=NO; [ -s "$SAIF" ] && sf=YES
  w=NO; [ -n "$wc_" ] && [ "$wc_" = "$gm" ] && w=YES
  { [ "$m" = YES ] && [ "$sf" = YES ] && [ "$w" = YES ]; } || fail=$((fail+1))
  echo "$k,${st:-NONE},${gm:-},${rm_:-},$m,${wc_:-},${t0:-},${t1:-},$sf" | tee -a "$CSV"
done
echo "[$([ $fail = 0 ] && echo PASS || echo FAIL)] $TAG: $fail kernel(s) failed (PASS needs self-check, mcycle = RTL, window = mcycle, SAIF written)"
exit $fail
