#!/usr/bin/env bash
# SA2 / DM_VC4 ASIC-view verification (2026-09-30, FLOW_JOURNAL: SA2 and DM_VC4 ASIC builds).
# Library work_asic_dse (scripts/metrics/compile_asic_view_dse.do): the frozen PD RTL
# asic/snapshots/rtl_r14 with the DSE data bank on OpenRAM macros
# (asic/dse_sram/cache_dse_data_bank_sram.v). Acceptance, the same rule the DM ASIC view
# has used since run_fullchain_rtlfix.sh, plus the bank shadow:
#   - 12 Embench kernels x CACHE_CONFIG 1,2, twice, pass 1 = pass 2 on every field;
#   - = FPGA view (results/r15_4kb_p1.csv) on every field except the memory-latency cycle
#     counts (snapshot_fields.CYCLE_FIELDS; the RAM macro wrapper ignores the MISS_PENALTY
#     hooks), with load_use, control and trap kept in;
#   - every run prints four DSE_BANK_EQUIV lines (both ways of both caches): the macro
#     view equalled the register bank in every cycle;
#   - CACHE_CONFIG 0 on this library = the DM ASIC view (results/upstream_asic_r15_p1.csv)
#     on every field, which checks the compile script itself;
#   - ramsweep x2, directed ISA (6 checks) per configuration, wrapper synchronisers per top.
# Progress: results/dse_asic_view.log, one line per result.
set -uo pipefail
cd "$(dirname "$0")/../.."
V=C:/questasim64_2024.1/win64/vsim.exe
LOG=results/dse_asic_view.log
UP=up_aha-mont64,up_crc32,up_depthconv,up_edn,up_huffbench,up_matmult-int,up_md5sum,up_nettle-sha256,up_slre,up_statemate,up_tarfind,up_ud
A="--asic-view --asic-compile scripts/metrics/compile_asic_view_dse.do --asic-lib work_asic_dse"
fail=0
say ()   { echo "$*" | tee -a "$LOG"; }
check () { if [ "$1" -eq 0 ]; then say "  [OK]   $2"; else say "  [FAIL] $2"; fail=$((fail + 1)); fi; }
: > "$LOG"

say "######## 1. Embench, CACHE_CONFIG 1 and 2, x2  $(date -Is)"
python scripts/run_ablation.py $A --compile --asic-configs 1,2 --kernels "$UP" --out results/dse_asic_view_p1.csv 2>&1 | tail -3 | tee -a "$LOG"
python scripts/run_ablation.py $A           --asic-configs 1,2 --kernels "$UP" --out results/dse_asic_view_p2.csv 2>&1 | tail -3 | tee -a "$LOG"
python scripts/verify_double.py results/dse_asic_view_p1.csv results/dse_asic_view_p2.csv --key kernel --also config >/dev/null 2>&1
check $? "pass 1 = pass 2 (every field)"
python - "$UP" <<'PY' 2>&1 | tee -a "$LOG"
import csv, re, sys
from pathlib import Path
sys.path.insert(0, 'scripts')
from snapshot_fields import FIELDS, CYCLE_FIELDS
kernels = sys.argv[1].split(',')
same = [f for f in FIELDS if f not in CYCLE_FIELDS] + ['load_use', 'control', 'trap']
fp = {(r['kernel'], r['config']): r for r in csv.DictReader(open('results/r15_4kb_p1.csv'))}
bad, n, eq_bad = [], 0, []
for p in (1, 2):
    rows = {(r['kernel'], r['config']): r for r in csv.DictReader(open('results/dse_asic_view_p%d.csv' % p))}
    for cfg in ('SA2', 'DM_VC4'):
        for k in kernels:
            a, f = rows.get((k, cfg)), fp.get((k, cfg))
            if a is None or f is None:
                bad.append((p, k, cfg, 'missing row')); continue
            n += 1
            bad += [(p, k, cfg, x, a[x], f[x]) for x in same if a[x] != f[x]]
            log = Path('results/ablation_logs_asic_view/dse_asic_view_p%d/%s_%s.log' % (p, k, cfg))
            t = log.read_text(errors='replace') if log.is_file() else ''
            m = re.findall(r'DSE_BANK_EQUIV \S+: (\d+) cycles matched', t)
            if len(m) != 4 or 'Fatal' in t:
                eq_bad.append((p, k, cfg, len(m)))
print('  ASIC view vs FPGA view: %d runs x %d fields: %s' % (n, len(same), 'IDENTICAL' if not bad else 'DIFF %s' % bad[:4]))
print('  bank shadow: %s' % ('4/4 DSE_BANK_EQUIV in all %d logs' % n if not eq_bad else 'MISSING %s' % eq_bad[:4]))
sys.exit(1 if bad or eq_bad or n != 4 * len(kernels) else 0)
PY
check ${PIPESTATUS[0]} "= FPGA view on every architectural field and cache counter; bank shadow in every run"

say "######## 2. CACHE_CONFIG 0 on this library = DM ASIC view  $(date -Is)"
python scripts/run_ablation.py $A --asic-configs 0 --kernels "$UP" --out results/dse_asic_view_cfg0.csv 2>&1 | tail -1 | tee -a "$LOG"
python - <<'PY' 2>&1 | tee -a "$LOG"
import csv, sys
a = {r['kernel']: r for r in csv.DictReader(open('results/dse_asic_view_cfg0.csv'))}
b = {r['kernel']: r for r in csv.DictReader(open('results/upstream_asic_r15_p1.csv'))}
bad = [(k, x) for k in b for x in b[k] if k not in a or a[k].get(x) != b[k][x]]
print('  cfg 0: %d kernels, %s' % (len(a), 'IDENTICAL on every field' if not bad and len(a) == 12 else 'DIFF %s' % bad[:4]))
sys.exit(1 if bad or len(a) != 12 else 0)
PY
check ${PIPESTATUS[0]} "DM on the SA2/VC4 library = DM ASIC view (12 kernels, every field)"

say "######## 3. ramsweep, CACHE_CONFIG 1 and 2, x2  $(date -Is)"
for pass in 1 2; do
  python scripts/run_ablation.py $A --asic-configs 1,2 --kernels ramsweep --out results/dse_asic_ramsweep_p$pass.csv 2>&1 | tail -1 | tee -a "$LOG"
done
python scripts/verify_double.py results/dse_asic_ramsweep_p1.csv results/dse_asic_ramsweep_p2.csv --key kernel --also config >/dev/null 2>&1
check $? "ramsweep pass 1 = pass 2"
python - <<'PY' 2>&1 | tee -a "$LOG"
import csv, sys
sys.path.insert(0, 'scripts')
from snapshot_fields import FIELDS, CYCLE_FIELDS
same = [f for f in FIELDS if f not in CYCLE_FIELDS] + ['load_use', 'control', 'trap']
a = {(r['kernel'], r['config']): r for r in csv.DictReader(open('results/dse_asic_ramsweep_p1.csv'))}
f = {(r['kernel'], r['config']): r for r in csv.DictReader(open('results/ramsweep_r15_p1.csv'))}
bad = [(k, x) for k in a for x in same if k not in f or a[k][x] != f[k][x]]
print('  ramsweep ASIC view vs FPGA view: %d runs: %s' % (len(a), 'IDENTICAL' if not bad and len(a) == 2 else 'DIFF %s' % bad[:4]))
sys.exit(1 if bad or len(a) != 2 else 0)
PY
check ${PIPESTATUS[0]} "ramsweep = FPGA view (architectural fields and cache counters)"

say "######## 4. directed ISA per configuration, wrapper synchronisers per top  $(date -Is)"
for cfg in 1 2; do
  "$V" -c -do "vsim -onfinish stop -voptargs=+acc -gVERBOSE=0 -gTB_LINE_COUNT=256 -gCACHE_CONFIG=$cfg work_asic_dse.tb_directed_isa work_asic_dse.asic_view_checker_isa; run -all; quit -f" > results/dse_asic_directed_isa_cfg$cfg.log 2>&1
  [ "$(grep -c '^# \[PASS\]' results/dse_asic_directed_isa_cfg$cfg.log)" -ge 6 ] && ! grep -q '\*\* Fatal' results/dse_asic_directed_isa_cfg$cfg.log
  check $? "directed ISA, CACHE_CONFIG $cfg: all six checks PASS"
done
for top in sa2 vc4; do
  "$V" -c -do "vlog -work work_asic_dse -sv +define+ASIC_VIEW_SIM asic/soc_${top}_4kb/soc_asic_top.v; quit -f" > results/dse_asic_top_$top.compile.log 2>&1
  for pass in 1 2; do
    "$V" -c -do "vsim -onfinish stop work_asic_dse.tb_soc_asic_top_sync; run -all; quit -f" > "results/dse_asic_top_sync_${top}_p$pass.log" 2>&1
    grep -q '^# \[PASS\] soc_asic_top' "results/dse_asic_top_sync_${top}_p$pass.log" && ! grep -qE '\[FAIL\]|\*\* (Fatal|Error)' "results/dse_asic_top_sync_${top}_p$pass.log"
    check $? "soc_${top}_4kb wrapper synchronisers pass $pass"
  done
done
say "######## done  $(date -Is): $fail failure(s)"
exit $fail
