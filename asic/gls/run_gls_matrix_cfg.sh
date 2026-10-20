#!/usr/bin/env bash
# FLOW_JOURNAL Incident 96: run_gls_matrix_lib.sh generalised for any cache configuration.
# Every standard Embench kernel on a gate-level netlist, compared with the ASIC-view RTL run of the
# same configuration:
#
#   bash asic/gls/run_gls_matrix_cfg.sh <netlist> <tag> <ref_csv> <config> [kernels...]
#   e.g. ... asic/soc_sa2_4kb/runs/sa2F_A/NN-.../soc_asic_top.nl.v sa2F_A results/dse_asic_view_p1.csv SA2
#
# A kernel passes only if (a) the firmware's self-check passes on the netlist (LEDR = 0xA5), (b) all
# eight HEX digits decode, and (c) the decoded mcycle equals the ASIC-view RTL mcycle of <config> in
# <ref_csv> exactly. Output: results/gls_<tag>.csv and results/gls_<tag>/<kernel>.log.
set -uo pipefail
cd "$(dirname "$0")/../.."
NET=$1; TAG=$2; REF=$3; CFG=$4; shift 4
KERNELS=${*:-"up_aha-mont64 up_crc32 up_depthconv up_edn up_huffbench up_matmult-int up_md5sum up_nettle-sha256 up_slre up_statemate up_tarfind up_ud"}
V=C:/questasim64_2024.1/win64/vsim.exe
OUT=results/gls_$TAG; mkdir -p "$OUT"
CSV=results/gls_$TAG.csv
[ -f "$REF" ] || { echo "[FAIL] no reference $REF"; exit 1; }
echo "kernel,status,gls_mcycle,rtl_mcycle,match,cycles_to_done" > "$CSV"
# All three 4 KiB builds (DM R14, SA2, DM_VC4) have the 16 KiB RAM: GLS_RAM16K unless GLS_DEFINES says otherwise.
"$V" -c -do "set NETLIST $NET; set LIB work_gls_$TAG; set TB_DEFINES {${GLS_DEFINES-+define+GLS_RAM16K}}; do asic/gls/compile_gls_lib.do; quit -f" > "$OUT/compile.log" 2>&1 \
  || { echo "[FAIL] compile, see $OUT/compile.log"; exit 1; }
fail=0
for k in $KERNELS; do
  "$V" -c -do "vsim -onfinish stop -gMEMFILE=fw/$k.hex -gMAX_CYCLES=8000000 work_gls_$TAG.tb_gls_soc; run -all; quit -f" > "$OUT/$k.log" 2>&1
  line=$(grep -o 'GLS_RESULT.*' "$OUT/$k.log" | head -1)
  st=$(echo "$line" | grep -o 'status=[A-Z]*' | cut -d= -f2)
  gm=$(echo "$line" | grep -o 'mcycle=[0-9]*' | cut -d= -f2)
  hx=$(echo "$line" | grep -o 'hex_decoded=[0-9]' | cut -d= -f2)
  cd_=$(echo "$line" | grep -o 'cycles_to_done=[0-9]*' | cut -d= -f2)
  rm_=$(python -c "
import csv, sys
r = [x for x in csv.DictReader(open('$REF')) if x['kernel'] == '$k' and x['config'] == '$CFG']
print(r[0]['mcycle'] if len(r) == 1 else '')")
  m=NO; [ "$st" = PASS ] && [ "$hx" = 1 ] && [ -n "$gm" ] && [ "$gm" = "$rm_" ] && m=YES
  [ "$m" = YES ] || fail=$((fail+1))
  echo "$k,${st:-NONE},${gm:-},${rm_:-},$m,${cd_:-}" | tee -a "$CSV"
done
echo "[$([ $fail = 0 ] && echo PASS || echo FAIL)] $TAG ($CFG vs $REF): $fail kernel(s) not matching"
exit $fail
