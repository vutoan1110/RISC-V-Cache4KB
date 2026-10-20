#!/usr/bin/env python3
"""Prepare an isolated second execution of the legacy SA2 mapped NegB control.

No RTL/PD/source inputs are edited. --prepare writes a frozen plan only; --run
requires its SHA256 and starts native tools only after explicit coordination.
The expected result is detected SAT counterexamples, not equivalence PASS.
"""
import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
LEC = ROOT/'asic/equiv/lec'
OLD = ROOT/'results/lec_sa2_20261013'
P1, P2 = OLD/'p1', OLD/'p2b'
FINAL = ROOT/'asic/soc_sa2_4kb/runs/sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1/56-openroad-fillinsertion/soc_asic_top.nl.v'
Y = '/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys'
ABC = '/nix/store/9r0bh7sp051dpm8km8bqlb028anpd3v3-yosys/bin/yosys-abc'
ABC_TARGET = '/nix/store/6l3aj1gi4lja8z5s4lan2k2cfz9mqkrz-yosys-abc/bin/abc'
HELPERS = ['evert.py','free_spec.py','spec_manual.py','mk_onehot_spec.py','aig_syms.py','aigsim.py','open_outputs.py','gold_god_aig.ys']
EXPECTED = ['pairs_bN.json','BN_spec.json','BN_gold.aig','BN_gate.aig']


def require(ok, message):
    if not ok:
        raise ValueError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    Path(path).write_text(json.dumps(value,indent=2)+'\n',encoding='ascii')


def linux(path):
    p = Path(path).resolve()
    return '/mnt/'+p.drive[0].lower()+p.as_posix()[2:]


def unc(path):
    return Path('\\\\wsl.localhost\\Ubuntu'+path.replace('/','\\'))


def stats(path):
    text = Path(path).read_text(encoding='utf-8-sig',errors='strict')
    result = {}
    for label in ['Unsat calls','Sat   calls','Undef calls']:
        matches = re.findall(re.escape(label)+r'\s+(\d+)\b',text)
        require(len(matches)==1,'Missing/duplicate SAT statistics: '+str(path))
        result[label]=int(matches[0])
    return result


def unchanged(plan):
    for path, expected in plan['inputs_sha256'].items():
        require(sha(path)==expected,'Pinned input changed: '+path)


def prepare(out):
    require(not out.exists(),'Preparation output already exists')
    comparison=load(OLD/'pass_comparison.json')
    require(comparison['status']=='PASS1_EQUALS_PASS2' and comparison['differences']==0,'Positive frontend pair is not verified')
    require(Path(comparison['pass2']).resolve()==P2.resolve(),'Wrong independent second frontend')
    for name in ['n1_flat.il','gate1_frontend.ys','gate1_pre.ys','gate1_flat.ys']:
        require(sha(P1/name)==sha(P2/name),'Independent frontend input differs: '+name)
    paths=[Path(__file__),LEC/'run_lec_sa2.ps1',OLD/'pass_comparison.json',FINAL,ROOT/'asic/equiv/sec/sram_cut.py']
    paths += [P2/name for name in ['n1_flat.il','gate1_frontend.ys','gate1_pre.ys','gate1_flat.ys','run_frontends.out','stepB.out']]
    paths += [P1/name for name in ['stepNegB.out','msatBN_a.log','msatBN_b.log','BN_open.txt','neg/soc_asic_top_mut.nl.v',*EXPECTED]]
    paths += [LEC/name for name in HELPERS]
    frontend=(P2/'gate1_frontend.ys').read_text(encoding='ascii')
    for path in re.findall(r'(/[^\s]+\.(?:v|lib))\b',frontend):
        paths.append(ROOT/path[len('/mnt/e/Projects/RISCV-research/'):] if path.startswith('/mnt/e/Projects/RISCV-research/') else unc(path))
    paths += [unc(Y),unc(ABC_TARGET)]
    inputs={str(p.resolve()):sha(p) for p in dict.fromkeys(paths)}
    a,b=stats(P1/'msatBN_a.log'),stats(P1/'msatBN_b.log')
    require(a['Sat   calls']==28 and b['Sat   calls']==32,'Legacy negative-control counterexamples differ')
    out.mkdir(parents=True)
    work=out/'independent_second_control'
    plan={'status':'PREPARED_NOT_EXECUTED','created':now(),'scope':'legacy rtl_r14 signed SA2 layout; mapped negative control only, not current-layout LEC',
          'positive_second_frontend':str(P2),'output':str(out),'work':str(work),
          'ABC_argv':ABC,'ABC_symlink_target':ABC_TARGET,
          'minimum_Windows_free_MiB':12000,'minimum_WSL_available_MiB':10000,'concurrency':'SoC formal alone; wait for root GO after RF/BHT',
          'inputs_sha256':inputs,'expected_stats':[a,b],'expected_SAT_counterexamples':60,
          'expected_objects_sha256':{n:sha(P1/n) for n in EXPECTED},
          'expected_mutated_netlist_sha256':sha(P1/'neg/soc_asic_top_mut.nl.v'),
          'expected_open_outputs':64,'prior_control_log':str(P1/'stepNegB.out'),
          'native_exit_semantics':'Every native tool must exit0; ABC returns0 after finding SAT. SAT statistics, matching networks and detected mutation establish control success.',
          'PD_jobs_started':False,'RTL_modified':False}
    write(out/'plan.json',plan)
    return {'status':plan['status'],'plan':str(out/'plan.json'),'plan_sha256':sha(out/'plan.json'),'inputs':len(inputs),'native_tools_started':False}


def resources(plan):
    result=subprocess.run(['powershell.exe','-NoProfile','-Command','[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1024)'],capture_output=True,text=True,timeout=30,check=True)
    free=int(result.stdout.strip())
    require(free>=plan['minimum_Windows_free_MiB'],'Insufficient Windows free memory: '+str(free))
    result=subprocess.run(['wsl.exe','-d','Ubuntu','-e','bash','-c',"awk '/MemAvailable:/ {print int($2/1024)}' /proc/meminfo"],capture_output=True,text=True,timeout=30,check=True)
    available=int(result.stdout.strip())
    require(available>=plan['minimum_WSL_available_MiB'],'Insufficient WSL available memory: '+str(available))
    result=subprocess.run(['wsl.exe','-d','Ubuntu','-e','readlink','-f',ABC],capture_output=True,text=True,timeout=30,check=True)
    require(result.stdout.strip()==plan['ABC_symlink_target'],'ABC symlink target changed')
    result=subprocess.run(['wsl.exe','-d','Ubuntu','-e','bash','-c','ps -eo pid,args'],capture_output=True,text=True,timeout=30,check=True)
    require(not any(re.search(r'(?:^|/)(?:yosys|yosys-abc|abc|openroad)(?:\s|$)',line) for line in result.stdout.splitlines()),'Another formal/PD native worker is active')
    return {'Windows_free_MiB':free,'WSL_available_MiB':available}


def run(plan_path, expected_sha):
    require(sha(plan_path)==expected_sha,'Plan SHA256 does not match explicit launch binding')
    plan=load(plan_path);require(plan['status']=='PREPARED_NOT_EXECUTED','Not a prepared plan')
    k=ctypes.windll.kernel32;k.GetCurrentProcess.restype=ctypes.c_void_p
    k.GetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_size_t),ctypes.POINTER(ctypes.c_size_t)]
    process,system=ctypes.c_size_t(),ctypes.c_size_t()
    require(k.GetProcessAffinityMask(k.GetCurrentProcess(),ctypes.byref(process),ctypes.byref(system)) and process.value==0x20,'Launch Windows Python pinned to affinity HEX20; children inherit it')
    unchanged(plan);memory=resources(plan)
    work=Path(plan['work']);require(not work.exists(),'Refuse to overwrite an earlier control execution');work.mkdir()
    receipt={'status':'RUNNING_INDEPENDENT_SECOND_CONTROL','started':now(),'plan_sha256':expected_sha,'resources':memory,'native_commands':[],'scope':plan['scope'],'positive_chain_rerun':False}
    receipt_path=Path(plan['output'])/'receipt.json';write(receipt_path,receipt)
    def command(args, label):
        unchanged(plan)
        entry={'argv':args,'cwd':str(work),'started':now(),'log':str(work/(label+'.native.log'))}
        receipt['native_commands'].append(entry);write(receipt_path,receipt)
        with Path(entry['log']).open('wb') as f:
            result=subprocess.run(args,cwd=work,stdout=f,stderr=subprocess.STDOUT)
        entry.update(native_exit=result.returncode,completed=now(),log_sha256=sha(entry['log']));write(receipt_path,receipt)
        require(result.returncode==0,'Native command failed: '+label)
        unchanged(plan)
    def py(helper,*args):command([sys.executable,'-B',str(helper),*args],Path(helper).stem+'_'+str(len(receipt['native_commands'])))
    def native(binary,args,label):command(['wsl.exe','-d','Ubuntu','-e','bash','-c','cd '+shlex.quote(linux(work))+' && exec '+shlex.join([binary,*args])],label)
    try:
        shutil.copyfile(P2/'n1_flat.il',work/'n1_flat.il')
        original=FINAL.read_bytes();old=b'sky130_fd_sc_hd__and2_1 ';new=b'sky130_fd_sc_hd__or2_1 '
        offset=original.find(old);require(offset>=0,'No exact first and2_1 cell')
        mutated=original[:offset]+new+original[offset+len(old):]
        (work/'neg').mkdir();(work/'neg/soc_asic_top_mut.nl.v').write_bytes(mutated)
        require(sha(work/'neg/soc_asic_top_mut.nl.v')==plan['expected_mutated_netlist_sha256'],'Mutation differs from first control')
        receipt['mutation']={'byte_offset':offset,'from':old.decode().strip(),'to':new.decode().strip(),'only_one_replacement':mutated[:offset]==original[:offset] and mutated[offset+len(new):]==original[offset+len(old):]}
        frontend=(P2/'gate1_frontend.ys').read_text(encoding='ascii');orig=linux(FINAL)
        require(frontend.count(orig)==1,'Expected one exact signed-netlist input')
        (work/'gateN_frontend.ys').write_text(frontend.replace(orig,linux(work/'neg/soc_asic_top_mut.nl.v')),encoding='ascii',newline='\n')
        for name,replacements in [('pre',{'gate1_frontend':'gateN_frontend','gate1_pre':'gateN_pre'}),('flat',{'gate1_cut':'gateN_cut','gate1_flat':'gateN_flat'})]:
            text=(P2/f'gate1_{name}.ys').read_text(encoding='ascii')
            for a,b in replacements.items():text=text.replace(a,b)
            (work/f'gateN_{name}.ys').write_text(text,encoding='ascii',newline='\n')
        native(Y,['-q','-l','gateN_pre.log','gateN_pre.ys'],'gateN_pre')
        py(ROOT/'asic/equiv/sec/sram_cut.py','gateN_pre.il','gateN_cut.il')
        native(Y,['-q','-l','gateN_flat.log','gateN_flat.ys'],'gateN_flat')
        py(LEC/'evert.py','pair','n1_flat.il','gateN_flat.il','pairs_bN.json')
        py(LEC/'free_spec.py','pairs_bN.json','specBN_base.json')
        py(LEC/'spec_manual.py','pairs_bN.json','specBN_base.json','BN_specm.json')
        py(LEC/'mk_onehot_spec.py','pairs_bN.json','BN_specm.json','BN_spec.json')
        for name,source,side in [('BN_gold','n1_flat.il','gold'),('BN_gate','gateN_flat.il','gate')]:
            py(LEC/'evert.py','cut',source,side,'pairs_bN.json',name+'.il','--spec','BN_spec.json')
            text=(LEC/'gold_god_aig.ys').read_text().replace('gold_god',name)
            (work/(name+'_aig.ys')).write_text(text,encoding='ascii',newline='\n')
            native(Y,['-q','-l',name+'_aig.log',name+'_aig.ys'],name+'_aig')
        py(LEC/'aig_syms.py','BN_gold.aig','BN_gate.aig')
        for name,expected in plan['expected_objects_sha256'].items():require(sha(work/name)==expected,'Fresh control object differs from pass1: '+name)
        native(ABC,['-c','&r BN_gold.aig; &miter BN_gate.aig; &ps; &sat -a -z -C 2000 -v; &ps; &w msatBN_a.aig'],'msatBN_a')
        native(ABC,['-c','&r msatBN_a.aig; &sat -a -z -C 200000 -v; &ps; &w msatBN_b.aig'],'msatBN_b')
        actual=[stats(work/'msatBN_a.native.log'),stats(work/'msatBN_b.native.log')]
        require(actual==plan['expected_stats'] and sum(s['Sat   calls'] for s in actual)==60,'SAT counterexamples/statistics differ from pass1')
        py(LEC/'open_outputs.py','msatBN_b.aig','BN_gold.aig','pairs_bN.json','--list')
        last=Path(receipt['native_commands'][-1]['log']).read_text()
        require(re.search(r'outputs 21471, open \(not proved\) 64\b',last),'Unexpected complete miter output/open count')
        unchanged(plan)
        receipt.update(status='VERIFIED_INDEPENDENT_SECOND_LEGACY_SA2_NEGB_CONTROL',completed=now(),SAT_counterexamples=60,stats=actual,open_outputs=64,
            original_inputs_unchanged=True,full_sequential_LEC_claim=False,artifacts_sha256={str(p.relative_to(work)):sha(p) for p in work.rglob('*') if p.is_file()})
        write(receipt_path,receipt)
    except Exception as error:
        receipt.update(status='STOPPED_REQUIRES_INSPECTION',error=str(error),stopped=now());write(receipt_path,receipt);raise
    return {'status':receipt['status'],'receipt':str(receipt_path),'native_commands':len(receipt['native_commands'])}


def main():
    ap=argparse.ArgumentParser(description=__doc__);g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--prepare',action='store_true');g.add_argument('--run',action='store_true')
    ap.add_argument('--output',type=Path,default=ROOT/'results/lec_sa2_negb_repeat_20261016')
    ap.add_argument('--plan',type=Path);ap.add_argument('--plan-sha256')
    args=ap.parse_args();out=args.output.resolve();require(out.is_relative_to(ROOT/'results'),'Output must stay inside research results')
    result=prepare(out) if args.prepare else run(args.plan or out/'plan.json',args.plan_sha256)
    print(json.dumps(result));return 0


if __name__=='__main__':
    raise SystemExit(main())
