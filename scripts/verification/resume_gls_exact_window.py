#!/usr/bin/env python3
"""Resume a successful native prefix of an interrupted exact-window GLS pass.

Default: prepare only. --run preserves the stopped receipt, original private
compilation, inputs, commands and successful outputs; only missing commands run.
This does not change the capture helper, RTL, firmware, or acceptance verifier.
"""
from __future__ import annotations
import argparse
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/verification'))
import run_gls_exact_window as capture
import verify_gls_exact_pair as verifier
require, stamp = capture.require, capture.stamp


def local(value):
    return ROOT / value


def digest(path):
    """UNC reads alone get bounded transport retries; no native job is retried."""
    path = Path(path)
    if not str(path).startswith('\\\\'):
        return capture.sha(path)
    code = ('import hashlib,sys; h=hashlib.sha256(); '
            'f=open(sys.argv[1],"rb"); '
            '[h.update(b) for b in iter(lambda:f.read(65536),b"")]; '
            'f.close(); print(h.hexdigest())')
    error = ''
    for attempt in range(3):
        try:
            result = subprocess.run([sys.executable, '-B', '-c', code, str(path)],
                                    capture_output=True, text=True, timeout=3)
            require(result.returncode == 0, result.stderr[-500:])
            value = result.stdout.strip()
            require(re.fullmatch('[0-9a-f]{64}', value), 'Malformed UNC hash response')
            return value
        except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
            error = str(exc)
            if attempt < 2:
                time.sleep(.2)
    raise RuntimeError(f'UNC_INPUT_UNAVAILABLE_AFTER_3_BOUNDED_READS: {path}: {error}')


def check_inputs(inputs):
    require(isinstance(inputs, dict) and inputs, 'Missing pinned inputs')
    for path, expected in inputs.items():
        require(re.fullmatch('[0-9a-f]{64}', expected) and digest(local(path)) == expected,
                f'Missing/changed pinned input: {path}')


def canonical_commands(r, folder):
    jobs = r['native_commands']
    require(len(jobs) >= 3, 'A preserved compile and completed conversion are required')
    vsim, conversion = jobs[0]['command'][0], jobs[2]['command']
    require(Path(vsim).name.lower() == 'vsim.exe', 'Wrong simulator')
    require(len(conversion) == 9 and conversion[:3] == [sys.executable, '-B', 'asic/gls/saif_to_pins.py'],
            'Conversion must retain this Windows Python and frozen converter')
    require({Path(p).name for p in conversion[6:]} == {
        'sky130_fd_sc_hd__tt_025C_1v80.lib',
        'sky130_sram_1kbyte_1rw1r_32x256_8_TT_1p8V_25C.lib',
        'sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib'}, 'Wrong TT libraries')
    result = []
    def sim(stem):
        return [vsim, '-c', '-l', str(folder / (stem+'.transcript')), '-wlf',
                str(folder / (stem+'.wlf')), '-do', 'do '+capture.tcl_path(folder / (stem+'.do'))]
    result.append((sim('compile'), folder/'compile.log'))
    for kernel in capture.KERNELS:
        result.append((sim(kernel), folder/(kernel+'.log')))
        result.append((conversion[:3] + [str(folder/(kernel+'.raw.saif')),
                       str(local(r['netlist'])), str(folder/(kernel+'.pins.saif'))] + conversion[6:],
                       folder/(kernel+'.pins.log')))
    return result


def check_prefix(r, commands):
    count = len(r.get('cases', {}))
    require(1 <= count < 12 and list(r['cases']) == list(capture.KERNELS[:count]),
            'Cases must be the exact completed canonical prefix')
    jobs = r.get('native_commands', [])
    require(len(jobs) in (1+2*count, 2+2*count), 'Only complete pairs and one optional pending simulation are resumable')
    for job, (command, log) in zip(jobs, commands):
        require(job.get('native_exit') == 0 and job.get('started') and job.get('completed'),
                'Failed/incomplete native command cannot be resumed by this helper')
        require(job.get('command') == command and local(job.get('log', '')) == log,
                'Native prefix command/log is not canonical')
    return count, len(jobs) == 2+2*count


def no_live_capture(folder, library):
    script = ('Get-CimInstance Win32_Process -ErrorAction Stop | '
              'Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress')
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
                            capture_output=True, text=True, timeout=10)
    require(result.returncode == 0, 'Cannot query active capture processes')
    rows = json.loads(result.stdout)
    for row in rows if isinstance(rows, list) else [rows]:
        command = (row.get('CommandLine') or '').lower().replace('\\', '/')
        if row['ProcessId'] != os.getpid() and row['Name'].lower() in ('vsim.exe', 'python.exe', 'python3.exe'):
            require(library.lower() not in command and folder.name.lower() not in command,
                    f'Capture/library already in use by PID {row["ProcessId"]}')


def prepare(receipt_path):
    raw = receipt_path.read_bytes()
    r = json.loads(raw)
    folder = receipt_path.parent
    require(r.get('status') == 'STOPPED_REQUIRES_INSPECTION', 'Expected an interrupted receipt')
    require(r.get('design') in capture.DESIGNS and r.get('pass') in (1, 2), 'Unknown capture profile')
    cfg = capture.DESIGNS[r['design']]
    require(r.get('PD_tag') == cfg['tag'] and r.get('freeze_expression') == cfg['freeze_expression'] and
            r.get('mapping_prerequisite') == 'VERIFIED_BOUND_TO_NETLIST', 'Unverified mapped profile')
    require(r.get('kernels') == list(capture.KERNELS) and r.get('full_twelve_kernel_matrix') is True and
            r.get('timing_period_ps') == 20000 and r.get('independent_interval_counter') is True and
            r.get('power_or_full_LEC_claim') is False, 'Wrong capture method/matrix')
    expected_profile = {'cache_KiB':4, 'RAM_KiB':16, 'current_reference_FAST_HIT':0,
        'frozen_snapshot_FAST_HIT_switch_absent':True, 'BRANCH_PREDICT_ENABLE':1,
        'L0_ENTRIES':8, 'CACHE_LINE_WORDS':4, 'VICTIM_ENTRIES':4, 'reference_counter_fields':40, 'PD_RTL_sources':42}
    require(r.get('profile') == expected_profile and r.get('minimum_Windows_free_MiB', 0) >= 6000,
            'Architecture/memory profile mismatch')
    library = f'work_gls_exact_{r["design"].lower()}_{folder.name}_p{r["pass"]}'
    require(r.get('library') == library and re.fullmatch('[a-zA-Z0-9_]+', library), 'Wrong private library')
    net = ROOT/f'asic/{cfg["design"]}/runs/{cfg["tag"]}/{cfg["fill"]}/soc_asic_top.nl.v'
    require(local(r['netlist']) == net, 'Wrong final netlist')
    check_inputs(r['inputs_sha256'])
    manifest = json.loads((ROOT/'results/rtl_manifest.json').read_text())
    require(len(manifest['files']) == 227 and all(r['inputs_sha256'].get(p) == h for p, h in manifest['files'].items()),
            'Missing current frozen manifest inputs')
    for path in [net, ROOT/'scripts/verification/run_gls_exact_window.py', ROOT/'asic/gls/tb_gls_soc.sv',
                 ROOT/'asic/gls/saif_to_pins.py', ROOT/'results/rtl_manifest.json']:
        require(r['inputs_sha256'].get(str(path)) == digest(path), f'Unpinned essential input: {path}')
    require((folder/'tb_gls_soc_exact_window.sv').read_text() == capture.generated_tb(
        (ROOT/'asic/gls/tb_gls_soc.sv').read_text(), r['freeze_expression']), 'Changed generated observer')
    require((folder/'power_capture_exact.do').read_text() == capture.capture_do(), 'Changed capture Tcl')
    commands = canonical_commands(r, folder)
    count, pending = check_prefix(r, commands)
    preserved = {}
    for job in r['native_commands']:
        log = local(job['log'])
        require(digest(log) == job.get('log_sha256'), f'Changed native log: {log}')
        preserved[str(log)] = digest(log)
    text = (folder/'compile.log').read_text()
    require(len(re.findall(r'^\s*(?:#\s*)?\[PASS\] EXACT_WINDOW_PRIVATE_LIBRARY_COMPILED\s*$', text, re.M)) == 1 and
            not re.search(r'\*\*\s+(?:Error|Fatal)|\[FAIL\]', text) and re.search(r'Errors:\s*0,', text), 'Incomplete private compilation')
    refs = [verifier.read_reference(ROOT/'results'/name, r['design']) for name in cfg['refs']]
    require(refs[0] == refs[1], 'Independent ASIC references differ')
    for index, kernel in enumerate(capture.KERNELS):
        expected_do = ('onerror {quit -code 1 -f}\nvsim -onfinish stop -voptargs={+acc=rn+tb_gls_soc +acc=n+soc_asic_top} '
            '-gMEMFILE=fw/'+kernel+'.hex -gMAX_CYCLES=8000000 '+library+'.tb_gls_soc\nset SAIF '+
            capture.tcl_path(folder/(kernel+'.raw.saif'))+'\ndo '+capture.tcl_path(folder/'power_capture_exact.do')+'\nquit -code 0 -f\n')
        do = folder/(kernel+'.do')
        require(do.read_text() == expected_do and r['inputs_sha256'].get(str(do)) == digest(do), 'Changed elaboration input')
        if index >= count + int(pending):
            require(all(not (folder/(kernel+suffix)).exists() for suffix in ('.log', '.raw.saif', '.pins.log', '.pins.saif')),
                    f'Unexpected future/stale output: {kernel}')
            continue
        window = capture.inspect_log(folder/(kernel+'.log'), int(refs[0][kernel]['mcycle']),
                                     r['native_commands'][1+2*index]['native_exit'], kernel)
        raw_stats = capture.inspect_saif(folder/(kernel+'.raw.saif'), window['duration_ps'])
        preserved[str(folder/(kernel+'.raw.saif'))] = raw_stats['sha256']
        if index < count:
            case = r['cases'][kernel]
            pin_stats = capture.inspect_saif(folder/(kernel+'.pins.saif'), window['duration_ps'])
            conversion_log = (folder/(kernel+'.pins.log')).read_text()
            require('PW_SAIF window ' in conversion_log and not re.search(r'\[FAIL\]|Traceback|\*\*\s+(?:Error|Fatal)', conversion_log), 'Incomplete conversion')
            require(case == {'window':window, 'raw_saif':raw_stats, 'pin_saif':pin_stats,
                'reference_minstret':int(refs[0][kernel]['minstret']), 'raw_log_sha256':digest(folder/(kernel+'.log'))}, 'Stored case differs from fresh raw/reference checks')
            preserved[str(folder/(kernel+'.pins.saif'))] = pin_stats['sha256']
        else:
            require(not (folder/(kernel+'.pins.saif')).exists() and not (folder/(kernel+'.pins.log')).exists(), 'Pending conversion output already exists')
    lib = ROOT/library
    require((lib/'_info').is_file() and (lib/'_lib.qdb').is_file(), 'Original compiled library is missing')
    library_hashes = {str(p):digest(p) for p in sorted(lib.rglob('*')) if p.is_file()}
    no_live_capture(folder, library)
    return r, raw, commands, refs[0], {'status':'PREPARED_NOT_EXECUTED', 'prepared_at':stamp(),
        'receipt':str(receipt_path.relative_to(ROOT)), 'stopped_receipt_sha256':digest(receipt_path),
        'resume_helper_sha256':digest(Path(__file__)), 'completed_cases':count, 'pending_simulation':pending,
        'preserved_native_commands':len(r['native_commands']), 'remaining_native_commands':25-len(r['native_commands']),
        'private_library':library, 'private_library_sha256_before':library_hashes,
        'preserved_outputs_sha256':preserved, 'inputs_sha256':r['inputs_sha256'], 'new_native_compilations':0}


def self_test():
    commands = [([str(i)], ROOT/f'{i}.log') for i in range(25)]
    r = {'cases':dict.fromkeys(capture.KERNELS[:7]), 'native_commands':[
        {'command':c, 'log':str(p), 'native_exit':0, 'started':'s', 'completed':'c'} for c, p in commands[:16]]}
    require(check_prefix(r, commands) == (7, True), 'Valid prefix rejected')
    bad = copy.deepcopy(r); bad['native_commands'][4]['native_exit'] = 1
    try: check_prefix(bad, commands)
    except RuntimeError: pass
    else: raise AssertionError('Failed native command was accepted')
    try: check_inputs({str(ROOT/'__missing_resume_input__'):'0'*64})
    except (RuntimeError, OSError): pass
    else: raise AssertionError('Missing input was accepted')
    print('PASS: 3 synthetic continuation controls; not measurements')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--receipt', type=Path)
    ap.add_argument('--output', type=Path)
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--wait-for-memory', action='store_true')
    ap.add_argument('--self-test', action='store_true')
    args = ap.parse_args()
    if args.self_test: self_test(); return 0
    require(args.receipt and args.output, '--receipt and --output are required')
    source, out = local(args.receipt).resolve(), local(args.output).resolve()
    require(source.is_relative_to(ROOT/'results') and out.is_relative_to(ROOT/'results') and
            not out.is_relative_to(source.parent), 'Evidence output must be separate under results')
    r, stopped_bytes, commands, refs, plan = prepare(source)
    if out.exists():
        old = json.loads((out/'plan.json').read_text())
        require(not (out/'stopped_receipt.json').exists() and all(old[k] == plan[k] for k in plan if k != 'prepared_at'), 'Existing plan changed/already executed')
    else:
        out.mkdir(); (out/'plan.json').write_text(json.dumps(plan, indent=2)+'\n', encoding='ascii')
    if not args.run:
        print(json.dumps({k:plan[k] for k in ('status','completed_cases','pending_simulation','remaining_native_commands')})); return 0
    (out/'stopped_receipt.json').write_bytes(stopped_bytes)
    require(digest(out/'stopped_receipt.json') == plan['stopped_receipt_sha256'], 'Stopped receipt backup differs')
    folder, count = source.parent, plan['completed_cases']
    def save():
        source.write_text(json.dumps(r, indent=2)+'\n', encoding='ascii')
    def unchanged():
        check_inputs(plan['inputs_sha256']); check_inputs(plan['preserved_outputs_sha256'])
        require(digest(Path(__file__)) == plan['resume_helper_sha256'], 'Resume helper changed')
    def native(command, log):
        while True:
            require(not (folder/'abort_before_next_native').exists(), 'COOPERATIVE_ABORT_BEFORE_NEXT_NATIVE')
            unchanged(); no_live_capture(folder, r['library'])
            available = capture.free_windows_mib()
            require(isinstance(available, int) and available >= 0, 'Invalid Windows memory response')
            if available >= r['minimum_Windows_free_MiB']: break
            require(args.wait_for_memory, f'WAITING_FOR_MEMORY: {available} MiB')
            wait = {'started':stamp(), 'Windows_free_MiB':available, 'required_MiB':r['minimum_Windows_free_MiB'],
                    'sleep_seconds':30, 'next_command':command, 'log':str(log.relative_to(ROOT))}
            r['memory_waits'].append(wait); save(); print(json.dumps({'status':'WAITING_FOR_MEMORY', **wait}), flush=True)
            time.sleep(30); wait['returned'] = stamp(); save()
        require(not log.exists(), f'Refuse existing native output: {log}')
        record = {'command':command, 'started':stamp(), 'Windows_free_MiB':available, 'log':str(log.relative_to(ROOT))}
        r['native_commands'].append(record); save()
        with log.open('xb') as stream: process = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
        record.update(completed=stamp(), native_exit=process.returncode, log_sha256=digest(log)); save(); unchanged()
        require(process.returncode == 0, f'Native command failed: {log}')
        return process.returncode
    try:
        r['status'] = 'RUNNING_RESUMED_GLS_CAPTURE'; r.pop('error', None)
        r.setdefault('continuations', []).append({'started':stamp(), 'evidence':str(out.relative_to(ROOT)),
            'stopped_receipt_sha256':plan['stopped_receipt_sha256'], 'resume_helper_sha256':plan['resume_helper_sha256'],
            'preserved_native_commands':plan['preserved_native_commands']}); save()
        for index in range(count, 12):
            kernel = capture.KERNELS[index]
            if len(r['native_commands']) == 1+2*index:
                require(not (folder/(kernel+'.raw.saif')).exists(), 'Refuse stale raw SAIF')
                native(*commands[1+2*index])
            require(len(r['native_commands']) == 2+2*index, 'Wrong simulation prefix')
            window = capture.inspect_log(folder/(kernel+'.log'), int(refs[kernel]['mcycle']), r['native_commands'][-1]['native_exit'], kernel)
            raw_stats = capture.inspect_saif(folder/(kernel+'.raw.saif'), window['duration_ps'])
            native(*commands[2+2*index])
            text = (folder/(kernel+'.pins.log')).read_text()
            require('PW_SAIF window ' in text and not re.search(r'Traceback|\[FAIL\]|\*\*\s+(?:Error|Fatal)', text), 'Incomplete pin conversion')
            pin_stats = capture.inspect_saif(folder/(kernel+'.pins.saif'), window['duration_ps'])
            r['cases'][kernel] = {'window':window, 'raw_saif':raw_stats, 'pin_saif':pin_stats,
                'reference_minstret':int(refs[kernel]['minstret']), 'raw_log_sha256':digest(folder/(kernel+'.log'))}; save()
        unchanged()
        require(len(r['native_commands']) == 25 and list(r['cases']) == list(capture.KERNELS), 'Incomplete resumed capture')
        r['status'] = 'VERIFIED_EXACT_CAPTURE_SINGLE_PASS'; r['completed'] = stamp(); save()
        verifier.check_capture(source, r['pass'])
        (out/'completed.json').write_text(json.dumps({'status':r['status'], 'completed':stamp(),
            'receipt_sha256':digest(source), 'native_commands':25, 'cases':12, 'new_native_compilations':0}, indent=2)+'\n', encoding='ascii')
    except BaseException as exc:
        r['status'] = 'STOPPED_REQUIRES_INSPECTION'; r['error'] = str(exc); save(); raise
    print(json.dumps({'status':r['status'], 'cases':12, 'native_commands':25})); return 0


if __name__ == '__main__':
    raise SystemExit(main())
