#!/usr/bin/env python3
"""Offline recording of ONE UART capture or explicitly supplied LED/HEX observation.

No programming, serial access, UI, reset, benchmark execution or next-case approval.
The first case's special reset/capture metadata is preserved.
"""
import argparse
import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
import re

import check_board_uart as uart

ROOT = Path(__file__).resolve().parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write_json(path, value):
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value, indent=2)+'\n', encoding='ascii')
    temporary.replace(path)


def hex_value(text, width):
    require(text is not None and re.fullmatch(r'(?:0[xX])?[0-9a-fA-F]+', text), 'Supply an actual hexadecimal observation')
    value = int(text, 16)
    require(value < 16**width, 'Observed hexadecimal value is out of range')
    return f'{value:0{width}X}'


def sync_tracking(folder, args, index, session, observation, checked):
    """Caller has already flushed Hercules; this only synchronizes records."""
    programmed = set()
    for path in (folder/'programming').glob('*.log.json'):
        p = read_json(path); case, number = p.get('case', 0), p.get('pass', 0)
        if isinstance(case, int) and 1 <= case <= 100 and number in (1, 2):
            item = index[case-1]
            if p.get('status') == 'PROGRAMMED_ONLY_NOT_BOARD_PASS' and p.get('native_exit') == 0 and all(
                p.get(k) == v for k, v in [('kernel', item['kernel']), ('config', item['config']), ('fit_seed', 2),
                ('sof_sha256', item['sha256']), ('firmware_sha256', item['fw_sha256']), ('rtl_aggregate', item['rtl_aggregate'])]):
                if p.get('started', '')[:10].replace('-', '') == args.session and Path(p['log']).is_file():
                    programmed.add((case, number))
    later_pass = next((p for p in sorted(session.get('scheduled_passes', [1, 2])) if p > args.pass_no), None)
    session.update(programmed_cases=len(programmed), logging_enabled=False,
        logging_evidence=observation['uart_log']+'.setup.json',
        next_case=args.case+1 if args.case < 100 else 1 if later_pass is not None else None,
        next_pass=args.pass_no if args.case < 100 else later_pass,
        next_programming_authorized=False)
    setup_path = folder/'setup_status.json'; setup = read_json(setup_path)
    setup.update(current_case=args.case, current_pass=args.pass_no, status=session['status'],
        current_case_evidence=session['current_case_evidence'], updated_at=observation['recorded_at'])
    write_json(setup_path, setup)
    journal = ROOT/'NHAT_KY.md'; original = journal.read_bytes()
    marker = f'board {args.session} case {args.case} pass {args.pass_no}'.encode('ascii')
    start, end = original.find(b'## 8a.'), original.find(b'\n## 9.')+1
    require(0 <= start < end, 'NHAT_KY section8a boundary is missing')
    if marker not in original:
        p = read_json(folder/observation['programming_receipt'])
        when = datetime.fromisoformat(observation['recorded_at']).astimezone().strftime('%Y-%m-%d %H:%M')
        text = (f'\n### {when} Board UART {observation["kernel"]} {observation["config"]}\n\n'
            f'- {marker.decode()}: native UART khop {checked["numeric_reference_checks"]} truong; '
            f'MCYCLE=0x{checked["observed_hex"]["MCYCLE"]}, MINSTRET=0x{checked["observed_hex"]["MINSTRET"]}.\n'
            f'- Nap SOF seed2 nativeexit0, ket thuc {p["completed"]}; evidence: '
            f'results/board_{args.session}/{observation["programming_receipt"]}, {observation["uart_log"]}.\n'
            '- Mot case vat ly; board_pair_complete=false. Quyen nap tiep van khoa, cho xac nhan.\n\n')
        addition = text.replace('\n', '\r\n').encode('ascii') if b'\r\n' in original else text.encode('ascii')
        require(journal.read_bytes() == original, 'History changed concurrently; inspect before retry')
        journal.write_bytes(original[:end]+addition+original[end:])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--session', required=True, help='YYYYMMDD')
    ap.add_argument('--case', type=int, required=True, choices=range(1, 101))
    ap.add_argument('--pass', dest='pass_no', type=int, required=True, choices=(1, 2))
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--record-uart', action='store_true')
    mode.add_argument('--confirm-display', action='store_true')
    ap.add_argument('--ledr', help='Actual observed hexadecimal LEDR value')
    ap.add_argument('--display', help='Actual observed HEX7..HEX0 value')
    ap.add_argument('--sync-tracking', action='store_true', help='Opt in after Hercules flush: synchronize tracking and one deduplicated history event; record-UART only')
    args = ap.parse_args()
    require(not args.sync_tracking or args.record_uart, '--sync-tracking is only valid with --record-uart')
    require(re.fullmatch(r'\d{8}', args.session), 'Session must be YYYYMMDD')
    datetime.strptime(args.session, '%Y%m%d')
    folder = ROOT/'results'/('board_'+args.session)
    session = read_json(folder/'session.json')
    scheduled = session.get('scheduled_passes', [1, 2])
    require(isinstance(scheduled, list) and args.pass_no in scheduled, f'Pass {args.pass_no} is not scheduled for this board session')
    require(session.get('session_date', '').replace('-', '') == args.session and
            session.get('per_case_confirmation_required') is True, 'Session date/confirmation policy mismatch')
    index = uart.rows(uart.OUT/'INDEX.csv')
    require(len(index) == 100, 'Board index is incomplete')
    item = index[args.case-1]
    kernel, config = item['kernel'], item['config']
    prefix = f'p{args.pass_no}_{kernel}_{config}'
    observation_path = folder/(prefix+'.observation.json')
    observation = read_json(observation_path) if observation_path.exists() else {}
    special = args.case == 1 and args.pass_no == 1 and (
        observation.get('manual_reset_confirmed') or observation.get('initial_empty_capture'))
    require(not (args.record_uart and special), 'Preserve the initial special case: use its existing dedicated UART evidence')
    for key, value in [('case', args.case), ('pass_number', args.pass_no), ('kernel', kernel), ('config', config)]:
        require(key not in observation or observation[key] == value, 'Existing observation identifies another case')
    successful = []
    for path in sorted((folder/'programming').glob(prefix+'.*.log.json')):
        p = read_json(path)
        if p.get('status') == 'PROGRAMMED_ONLY_NOT_BOARD_PASS' and p.get('native_exit') == 0 and all(
            p.get(k) == v for k, v in [('case', args.case), ('pass', args.pass_no), ('kernel', kernel),
            ('config', config), ('fit_seed', 2), ('sof_sha256', item['sha256']),
            ('firmware_sha256', item['fw_sha256']), ('rtl_aggregate', item['rtl_aggregate'])]):
            require(Path(p['sof']).resolve() == (uart.OUT/item['sof']).resolve() and
                    Path(p['log']).is_file() and p.get('started', '')[:10].replace('-', '') == args.session,
                    'Successful programming receipt has wrong SOF/log/date')
            successful.append(path)
    require(len(successful) == 1, 'Require exactly one matching successful fresh programming receipt')
    validation_path = folder/'uart'/(prefix+'.uart_validation.json')
    if args.record_uart:
        require(args.ledr is None and args.display is None, 'Record UART separately from display confirmation')
        log = folder/'uart'/(prefix+'.uart.log')
        checked = uart.check(log, kernel, config)
        if validation_path.exists():
            old = read_json(validation_path)
            recorded = old.get('checker_result', old)
            require({k:recorded.get(k) for k in checked} == checked, 'Existing UART validation differs; preserve and inspect it')
        validation = {'status':checked['status'], 'capture_method':'NATIVE_HERCULES_LOG_FILE',
            'single_physical_execution':True, 'physical_execution_count':1, 'board_pair_complete':False,
            'log_bytes':log.stat().st_size, 'checker_sha256':uart.sha(ROOT/'scripts/fpga/check_board_uart.py'),
            'checker_result':checked}
        confirmed = observation.get('display_matches_reference') is True
    else:
        validation_path = folder/observation.get('uart_validation_evidence', 'uart/'+prefix+'.uart_validation.json')
        require(validation_path.resolve().is_relative_to((folder/'uart').resolve()), 'UART validation is outside the session')
        saved = read_json(validation_path)
        recorded = saved.get('checker_result', saved)
        log = Path(recorded['uart'])
        require(log.resolve().is_relative_to((folder/'uart').resolve()), 'UART log is outside the session')
        checked = uart.check(log, kernel, config)
        require({k:recorded.get(k) for k in checked} == checked, 'UART bytes/source/reference changed after validation')
        led, display = hex_value(args.ledr, 2), hex_value(args.display, 8)
        require(led == 'A5' and display == item['expected_mcycle_hex'], 'Actual LED/HEX does not match the expected result')
        observation.update(observed_ledr_hex=led, observed_display_hex=display, display_matches_reference=True,
            display_confirmation_input={'ledr':args.ledr, 'display':args.display},
            observation_method='MANUAL_PHYSICAL_DISPLAY_READBACK')
        confirmed = True
    status = ('SINGLE_PASS_DISPLAY_AND_UART_MATCH_PHOTO_MISSING' if not observation.get('photo') else
              'SINGLE_PASS_DISPLAY_AND_UART_MATCH') if confirmed else 'UART_MATCH_SINGLE_PASS_WAIT_DISPLAY_CONFIRMATION'
    observation.update(status=status, recorded_at=datetime.now(timezone.utc).isoformat(), case=args.case,
        pass_number=args.pass_no, kernel=kernel, config=config, fit_seed=2,
        observed_mcycle_hex=checked['observed_hex']['MCYCLE'], observed_minstret_hex=checked['observed_hex']['MINSTRET'],
        expected_ledr_hex='A5', expected_mcycle_hex=item['expected_mcycle_hex'], expected_minstret_hex=item['expected_minstret_hex'],
        uart_log=log.relative_to(folder).as_posix(), uart_bytes=log.stat().st_size,
        uart_validation='28_NUMERIC_FIELDS_MATCH_PAIRED_RTL_REFERENCE',
        uart_validation_evidence=validation_path.relative_to(folder).as_posix(),
        programming_receipt=successful[0].relative_to(folder).as_posix(), sof_sha256=item['sha256'],
        firmware_sha256=item['fw_sha256'], next_case_authorized=False, board_pair_complete=False)
    observation.setdefault('observed_ledr_hex', None)
    observation.setdefault('observed_display_hex', None)
    observation.setdefault('photo', None)
    observation.setdefault('capture_method', 'NATIVE_HERCULES_LOG_FILE')
    csv_path = folder/'results.csv'
    with csv_path.open(encoding='utf-8-sig', newline='') as stream:
        original = stream.read()
    reader = csv.DictReader(io.StringIO(original))
    rows, fields = list(reader), reader.fieldnames
    matches = [i for i, r in enumerate(rows) if (r['pass'], r['kernel'], r['config']) == (str(args.pass_no), kernel, config)]
    lines = original.splitlines(keepends=True)
    require(len(rows) == 200 and len(matches) == 1 and len(lines) == 201, 'Results CSV has missing/ambiguous/multiline rows')
    selected = matches[0]; row = rows[selected]
    require(row['sof_sha256'] == item['sha256'] and row['fit_seed'] == '2', 'Results row has wrong SOF/seed')
    row.update(observed_ledr_hex=observation['observed_ledr_hex'] or '', observed_mcycle_hex=observation['observed_mcycle_hex'],
        observed_minstret_hex=observation['observed_minstret_hex'], uart_log=observation['uart_log'], status=status)
    rendered = io.StringIO(newline='')
    newline = '\r\n' if lines[selected+1].endswith('\r\n') else '\n'
    csv.DictWriter(rendered, fieldnames=fields, lineterminator=newline,
        quoting=csv.QUOTE_ALL if lines[selected+1].startswith('"') else csv.QUOTE_MINIMAL).writerow(row)
    lines[selected+1] = rendered.getvalue()
    session.update(status=f'CASE{args.case}_'+('DISPLAY_AND_UART_MATCH_WAITING_OWNER_CONFIRMATION' if confirmed else
        'UART_PASS_WAITING_DISPLAY_AND_NEXT_CASE_CONFIRMATION'), current_case=args.case,
        current_case_evidence=observation_path.name, current_uart_log=observation['uart_log'],
        next_programming_authorized=False, confirmation_state=f'CASE{args.case}_OWNER_CONFIRMATION_REQUIRED',
        measured_cases=sum(bool(r['observed_mcycle_hex']) for r in rows),
        display_observed_cases=sum(bool(r['observed_ledr_hex']) for r in rows), updated_at=observation['recorded_at'])
    if args.record_uart and not validation_path.exists():
        write_json(validation_path, validation)
    write_json(observation_path, observation)
    temporary = csv_path.with_name(csv_path.name+'.tmp')
    with temporary.open('w', encoding='utf-8', newline='') as stream:
        stream.write(''.join(lines))
    temporary.replace(csv_path)
    if args.sync_tracking:
        sync_tracking(folder, args, index, session, observation, checked)
    write_json(folder/'session.json', session)
    print(json.dumps({'status':status, 'case':args.case, 'pass':args.pass_no,
        'numeric_reference_checks':checked['numeric_reference_checks'], 'MCYCLE':observation['observed_mcycle_hex'],
        'MINSTRET':observation['observed_minstret_hex'], 'next_programming_authorized':False}))


if __name__ == '__main__':
    main()
