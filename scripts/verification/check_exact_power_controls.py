#!/usr/bin/env python3
"""Synthetic negative controls for the exact GLS pair/power readers; no STA/GLS."""
from __future__ import annotations
import argparse
import ctypes
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import copy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/verification'))
sys.path.insert(0,str(ROOT/'scripts/metrics'))
import verify_gls_exact_pair as v
import run_activity_power_exact as p
import run_gls_exact_window as c

def peak_mib():
    class Counters(ctypes.Structure):
        _fields_=[('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong)]+[(name,ctypes.c_size_t) for name in
          ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    counters=Counters();counters.cb=ctypes.sizeof(counters)
    current=ctypes.windll.kernel32.GetCurrentProcess;current.restype=ctypes.c_void_p
    query=ctypes.windll.psapi.GetProcessMemoryInfo
    query.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_ulong]
    v.require(query(current(),ctypes.byref(counters),ctypes.sizeof(counters))!=0,'Memory query failed')
    return counters.PeakWorkingSetSize/1024/1024

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();out=v.local(args.output)
    v.require(out.is_relative_to(ROOT/'results') and not out.exists(),'New control folder required')
    out.mkdir()
    controls=[]
    stage=p.read_sta_inputs('asic/soc_dm_4kb/runs/r14F_A/58-openroad-stapostpnr')
    original_inputs=dict(stage['inputs_sha256'])
    def rejects(label,action):
        try: action()
        except (RuntimeError,ValueError,KeyError,TypeError,OSError) as error:
            controls.append({'control':label,'status':'REJECTED_EXPECTED','reason':str(error)});return
        raise RuntimeError('False PASS: '+label)
    saif='''(SAIFILE
(SAIFVERSION "2.0")
(DIRECTION "backward")
(DESIGN )
(DATE "first fixture")
(VENDOR "synthetic checker fixture; not measurement")
(PROGRAM_NAME "vsim")
(PROGRAM_VERSION "2024.1")
(DIVIDER /)
(TIMESCALE 1 ps)
(DURATION 200000)
(INSTANCE tb_gls_soc
(INSTANCE dut
(NET
(clk (T0 100000) (T1 100000) (TX 0) (TC 20) (IG 0))
(x (T0 200000) (T1 0) (TX 0) (TC 2) (IG 0))
)
)
)
)
'''
    first=out/'synthetic_first.saif';first.write_text(saif,encoding='ascii')
    second=out/'synthetic_second.saif';second.write_text(saif.replace('first fixture','second fixture'),encoding='ascii')
    good=v.compare_saif(first,second,200000)
    mutants={
      'same_duration_wrong_TC':saif.replace('(TC 20)','(TC 21)'),
      'same_duration_wrong_IG':saif.replace('(IG 0)','(IG 1)',1),
      'same_duration_wrong_T0_T1':saif.replace('(T0 100000) (T1 100000)','(T0 99999) (T1 100001)'),
      'same_duration_wrong_TX':saif.replace('(T0 100000) (T1 100000) (TX 0)','(T0 99999) (T1 100000) (TX 1)'),
      'missing_signal':saif.replace('(x (T0 200000) (T1 0) (TX 0) (TC 2) (IG 0))\n',''),
      'renamed_signal':saif.replace('(x (T0','(y (T0'),
      'unsupported_units':saif.replace('(TIMESCALE 1 ps)','(TIMESCALE 1 ns)'),
      'late_one_cycle':saif.replace('200000','220000').replace('(T1 100000)','(T1 120000)'),
      'truncated_parenthesis':saif[:-2],
      'wrong_hierarchy':saif.replace('(INSTANCE dut','(INSTANCE other'),
      'duplicate_signal':saif.replace('(x (T0','(clk (T0'),
      'changed_program_version':saif.replace('2024.1','2025.1'),
      'extra_functional_header':saif.replace('(DESIGN )','(DESIGN )\n(EXTRA 1)'),
      'trailing_content':saif+'(TRAILER 1)\n',
      'duplicate_header':saif.replace('(DURATION 200000)','(DURATION 200000)\n(DURATION 200000)'),
      'extra_UNKNOWN_activity_field':saif.replace('(TC 20)','(EXTRA 20) (TC 20)'),
    }
    for label,text in mutants.items():
        dest=out/(label+'.saif');dest.write_text(text,encoding='ascii')
        rejects(label,lambda dest=dest:v.compare_saif(first,dest,200000))
    # Both equal malformed inputs must also fail, not just a p1/p2 difference.
    for label in ('duplicate_signal','truncated_parenthesis','unsupported_units','duplicate_header'):
        dest=out/(label+'.saif')
        rejects('both_'+label,lambda dest=dest:v.compare_saif(dest,dest,200000))
    source=ROOT/'results/gls_power_r14F_A/up_crc32.power.rpt'
    # Preserved PowerShell reports replaced the UTF-8 ellipsis with U+FFFD.
    # This fixture repairs that punctuation only in its new synthetic copy;
    # the strict fresh native-byte reader deliberately requires valid output.
    template=source.read_text(encoding='utf-8').replace('\ufffd','…')
    power='# SYNTHETIC CHECKER FIXTURE, not a native STA execution\n'+template+'EXACT_POWER_NATIVE_EXIT 0\nEXACT_POWER_EXECUTION_COMPLETE\n'
    activity=p.LINUX_ROOT+'results/gls_power_r14F_A/up_crc32.pins.saif'
    report=out/'synthetic_complete.power.rpt';report.write_text(power,encoding='utf-8')
    accepted=p.inspect_power(report,0,stage,activity)
    rejects('native_nonzero_despite_complete_power',lambda:p.inspect_power(report,7,stage,activity))
    power_mutants={
      'fatal_after_complete':power+'Fatal: synthetic failure\n',
      'Tcl_error_with_zero_native_exit':power+'Error: invalid command name synthetic\n',
      'missing_native_completion':power.replace('EXACT_POWER_EXECUTION_COMPLETE\n',''),
      'missing_native_exit':power.replace('EXACT_POWER_NATIVE_EXIT 0\n',''),
      'inner_native_nonzero':power.replace('EXACT_POWER_NATIVE_EXIT 0','EXACT_POWER_NATIVE_EXIT 7'),
      'duplicate_completion':power+'EXACT_POWER_EXECUTION_COMPLETE\n',
      'missing_named_group':re.sub(r'^Macro .*\n','',power,flags=re.M),
      'duplicate_named_group':power+next(s for s in power.splitlines() if s.startswith('Macro '))+'\n',
      'missing_named_origin':re.sub(r'^PW_ORIGIN unknown .*\n','',power,flags=re.M),
      'duplicate_named_origin':power+next(s for s in power.splitlines() if s.startswith('PW_ORIGIN unknown '))+'\n',
      'missing_total_origin':re.sub(r'^PW_ORIGIN total_output_pins .*\n','',power,flags=re.M),
      'wrong_power_corner':power.replace('corner='+p.CORNER,'corner=max_ff_n40C_1v95',1),
      'wrong_loaded_SPEF':power.replace(stage['spef_linux'],stage['spef_linux']+'.wrong'),
      'wrong_loaded_SDC':power.replace(stage['sdc_linux'],stage['sdc_linux']+'.wrong'),
      'wrong_loaded_netlist':power.replace(stage['netlist_linux'],stage['netlist_linux']+'.wrong'),
      'wrong_SAIF_scope':power.replace('scope tb_gls_soc/dut','scope dut'),
      'wrong_activity_file':power.replace(activity,activity+'.wrong'),
      'nonfinite_power':re.sub(r'^(Total\s+)\S+',r'\1NaN',power,flags=re.M),
    }
    for label,text in power_mutants.items():
        dest=out/(label+'.power.rpt');dest.write_text(text,encoding='utf-8')
        rejects(label,lambda dest=dest:p.inspect_power(dest,0,stage,activity))
    for label,field in [('pair_power_group_mismatch','groups_W_and_percent'),('pair_origin_mismatch','origins'),('pair_pin_count_mismatch','total_output_pins')]:
        other=copy.deepcopy(accepted)
        if field=='groups_W_and_percent':other[field]['Macro'][0]='0.125'
        elif field=='origins':other[field]['unknown']['count']+=1
        else:other[field]+=1
        rejects(label,lambda other=other:p.compare_power(accepted,other))
    # Full synthetic native provenance fixture. Actual native job count is zero;
    # fixture receipts are clearly labeled and never promoted to result receipts.
    fixture=out/'synthetic_capture_fixtures';fixture.mkdir()
    cfg=c.DESIGNS['DM'];net=ROOT/f'asic/{cfg["design"]}/runs/{cfg["tag"]}/{cfg["fill"]}/soc_asic_top.nl.v'
    resolved=net.parent.parent/'resolved.json';recipe=json.loads(resolved.read_text())
    base=dict(json.loads((ROOT/'results/rtl_manifest.json').read_text())['files'])
    paths=[net,resolved,Path(r'C:/questasim64_2024.1/win64/vsim.exe'),ROOT/'scripts/verification/run_gls_exact_window.py',ROOT/'asic/gls/tb_gls_soc.sv',ROOT/'asic/gls/saif_to_pins.py',ROOT/'results/mapped_counter_freeze_checked_20261010/dm_p1.json']
    paths += [ROOT/q for q in c.MODELS]+[ROOT/'fw'/(k+'.hex') for k in c.KERNELS]+[ROOT/'results'/q for q in cfg['refs']]
    paths += [ROOT/q.removeprefix(p.LINUX_ROOT) for q in recipe['VERILOG_FILES']]+[p.windows_path(q) for q in stage['liberties_linux']]
    for q in paths:base[str(q.resolve())]=v.sha(q)
    refs=v.read_reference(ROOT/'results'/cfg['refs'][0],'DM')
    receipts=[]
    for pass_no in (1,2):
        folder=fixture/f'p{pass_no}';folder.mkdir();lib=f'work_gls_exact_dm_{folder.name}_p{pass_no}'
        inputs=dict(base)
        tb=folder/'tb_gls_soc_exact_window.sv';tb.write_text(c.generated_tb((ROOT/'asic/gls/tb_gls_soc.sv').read_text(),cfg['freeze_expression']),encoding='ascii')
        capture=folder/'power_capture_exact.do';capture.write_text(c.capture_do(),encoding='ascii')
        comp=folder/'compile.do'
        prepared=ROOT/'results/gls_exact_dm_ud_screen_20261010/compile.do'
        native_recipe=prepared.read_text()
        old_lib=re.search(r'^vlib (\S+)$',native_recipe,re.M)[1]
        native_recipe=native_recipe.replace(old_lib,lib).replace(c.tcl_path(prepared.parent/'tb_gls_soc_exact_window.sv'),c.tcl_path(tb))
        comp.write_text(native_recipe,encoding='ascii')
        (folder/'compile.log').write_text('# [PASS] EXACT_WINDOW_PRIVATE_LIBRARY_COMPILED\n# Errors: 0, Warnings: 0\n',encoding='ascii')
        def simcommand(stem):return [r'C:/questasim64_2024.1/win64/vsim.exe','-c','-l',str(folder/(stem+'.transcript')),'-wlf',str(folder/(stem+'.wlf')),'-do','do '+c.tcl_path(folder/(stem+'.do'))]
        def job(command,log):return {'command':command,'started':'SYNTHETIC_FIXTURE_NOT_MEASUREMENT','completed':'SYNTHETIC_FIXTURE_NOT_MEASUREMENT','native_exit':0,'log':str(log.relative_to(ROOT)),'log_sha256':v.sha(log)}
        jobs=[job(simcommand('compile'),folder/'compile.log')];cases={}
        for k in c.KERNELS:
            mc=int(refs[k]['mcycle']);duration=mc*20000
            do=folder/(k+'.do');do.write_text('onerror {quit -code 1 -f}\nvsim -onfinish stop -voptargs={+acc=rn+tb_gls_soc +acc=n+soc_asic_top} -gMEMFILE=fw/'+k+'.hex -gMAX_CYCLES=8000000 '+lib+'.tb_gls_soc\nset SAIF '+c.tcl_path(folder/(k+'.raw.saif'))+'\ndo '+c.tcl_path(capture)+'\nquit -code 0 -f\n',encoding='ascii')
            text=saif.replace('200000',str(duration)).replace('100000',str(duration//2))
            for suffix in ('.raw.saif','.pins.saif'):(folder/(k+suffix)).write_text(text,encoding='ascii')
            log=folder/(k+'.log');log.write_text(f'# PW_WIN_START 100000\n# PW_WIN_END {100000+duration}\n# GLS_RESULT memfile=fw/{k}.hex status=PASS mcycle={mc} hex_decoded=1 LEDR=a5 win_cycles={mc} win_t0=100000 win_t1={100000+duration} win_starts=1 win_stops=1\n# Errors: 0, Warnings: 0\n',encoding='ascii')
            pinlog=folder/(k+'.pins.log');pinlog.write_text('PW_SAIF window '+str(duration)+' synthetic fixture, not measurement\n',encoding='ascii')
            jobs += [job(simcommand(k),log),job([sys.executable,'-B','asic/gls/saif_to_pins.py',str(folder/(k+'.raw.saif')),str(net),str(folder/(k+'.pins.saif'))]+[str(p.windows_path(q).resolve()) for q in stage['liberties_linux']],pinlog)]
            cases[k]={'window':c.inspect_log(log,mc,0,k),'raw_saif':c.inspect_saif(folder/(k+'.raw.saif'),duration),'pin_saif':c.inspect_saif(folder/(k+'.pins.saif'),duration),'reference_minstret':int(refs[k]['minstret']),'raw_log_sha256':v.sha(log)}
        for q in [tb,capture,comp]+[folder/(k+'.do') for k in c.KERNELS]:inputs[str(q)]=v.sha(q)
        r={'fixture_only':True,'status':'VERIFIED_EXACT_CAPTURE_SINGLE_PASS','design':'DM','pass':pass_no,'PD_tag':cfg['tag'],'netlist':str(net.relative_to(ROOT)),'freeze_expression':cfg['freeze_expression'],'mapping_prerequisite':'VERIFIED_BOUND_TO_NETLIST','kernels':list(c.KERNELS),'full_twelve_kernel_matrix':True,'timing_period_ps':20000,'independent_interval_counter':True,'power_or_full_LEC_claim':False,'profile':{'cache_KiB':4,'RAM_KiB':16,'current_reference_FAST_HIT':0,'frozen_snapshot_FAST_HIT_switch_absent':True,'BRANCH_PREDICT_ENABLE':1,'L0_ENTRIES':8,'CACHE_LINE_WORDS':4,'VICTIM_ENTRIES':4,'reference_counter_fields':40,'PD_RTL_sources':42},'library':lib,'inputs_sha256':inputs,'native_commands':jobs,'cases':cases}
        path=folder/'receipt.json';path.write_text(json.dumps(r,indent=2)+'\n',encoding='ascii');receipts.append(path)
    v.verify(*receipts) # Returned positive fixture result is deliberately not saved as measurement.
    original=receipts[1].read_text()
    r=json.loads(original)
    capture_mutants={
      'IN_PROGRESS_capture':dict(r,status='RUNNING_FRESH_GLS_CAPTURE'),
      'screen_only_capture':dict(r,status='SINGLE_SCREEN_NOT_RESULT'),
      'missing_kernel_pair':dict(r,cases={k:val for k,val in r['cases'].items() if k!='up_ud'}),
      'reused_private_compilation':dict(r,library=json.loads(receipts[0].read_text())['library']),
      'changed_input_SHA':dict(r,inputs_sha256=dict(r['inputs_sha256'],**{str(net):'0'*64})),
      'missing_native_job':dict(r,native_commands=r['native_commands'][:-1]),
      'wrong_architecture_profile':dict(r,profile=dict(r['profile'],RAM_KiB=32)),
      'missing_native_exit_status':copy.deepcopy(r),
      'stored_window_not_raw':copy.deepcopy(r),
      'missing_frozen_PD_source':dict(r,inputs_sha256={key:val for key,val in r['inputs_sha256'].items() if key!=str((ROOT/recipe['VERILOG_FILES'][0].removeprefix(p.LINUX_ROOT)).resolve())}),
      'simulation_native_nonzero':copy.deepcopy(r),
    }
    capture_mutants['missing_native_exit_status']['native_commands'][1].pop('native_exit')
    capture_mutants['stored_window_not_raw']['cases']['up_ud']['window']['duration_ps']+=20000
    capture_mutants['simulation_native_nonzero']['native_commands'][1]['native_exit']=7
    for label,mutant in capture_mutants.items():
        receipts[1].write_text(json.dumps(mutant,indent=2)+'\n',encoding='ascii')
        rejects(label,lambda:v.verify(*receipts))
    receipts[1].write_text(original,encoding='ascii')
    compile_path=receipts[1].parent/'compile.do'
    original_compile=compile_path.read_text()
    for label,old,new in [('rehashed_wrong_RAM_profile','+define+GLS_RAM16K','+define+GLS_RAM32K'),('rehashed_wrong_unit_delay','+define+UNIT_DELAY=#0','+define+UNIT_DELAY=#1')]:
        compile_path.write_text(original_compile.replace(old,new),encoding='ascii')
        mutant=json.loads(original);mutant['inputs_sha256'][str(compile_path)]=v.sha(compile_path)
        receipts[1].write_text(json.dumps(mutant,indent=2)+'\n',encoding='ascii')
        rejects(label,lambda:v.verify(*receipts))
    compile_path.write_text(original_compile,encoding='ascii')
    receipts[1].write_text(original,encoding='ascii')
    # Real native shell control with fake memory and fake STA, not WSL/OpenSTA.
    mock=out/'synthetic_shell';mock.mkdir();bin_dir=mock/'bin';bin_dir.mkdir()
    env=dict(os.environ);env['MOCK_ROOT']=str(mock).replace('\\','/')
    # Git Bash prepends /usr/bin before the inherited Windows PATH. Inject the
    # private fake-tool directory after initialization in this process only.
    startup=mock/'mock_startup.sh'
    startup.write_text('export PATH="'+str(bin_dir).replace('\\','/').replace('E:','/e')+':$PATH"\n',encoding='ascii',newline='\n')
    env['BASH_ENV']=str(startup).replace('\\','/')
    for name,body in {
      'free':'#!/usr/bin/env bash\nif [ -f "$MOCK_ROOT/memory_checked" ]; then n=6000; else n=4999; touch "$MOCK_ROOT/memory_checked"; fi\necho "Mem: 10000 1000 1000 0 0 $n"\n',
      'sleep':'#!/usr/bin/env bash\necho "$1" >> "$MOCK_ROOT/mock_sleeps.txt"\n',
      'bash':'#!/usr/bin/env bash\ncat "$MOCK_ROOT/mock_report.txt"\nexit "$(cat "$MOCK_ROOT/mock_exit.txt")"\n',
    }.items():
        # Use installed Git Bash directly in the shebang, avoiding recursion on fake bash.
        (bin_dir/name).write_text(body.replace('#!/usr/bin/env bash','#!/bin/sh',1),encoding='ascii',newline='\n')
    script=mock/'foreground_fixture.sh'
    script.write_text(p.queue_script(stage['step'],None,mock/'abort',5000).replace(p.LINUX_ROOT,'/e/Projects/RISCV-research/'),encoding='ascii',newline='\n')
    (mock/'mock_report.txt').write_text(template,encoding='utf-8')
    shell_jobs=[]
    for rc in (0,7):
        (mock/'mock_exit.txt').write_text(str(rc),encoding='ascii')
        log=mock/f'mock_native_rc{rc}.log'
        with log.open('wb') as f:result=subprocess.run([r'C:/Program Files/Git/bin/bash.exe',str(script)],cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT)
        v.require(result.returncode==rc,'Foreground shell masked mock tool native exit')
        shell_jobs.append({'fixture_only':True,'expected_native_exit':rc,'actual_native_exit':result.returncode,'log':str(log.relative_to(ROOT)),'sha256':v.sha(log)})
        if rc:rejects('foreground_mock_native_failure',lambda log=log:p.inspect_power(log,rc,stage,activity))
    v.require((mock/'mock_sleeps.txt').read_text().splitlines()==['30'],'Memory queue must wait 30 seconds only when unavailable (mock sleep)')
    (mock/'abort').write_text('synthetic cooperative pre-launch abort\n',encoding='ascii')
    result=subprocess.run([r'C:/Program Files/Git/bin/bash.exe',str(script)],cwd=ROOT,env=env,capture_output=True)
    v.require(result.returncode==75,'Cooperative pre-launch abort did not reject')
    controls.append({'control':'foreground_mock_cooperative_abort','status':'REJECTED_EXPECTED','native_exit':75})
    # No real WSL/Questa/OpenSTA process was started by this control program.
    for q,h in original_inputs.items():v.require(v.sha(v.local(q))==h,'Source changed during controls: '+q)
    peak=peak_mib();v.require(peak<=256,'Control process exceeded memory bound')
    result={'status':'PASSED_SYNTHETIC_REJECTION_CONTROLS_NOT_MEASUREMENTS','checked_at':v.stamp(),'controls':controls,'negative_controls':len(controls),'valid_synthetic_SAIF_pair':good,'valid_synthetic_full_capture_pair':True,'valid_synthetic_power_report':True,'native_mock_shell_jobs':shell_jobs,'actual_WSL_STA_GLS_executions':0,'memory_peak_MiB':peak,'bound_MiB':256,'source_sha256_before_after':original_inputs,'new_helpers_sha256':{str(q.relative_to(ROOT)):v.sha(q) for q in [Path(__file__),Path(v.__file__),Path(p.__file__)]},'artifacts_sha256':{str(q.relative_to(ROOT)):v.sha(q) for q in out.rglob('*') if q.is_file()}}
    with (out/'receipt.json').open('x',encoding='ascii') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'negative_controls':len(controls),'peak_MiB':peak,'actual_STA_GLS_jobs':0}))
    return 0

if __name__=='__main__':raise SystemExit(main())
