#!/usr/bin/env bash
# Rebuild results/gls_power_<tag>.csv from the per-kernel logs and SAIFs already in results/gls_power_<tag>/,
# with exactly the pass rules of run_gls_power_cfg.sh (self-check PASS, all HEX digits decoded, mcycle = the
# ASIC-view RTL mcycle of <config> in <ref_csv>, measured window = mcycle, SAIF written). Use it after a restart
# that re-ran only the missing kernels (run_gls_power_cfg.sh writes its CSV for the kernels of that call only).
#   bash asic/gls/gls_power_csv_rebuild.sh <tag> <ref_csv> <config> [kernels...]
set -uo pipefail
cd "$(dirname "$0")/../.."
TAG=$1; REF=$2; CFG=$3; shift 3
KERNELS=${*:-"up_aha-mont64 up_crc32 up_depthconv up_edn up_huffbench up_matmult-int up_md5sum up_nettle-sha256 up_slre up_statemate up_tarfind up_ud"}
OUT=results/gls_power_$TAG
CSV=results/gls_power_$TAG.csv
[ -d "$OUT" ] || { echo "[FAIL] no $OUT"; exit 1; }
echo "kernel,status,gls_mcycle,rtl_mcycle,match,win_cycles,win_t0_ns,win_t1_ns,saif" > "$CSV"
fail=0
for k in $KERNELS; do
  SAIF=$OUT/$k.raw.saif
  line=$(grep -o 'GLS_RESULT.*' "$OUT/$k.log" 2>/dev/null | head -1)
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
echo "[$([ $fail = 0 ] && echo PASS || echo FAIL)] $TAG ($CFG vs $REF): $fail kernel(s) failed (rebuilt from logs)"
exit $fail
