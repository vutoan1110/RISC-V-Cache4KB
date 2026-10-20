#!/usr/bin/env python3
"""Foreground single-pass board continuation; default mode only prints a plan.

Uses existing logging, programmer and offline recorder helpers. Never fits,
rebuilds, resets, retries failed programming, or supplies physical LED values.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import check_board_uart as uart
import record_board_case as recorder
from board_common import manifest, sha

ROOT = Path(__file__).resolve().parents[2]


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def last_json(text):
    for line in reversed(text.splitlines()):
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict):
            return value
    raise RuntimeError('Native helper produced no JSON result')


class StopRequested(RuntimeError):
    pass


class WaitTimeout(RuntimeError):
    pass


class Controller:
    def __init__(self, args, folder, index):
        self.args, self.folder, self.index = args, folder, index
        self.stop_flag = folder/('.stop_board_uart_matrix_'+args.measurement_date)
        self.open_helper = folder/'open_serial_20261016.py'
        self.ui_helper = ROOT/'scripts/fpga/hercules_case_ui.py'
        self.programmer = ROOT/'scripts/fpga/program_board_case.ps1'
        self.recorder = ROOT/'scripts/fpga/record_board_case.py'
        self.pins = {str(p): sha(p) for p in (
            Path(__file__), self.open_helper, self.ui_helper, self.programmer,
            self.recorder, ROOT/'scripts/fpga/check_board_uart.py',
            ROOT/'scripts/fpga/hercules_controls.py', ROOT/'results/rtl_manifest.json',
            uart.OUT/'INDEX.csv', uart.OUT/'BUILD_STATE.json',
            ROOT/'results/board_reference_6c4ccffd_20261009_p1.csv',
            ROOT/'results/board_reference_6c4ccffd_20261009_p2.csv')}
        self.output = folder/('uart_matrix_'+args.measurement_date+'_'+datetime.now().strftime('%H%M%S_%f'))
        self.lock = folder/('.board_uart_matrix_'+args.measurement_date+'.lock.json')
        self.output.mkdir(exist_ok=False)
        self.state = {'status': 'STARTING', 'pid': os.getpid(), 'started': timestamp(),
                      'session': args.session, 'measurement_date': args.measurement_date,
                      'completed_this_run': [], 'skipped_verified_today': [],
                      'current_case': None, 'child_pid': None, 'logging_active': False,
                      'stop_flag': str(self.stop_flag), 'input_sha256': self.pins,
                      'physical_display_observations_supplied': False}
        self.counter, self.last_pulse, self.child = 0, 0.0, None
        with self.lock.open('x', encoding='ascii') as stream:
            json.dump({'pid': os.getpid(), 'output': str(self.output), 'started': timestamp()}, stream)
        self.event('STARTING', output=str(self.output), stop_flag=str(self.stop_flag))

    def pulse(self, force=False):
        if force or time.monotonic()-self.last_pulse >= 10:
            self.state['heartbeat_at'] = timestamp()
            target = self.output/'state.json'
            temporary = target.with_suffix('.json.tmp')
            temporary.write_text(json.dumps(self.state, indent=2)+'\n', encoding='ascii')
            temporary.replace(target)
            self.last_pulse = time.monotonic()
            print(json.dumps({'heartbeat': self.state['heartbeat_at'], 'status': self.state['status'],
                              'case': self.state['current_case'], 'child_pid': self.state['child_pid']}), flush=True)

    def event(self, status, **details):
        self.state.update(status=status, **details)
        with (self.output/'events.jsonl').open('a', encoding='ascii') as stream:
            stream.write(json.dumps({'at': timestamp(), 'status': status, **details})+'\n')
        self.pulse(True)

    def policy(self, case, action=False):
        if self.stop_flag.exists():
            raise StopRequested('Cooperative stop flag present; no further UI/programming action')
        session = read_json(self.folder/'session.json')
        require(session.get('session_date', '').replace('-', '') == self.args.session, 'Wrong canonical session date')
        require(session.get('automatic_uart_continuation_authorized') is True and
                session.get('automatic_case_range') == [43, 100] and
                session.get('per_case_confirmation_required') is False and
                session.get('manual_display_observation_required') is False,
                'Automatic continuation is held or is not explicitly authorized')
        require(session.get('scheduled_passes') == [1] and
                self.args.measurement_date in recorder.approved_dates(session, self.args.session),
                'Pass/date is not approved')
        require(43 <= case <= 100, 'Case is outside approved automatic range')
        require(datetime.now().strftime('%Y%m%d') == self.args.measurement_date, 'Actual measurement date changed')
        if action:
            require(session.get('next_programming_authorized') is True and session.get('next_case') == case,
                    'Current case is not the authorized next case; no hardware action')
        for path, digest in self.pins.items():
            require(sha(Path(path)) == digest, 'Pinned input changed: '+path)

    def command(self, label, command, case, action=False, allow_timeout=False, limit=120):
        self.policy(case, action)
        self.counter += 1
        log = self.output/(f'{self.counter:04d}_{case}_{label}.log')
        self.event(label, command=command, native_log=str(log))
        started = time.monotonic()
        with log.open('xb') as stream:
            self.child = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                          env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            self.state['child_pid'] = self.child.pid
            while self.child.poll() is None:
                self.pulse()
                if time.monotonic()-started >= limit:
                    raise WaitTimeout('Helper wait limit reached; child remains unmodified, no reset or retry')
                time.sleep(.25)
        code = self.child.returncode
        self.child = None
        self.state['child_pid'] = None
        output = log.read_text(encoding='utf-8-sig', errors='replace')
        self.event(label+'_EXIT', native_exit=code, native_log=str(log))
        if not allow_timeout:
            require(code == 0, f'{label} failed with native exit {code}; no automatic retry; see {log}')
        return code, output

    def open_serial(self, case, label):
        _, output = self.command(label, [sys.executable, '-B', str(self.open_helper), '--pid', str(self.args.pid)],
                                 case, action=True)
        result = last_json(output)
        require(result.get('status') == 'COM3_OPEN' and result.get('pid') == self.args.pid and
                isinstance(result.get('receive_hwnd'), int) and result['receive_hwnd'] > 0,
                'Hercules COM3/receive control readiness failed')
        return result['receive_hwnd']

    def ui(self, label, case, hwnd, *options, action=False, allow_timeout=False):
        return self.command(label, [sys.executable, '-B', str(self.ui_helper), '--pid', str(self.args.pid),
                                   '--receive-hwnd', str(hwnd), *map(str, options)],
                            case, action=action, allow_timeout=allow_timeout)

    def checked_receipt(self, path, case):
        item = self.index[case-1]
        value = read_json(path)
        require(recorder.receipt_matches(value, self.folder, item, case, 1,
                                        self.args.session, self.args.measurement_date),
                'Programming receipt does not match current case/date/SOF/firmware: '+str(path))
        native = Path(value['log']).read_text(encoding='utf-8-sig', errors='replace')
        require('Configuration succeeded' in native and 'Successfully performed operation' in native,
                'Native programming log does not confirm successful configuration')
        return value

    def completed_today(self, case):
        item = self.index[case-1]
        path = self.folder/f"p1_{item['kernel']}_{item['config']}.observation.json"
        if not path.exists():
            return False
        observation = read_json(path)
        require(all(observation.get(k) == v for k, v in (
            ('case', case), ('pass_number', 1), ('kernel', item['kernel']), ('config', item['config']),
            ('measurement_date', self.args.measurement_date), ('session_date', self.args.session),
            ('sof_sha256', item['sha256']), ('firmware_sha256', item['fw_sha256']))),
            'Existing observation is not a valid today result; preserve it and inspect instead of rerunning')
        log = recorder.session_path(self.folder, observation['uart_log'], 'uart')
        validation = read_json(recorder.session_path(self.folder, observation['uart_validation_evidence'], 'uart'))
        checked = uart.check(log, item['kernel'], item['config'])
        saved = validation.get('checker_result', validation)
        require({key: saved.get(key) for key in checked} == checked, 'Recorded UART bytes/reference/hash changed')
        self.checked_receipt(recorder.session_path(self.folder, observation['programming_receipt'], 'programming'), case)
        return True

    def wait_done(self, case, hwnd):
        deadline = time.monotonic()+self.args.case_timeout_seconds
        while time.monotonic() < deadline:
            self.policy(case)
            code, output = self.ui('WAIT_DONE', case, hwnd, '--wait-done', '--timeout-seconds', 5, allow_timeout=True)
            result = last_json(output)
            if result.get('status') == 'DONE':
                require(code == 0 and result.get('done_count') == 1, 'Invalid DONE result')
                return
            require(code == 1 and result.get('status') == 'WAIT_TIMEOUT',
                    'UART receive helper failed: '+str(result.get('status')))
            self.event('WAITING_FOR_DONE', remaining_seconds=max(0, round(deadline-time.monotonic(), 1)))
        raise WaitTimeout('UART DONE not yet observed within bounded wait; not a benchmark failure; preserve active capture, no reset/rerun')

    def run_case(self, case):
        self.state['current_case'] = case
        self.policy(case)
        require(manifest()['aggregate'] == self.index[case-1]['rtl_aggregate'], 'Live RTL changed')
        if self.completed_today(case):
            self.state['skipped_verified_today'].append(case)
            self.event('SKIPPED_VERIFIED_TODAY')
            return
        item = self.index[case-1]
        prefix = f"p1_{item['kernel']}_{item['config']}"
        relative = f'uart/{prefix}.{self.args.measurement_date}.uart.log'
        log = recorder.session_path(self.folder, relative, 'uart')
        require(not any(p.exists() for p in (log, log.with_suffix('.previous_receive.txt'),
                                             log.with_suffix('.log.setup.json'),
                                             log.with_name(log.name[:-len('.uart.log')]+'.uart_validation.json'))),
                'Fresh capture/evidence filename already exists; preserve it, no automatic overwrite or rerun')
        hwnd = self.open_serial(case, 'OPEN_RESTORE_BEFORE_PROGRAM')
        _, output = self.ui('FRESH_LOG', case, hwnd, '--log', str(log), action=True)
        ready = last_json(output)
        require(ready.get('logging_enabled') is True and Path(ready.get('log', '')).resolve() == log and
                ready.get('pid') == self.args.pid and ready.get('receive_hwnd') == hwnd,
                'Fresh Hercules logging readiness failed')
        self.state['logging_active'] = True
        before = set((self.folder/'programming').glob(prefix+'.*.log.json'))
        self.command('PROGRAM', ['pwsh', '-NoProfile', '-File', str(self.programmer), '-Case', str(case),
                                '-Pass', '1', '-SessionDate', self.args.session,
                                '-MeasurementDate', self.args.measurement_date, '-Program'], case, action=True)
        created = set((self.folder/'programming').glob(prefix+'.*.log.json'))-before
        require(len(created) == 1, 'Require exactly one newly created programming receipt; no automatic retry')
        receipt = created.pop()
        self.checked_receipt(receipt, case)
        hwnd = self.open_serial(case, 'RESTORE_AFTER_PROGRAM')
        self.wait_done(case, hwnd)
        _, output = self.ui('FLUSH_LOG', case, hwnd, '--stop', action=True)
        require(last_json(output).get('logging_enabled') is False, 'Hercules did not flush/stop logging')
        self.state['logging_active'] = False
        self.command('RECORD_UART', [sys.executable, '-B', str(self.recorder), '--session', self.args.session,
                                   '--measurement-date', self.args.measurement_date, '--case', str(case), '--pass', '1',
                                   '--uart-log', relative, '--programming-receipt', receipt.relative_to(self.folder).as_posix(),
                                   '--record-uart', '--sync-tracking'], case)
        require(self.completed_today(case), 'Post-record evidence verification failed')
        self.state['completed_this_run'].append(case)
        self.event('CASE_UART_VERIFIED', kernel=item['kernel'], config=item['config'],
                   uart=str(log), uart_sha256=sha(log), programming_receipt=str(receipt))

    def run(self):
        try:
            for case in range(self.args.start_case, self.args.end_case+1):
                self.run_case(case)
            self.event('REQUESTED_RANGE_UART_VERIFIED_SINGLE_PASS')
            return 0
        except StopRequested as error:
            self.event('STOPPED_COOPERATIVE', reason=str(error))
            return 2
        except WaitTimeout as error:
            self.event('WAIT_TIMEOUT_PRESERVE_ACTIVE_CASE', reason=str(error))
            return 3
        except Exception as error:
            self.event('STOPPED_ERROR_NO_AUTOMATIC_RETRY', reason=str(error), error_type=type(error).__name__)
            return 1
        finally:
            if self.child is None or self.child.poll() is not None:
                self.lock.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--session', default='20261013', choices=('20261013',))
    parser.add_argument('--measurement-date', default='20261016')
    parser.add_argument('--pid', type=int, default=42920)
    parser.add_argument('--start-case', type=int, default=43, choices=range(43, 101))
    parser.add_argument('--end-case', type=int, default=100, choices=range(43, 101))
    parser.add_argument('--case-timeout-seconds', type=int, default=900)
    args = parser.parse_args()
    require(args.start_case <= args.end_case and args.case_timeout_seconds >= 300, 'Invalid case range/wait limit')
    datetime.strptime(args.measurement_date, '%Y%m%d')
    folder = ROOT/'results'/('board_'+args.session)
    index = uart.rows(uart.OUT/'INDEX.csv')
    require(len(index) == 100 and sha(folder/'INDEX.csv') == sha(uart.OUT/'INDEX.csv'), 'Canonical board index differs')
    current = manifest()
    build = read_json(uart.OUT/'BUILD_STATE.json')
    require(build.get('state') == 'READY_FOR_PHYSICAL_SESSION' and build.get('common_seed') == 2 and
            build.get('canonical_restoration') == 'PASS' and build.get('rtl_id') == current['aggregate'] and
            all(row['fit_seed'] == '2' and row['rtl_aggregate'] == current['aggregate'] for row in index),
            'Current RTL/common-seed2 package is not ready')
    if not args.run:
        print(json.dumps({'status': 'PLAN_ONLY_NO_UI_SERIAL_OR_PROGRAMMING', 'session': str(folder),
                          'measurement_date': args.measurement_date, 'case_range': [args.start_case, args.end_case],
                          'case_timeout_seconds': args.case_timeout_seconds,
                          'stop_flag': str(folder/('.stop_board_uart_matrix_'+args.measurement_date)),
                          'requirements': 'Explicit automatic authorization, exact range43..100, pass1, approved date, fresh capture, current hashes. Valid today records are skipped.'}, indent=2))
        return 0
    require(sys.platform == 'win32', 'Hardware controller requires Windows')
    import ctypes
    kernel = ctypes.windll.kernel32
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    kernel.GetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
    process_mask, system_mask = ctypes.c_size_t(), ctypes.c_size_t()
    require(kernel.GetProcessAffinityMask(kernel.GetCurrentProcess(),
            ctypes.byref(process_mask), ctypes.byref(system_mask)) and process_mask.value == 0x20,
            'Launch this foreground Python controller pinned to affinity HEX20')
    return Controller(args, folder, index).run()


if __name__ == '__main__':
    raise SystemExit(main())
