#!/usr/bin/env bash
# FLOW_JOURNAL Incident 96: run_gls_power.sh generalised for any cache configuration and the 16 KiB designs.
# Gate-level toggle capture for activity-based power:
#
#   bash asic/gls/run_gls_power_cfg.sh <netlist> <tag> <ref_csv> <config> [kernels...]
#   JOBS=4 bash asic/gls/run_gls_power_cfg.sh ...   # kernels in parallel (one vsim each, shared read-only library)
#   e.g. ... soc_asic_top.nl.v r14F_A results/upstream_asic_r15_p1.csv DM
#        ... soc_asic_top.nl.v sa2F_A results/dse_asic_view_p1.csv SA2
#
# Same harness and pass rules as run_gls_power.sh (self-check PASS, all HEX digits decode, mcycle = the
# ASIC-view RTL mcycle of <config> in <ref_csv>, the tb's window spans exactly that mcycle, SAIF written to
# results/gls_power_<tag>/<kernel>.raw.saif). The testbench is compiled with GLS_RAM16K (all R14-era designs
# have the 16 KiB RAM) unless GLS_DEFINES says otherwise. Own library work_glsp_<tag>.
set -uo pipefail
cd "$(dirname "$0")/../.."
NET=$1; TAG=$2; REF=$3; CFG=$4; shift 4
KERNELS=${*:-"up_aha-mont64 up_crc32 up_depthconv up_edn up_huffbench up_matmult-int up_md5sum up_nettle-sha256 up_slre up_statemate up_tarfind up_ud"}
JOBS=${JOBS:-1}
V=C:/questasim64_2024.1/win64/vsim.exe
LIB=work_glsp_$TAG
OUT=results/gls_power_$TAG; mkdir -p "$OUT"
CSV=results/gls_power_$TAG.csv
[ -f "$REF" ] || { echo "[FAIL] no reference $REF"; exit 1; }
"$V" -c -do "set NETLIST $NET; set LIB $LIB; set TB_DEFINES {${GLS_DEFINES-+define+GLS_RAM16K}}; do asic/gls/compile_gls_lib.do; quit -f" > "$OUT/compile.log" 2>&1 \
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
  rm_=$(python -c "
import csv
r = [x for x in csv.DictReader(open('$REF')) if x['kernel'] == '$k' and x['config'] == '$CFG']
print(r[0]['mcycle'] if len(r) == 1 else '')")
  m=NO; [ "$st" = PASS ] && [ "$hx" = 1 ] && [ -n "$gm" ] && [ "$gm" = "$rm_" ] && m=YES
  sf=NO; [ -s "$SAIF" ] && sf=YES
  w=NO; [ -n "$wc_" ] && [ "$wc_" = "$gm" ] && w=YES
  { [ "$m" = YES ] && [ "$sf" = YES ] && [ "$w" = YES ]; } || fail=$((fail+1))
  echo "$k,${st:-NONE},${gm:-},${rm_:-},$m,${wc_:-},${t0:-},${t1:-},$sf" | tee -a "$CSV"
done
echo "[$([ $fail = 0 ] && echo PASS || echo FAIL)] $TAG ($CFG vs $REF): $fail kernel(s) failed (PASS needs self-check, mcycle = RTL, window = mcycle, SAIF written)"
exit $fail
