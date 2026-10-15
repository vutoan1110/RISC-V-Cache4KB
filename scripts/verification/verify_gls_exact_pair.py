#!/usr/bin/env python3
"""Re-read two complete independent exact-window GLS captures, without editing them.

SAIF comparison streams the complete ordered S-expression. Whitespace is
irrelevant and the one top-level DATE may differ; every other field, hierarchy,
signal name and activity value must agree. Reordered otherwise equal entries
are conservatively rejected. Duplicate members and malformed files fail.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path
import re
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/verification'))
sys.path.insert(0, str(ROOT / 'scripts'))
import run_gls_exact_window as capture
from snapshot_fields import FIELDS, invariants

MAX_SAIF_BYTES = 64 * 1024 * 1024
TOKEN = re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+')
ENTRY = re.compile(r'^\(([^\s()]+) \(T0 (\d+)\) \(T1 (\d+)\) \(TX (\d+)\) \(TC (\d+)\) \(IG (\d+)\)\)$')

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(65536), b''):
            h.update(block)
    return h.hexdigest()

def local(path):
    return (ROOT / path).resolve()

def stamp():
    return datetime.now(timezone.utc).isoformat()

def saif_tokens(path, duration):
    """Validate the known Questa/converter line format while streaming tokens.

    Memory is bounded by one line and a set of names in the current NET block;
    no raw SAIF or gate netlist is read into a single string.
    """
    path = Path(path)
    require(path.is_file() and 0 < path.stat().st_size <= MAX_SAIF_BYTES, f'Missing/oversized SAIF: {path}')
    stack = []
    members = set()
    entries = 0
    headers = {}
    instances = []
    seen_instances = set()
    seen_nets = set()
    finished = False
    with path.open(encoding='ascii', errors='strict') as f:
        for number, line in enumerate(f, 1):
            require(len(line) < 65536, f'Oversized SAIF line: {path}:{number}')
            text = line.strip()
            if not text:
                continue
            require(not finished, f'Trailing SAIF data: {path}:{number}')
            if text == ')':
                require(stack, f'Unbalanced SAIF close: {path}:{number}')
                kind, _ = stack.pop()
                if kind == 'NET':
                    members.clear()
                elif kind == 'INSTANCE':
                    instances.pop()
                if not stack:
                    finished = True
            elif text == '(SAIFILE':
                require(not stack and not headers, f'Repeated SAIFILE: {path}')
                stack.append(('SAIFILE', None))
            elif text.startswith('(INSTANCE ') and not text.endswith(')'):
                name = text[len('(INSTANCE '):]
                require(stack and stack[-1][0] in ('SAIFILE', 'INSTANCE') and name and not re.search(r'\s|[()]', name), f'Unsupported INSTANCE: {path}:{number}')
                require(name not in {n for k, n in stack if k == 'INSTANCE'}, f'Repeated instance in hierarchy: {path}:{number}')
                # Both raw nets and converted driver pins are scoped below this pair.
                if len(instances) < 2:
                    require(name == ('tb_gls_soc', 'dut')[len(instances)], f'Wrong SAIF hierarchy: {path}:{number}')
                identity = tuple(instances + [name])
                require(identity not in seen_instances, f'Duplicate SAIF instance: {path}:{number}')
                seen_instances.add(identity)
                stack.append(('INSTANCE', name)); instances.append(name)
            elif text == '(NET':
                require(stack and stack[-1][0] == 'INSTANCE' and len(instances) >= 2, f'NET outside DUT: {path}:{number}')
                require(tuple(instances) not in seen_nets, f'Repeated NET block: {path}:{number}')
                seen_nets.add(tuple(instances))
                stack.append(('NET', None)); members.clear()
            elif stack and stack[-1][0] == 'NET':
                m = ENTRY.fullmatch(text)
                require(m is not None, f'Unsupported/malformed activity entry: {path}:{number}')
                name = m[1]
                require(name not in members, f'Duplicate SAIF member: {path}:{number}')
                members.add(name)
                values = tuple(map(int, m.groups()[1:]))
                require(sum(values[:3]) == duration, f'Wrong entry duration: {path}:{number}')
                entries += 1
                require(entries <= 300000, f'SAIF member bound exceeded: {path}')
            elif stack == [('SAIFILE', None)]:
                tokens = TOKEN.findall(text)
                require(len(tokens) >= 3 and tokens[0] == '(' and tokens[-1] == ')' and text.count('(') == text.count(')') == 1, f'Malformed SAIF header: {path}:{number}')
                key = tokens[1]
                require(key not in headers, f'Duplicate SAIF header: {path}:{number}')
                headers[key] = tokens[2:-1]
                if key == 'DATE':
                    require(len(tokens) == 4 and tokens[2].startswith('"') and tokens[2].endswith('"'), f'Malformed DATE: {path}')
                    continue
            else:
                raise RuntimeError(f'Unsupported SAIF structure: {path}:{number}')
            tokens = TOKEN.findall(text)
            require(''.join(tokens) == re.sub(r'\s+', '', text) or any(t.startswith('"') for t in tokens), f'Unparsed SAIF token: {path}:{number}')
            yield from tokens
    require(finished and not stack and entries > 0, f'Truncated/empty SAIF: {path}')
    require(headers.get('TIMESCALE') == ['1', 'ps'] and headers.get('DURATION') == [str(duration)], f'SAIF header span/unit mismatch: {path}')
    require(headers.get('SAIFVERSION') == ['"2.0"'] and headers.get('DIRECTION') == ['"backward"'] and headers.get('DIVIDER') == ['/'], f'Unsupported SAIF ABI: {path}')

def compare_saif(first, second, duration):
    missing = object()
    count = 0
    for count, (a, b) in enumerate(itertools.zip_longest(saif_tokens(first, duration), saif_tokens(second, duration), fillvalue=missing), 1):
        require(a == b, f'SAIF functional token mismatch at {count}: {first} vs {second}')
    return {'functional_tokens': count, 'ignored_header': 'DATE only', 'ordered_entries_required': True,
            'pass1_sha256': sha(first), 'pass2_sha256': sha(second)}

def read_reference(path, design):
    with Path(path).open(newline='') as f:
        reader = csv.DictReader(f)
        require(len(reader.fieldnames or []) == 43 and set(reader.fieldnames or []) == {'kernel', 'config', 'config_id'} | set(FIELDS), f'Incomplete reference schema: {path}')
        rows = [r for r in reader if r['config'] == design]
    require(len(rows) == 12 and {r['kernel'] for r in rows} == set(capture.KERNELS), f'Incomplete/duplicated reference matrix: {path}')
    for r in rows:
        require(all(r.get(k) is not None and str(r[k]).strip() for k in FIELDS), f'Missing reference field: {path}')
        nums = {k: int(r[k]) for k in FIELDS}
        require(not invariants(nums) and nums['result_pass'] == nums['invariant_pass'] == 1, f'Bad reference snapshot: {path}')
    return {r['kernel']: r for r in rows}

def check_capture(receipt_path, pass_no):
    receipt_path = local(receipt_path)
    folder = receipt_path.parent
    r = json.loads(receipt_path.read_text())
    require(r.get('status') == 'VERIFIED_EXACT_CAPTURE_SINGLE_PASS' and r.get('pass') == pass_no, 'Capture is not a completed full independent pass')
    require(r.get('design') in capture.DESIGNS, 'Unknown capture design')
    cfg = capture.DESIGNS[r['design']]
    require(r.get('PD_tag') == cfg['tag'] and r.get('freeze_expression') == cfg['freeze_expression'] and r.get('mapping_prerequisite') == 'VERIFIED_BOUND_TO_NETLIST', 'Unverified mapped profile')
    require(r.get('full_twelve_kernel_matrix') is True and r.get('kernels') == list(capture.KERNELS) and set(r.get('cases', {})) == set(capture.KERNELS), 'Incomplete or reordered twelve-kernel capture')
    require(r.get('timing_period_ps') == 20000 and r.get('independent_interval_counter') is True and r.get('power_or_full_LEC_claim') is False, 'Unverified timing/method scope')
    profile = {'cache_KiB':4, 'RAM_KiB':16, 'current_reference_FAST_HIT':0, 'frozen_snapshot_FAST_HIT_switch_absent':True,
               'BRANCH_PREDICT_ENABLE':1, 'L0_ENTRIES':8, 'CACHE_LINE_WORDS':4, 'VICTIM_ENTRIES':4, 'reference_counter_fields':40, 'PD_RTL_sources':42}
    require(r.get('profile') == profile, 'Capture architecture profile mismatch')
    library = f'work_gls_exact_{r["design"].lower()}_{folder.name}_p{pass_no}'
    require(r.get('library') == library and re.fullmatch(r'[a-zA-Z0-9_]+', library), 'Wrong/private library identity')
    net = local(r['netlist'])
    expected = ROOT / f'asic/{cfg["design"]}/runs/{cfg["tag"]}/{cfg["fill"]}/soc_asic_top.nl.v'
    require(net == expected.resolve(), 'Wrong final netlist')
    inputs = r.get('inputs_sha256', {})
    require(inputs, 'No frozen capture inputs')
    for p, h in inputs.items():
        require(re.fullmatch('[0-9a-f]{64}', h) and sha(local(p)) == h, f'Changed capture input: {p}')
    manifest = json.loads((ROOT / 'results/rtl_manifest.json').read_text())
    require(manifest.get('count') == 227 and len(manifest['files']) == 227, 'RTL manifest membership changed')
    require(all(inputs.get(p) == h and sha(ROOT / p) == h for p, h in manifest['files'].items()), 'Capture lacks current frozen RTL manifest')
    resolved = net.parent.parent/'resolved.json'
    recipe = json.loads(resolved.read_text())
    prefix = '/mnt/e/Projects/RISCV-research/'
    require(recipe.get('CLOCK_PERIOD') == 20 and len(recipe.get('VERILOG_FILES',[])) == 42 and all(p.startswith(prefix) for p in recipe['VERILOG_FILES']), 'Wrong frozen PD recipe/source membership')
    frozen_rtl = [ROOT/p.removeprefix(prefix) for p in recipe['VERILOG_FILES']]
    for p in [net, resolved, ROOT / 'scripts/verification/run_gls_exact_window.py', ROOT / 'asic/gls/tb_gls_soc.sv', ROOT / 'asic/gls/saif_to_pins.py'] + frozen_rtl + [ROOT / p for p in capture.MODELS] + [ROOT / 'fw' / (k + '.hex') for k in capture.KERNELS] + [ROOT / 'results' / n for n in cfg['refs']]:
        require(inputs.get(str(p.resolve())) == sha(p), f'Unpinned essential capture input: {p}')
    proofs = []
    shared = {}
    for p, h in inputs.items():
        pp = local(p)
        if pp.is_relative_to(folder):
            continue
        if pp.suffix == '.json' and pp.name != 'rtl_manifest.json':
            try:
                proof = json.loads(pp.read_text())
            except (ValueError, OSError):
                proof = {}
            if proof.get('status') == 'VERIFIED_COUNTER_FREEZE_ALIAS':
                require(proof.get('design') == r['design'] and proof.get('netlist_sha256') == sha(net) and proof.get('expression') == r['freeze_expression'] and proof.get('counter_hold_increment_bridge_verified') is True, 'Mapped alias proof mismatch')
                proofs.append(h); continue
        shared[p] = h
    require(len(proofs) == 1, 'Missing/ambiguous actual mapped observer proof')
    refs = [read_reference(ROOT / 'results' / n, r['design']) for n in cfg['refs']]
    require(refs[0] == refs[1], 'Paired reference snapshots differ')
    tb = folder / 'tb_gls_soc_exact_window.sv'
    require(tb.read_text() == capture.generated_tb((ROOT / 'asic/gls/tb_gls_soc.sv').read_text(), r['freeze_expression']), 'Changed generated observer')
    require((folder / 'power_capture_exact.do').read_text() == capture.capture_do(), 'Changed generated capture Tcl')
    compile_text = (folder / 'compile.do').read_text()
    expected_compile = ('onerror {quit -code 1 -f}\nvlib '+library+'\n'+
        'vlog -work '+library+' -timescale 1ns/1ps +define+FUNCTIONAL +define+UNIT_DELAY=#0 -suppress 2892,2902 '+ ' '.join(capture.tcl_path(ROOT/p) for p in capture.MODELS[:2])+'\n'+
        'vlog -work '+library+' -timescale 1ns/1ps '+' '.join(capture.tcl_path(ROOT/p) for p in capture.MODELS[2:])+'\n'+
        'vlog -work '+library+' -timescale 1ns/1ps -suppress 2892 '+capture.tcl_path(net)+'\n'+
        'vlog -work '+library+' -sv +define+GLS_RAM16K '+capture.tcl_path(tb)+'\necho {[PASS] EXACT_WINDOW_PRIVATE_LIBRARY_COMPILED}\nquit -code 0 -f\n')
    require(compile_text == expected_compile, 'Wrong private compilation source/profile/recipe')
    require(inputs.get(str(tb)) == sha(tb) and inputs.get(str(folder / 'compile.do')) == sha(folder / 'compile.do') and inputs.get(str(folder / 'power_capture_exact.do')) == sha(folder / 'power_capture_exact.do'), 'Unpinned generated compilation/capture inputs')
    jobs = r.get('native_commands', [])
    require(len(jobs) == 25, 'Expected one private compile and twelve native simulations/conversions')
    for job in jobs:
        log = local(job['log'])
        require(log.is_relative_to(folder) and job.get('native_exit') == 0 and job.get('started') and job.get('completed') and sha(log) == job.get('log_sha256'), 'Native command incomplete/changed/failed')
    vsim = jobs[0]['command'][0]
    simulator = Path(vsim).resolve()
    require(simulator.name.lower() == 'vsim.exe' and simulator.is_file() and inputs.get(str(simulator)) == sha(simulator), 'Native Questa executable is not pinned')
    def simulation_command(stem, do):
        return [vsim, '-c', '-l', str(folder / (stem+'.transcript')), '-wlf', str(folder / (stem+'.wlf')), '-do', 'do '+capture.tcl_path(do)]
    require(jobs[0]['command'] == simulation_command('compile', folder/'compile.do') and local(jobs[0]['log']) == folder/'compile.log', 'Wrong native compilation command')
    compile_log = (folder / 'compile.log').read_text(errors='strict')
    require(len(re.findall(r'^\s*(?:#\s*)?\[PASS\] EXACT_WINDOW_PRIVATE_LIBRARY_COMPILED\s*$', compile_log, re.M)) == 1 and not re.search(r'\*\*\s+(?:Error|Fatal)|\[FAIL\]', compile_log) and re.search(r'Errors:\s*0,', compile_log), 'Private compile did not complete cleanly')
    cases = {}
    for index, k in enumerate(capture.KERNELS):
        sim, conv = jobs[1+index*2:3+index*2]
        expected_do = 'onerror {quit -code 1 -f}\nvsim -onfinish stop -voptargs={+acc=rn+tb_gls_soc +acc=n+soc_asic_top} -gMEMFILE=fw/'+k+'.hex -gMAX_CYCLES=8000000 '+library+'.tb_gls_soc\nset SAIF '+capture.tcl_path(folder/(k+'.raw.saif'))+'\ndo '+capture.tcl_path(folder/'power_capture_exact.do')+'\nquit -code 0 -f\n'
        do = folder/(k+'.do')
        require(do.read_text() == expected_do and inputs.get(str(do)) == sha(do), f'Changed firmware/elaboration recipe: {k}')
        require(sim['command'] == simulation_command(k, do) and local(sim['log']) == folder/(k+'.log'), f'Wrong native simulation command: {k}')
        cc = conv['command']
        require(len(cc) == 9 and cc[1:3] == ['-B','asic/gls/saif_to_pins.py'] and local(cc[3]) == folder/(k+'.raw.saif') and local(cc[4]) == net and local(cc[5]) == folder/(k+'.pins.saif') and local(conv['log']) == folder/(k+'.pins.log'), f'Wrong native conversion command: {k}')
        require(Path(cc[0]).name.lower() in ('python.exe','python3.exe','python') and Path(cc[0]).resolve() == Path(sys.executable).resolve() and {Path(p).name for p in cc[6:]} == {'sky130_fd_sc_hd__tt_025C_1v80.lib','sky130_sram_1kbyte_1rw1r_32x256_8_TT_1p8V_25C.lib','sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib'} and all(inputs.get(str(local(p))) == sha(local(p)) for p in cc[6:]), 'Conversion must use this Windows Python and pinned TT libraries')
        conversion_log = local(conv['log']).read_text(errors='strict')
        require('PW_SAIF window ' in conversion_log and not re.search(r'\[FAIL\]|Traceback|\*\*\s+(?:Error|Fatal)', conversion_log), 'Failed/incomplete pin conversion')
        case = r['cases'][k]
        window = capture.inspect_log(folder/(k+'.log'), int(refs[0][k]['mcycle']), sim['native_exit'], k)
        require(case.get('window') == window and case.get('raw_log_sha256') == sha(folder/(k+'.log')) and case.get('reference_minstret') == int(refs[0][k]['minstret']), f'Stored result differs from raw/reference: {k}')
        for kind, suffix in [('raw_saif','.raw.saif'), ('pin_saif','.pins.saif')]:
            path = folder/(k+suffix)
            stats = capture.inspect_saif(path, window['duration_ps'])
            require(case.get(kind) == stats, f'Stored SAIF stats differ from raw: {k}/{kind}')
        cases[k] = {'window': window, 'reference_minstret': int(refs[0][k]['minstret'])}
    return r, folder, shared, proofs[0], cases

def verify(first, second):
    a, fa, ia, pa, ca = check_capture(first, 1)
    b, fb, ib, pb, cb = check_capture(second, 2)
    require(fa != fb and a['library'] != b['library'], 'Passes reused a capture folder/private compilation')
    require(a['design'] == b['design'] and a['PD_tag'] == b['PD_tag'] and a['netlist'] == b['netlist'] and ia == ib and pa == pb and ca == cb, 'Capture inputs/profile/reference/window differ between independent passes')
    comparisons = {}
    for k in capture.KERNELS:
        duration = ca[k]['window']['duration_ps']
        comparisons[k] = {'raw': compare_saif(fa/(k+'.raw.saif'), fb/(k+'.raw.saif'), duration),
                          'pins': compare_saif(fa/(k+'.pins.saif'), fb/(k+'.pins.saif'), duration), **ca[k]}
    return {'status':'VERIFIED_TWO_INDEPENDENT_EXACT_GLS_CAPTURES', 'checked_at':stamp(), 'design':a['design'],
            'PD_tag':a['PD_tag'], 'netlist':a['netlist'], 'netlist_sha256':sha(local(a['netlist'])),
            'captures':[{'receipt':str(local(p).relative_to(ROOT)), 'sha256':sha(local(p)), 'library':r['library']} for p,r in [(first,a),(second,b)]],
            'inputs_sha256':ia, 'mapping_proof_sha256':pa, 'profile':a['profile'], 'timing_period_ps':20000,
            'kernels':list(capture.KERNELS), 'comparisons':comparisons, 'native_compilations':2, 'native_simulations':24,
            'native_Windows_SAIF_conversions':24, 'power_or_full_LEC_claim':False,
            'verifier_sha256':sha(Path(__file__)), 'capture_helper_sha256':sha(Path(capture.__file__))}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pass1', type=Path, required=True)
    ap.add_argument('--pass2', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    out = local(args.output)
    require(out.is_relative_to(ROOT/'results') and not out.exists(), 'Output must be a new receipt under results')
    result = verify(args.pass1, args.pass2)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('x', encoding='ascii') as f:
        f.write(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'status':result['status'], 'kernels':12, 'receipt':str(out.relative_to(ROOT))}))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
