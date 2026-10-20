#!/usr/bin/env python3
"""Prepare and test an opt-in GLS memory-queue patch without editing the runner."""
from __future__ import annotations
import argparse
import ast
import copy
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'scripts/verification/run_gls_exact_window.py'
SOURCE_SHA='aded02d0f6b2a12ac78bae89d4aeb889318a244208424f5324751d3f39f12633'

def sha(path):return hashlib.file_digest(Path(path).open('rb'),'sha256').hexdigest()
def require(ok,message):
    if not ok:raise RuntimeError(message)

def propose(text):
    def replace(old,new):
        nonlocal text
        require(text.count(old)==1,'Source anchor differs: '+old[:60]);text=text.replace(old,new)
    replace('import sys\n','import sys\nimport time\n')
    replace("    ap.add_argument('--run',action='store_true')", "    ap.add_argument('--wait-for-memory',action='store_true',help='Opt in to foreground 30 s waits before each next native tool; minimum RAM remains 6000 MiB')\n    ap.add_argument('--run',action='store_true')")
    replace("             'inputs_sha256':inputs,'native_commands':[],'cases':{},'minimum_Windows_free_MiB':args.min_free_mib,",
            "             'inputs_sha256':inputs,'native_commands':[],'cases':{},'minimum_Windows_free_MiB':args.min_free_mib,\n             'wait_for_memory_opt_in':args.wait_for_memory,'memory_waits':[],\n             'abort_before_next_native':str((out/'abort_before_next_native').relative_to(ROOT)),")
    replace("        unchanged();available=free_windows_mib();require(available>=args.min_free_mib,f'WAITING_FOR_MEMORY: Windows free {available} MiB < {args.min_free_mib}; no native tool started')",
'''        while True:
            require(not (out/'abort_before_next_native').exists(),'COOPERATIVE_ABORT_BEFORE_NEXT_NATIVE: no next tool started')
            unchanged()
            available=free_windows_mib()
            require(isinstance(available,int) and available>=0,'Windows memory query returned invalid data; no next tool started')
            if available>=args.min_free_mib:break
            require(args.wait_for_memory,f'WAITING_FOR_MEMORY: Windows free {available} MiB < {args.min_free_mib}; no native tool started')
            wait={'started':stamp(),'Windows_free_MiB':available,'required_MiB':args.min_free_mib,
                  'sleep_seconds':30,'next_command':command,'log':str(log.relative_to(ROOT))}
            receipt['memory_waits'].append(wait);save()
            print(json.dumps({'status':'WAITING_FOR_MEMORY',**wait}),flush=True)
            time.sleep(30)
            wait['returned']=stamp();save()''')
    return text

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();out=(ROOT/args.output).resolve()
    require(out.is_relative_to(ROOT/'results') and not out.exists(),'Use a new preparation folder')
    require(sha(SOURCE)==SOURCE_SHA,'Live source differs; patch not prepared')
    before=SOURCE.read_text(encoding='ascii');after=propose(before)
    old_ast=ast.parse(before);new_ast=ast.parse(after)
    for tree in (old_ast,new_ast):
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        require(len([n for n in function.body if isinstance(n,ast.FunctionDef) and n.name=='native'])==1,'Native-function anchor changed')
    # All functional testbench/capture/parser/profile functions are unchanged.
    old_defs={n.name:ast.dump(n,include_attributes=False) for n in old_ast.body if isinstance(n,ast.FunctionDef)}
    new_defs={n.name:ast.dump(n,include_attributes=False) for n in new_ast.body if isinstance(n,ast.FunctionDef)}
    require(set(old_defs)==set(new_defs) and all(old_defs[k]==new_defs[k] for k in old_defs if k!='main'),'Functional GLS helper changed')
    out.mkdir()
    candidate=out/'run_gls_exact_window.proposed.py';candidate.write_text(after,encoding='ascii',newline='\n')
    patch=out/'proposed.patch'
    patch.write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/scripts/verification/run_gls_exact_window.py',tofile='b/scripts/verification/run_gls_exact_window.py')),encoding='ascii',newline='\n')
    native_node=next(n for n in next(n for n in new_ast.body if isinstance(n,ast.FunctionDef) and n.name=='main').body if isinstance(n,ast.FunctionDef) and n.name=='native')
    native_code=compile(ast.fix_missing_locations(ast.Module(body=[native_node],type_ignores=[])),str(candidate),'exec')
    scenarios=[]
    def scenario(label,enabled,memories,abort_at_sleep=False,abort_before=False,change_at_sleep=False,change_during_native=False,native_rc=0,expected_error=False):
        folder=out/label;folder.mkdir();input_file=folder/'synthetic_frozen_input.txt';input_file.write_text('fixture not measurement\n',encoding='ascii')
        input_sha=sha(input_file);ledger={'native_commands':[],'memory_waits':[]};sleeps=[];native_calls=[];snapshots=[];checks=[]
        memory=iter(memories)
        def unchanged():
            checks.append(sha(input_file));require(checks[-1]==input_sha,'synthetic frozen input changed')
        def sleep(seconds):
            require(seconds==30,'Wait interval changed');sleeps.append(seconds)
            if abort_at_sleep:(folder/'abort_before_next_native').write_text('synthetic cooperative request\n',encoding='ascii')
            if change_at_sleep:input_file.write_text('changed synthetic input\n',encoding='ascii')
        def run(command,**kwargs):
            native_calls.append(command)
            kwargs['stdout'].write(b'SYNTHETIC MOCK NATIVE OUTPUT: not a measurement\n')
            if change_during_native:input_file.write_text('changed during fake native\n',encoding='ascii')
            return SimpleNamespace(returncode=native_rc)
        if abort_before:(folder/'abort_before_next_native').write_text('synthetic prelaunch abort\n',encoding='ascii')
        namespace={'require':require,'out':folder,'ROOT':ROOT,'unchanged':unchanged,'free_windows_mib':lambda:next(memory),
                   'args':SimpleNamespace(min_free_mib=6000,wait_for_memory=enabled),'receipt':ledger,'stamp':lambda:'SYNTHETIC_NOT_MEASUREMENT',
                   'save':lambda:snapshots.append(copy.deepcopy(ledger)),'time':SimpleNamespace(sleep=sleep),
                   'subprocess':SimpleNamespace(run=run,STDOUT='SYNTHETIC_STDOUT'),'sha':sha,'json':json}
        exec(native_code,namespace)
        error=None
        try:namespace['native'](['SYNTHETIC_PRIVATE_TOOL_NOT_EXECUTED'],folder/'synthetic.log')
        except RuntimeError as e:error=str(e)
        require((error is not None)==expected_error,'Unexpected decision: '+label)
        if abort_at_sleep or abort_before or change_at_sleep or label in ('default_off_memory_dip','invalid_memory_query'):
            require(not native_calls,'Mock tool launched before guard satisfied: '+label)
        elif not change_during_native:
            require(len(native_calls)==1,'Expected exactly one fake native invocation: '+label)
        require(all(w['required_MiB']==6000 and w['sleep_seconds']==30 for w in ledger['memory_waits']),'RAM threshold/wait weakened')
        scenarios.append({'scenario':label,'fixture_only':True,'expected_error':expected_error,'observed_error':error,
                          'mock_memory_queries':memories,'mock_sleep_seconds':sleeps,'mock_native_calls':len(native_calls),
                          'guard_checks':len(checks),'ledger':ledger,'ledger_snapshots':snapshots})
    scenario('default_off_memory_dip',False,[5999],expected_error=True)
    scenario('default_off_enough_RAM',False,[6000])
    scenario('opt_in_two_dips_then_threshold',True,[5999,4000,6000])
    scenario('opt_in_enough_RAM_no_wait',True,[7000])
    scenario('cooperative_abort_during_wait',True,[5999],abort_at_sleep=True,expected_error=True)
    scenario('cooperative_abort_before_next_tool',True,[],abort_before=True,expected_error=True)
    scenario('changed_frozen_input_during_wait',True,[5999],change_at_sleep=True,expected_error=True)
    scenario('changed_frozen_input_during_fake_native',True,[6000],change_during_native=True,expected_error=True)
    scenario('fake_native_failure',True,[6000],native_rc=7,expected_error=True)
    scenario('invalid_memory_query',True,[-1],expected_error=True)
    # Real lightweight native CLI help only; no compile, simulation or WSL.
    help_log=out/'proposed_help.log'
    with help_log.open('wb') as f:help_result=subprocess.run([sys.executable,'-B',str(candidate),'--help'],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
    require(help_result.returncode==0 and '--wait-for-memory' in help_log.read_text(),'New opt-in CLI help failed')
    check_log=out/'git_apply_check.log'
    with check_log.open('wb') as f:check=subprocess.run(['git','apply','--check',str(patch)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
    require(check.returncode==0,'Patch does not apply exactly to current source')
    require(sha(SOURCE)==SOURCE_SHA,'Original live runner changed')
    result={'status':'PREPARED_AND_MOCK_CHECKED_NOT_APPLIED','source':str(SOURCE.relative_to(ROOT)), 'source_sha256_before_after':SOURCE_SHA,
            'proposed_sha256':sha(candidate),'patch_sha256':sha(patch),'functional_helpers_AST_identical':True,
            'default_wait_enabled':False,'minimum_RAM_MiB_unchanged':6000,'foreground_wait_seconds':30,
            'cooperative_abort_scope':'new output/abort_before_next_native; checked before next tool, never stops an active tool',
            'mock_scenarios':scenarios,'native_help_exit':help_result.returncode,'git_apply_check_exit':check.returncode,
            'actual_GLS_STA_WSL_executions':0,'application_prerequisite':'All original GLS runner instances, conversion and final unchanged checks must finish first',
            'pair_verifier_compatibility':'Extra opt-in/wait receipt fields accepted; native commands, profile, frozen inputs and complete capture gates remain exact',
            'artifacts_sha256':{str(q.relative_to(ROOT)):sha(q) for q in out.rglob('*') if q.is_file()}}
    with (out/'receipt.json').open('x',encoding='ascii') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'mock_scenarios':len(scenarios),'live_runner_unchanged':True,'native_heavy_executions':0}))
    return 0

if __name__=='__main__':raise SystemExit(main())
