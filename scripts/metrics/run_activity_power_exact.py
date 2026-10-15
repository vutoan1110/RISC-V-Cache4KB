#!/usr/bin/env python3
"""Prepare or execute paired OpenSTA power for two verified exact GLS captures.

Default: preparation only, no WSL or native STA process. --run is an explicit
resource scheduling decision. Preserved helpers/layout/capture files are read
only. A new output directory is required; no resume or overwrite is attempted.
"""
from __future__ import annotations
import argparse
import csv
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts/verification'))
import verify_gls_exact_pair as pair
import run_gls_exact_window as capture

CORNER = 'nom_tt_025C_1v80'
GROUPS = ('Sequential','Combinational','Clock','Macro','Pad','Total')
STA = '/nix/store/q5ycjmn0d9awbcq05c75z2rmgwjgbc9g-opensta/bin/sta'
LINUX_ROOT = '/mnt/e/Projects/RISCV-research/'
NUMBER = r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'
GROUP_LINE = re.compile(r'^('+'|'.join(GROUPS)+r')\s+('+NUMBER+r')\s+('+NUMBER+r')\s+('+NUMBER+r')\s+('+NUMBER+r')\s+('+NUMBER+r')%\s*$')

def require(ok, message):
    pair.require(ok, message)

def sha(path):
    return pair.sha(path)

def local(path):
    return pair.local(path)

def linux(path):
    pp = local(path)
    require(pp.is_relative_to(ROOT), 'WSL command path must stay in the research repository')
    return LINUX_ROOT + pp.relative_to(ROOT).as_posix()

def windows_path(path):
    if path.startswith(LINUX_ROOT):
        return ROOT / path.removeprefix(LINUX_ROOT)
    require(path.startswith('/home/') or path.startswith('/nix/store/'), f'Unsupported external tool input: {path}')
    require(not any(x in path for x in ('\n','\r','\x00')) and '..' not in Path(path).parts, 'Unsafe tool input path')
    return Path(r'\\wsl.localhost\Ubuntu') / path.lstrip('/').replace('/', '\\')

def power_groups(lines):
    groups = {}
    for line in lines:
        m = GROUP_LINE.fullmatch(line.strip())
        if not m:
            continue
        require(m[1] not in groups, 'Duplicate power group '+m[1])
        values = tuple(Decimal(v) for v in m.groups()[1:])
        require(all(v.is_finite() and v >= 0 for v in values), 'Negative/nonfinite power value')
        require(values[-1] <= 100, 'Invalid power group share')
        groups[m[1]] = values
    require(set(groups) == set(GROUPS), 'Missing/malformed named power group')
    return {k: list(map(str, groups[k])) for k in GROUPS}

def read_sta_inputs(step):
    step = local(step)
    require(step.is_relative_to(ROOT/'asic') and step.name.endswith('-openroad-stapostpnr'), 'Use final STAPostPNR, never mid-PnR')
    corner = step / CORNER
    log = corner/'sta.log'
    patterns = {
        'libs': re.compile(r"^Reading cell library for the '"+CORNER+r"' corner at '([^']+)'…$"),
        'netlist': re.compile(r"^Reading top-level netlist at '([^']+)'…$"),
        'sdc': re.compile(r"^Reading design constraints file at '([^']+)'…$"),
        'spef': re.compile(r"^Reading top-level design parasitics for the '"+CORNER+r"' corner at '([^']+)'…$")}
    found = {k: [] for k in patterns}
    with log.open(encoding='utf-8') as f:
        for line in f:
            for key, pattern in patterns.items():
                m = pattern.fullmatch(line.rstrip('\r\n'))
                if m: found[key].append(m[1])
    require(len(found['libs']) == 3 and len(set(found['libs'])) == 3 and all(len(found[k]) == 1 for k in ('netlist','sdc','spef')), 'Missing/ambiguous final STA corner inputs')
    require({Path(p).name for p in found['libs']} == {'sky130_fd_sc_hd__tt_025C_1v80.lib','sky130_sram_1kbyte_1rw1r_32x256_8_TT_1p8V_25C.lib','sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib'}, 'Wrong nominal TT libraries')
    envs = sorted(corner.glob('_env*.tcl'))
    require(len(envs) == 1, 'Ambiguous final STA environment')
    env = envs[0]
    env_text = env.read_text()
    require(re.search(r'^set ::env\(CLOCK_PERIOD\) 20(?:\.0)?$', env_text, re.M) and re.search(r'^set ::env\(OPENLANE_SDC_IDEAL_CLOCKS\) 0$', env_text, re.M), 'Final STA clock/propagation profile mismatch')
    require(re.search(r'^set ::env\(CURRENT_NETLIST\) '+re.escape(found['netlist'][0])+r'$', env_text, re.M), 'STA log/environment netlist mismatch')
    scripts = set(re.findall(r'^sta .* (/.*/scripts)/openroad/sta/corner\.tcl$', (step/'COMMANDS').read_text(), re.M))
    require(len(scripts) == 1, 'Missing/ambiguous final flow script tree')
    scripts_dir = windows_path(next(iter(scripts)))
    require(scripts_dir.is_relative_to(ROOT/'asic/openlane-local'), 'Unexpected OpenLane script tree')
    net = windows_path(found['netlist'][0])
    require(net.is_relative_to(step.parent) and net.parent.name.endswith('-openroad-fillinsertion'), 'STA is not bound to final fill netlist')
    sdc = windows_path(found['sdc'][0])
    require('create_clock -name $clock_port -period $clock_period' in sdc.read_text(), 'Unknown SDC clock definition')
    require('/nom/' in found['spef'][0] and found['spef'][0].endswith('.nom.spef') and windows_path(found['spef'][0]).is_relative_to(step.parent), 'Use nominal RCX SPEF from this layout')
    flow_groups = power_groups((corner/'power.rpt').read_text().splitlines())
    paths = [log, env, step/'COMMANDS', corner/'power.rpt', step/'config.json', step/'state_out.json', step.parent/'resolved.json', net, net.with_name('soc_asic_top.def'), sdc,
             windows_path(found['spef'][0]), ROOT/'asic/gls/sta_power.sh', ROOT/'asic/gls/power_saif.tcl', Path(__file__), Path(pair.__file__), Path(capture.__file__), windows_path(STA)]
    paths += [windows_path(p) for p in found['libs']]
    paths += sorted(scripts_dir.rglob('*.tcl'))
    require(paths and len(paths) <= 500, 'Unexpected flow input membership')
    hashes, missing = {}, []
    for p in paths:
        if not p.is_file(): missing.append(str(p))
        else: hashes[str(p.resolve())] = sha(p)
    return {'step':str(step.relative_to(ROOT)), 'corner':CORNER, 'netlist_linux':found['netlist'][0], 'netlist':str(net.relative_to(ROOT)),
            'netlist_sha256':sha(net), 'sdc_linux':found['sdc'][0], 'spef_linux':found['spef'][0], 'liberties_linux':found['libs'],
            'sta_linux':STA, 'flow_vectorless_groups':flow_groups, 'inputs_sha256':hashes, 'missing_external_inputs':missing,
            'period_ps':20000, 'method':'fresh exact GLS SAIF -> driver-pin SAIF -> OpenSTA with final nominal RCX SPEF and signoff SDC'}

def inspect_power(path, native_exit, expected, saif_linux=None):
    require(native_exit == 0, 'Native WSL/OpenSTA command failed')
    groups = []
    origins = {}
    total = None
    info = []
    loaded = {'libs':[], 'netlist':[], 'sdc':[], 'spef':[]}
    inner = []; complete = 0
    with Path(path).open(encoding='utf-8', errors='strict') as f:
        for line in f:
            text = line.rstrip('\r\n')
            require(not re.search(r'(?:^|\s)(?:Error|Fatal)(?:\s|:|\[)|\*\*\s+(?:Error|Fatal)|\[FAIL\]|Traceback|error while|invalid command name|can\x27t read|couldn\x27t', text, re.I), 'Error/fatal in native power report')
            groups.append(text) if GROUP_LINE.fullmatch(text.strip()) else None
            if text.startswith('PW_INFO '): info.append(text)
            if text.startswith('EXACT_POWER_NATIVE_EXIT '): inner.append(int(text.split()[-1]))
            if text == 'EXACT_POWER_EXECUTION_COMPLETE': complete += 1
            if text.startswith('PW_ORIGIN total_output_pins '):
                require(total is None, 'Repeated total output-pin count'); total = int(text.split()[-1])
            elif text.startswith('PW_ORIGIN '):
                m = re.fullmatch(r'PW_ORIGIN\s+(\S+)\s+(\d+)\s+('+NUMBER+r')\s+%', text)
                require(m is not None and m[1] not in origins, 'Missing/malformed/duplicate power origin')
                share = Decimal(m[3])
                require(share.is_finite() and 0 <= share <= 100, 'Invalid origin share')
                origins[m[1]] = {'count':int(m[2]), 'percent':str(share)}
            for key, pattern in (
                ('libs', r"^Reading cell library for the '"+CORNER+r"' corner at '([^']+)'…$"),
                ('netlist', r"^Reading top-level netlist at '([^']+)'…$"),
                ('sdc', r"^Reading design constraints file at '([^']+)'…$"),
                ('spef', r"^Reading top-level design parasitics for the '"+CORNER+r"' corner at '([^']+)'…$")):
                m = re.fullmatch(pattern, text)
                if m: loaded[key].append(m[1])
    require(inner == [0] and complete == 1, 'Missing native exit/completion proof')
    require(loaded == {'libs':expected['liberties_linux'], 'netlist':[expected['netlist_linux']], 'sdc':[expected['sdc_linux']], 'spef':[expected['spef_linux']]}, 'STA loaded wrong/missing/duplicate libraries/netlist/SDC/SPEF')
    expected_info = ['PW_INFO sta='+expected['sta_linux']+' corner='+CORNER+' spef='+expected['spef_linux'],
                     'PW_INFO reading activity from '+saif_linux+' scope tb_gls_soc/dut' if saif_linux else 'PW_INFO vectorless (no SAIF)']
    require(info == expected_info, 'Wrong power corner/method/activity scope')
    require(total is not None and total > 0 and origins and sum(v['count'] for v in origins.values()) == total, 'Incomplete output-pin activity origin accounting')
    for origin, value in origins.items():
        require(abs(Decimal(value['percent']) - Decimal(value['count'])*100/total) <= Decimal('0.00501'), 'Inconsistent activity origin share '+origin)
    if saif_linux:
        require(origins.get('saif', {}).get('count',0) > 0, 'Activity power contains no SAIF annotation')
    return {'groups_W_and_percent':power_groups(groups), 'origins':origins, 'total_output_pins':total,
            'native_exit':0, 'report_sha256':sha(path)}

def compare_power(a, b):
    for field in ('groups_W_and_percent','origins','total_output_pins','native_exit'):
        require(a.get(field) == b.get(field), 'Paired independent power differs: '+field)

def queue_script(step, saif, abort, minimum_wsl):
    require(minimum_wsl >= 5000, 'WSL memory threshold must be at least 5000 MiB')
    # Direct foreground bash/sta; no Start-Process/nohup/helper/persistence.
    return '''#!/usr/bin/env bash
set -uo pipefail
while true; do
  if [ -e '''+shlex.quote(linux(abort))+''' ]; then echo '[FAIL] cooperative power queue abort before next tool'; exit 75; fi
  available=$(free -m | awk '/^Mem:/{print $7}')
  [[ "$available" =~ ^[0-9]+$ ]] || { echo '[FAIL] memory query incomplete'; exit 76; }
  if [ "$available" -ge '''+str(minimum_wsl)+''' ]; then break; fi
  echo "EXACT_POWER_WAITING_FOR_WSL_MEMORY available_MiB=$available required_MiB='''+str(minimum_wsl)+'''"
  sleep 30
done
bash '''+shlex.quote(LINUX_ROOT+'asic/gls/sta_power.sh')+' '+shlex.quote(linux(step))+' '+shlex.quote(linux(saif) if saif else '')+' '+shlex.quote(CORNER)+'''
native_rc=$?
echo "EXACT_POWER_NATIVE_EXIT $native_rc"
if [ "$native_rc" -eq 0 ]; then echo EXACT_POWER_EXECUTION_COMPLETE; fi
exit "$native_rc"
'''

def power_row(k, report, reference):
    total = list(map(Decimal, report['groups_W_and_percent']['Total'][:4]))
    cycles, instructions = int(reference['window']['mcycle']), int(reference['reference_minstret'])
    require(cycles > 0 and instructions > 0 and reference['window']['duration_ps'] == cycles*20000, 'Invalid exact power window/counter denominator')
    return {'kernel':k, 'mcycle':str(cycles), 'minstret':str(instructions), 'CPI':str(Decimal(cycles)/instructions),
            'window_ps':str(cycles*20000), 'power_corner':CORNER, 'method':'activity_exact_GLS_SAIF_OpenSTA_RCX',
            'internal_mW':str(total[0]*1000), 'switching_mW':str(total[1]*1000), 'dynamic_mW':str((total[0]+total[1])*1000),
            'leakage_mW':str(total[2]*1000), 'total_mW':str(total[3]*1000), 'EPI_pJ':str(total[3]*cycles*20000/instructions),
            'unknown_output_pins':str(report['origins'].get('unknown',{}).get('count',0)),
            'total_output_pins':str(report['total_output_pins']), 'unknown_percent':report['origins'].get('unknown',{}).get('percent','0')}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--design', choices=capture.DESIGNS, required=True)
    ap.add_argument('--capture-pass1', type=Path, required=True)
    ap.add_argument('--capture-pass2', type=Path, required=True)
    ap.add_argument('--sta-step', type=Path)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--min-windows-free-mib', type=int, default=6000)
    ap.add_argument('--min-wsl-free-mib', type=int, default=5000)
    ap.add_argument('--run', action='store_true')
    args = ap.parse_args()
    require(args.min_windows_free_mib >= 6000 and args.min_wsl_free_mib >= 5000, 'Memory guard must not be weakened')
    out = local(args.output)
    require(out.is_relative_to(ROOT/'results') and not out.exists(), 'Use a new output directory under results')
    cfg = capture.DESIGNS[args.design]
    step = local(args.sta_step or f'asic/{cfg["design"]}/runs/{cfg["tag"]}/{cfg["sta"]}')
    stage = read_sta_inputs(step)
    require(stage['netlist'] == str((ROOT/f'asic/{cfg["design"]}/runs/{cfg["tag"]}/{cfg["fill"]}/soc_asic_top.nl.v').relative_to(ROOT)), 'Layout differs from the capture runner chosen final layout')
    receipts = [local(args.capture_pass1), local(args.capture_pass2)]
    available = all(p.is_file() for p in receipts)
    paired = None
    if available:
        paired = pair.verify(*receipts)
        require(paired['design'] == args.design and paired['netlist_sha256'] == stage['netlist_sha256'], 'Capture pair differs from selected STA layout')
    if args.run:
        require(paired is not None, 'A completed verified full12 capture pair is required before --run')
        require(not stage['missing_external_inputs'], 'Missing frozen STA executable/library inputs')
    out.mkdir()
    abort = out/'abort_before_next_sta'
    receipt = {'status':'PREPARED_NOT_EXECUTED' if paired else 'PREPARED_WAITING_FOR_VERIFIED_PAIRED_CAPTURE',
               'created':pair.stamp(), 'design':args.design, 'capture_receipts':list(map(str, receipts)), 'capture_pair_available':paired is not None,
               'stage':stage, 'planned_independent_native_STA_executions':26, 'planned_activity_kernel_pairs':12, 'planned_vectorless_executions':2,
               'min_Windows_free_MiB':args.min_windows_free_mib, 'min_WSL_available_MiB':args.min_wsl_free_mib,
               'queue_abort':str(abort.relative_to(ROOT)), 'jobs':[], 'reports':{}, 'power_result':False,
               'PD_rerun':False, 'physical_board_status':'NOT_RUN', 'full_sequential_LEC_claim':False,
               'counter_origin':{'actual_GLS_outputs':['MCYCLE','LEDR self-check','HEX decode'],
                                 'EPI_MINSTRET':'paired current/reference RTL ASIC-view simulation; not directly emitted by GLS',
                                 'reference_validation':'all forty snapshot fields, invariants and independent equality'},
               'workload_scope':'twelve reduced-iteration firmware kernels; not the official nineteen-kernel Embench speed score',
               'SA2_layout_scope':'Old signed 11.56 mm2 only; replace with chosen T4 layout before final T3 if T4 changes layout' if args.design == 'SA2' else 'Locked DM layout r14F_A'}
    if paired:
        (out/'capture_pair_checked.json').write_text(json.dumps(paired,indent=2)+'\n',encoding='ascii')
        stage['inputs_sha256'][str(out/'capture_pair_checked.json')] = sha(out/'capture_pair_checked.json')
        for p in receipts:
            stage['inputs_sha256'][str(p)] = sha(p)
        for item in paired['captures']:
            folder = local(item['receipt']).parent
            for k in capture.KERNELS:
                p = folder/(k+'.pins.saif'); stage['inputs_sha256'][str(p)] = sha(p)
        stage['inputs_sha256'].update(paired['inputs_sha256'])
    schedules = []
    for pass_no in (1,2):
        pf = out/f'p{pass_no}'; pf.mkdir()
        for k in ('vectorless',)+capture.KERNELS:
            saif = receipts[pass_no-1].parent/(k+'.pins.saif') if k != 'vectorless' else None
            script = pf/(k+'.foreground.sh')
            script.write_text(queue_script(step, saif, abort, args.min_wsl_free_mib), encoding='ascii',newline='\n')
            stage['inputs_sha256'][str(script)] = sha(script)
            schedules.append({'pass':pass_no, 'kernel':k, 'saif_linux':linux(saif) if saif else None,
                              'command':['wsl.exe','-d','Ubuntu','-e','bash',linux(script)], 'log':str((pf/(k+'.power.rpt')).relative_to(ROOT))})
    receipt['planned_jobs'] = schedules
    dest = out/'receipt.json'
    def save():
        dest.write_text(json.dumps(receipt,indent=2)+'\n', encoding='ascii')
    def unchanged():
        for p,h in stage['inputs_sha256'].items():
            require(sha(local(p)) == h, 'Frozen power input changed: '+p)
    save()
    if not args.run:
        print(json.dumps({'status':receipt['status'], 'folder':str(out.relative_to(ROOT)), 'native_STA_executions':0, 'missing_STA_inputs':stage['missing_external_inputs']}))
        return 0
    try:
        receipt['status']='RUNNING_FRESH_PAIRED_ACTIVITY_POWER'; save()
        for job in schedules:
            require(not abort.exists(), 'Cooperative queue abort before next native tool')
            unchanged()
            memory = capture.free_windows_mib()
            require(memory >= args.min_windows_free_mib, f'WAITING_FOR_MEMORY: Windows free {memory} MiB; no next native tool started')
            log = local(job['log'])
            require(not log.exists(), 'Refuse stale native power report')
            record = dict(job, started=pair.stamp(), Windows_free_MiB=memory)
            receipt['jobs'].append(record); save()
            with log.open('xb') as f:
                process = subprocess.Popen(job['command'], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
                record['foreground_WSL_client_pid'] = process.pid; save()
                process.wait()
            record.update(completed=pair.stamp(), native_exit=process.returncode, log_sha256=sha(log)); save()
            unchanged()
            report = inspect_power(log, process.returncode, stage, job['saif_linux'])
            if job['kernel'] == 'vectorless':
                require(report['groups_W_and_percent'] == stage['flow_vectorless_groups'], 'Fresh vectorless STA does not reproduce final flow report')
            receipt['reports'].setdefault(str(job['pass']),{})[job['kernel']] = report; save()
            print(json.dumps({'STA_completed':job['kernel'],'pass':job['pass'],'native_exit':0}),flush=True)
        require(len(receipt['jobs']) == 26 and all(set(receipt['reports'][str(p)]) == {'vectorless'}|set(capture.KERNELS) for p in (1,2)), 'Incomplete independent STA matrix')
        for k in ('vectorless',)+capture.KERNELS:
            compare_power(receipt['reports']['1'][k],receipt['reports']['2'][k])
        rows = []
        for pass_no in (1,2):
            rr = [power_row(k,receipt['reports'][str(pass_no)][k],paired['comparisons'][k]) for k in capture.KERNELS]
            path = out/f'activity_power_p{pass_no}.csv'
            with path.open('x',encoding='ascii',newline='') as f:
                writer = csv.DictWriter(f,fieldnames=list(rr[0])); writer.writeheader(); writer.writerows(rr)
            rows.append(rr)
        require(rows[0] == rows[1], 'Independent power/counter/EPI rows differ')
        unchanged()
        receipt.update(status='VERIFIED_TWO_GLS_AND_TWO_STA_ACTIVITY_POWER_PASSES', completed=pair.stamp(), power_result=True,
                       artifacts_sha256={str(p.relative_to(ROOT)):sha(p) for p in out.rglob('*') if p.is_file() and p != dest})
        save()
    except BaseException as exc:
        receipt.update(status='STOPPED_REQUIRES_INSPECTION',error=str(exc)); save(); raise
    print(json.dumps({'status':receipt['status'],'kernels':12,'native_STA_executions':26,'corner':CORNER}))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
