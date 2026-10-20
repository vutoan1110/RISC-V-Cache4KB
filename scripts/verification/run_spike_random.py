"""Compare two preserved independent RTL random runs with fresh Spike executions.

No RTL or old evidence is modified. The scope is the generated RV32I/Zmmul
core programs, not SoC MMIO, interrupts, caches or cycle equivalence.
"""
from __future__ import annotations
import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
SPIKE = ROOT/'results/spike_random_adapter_20261011/spike_reference'
SPIKE_LIBRARY = Path(r'\\wsl.localhost\Ubuntu\home\toanl\tools\spike\lib\libriscv.so')
SOFTFLOAT_LIBRARY = Path(r'\\wsl.localhost\Ubuntu\home\toanl\tools\spike\lib\libsoftfloat.so')
COMMIT = re.compile(r'core\s+\d+:\s+\d+\s+0x([\da-f]+)\s+\(0x([\da-f]+)\)(.*)', re.I)
RD = re.compile(r'\bx\s*(\d+)\s+0x([\da-f]+)', re.I)
MEM = re.compile(r'\bmem\s+0x([\da-f]+)\s+0x([\da-f]+)', re.I)
HALT = 0x6f

def require(value, reason):
    if not value:
        raise RuntimeError(reason)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def stamp():
    return datetime.now(timezone.utc).isoformat()

def rtl_rows(path):
    with path.open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    require(rows and set(rows[0]) == {'order','pc','instr','rd','we','rd_data','mem_we','mem_addr','mem_wdata','mem_wstrb'}, 'Bad RTL trace schema')
    result = []
    for i, row in enumerate(rows):
        require(int(row['order']) == i, 'Noncontiguous RTL retirement order')
        we, store = int(row['we']), int(row['mem_we'])
        require(we in (0,1) and store in (0,1), 'Invalid RTL enable')
        mask = int(row['mem_wstrb'],16) if store else 0
        byte_mask = sum(255 << (8*b) for b in range(4) if mask >> b & 1)
        result.append([int(row['pc'],16), int(row['instr'],16), we,
                       int(row['rd']) if we else 0, int(row['rd_data'],16) if we else 0,
                       store, int(row['mem_addr'],16) if store else 0,
                       int(row['mem_wdata'],16) & byte_mask if store else 0, mask])
    return result

def spike_rows(path, words):
    result, halted = [], False
    for line in path.read_text().splitlines():
        require(not re.search(r'exception|trap_|illegal instruction',line,re.I), 'Spike trap/error')
        match = COMMIT.fullmatch(line.strip())
        if not match:
            continue
        pc, insn = int(match[1],16) & 0xffffffff, int(match[2],16)
        if halted:
            require(pc == 640 and insn == HALT, 'Unexpected execution after HALT')
            continue
        require(pc % 4 == 0 and 0 <= pc <= 640 and words[pc//4] == insn, 'Spike PC/instruction differs from loaded program')
        if insn == HALT:
            require(pc == 640 and result, 'Early HALT')
            halted = True
            continue
        tail = match[3]
        rd, mem = RD.search(tail), MEM.search(tail)
        we = int(rd is not None and int(rd[1]) != 0)
        store = int(insn & 127 == 0x23)
        addr, data, mask = 0, 0, 0
        if store:
            require(mem is not None, 'Spike store record lacks address/data')
            width = {0:1,1:2,2:4}.get(insn >> 12 & 7)
            require(width is not None, 'Unsupported store width')
            addr = int(mem[1],16) & 0xffffffff
            require(0x400 <= addr and addr+width <= 0x500 and addr % width == 0, 'Data address outside frozen DUT profile')
            mask = ((1 << width)-1) << (addr & 3)
            data = (int(mem[2],16) & ((1 << (width*8))-1)) << (8*(addr & 3))
        result.append([pc,insn,we,int(rd[1]) if we else 0,int(rd[2],16)&0xffffffff if we else 0,store,addr,data,mask])
    require(halted and result[0][0] == 0, 'Incomplete Spike program')
    return result

def compare(a,b):
    require(len(a) == len(b), f'Retirement length differs: {len(a)} vs{len(b)}')
    for i,(x,y) in enumerate(zip(a,b)):
        require(x == y, f'Architectural mismatch retirement{i}: RTL{x} Spike{y}')

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--run',action='store_true')
    args = ap.parse_args()
    out = (ROOT/args.output).resolve()
    require(out.is_relative_to(ROOT/'results') and not out.exists(), 'Use a fresh result folder')
    prior = ROOT/'results/random_diff_checked_20261009/verification.json'
    old = json.loads(prior.read_text())
    require(old['status'] == 'VERIFIED' and old['paired_rows'] == 50 and len(old['passes']) == 2, 'Missing paired RTL evidence')
    manifest = json.loads((ROOT/'results/rtl_manifest.json').read_text())
    hashes = {str(ROOT/p):h for p,h in manifest['files'].items()}
    hashes.update({str(ROOT/p):h for p,h in old['source_sha256'].items()})
    adapter_source = ROOT/'verification/diff/spike_random_reference.cc'
    for p in (prior,Path(__file__),SPIKE,SPIKE_LIBRARY,SOFTFLOAT_LIBRARY,adapter_source):
        hashes[str(p)] = sha(p)
    require(all(sha(p)==h for p,h in hashes.items()), 'Frozen input changed')
    out.mkdir()
    receipt = {'status':'PREPARED_NOT_EXECUTED','created':stamp(),'scope':'RV32I/Zmmul generated core subset, BPoff and BPon; no SoC MMIO/interrupt/cache/timing claim',
               'RTL_runs':'Two preserved independently executed current-RTL runs; fresh Spike process per seed/pass',
               'Spike_ISA':'RV32I_Zmmul; installed Spike1.1.1-dev library, direct processor_t adapter without boot ROM or debug device',
               'initialization':'PC0, all32GPR zero, data0x400..0x7ff zero, original code0..0x283; same frozen DUT initialization, no relocation',
               'compared_fields':['PC','instruction','GPR write enable/register/data','store enable/address/enabled bytes/strobes'],
               'ignored_fields':'GPR index/data when write disabled; memory fields when not a store; disabled store data lanes',
               'inputs_sha256':hashes,'passes':[],'native_commands':[]}
    def save():
        (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    save()
    if not args.run:
        print(receipt['status']); return
    try:
        receipt['status']='RUNNING_FRESH_SPIKE_COMPARISON';save()
        normalized = []
        for pass_info in old['passes']:
            number = pass_info['pass']; folder = out/f'p{number}';folder.mkdir()
            raw = ROOT/pass_info['raw_directory']; cases = []
            for case in pass_info['cases']:
                seed = case['seed']; proofpath = ROOT/case['receipt']
                require(sha(proofpath)==case['sha256'],'RTL case receipt changed')
                proof = json.loads(proofpath.read_text())
                hexpath = raw/f'rand_{seed}.hex'
                words = [int(x,16) for x in hexpath.read_text().split()]
                require(sha(hexpath)==proof['firmware_sha256'],'Program changed')
                require(len(words)==161 and words[-1]==HALT,'Unexpected generated program')
                target = folder/f'seed{seed}.hex';target.write_bytes(hexpath.read_bytes())
                log = folder/f'seed{seed}.spike.log'
                stderr = folder/f'seed{seed}.stderr.log'
                linux = '/mnt/e/Projects/RISCV-research/'+target.relative_to(ROOT).as_posix()
                adapter_linux = '/mnt/e/Projects/RISCV-research/'+SPIKE.relative_to(ROOT).as_posix()
                command = ['wsl.exe','-d','Ubuntu','-e',adapter_linux,linux]
                record = {'pass':number,'seed':seed,'command':command,'started':stamp()};receipt['native_commands'].append(record);save()
                require(all(sha(p)==h for p,h in hashes.items()), 'Frozen input changed before Spike')
                with log.open('xb') as stream, stderr.open('xb') as errors:
                    process = subprocess.run(command,stdout=stream,stderr=errors,cwd=ROOT,timeout=30)
                record.update(native_exit=process.returncode,completed=stamp(),log_sha256=sha(log),stderr_sha256=sha(stderr));save()
                require(process.returncode==0,'Spike native failure')
                require(stderr.read_text().strip()=='[PASS] Spike generated program reached HALT','Spike completion/error status differs')
                reference = spike_rows(log,words)
                for mode in ('off','on'):
                    trace = raw/f'trace_{seed}_{mode}.txt'
                    require(sha(trace)==case[f'{mode}_sha256'],'RTL raw trace changed')
                    compare(rtl_rows(trace),reference)
                controls = []
                for field in (0,1,4):
                    wrong = copy.deepcopy(reference)
                    index = next(i for i,r in enumerate(wrong) if field != 4 or r[2])
                    wrong[index][field] ^= 1
                    try: compare(reference,wrong)
                    except RuntimeError: controls.append(field)
                require(controls == [0,1,4],'Comparator failed wrong-PC/instruction/register controls')
                norm = folder/f'seed{seed}.normalized.json';norm.write_text(json.dumps(reference)+'\n')
                cases.append({'seed':seed,'retirements':len(reference),'normalized_sha256':sha(norm),'firmware_sha256':sha(target),'raw_spike_log_sha256':sha(log),'controls_detected':controls})
            require(len(cases)==50,'Incomplete pass')
            receipt['passes'].append({'pass':number,'cases':cases}); normalized.append(cases);save()
        require(normalized[0]==normalized[1],'Independent Spike executions differ')
        require(all(sha(p)==h for p,h in hashes.items()),'Frozen inputs changed after execution')
        receipt.update(status='VERIFIED_TWO_SPIKE_PASSES_MATCH_PAIRED_RTL',paired_seeds=50,native_Spike_executions=100,
                       paired_RTL_traces=200,completed=stamp())
        save();print(json.dumps({k:receipt[k] for k in ('status','paired_seeds','native_Spike_executions','paired_RTL_traces')}))
    except Exception as exc:
        receipt.update(status='STOPPED_REQUIRES_INSPECTION',error=str(exc));save();raise

if __name__ == '__main__':
    main()
