"""Read-only job diagnostics; --watch polls in the foreground every 600 seconds."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JOBS = [
    ('pd', 'VC4_padding', 'asic/soc_vc4_4kb/runs/vc4_corr3600x3400_f220_capm20_pad1_antoff_nogrtt_nogrtd_r1'),
    ('pd', 'SA2_minimality', 'asic/soc_sa2_4kb/runs/sa2_corr3400x3325_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_r1'),
    ('capture', 'DM_capture_p1', 'results/gls_exact_dm_full_p1_20261011/receipt.json'),
    ('capture', 'DM_capture_p2_stopped', 'results/gls_exact_dm_full_p2_20261011/receipt.json'),
    ('capture', 'DM_capture_p2_retry', 'results/gls_exact_dm_full_p2_retry_20261011/receipt.json'),
    ('pipeline', 'DM_exact_power_retry', 'results/exact_power_queue_dm_retry_20261011.json'),
]


def command(argv):
    p = subprocess.run(argv, capture_output=True, text=True, timeout=15)
    if p.returncode:
        raise RuntimeError(f'Query exit {p.returncode}: {p.stderr[:300]}')
    return p.stdout


def process_queries():
    tables, errors = {}, {}
    for platform in ('windows', 'wsl'):
        try:
            if platform == 'windows':
                script = ('Get-CimInstance Win32_Process -ErrorAction Stop | Select-Object '
                          'ProcessId,ParentProcessId,Name,CommandLine,UserModeTime,KernelModeTime,'
                          'WorkingSetSize,CreationDate | ConvertTo-Json -Depth 3 -Compress')
                raw = json.loads(command(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script]))
                raw = raw if isinstance(raw, list) else [raw]
                table = {int(r['ProcessId']): {'ppid': int(r['ParentProcessId']),
                    'cpu': (int(r['UserModeTime']) + int(r['KernelModeTime'])) / 1e7,
                    'rss': int(r['WorkingSetSize']), 'name': r['Name'], 'cmd': r['CommandLine'] or '',
                    'identity': f"{r['ProcessId']}@{r['CreationDate']}"} for r in raw}
            else:
                raw = command(['wsl.exe', '-d', 'Ubuntu', '-e', 'bash', '-c',
                               'ps -eo pid=,ppid=,cputimes=,rss=,args='])
                table = {}
                for line in raw.splitlines():
                    pid, ppid, cpu, rss, args = line.split(None, 4)
                    table[int(pid)] = {'ppid': int(ppid), 'cpu': int(cpu), 'rss': int(rss) * 1024,
                                      'name': args.split()[0], 'cmd': args, 'identity': f'{pid}@{args}'}
            tables[platform] = table
        except (OSError, ValueError, TypeError, RuntimeError, subprocess.TimeoutExpired) as exc:
            tables[platform] = None
            errors[platform] = str(exc)[:400]
    return tables, errors


def process_tree(table, tokens):
    if table is None:
        return None, None, None
    patterns = [re.compile(r'(?<![\w.-])' + re.escape(token.lower().replace('\\', '/')) + r'(?![\w.-])') for token in tokens if token]
    roots = {pid for pid, p in table.items() if any(pattern.search(p['cmd'].lower().replace('\\', '/')) for pattern in patterns)}
    owned = set(roots)
    while True:
        children = {pid for pid, p in table.items() if p['ppid'] in owned}
        if children <= owned:
            break
        owned |= children
    return sorted(table[pid]['identity'] for pid in owned), sum(table[p]['cpu'] for p in owned), sum(table[p]['rss'] for p in owned)


def output_signature(paths):
    digest, count, started = hashlib.sha256(), 0, time.monotonic()
    try:
        files = []
        for path in paths:
            if path.is_dir():
                for directory, dirs, names in os.walk(path):
                    dirs.sort()
                    files.extend(Path(directory) / n for n in sorted(names))
                    if len(files) > 20000 or time.monotonic() - started > 10:
                        raise RuntimeError('Output inventory bound exceeded')
            elif path.exists():
                files.append(path)
        for path in sorted(set(files)):
            s = path.stat()
            digest.update(f'{path}:{s.st_size}:{s.st_mtime_ns}\n'.encode())
            count += 1
        return digest.hexdigest(), count, None
    except (OSError, RuntimeError) as exc:
        return None, None, str(exc)


def classify(current, previous=None):
    state = current['recorded_state']
    if state in ('DONE', 'FAILED', 'HELD', 'HELD_INSPECT'):
        return state, None
    if not current['query_ok'] or state == 'UNKNOWN':
        return 'UNKNOWN', None
    if not current['processes']:
        return 'DEAD_ALERT', None
    if state == 'WAITING':
        return 'WAITING', None
    unchanged = previous and previous.get('query_ok') and all(current.get(k) == previous.get(k)
                 for k in ('recorded_state', 'processes', 'cpu_seconds', 'rss_bytes', 'output_signature'))
    quiet = previous.get('quiet_since', previous['observed_epoch']) if unchanged else current['observed_epoch']
    quiet = quiet if quiet is not None else current['observed_epoch']
    return ('SUSPECTED_STALL' if unchanged and current['observed_epoch'] - quiet >= 600 else 'RUNNING'), quiet


def inspect_job(kind, name, rel, tables, previous):
    path, now = ROOT / rel, time.time()
    report = {'job': name, 'observed_epoch': now, 'recorded_state': 'UNKNOWN', 'phase': 'UNKNOWN',
              'progress': 'UNKNOWN', 'error': None, 'evidence': rel}
    paths, tokens, platform = [path], [path.parent.name if kind == 'capture' else path.name], 'windows'
    try:
        if kind == 'pd':
            platform = 'wsl'
            steps = sorted((p for p in path.iterdir() if p.is_dir() and p.name.split('-')[0].isdigit()),
                           key=lambda p: int(p.name.split('-')[0]))
            report['phase'] = steps[-1].name if steps else 'NO_STEPS'
            report['progress'] = f'{sum((p / "state_out.json").exists() for p in steps)}/{len(steps)} steps'
            log = (ROOT / 'asic/gated_pd.log').read_text(errors='replace')[-150000:]
            events = [line for line in log.splitlines() if path.name in line]
            terminal = next((line for line in reversed(events) if any(x in line for x in
                (' HOLD ', ' STOP ', ' WAIT ', ' RESUME ', ' start ', ' CONTINUE ',
                 ' PASS final:', ' FAIL final:', ' SIGNOFF CLEAN ', ' SIGNOFF FAILED '))), '')
            report['recorded_state'] = ('FAILED' if any(x in terminal for x in (' STOP ', ' FAIL final:', ' SIGNOFF FAILED '))
                else 'DONE' if any(x in terminal for x in (' PASS final:', ' SIGNOFF CLEAN '))
                else 'WAITING' if ' WAIT ' in terminal else 'HELD' if ' HOLD ' in terminal
                else 'RUNNING' if events else 'UNKNOWN')
            report['error'] = terminal if report['recorded_state'] == 'FAILED' else None
            if report['recorded_state'] == 'FAILED' and (path / 'error.log').exists():
                report['error'] += ' | native: ' + (path / 'error.log').read_text(errors='replace')[-1000:].strip()
        else:
            receipt = json.loads(path.read_text())
            state = receipt.get('status', receipt.get('state', 'UNKNOWN'))
            report['phase'] = state
            report['recorded_state'] = ('FAILED' if state.startswith(('STOPPED', 'FAILED', 'ABORTED')) else
                'HELD_INSPECT' if state == 'PAIRED_STA_DRIVER_RETURNED_INSPECT_RECEIPT' else
                'DONE' if state.startswith(('VERIFIED', 'COMPLETE')) else 'HELD' if state.startswith(('HELD', 'PREPARED', 'PLAN')) else
                'WAITING' if state.startswith(('WAITING', 'QUEUED')) else
                'RUNNING' if state.startswith(('RUNNING', 'ENTERING_', 'VERIFYING_', 'STARTED')) or state == 'IN_PROGRESS' else 'UNKNOWN')
            report['progress'] = f"{len(receipt.get('cases', {}))}/{len(receipt.get('kernels', []))} kernels" if kind == 'capture' else state
            native = receipt.get('native_commands', [])
            if native:
                report['phase'] = Path(native[-1].get('log', state)).name
            report['error'] = receipt.get('error')
            if kind == 'capture':
                paths = [path.parent]
                tokens.append(receipt.get('library', path.parent.name))
            elif receipt.get('power_output'):
                paths.append(ROOT / receipt['power_output'])
                tokens.append(Path(receipt['power_output']).name)
            if kind == 'pipeline':
                tokens.append('run_dm_capture_power_retry.ps1')
    except (OSError, ValueError, TypeError) as exc:
        report['error'] = str(exc)[:400]
    report['processes'], report['cpu_seconds'], report['rss_bytes'] = process_tree(tables[platform], tokens)
    report['output_signature'], report['output_files'], file_error = output_signature(paths)
    report['query_ok'] = tables[platform] is not None and file_error is None
    report['output_error'] = file_error
    report['status'], report['quiet_since'] = classify(report, previous)
    return report


def controls():
    table = {1: {'ppid': 0, 'cpu': 0, 'rss': 100, 'cmd': 'job', 'identity': '1'},
             2: {'ppid': 1, 'cpu': 0, 'rss': 100, 'cmd': 'child', 'identity': '2'}}
    old = dict(recorded_state='RUNNING', query_ok=True, observed_epoch=0, quiet_since=0,
               processes=['1', '2'], cpu_seconds=0, rss_bytes=200, output_signature='same')
    table[2]['cpu'] = 10
    p, cpu, rss = process_tree(table, ['job'])
    fresh = dict(old, observed_epoch=600, processes=p, cpu_seconds=cpu, rss_bytes=rss)
    assert classify(fresh, old)[0] == 'RUNNING'
    assert classify(dict(old, observed_epoch=600), old)[0] == 'SUSPECTED_STALL'
    assert classify(dict(old, observed_epoch=600, query_ok=False), old)[0] == 'UNKNOWN'
    print('PASS: 3 synthetic diagnostic controls; not measurements')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--watch', action='store_true')
    ap.add_argument('--output', type=Path)
    ap.add_argument('--self-test', action='store_true')
    args = ap.parse_args()
    if args.self_test:
        controls()
        return
    output = (ROOT / args.output).resolve() if args.output else None
    if output and not output.is_relative_to(ROOT / 'results'):
        ap.error('Diagnostic output must stay under results/')
    previous = {}
    if output and output.exists():
        previous = {r['job']: r for r in json.loads(output.read_text()).get('jobs', [])}
    while True:
        tables, errors = process_queries()
        rows = [inspect_job(*job, tables, previous.get(job[1])) for job in JOBS]
        stamp = datetime.now(timezone.utc).isoformat()
        for r in rows:
            print(f"{stamp} {r['job']}: {r['status']} phase={r['phase']} progress={r['progress']} "
                  f"processes={len(r['processes']) if r['processes'] is not None else 'UNKNOWN'} "
                  f"cpu={r['cpu_seconds']}s rss={r['rss_bytes']} error={r['error']}", flush=True)
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps({'status': 'DIAGNOSTIC_ONLY_NOT_MEASUREMENT', 'time_utc': stamp,
                'poll_seconds': 600, 'process_query_errors': errors, 'jobs': rows}, indent=2) + '\n', encoding='ascii')
        previous = {r['job']: r for r in rows}
        if not args.watch:
            return
        time.sleep(600)


if __name__ == '__main__':
    main()
