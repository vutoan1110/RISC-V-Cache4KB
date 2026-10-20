#!/usr/bin/env python3
"""Audit the retained FAST cache-model pair and its isolated retry; never simulate.

--run writes a new dated evidence bundle. Original CSVs/logs remain unchanged.
Two independent model replays audit the retained retry trace; they are not new RTL runs.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'results/crossval_fast_receipt_20261016'
KERNELS = ('aha-mont64 crc32 depthconv edn huffbench matmult-int md5sum '
           'nettle-sha256 slre statemate tarfind ud').split()
CONFIGS = {'SA2': 1, 'DM_VC4': 2, 'DM_DSE': 3, 'SA4': 4, 'SA2N': 5}
COUNTERS = 'i_access i_main i_victim i_miss d_read d_write d_main d_victim d_miss'.split()
FIELDS = ['kernel', 'config', 'match'] + [c+s for s in ('_rtl', '_model') for c in COUNTERS]
EXPECTED = {('up_'+k, c) for k in KERNELS for c in CONFIGS}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def table(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == FIELDS, 'CSV schema differs: '+str(path))
        rows = list(reader)
    require(all(None not in r and all(v is not None for v in r.values()) for r in rows), 'Incomplete CSV')
    return rows


def keyed(rows):
    values = {}
    for row in rows:
        key = row['kernel'], row['config']
        require(key not in values, 'Duplicate case: '+str(key))
        require(row['match'] == 'EXACT', 'Non-exact case: '+str(key))
        for c in COUNTERS:
            require(row[c+'_rtl'].isdigit() and row[c+'_model'].isdigit() and
                    row[c+'_rtl'] == row[c+'_model'], 'RTL/model counter differs: '+str((key, c)))
        values[key] = row
    return values


def validate(first, partial, retry):
    a, b, r = keyed(first), keyed(partial), keyed(retry)
    require(set(a) == EXPECTED and len(b) == 59 and set(r) == {('up_crc32', 'SA4')}, 'Unexpected case grid')
    require(not set(b) & set(r) and set(b) | set(r) == EXPECTED, 'Retry must fill exactly the one missing case')
    merged = dict(b, **{})
    merged.update(r)
    require(a == merged, 'Paired CSV field mismatch')
    return merged


def raw_check(path, row):
    text = path.read_text(encoding='utf-8-sig')
    snapshots = re.findall(r'^# BENCHMARK_SNAPSHOT (.*)$', text, re.M)
    require(len(snapshots) == 1 and '# [PASS] Atomic benchmark snapshot' in text and
            re.search(r'^# Errors: 0, Warnings: \d+\s*$', text, re.M) and
            not re.search(r'\*\* (?:Error|Fatal):', text), 'Incomplete/failed native log: '+str(path))
    fields = re.findall(r'(\w+)=([^\s]+)', snapshots[0])
    require(len(fields) == len(dict(fields)), 'Duplicate raw snapshot field')
    fields = dict(fields)
    require(fields['benchmark'] == row['kernel'] and int(fields['config']) == CONFIGS[row['config']] and
            fields['result_pass'] == fields['invariant_pass'] == '1', 'Wrong native snapshot identity')
    require('-gCACHE_FAST_HIT=1' in text and '-gICACHE_LINE_COUNT=256' in text and
            '-gDCACHE_LINE_COUNT=256' in text, 'Wrong elaborated FAST/capacity command')
    require(all(fields[c] == row[c+'_rtl'] for c in COUNTERS), 'Raw/CSV counter mismatch')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', action='store_true')
    args = ap.parse_args()
    if not args.run:
        print('PLAN_ONLY: preserve originals; audit60 paired cases,120 native captures, two model replays; no RTL simulation/PD')
        return 0
    require(not OUT.exists(), 'Refuse to overwrite an existing evidence bundle')
    paths = [ROOT / ('results/crossval_6c4ccffd_fast_'+s+'.csv')
             for s in ('p1', 'p2', 'p2_retry_up_crc32_SA4')]
    first, partial, retry = [table(p) for p in paths]
    merged = validate(first, partial, retry)
    controls = 0
    bad_sets = [(first, partial, []), (first, partial+retry, retry), (first[:-1], partial, retry)]
    changed = [dict(retry[0])];changed[0]['i_main_rtl'] = str(int(changed[0]['i_main_rtl'])+1)
    bad_sets.append((first, partial, changed))
    for bad in bad_sets:
        try:
            validate(*bad)
        except ValueError:
            controls += 1
    require(controls == 4, 'Evidence-rejection control escaped')
    manifest_path = ROOT/'results/rtl_manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    require(manifest['count'] == 227 and all(sha(ROOT/p) == h for p,h in manifest['files'].items()), 'Live RTL manifest mismatch')
    raw = []
    for number, rows in ((1, keyed(first)), (2, merged)):
        for key, row in sorted(rows.items()):
            log = ROOT/'results/review_sims_6c4ccffd'/f'crossval_logs_fast_p{number}'/(key[0]+'_'+key[1]+'_fast.log')
            if number == 2 and key == ('up_crc32','SA4'):
                log = ROOT/'results/crossval_logs/up_crc32_SA4_fast.log'
            raw_check(log, row)
            raw.append(log)
    trace, model = ROOT/'results/cache_trace.txt', ROOT/'scripts/cache_model.py'
    inputs = dict((str(p.relative_to(ROOT)), sha(p)) for p in paths+raw+[trace,model,manifest_path,Path(__file__)])
    OUT.mkdir()
    reports = []
    for number in (1,2):
        command = [sys.executable, '-B', str(model), str(trace), '--config','4','--lines','256']
        native = subprocess.run(command,cwd=ROOT,capture_output=True)
        (OUT/f'retry_model_p{number}.log').write_bytes(native.stdout+native.stderr)
        require(native.returncode == 0, 'Native model replay failed')
        stdout = native.stdout.decode('utf-8')
        counts = {}
        for c in COUNTERS:
            hits = re.findall(r'^\s*'+c+r'\s*=\s*(\d+)\s*$',stdout,re.M)
            require(len(hits) == 1 and hits[0] == retry[0][c+'_model'], 'Retained trace does not reproduce retry model: '+c)
            counts[c] = int(hits[0])
        require(validate(*(table(p) for p in paths)) == merged, 'CSV input changed')
        require(all(sha(ROOT/p) == h for p,h in inputs.items()), 'Evidence input changed during audit')
        report = {'status':'VERIFIED_RETAINED_FAST_PAIR_WITH_ISOLATED_RETRY','cases_per_pass':60,
                  'columns_compared':len(FIELDS),'field_comparisons':60*len(FIELDS),'field_differences':0,
                  'native_logs_checked':120,'retry_key':['up_crc32','SA4'],'retry_model_counts':counts,
                  'model_native_exit':native.returncode,'rejection_controls_passed':controls,
                  'rtl_manifest':manifest['aggregate'],'inputs_sha256':inputs,
                  'scope':'Derived evidence audit; no new RTL simulation, no new PD, no additional physical measurement'}
        (OUT/f'comparison_p{number}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='ascii')
        reports.append(report)
    require(reports[0] == reports[1], 'Independent audit computations differ')
    buffer = io.StringIO(newline='');writer = csv.DictWriter(buffer,fieldnames=FIELDS);writer.writeheader()
    writer.writerows(merged[(r['kernel'],r['config'])] for r in first)
    (OUT/'fast_pass2_complete.csv').write_bytes(buffer.getvalue().encode('utf-8'))
    receipt = {'status':'VERIFIED_TWO_AUDIT_COMPUTATIONS','measurement_passes':2,'new_RTL_simulations':0,
               'cases_per_pass':60,'numeric_counters_per_side':9,'all_CSV_columns_compared':21,
               'native_logs_checked':120,'derived_csv_sha256':sha(OUT/'fast_pass2_complete.csv'),
               'comparison_sha256':sha(OUT/'comparison_p1.json'),'comparison_bytes_identical':sha(OUT/'comparison_p1.json') == sha(OUT/'comparison_p2.json'),
               'originals_preserved':True,'old_comparison_retained':'results/review_sims_6c4ccffd/comparison.json'}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='ascii')
    print(json.dumps(receipt))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
