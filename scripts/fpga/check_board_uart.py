"""Read-only check of one Hercules capture against paired board references.

No programming, CSV observation filling, measurement fabrication or RTL changes.
Full/routine workload identity comes from the SOF association, not BENCH alone.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output_files_board_matrix_6c4ccffd_seed2'
MAP = {
    'MCYCLE':'mcycle', 'MINSTRET':'minstret', 'CPI_NUM':'mcycle', 'CPI_DEN':'minstret',
    'I_ACCESS':'i_access', 'I_MAIN_HIT':'i_main', 'I_VICTIM_HIT':'i_victim', 'I_TRUE_MISS':'i_miss',
    'D_MAIN_HIT':'d_main', 'D_VICTIM_HIT':'d_victim', 'D_TRUE_MISS':'d_miss',
    'I_WAIT':'i_wait', 'D_WAIT':'d_wait', 'LOAD_USE':'load_use', 'CONTROL_REDIRECT':'control',
    'TRAP_REDIRECT':'trap', 'MMIO_WAIT':'mmio', 'PIPE_FILL_DRAIN':'fill_drain', 'OTHER':'other',
    'BRANCH':'branches', 'BRANCH_TAKEN':'taken', 'BRANCH_NOT_TAKEN':'not_taken',
    'PRED':'predictions', 'CORRECT':'correct', 'MISPRED':'mispredict',
    'AXI_READ':'axi_read', 'AXI_WRITE':'axi_write'
}

def rows(path):
    with path.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check(log, kernel, config):
    index = rows(OUT / 'INDEX.csv')
    selected = [r for r in index if (r['kernel'],r['config']) == (kernel,config)]
    if len(index) != 100 or len(selected) != 1:
        raise ValueError('Missing/ambiguous indexed case')
    row = selected[0]
    state = json.loads((OUT / 'BUILD_STATE.json').read_text())
    manifest = json.loads((ROOT / 'results/rtl_manifest.json').read_text())
    if state['state'] != 'READY_FOR_PHYSICAL_SESSION' or state['rtl_id'] != manifest['aggregate']:
        raise ValueError('Build not ready on current manifest')
    if row['fit_seed'] != '2' or row['rtl_aggregate'] != manifest['aggregate']:
        raise ValueError('Wrong seed/RTL')
    if sha(OUT / row['sof']) != row['sha256'] or sha(ROOT / row['fw']) != row['fw_sha256']:
        raise ValueError('SOF/firmware hash mismatch')
    references = []
    for n in (1,2):
        ref = rows(ROOT / f'results/board_reference_6c4ccffd_20261009_p{n}.csv')
        match = [r for r in ref if (r['kernel'],r['config']) == (kernel,config)]
        if len(match) != 1: raise ValueError('Missing paired simulation reference')
        references.append(match[0])
    if references[0] != references[1]: raise ValueError('Simulation references differ')
    ref = references[0]
    if any(int(row['expected_'+k]) != int(ref[k]) for k in ('mcycle','minstret')):
        raise ValueError('Index and reference counts differ')
    raw = log.read_bytes()
    text = raw.decode('utf-16') if raw[:2] in (b'\xff\xfe',b'\xfe\xff') else raw.decode('utf-8-sig')
    lines = [s.strip() for s in text.splitlines()]
    expected_bench = kernel.replace('upfull_', 'up_', 1)
    for key,value in {'BENCH':expected_bench,'CONFIG':'HOST_ASSOCIATED_SOF','RESULT':'PASS','CPI':'MCYCLE/MINSTRET'}.items():
        found = [s.split('=',1)[1] for s in lines if s.startswith(key+'=')]
        if found != [value]: raise ValueError(f'Missing, wrong or duplicated {key}')
    if lines.count('DONE') != 1: raise ValueError('Missing/duplicated DONE')
    observed = {}
    for key in (*MAP,'D_ACCESS','VERIFY_CODE'):
        found = [s for s in lines if s.startswith(key+'=')]
        if len(found) != 1 or not re.fullmatch(key+r'=0x[0-9a-fA-F]{8}',found[0]):
            raise ValueError(f'Missing, corrupt or duplicated {key}')
        observed[key] = int(found[0].split('=',1)[1],16)
        expected = int(ref[MAP[key]]) if key in MAP else int(ref['d_read'])+int(ref['d_write']) if key=='D_ACCESS' else None
        if expected is not None and observed[key] != expected: raise ValueError(f'{key} differs from paired RTL reference')
    return {'status':'VERIFIED_UART_SINGLE_CAPTURE_LED_PHOTO_PROGRAMMING_PAIR_NOT_CHECKED',
        'kernel':kernel,'config':config,'seed':2,'sof_sha256':row['sha256'],
        'uart_sha256':sha(log),'uart':str(log),'observed_hex':{k:f'{v:08X}' for k,v in observed.items()},
        'numeric_reference_checks':len(MAP)+1,'board_pair_complete':False}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--log',required=True,type=Path)
    ap.add_argument('--kernel',required=True)
    ap.add_argument('--config',required=True,choices=('DM','SA2','DM_VC4','DM_DSE'))
    args=ap.parse_args()
    print(json.dumps(check(args.log.resolve(),args.kernel,args.config),indent=2))

if __name__=='__main__': main()
