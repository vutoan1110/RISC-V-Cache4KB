#!/usr/bin/env python3
"""Fresh private GLS captures with an independently counted exact 20 ns window.

Preparation is read-only apart from a new output folder. --run requires a
reviewed mapped counter-freeze receipt and available Windows RAM. This runs
no WSL, PD or STA. Preserved captures and frozen source files are never edited.
"""
from __future__ import annotations
import argparse
import collections
import csv
import ctypes
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from snapshot_fields import FIELDS, invariants
KERNELS=tuple('up_'+k for k in ('aha-mont64','crc32','depthconv','edn','huffbench','matmult-int','md5sum','nettle-sha256','slre','statemate','tarfind','ud'))
SA2='sa2_corr3400x3400_f220_capm20_fo16_pad1_tdp_clkm3_rsztf_ecomaxmin_r1'
DESIGNS={
 'DM':{'design':'soc_dm_4kb','tag':'r14F_A','fill':'55-openroad-fillinsertion','sta':'58-openroad-stapostpnr',
       'freeze_expression':'~dut._029058_', 'refs':('upstream_asic_rfbht_p1.csv','upstream_asic_rfbht_p2.csv')},
 'SA2':{'design':'soc_sa2_4kb','tag':SA2,'fill':'56-openroad-fillinsertion','sta':'59-openroad-stapostpnr',
        'freeze_expression':'~dut._031249_', 'refs':('dse_asic_view_p1.csv','dse_asic_view_p2.csv')},
}
MODELS=('asic/gls/lib/primitives.v','asic/gls/lib/sky130_fd_sc_hd.v',
        'asic/soc_dm_4kb/macros/verilog/sky130_sram_2kbyte_1rw1r_32x512_8.v',
        'asic/soc_dm_4kb/macros/verilog/sky130_sram_1kbyte_1rw1r_32x256_8.v')

def require(condition,message):
    if not condition: raise RuntimeError(message)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(65536),b''):h.update(block)
    return h.hexdigest()

def stamp():return datetime.now(timezone.utc).isoformat()

def free_windows_mib():
    class Memory(ctypes.Structure):
        _fields_=[('dwLength',ctypes.c_ulong),('dwMemoryLoad',ctypes.c_ulong)]+[(n,ctypes.c_ulonglong) for n in
          ('ullTotalPhys','ullAvailPhys','ullTotalPageFile','ullAvailPageFile','ullTotalVirtual','ullAvailVirtual','ullAvailExtendedVirtual')]
    m=Memory();m.dwLength=ctypes.sizeof(m)
    require(ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))!=0,'Windows memory query failed')
    return m.ullAvailPhys//(1024*1024)

def inspect_log(path,expected_mcycle,native_exit,expected_kernel=None):
    require(native_exit==0,f'Native simulation exit {native_exit}: {path}')
    markers=collections.defaultdict(list);order=[];footer=None
    with path.open('rb') as f:
        for line in f:
            require(not re.search(rb'\*\*\s+(?:Error|Fatal)|\[FAIL\]',line),f'Simulation error/fatal: {path}')
            if b'Errors:' in line:footer=line
            for token in (b'GLS_RESULT ',b'PW_WIN_START ',b'PW_WIN_END '):
                if token in line:
                    markers[token].append(line.decode(errors='replace').strip());order.append(token)
    require(footer is not None and re.search(rb'Errors:\s*0,',footer),f'Missing complete zero-error footer: {path}')
    require(all(len(markers[k])==1 for k in (b'GLS_RESULT ',b'PW_WIN_START ',b'PW_WIN_END ')),f'Missing/duplicate capture/result marker: {path}')
    require(order==[b'PW_WIN_START ',b'PW_WIN_END ',b'GLS_RESULT '],f'Capture/result marker ordering is incomplete: {path}')
    pairs=[token.split('=',1) for token in markers[b'GLS_RESULT '][0].split() if '=' in token]
    require(len(pairs)==len({p[0] for p in pairs}),f'Duplicate GLS_RESULT key: {path}')
    data=dict(pairs)
    if expected_kernel is not None:
        require(data.get('memfile')==f'fw/{expected_kernel}.hex',f'Wrong elaborated firmware result: {path}')
    require(data.get('status')=='PASS' and data.get('hex_decoded')=='1' and data.get('LEDR','').lower()=='a5',f'Functional self-check failure: {path}')
    require(int(data.get('win_starts','0'))==int(data.get('win_stops','0'))==1,f'Independent boundary count failure: {path}')
    mc,wc=int(data['mcycle']),int(data['win_cycles'])
    t0,t1=int(data['win_t0']),int(data['win_t1'])
    start=int(markers[b'PW_WIN_START '][0].split()[-1]);stop=int(markers[b'PW_WIN_END '][0].split()[-1])
    require(mc==wc==expected_mcycle>0,f'Counter/reference mismatch: {path}')
    require((start,stop)==(t0,t1) and t1-t0==mc*20000,f'Physical capture duration is not MCYCLE*20000 ps: {path}')
    return {'mcycle':mc,'win_cycles':wc,'win_t0_ps':t0,'win_t1_ps':t1,'duration_ps':t1-t0,
            'win_starts':1,'win_stops':1,'LEDR':'a5','hex_decoded':1,'status':'PASS'}

def inspect_saif(path,duration_ps):
    require(path.is_file() and path.stat().st_size>0,f'Missing/empty SAIF: {path}')
    headers={};spans=collections.Counter();top=0;dut=0
    with path.open('rb') as f:
        for line in f:
            m=re.match(rb'^\((TIMESCALE|DURATION) ([^)]*)\)',line.strip())
            if m:
                key=m[1].decode();require(key not in headers,f'Repeated SAIF header: {path}');headers[key]=m[2].decode()
            if re.match(rb'^\(INSTANCE tb_gls_soc\s*$',line.strip()):top+=1
            if re.match(rb'^\(INSTANCE dut\s*$',line.strip()):dut+=1
            m=re.search(rb'\(T0 (\d+)\) \(T1 (\d+)\) \(TX (\d+)\)',line)
            if m:spans[sum(map(int,m.groups()))]+=1
    require(headers.get('TIMESCALE')=='1 ps' and headers.get('DURATION')==str(duration_ps),f'Wrong SAIF units/duration: {path}')
    require(top==dut==1 and set(spans)=={duration_ps} and spans[duration_ps]>0,f'Wrong SAIF scope/entry span: {path}')
    return {'duration_ps':duration_ps,'timescale':'1 ps','entries':spans[duration_ps],'sha256':sha(path)}

def generated_tb(source,expression):
    # Remove the historical, unsupported claim that twelve GLS workloads
    # substitute for full LEC. The remaining frozen bench body is kept exactly
    # except for passive observation/boundary assertions listed below.
    header='`timescale 1ns/1ps\n// Private generated exact-window observer; functional GLS only, not full LEC.\n'
    text=header+source[source.index('module tb_gls_soc;'):]
    old=r'wire frz = dut.\u_soc.u_observability.u_sysmon.freeze_q ;'
    require(text.count(old)==1,'Frozen TB freeze declaration changed')
    text=text.replace(old,'wire frz = '+expression+';')
    text=text.replace('integer    win_cycles = 0;','integer    win_cycles = 0;\n    integer win_starts = 0, win_stops = 0;')
    require(text.count('win_cycles <= 0;')==1,'Frozen TB start branch changed')
    text=text.replace('win_cycles <= 0;','win_cycles <= 0;\n                win_starts <= win_starts + 1;')
    require(text.count('win_done <= 1\'b1;')==1,'Frozen TB close branch changed')
    text=text.replace("win_done <= 1'b1;","win_done <= 1'b1;\n                win_cycles <= win_cycles + 1;\n                win_stops <= win_stops + 1;")
    old='if (mcyc < mcyc_q) begin'
    require(text.count(old)==1,'Frozen TB clear detector changed')
    text=text.replace(old,old+'\n                if (win_on || win_starts != 0) $fatal(1, "repeated capture clear");')
    old='if (reset_n && !win_done) begin'
    require(text.count(old)==1,'Frozen TB sample guard changed')
    text=text.replace(old,old+'\n            if (win_on && frz !== 1\'b0 && frz !== 1\'b1) $fatal(1, "unknown freeze boundary");')
    old='if (cycles >= MAX_CYCLES)'
    require(text.count(old)==1,'Frozen TB completion guard changed')
    text=text.replace(old,'if (cycles < MAX_CYCLES && (win_starts != 1 || win_stops != 1 || !win_done ||\n            win_cycles != disp || (win_t1-win_t0) != win_cycles*20))\n            $fatal(1, "exact independent capture interval/duration gate failed");\n        '+old)
    old='win_t0=%0t win_t1=%0t"'
    require(text.count(old)==1,'Frozen TB result marker changed')
    text=text.replace(old,'win_t0=%0t win_t1=%0t win_starts=%0d win_stops=%0d"')
    require(text.count('win_cycles, win_t0, win_t1);')==1,'Frozen TB result arguments changed')
    text=text.replace('win_cycles, win_t0, win_t1);','win_cycles, win_t0, win_t1, win_starts, win_stops);')
    return text

def capture_do():
    return '''set ::pw_added 0
set ::pw_ended 0
when -label pw_start {/tb_gls_soc/win_on == 1} {
    if {$::pw_added || $::pw_ended} {error "Repeated capture start"}
    power add -in -out -internal /tb_gls_soc/dut/*
    set ::pw_added 1
    echo "PW_WIN_START $now"
}
when -label pw_end {/tb_gls_soc/win_done == 1} {
    if {!$::pw_added || $::pw_ended} {error "Missing start or repeated capture stop"}
    power report -all -bsaif $::SAIF
    set ::pw_ended 1
    echo "PW_WIN_END $now"
}
run -all
if {!$::pw_added || !$::pw_ended} {error "Incomplete capture"}
'''

def tcl_path(path):
    value=path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path).replace('\\','/')
    require(not any(c in value for c in '{}\n\r'),'Unsupported Tcl path characters')
    return '{'+value+'}'

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--design',choices=DESIGNS,required=True)
    ap.add_argument('--pass',dest='pass_no',type=int,choices=(1,2),required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--kernels',default=','.join(KERNELS))
    ap.add_argument('--kernel',help='Single screening kernel; accepts crc32 or up_crc32')
    ap.add_argument('--freeze-proof',type=Path)
    ap.add_argument('--liberty',type=Path,action='append',default=[])
    ap.add_argument('--vsim',default=r'C:/questasim64_2024.1/win64/vsim.exe')
    ap.add_argument('--min-free-mib',type=int,default=6000)
    ap.add_argument('--wait-for-memory',action='store_true',help='Opt in to foreground 30 s waits before each next native tool; minimum RAM remains 6000 MiB')
    ap.add_argument('--run',action='store_true')
    args=ap.parse_args();cfg=DESIGNS[args.design]
    require(args.min_free_mib>=6000,'Windows GLS memory threshold must be at least 6000 MiB')
    kernels=args.kernels.split(',') if not args.kernel else [args.kernel if args.kernel.startswith('up_') else 'up_'+args.kernel]
    require(kernels and len(set(kernels))==len(kernels) and set(kernels).issubset(KERNELS),'Unknown/duplicate kernel')
    out=(ROOT/args.output).resolve();require(out.is_relative_to(ROOT/'results') and not out.exists(),'Output must be a new folder under results')
    library=f'work_gls_exact_{args.design.lower()}_{out.name}_p{args.pass_no}'
    require(re.fullmatch(r'[a-zA-Z0-9_]+',library) is not None and not (ROOT/library).exists(),'Unsafe/existing private library')
    net=ROOT/f"asic/{cfg['design']}/runs/{cfg['tag']}/{cfg['fill']}/soc_asic_top.nl.v"
    resolved=net.parent.parent/'resolved.json'
    recipe=json.loads(resolved.read_text())
    require(recipe.get('CLOCK_PERIOD')==20,'PD recipe clock period is not 20 ns')
    prefix='/mnt/e/Projects/RISCV-research/'
    rtl=[]
    for value in recipe['VERILOG_FILES']:
        require(value.startswith(prefix),'PD source path is outside the authorized research source')
        rtl.append(ROOT/value.removeprefix(prefix))
    wrapper=next(p for p in rtl if p.name=='soc_asic_top.v')
    wrapper_text=wrapper.read_text()
    for name,value in [('CACHE_CONFIG',0 if args.design=='DM' else 1),('ICACHE_LINE_COUNT',256),
                       ('DCACHE_LINE_COUNT',256),('IMEM_DEPTH',2048),('DMEM_DEPTH',2048)]:
        require(re.search(r'\.'+name+r'\s*\(\s*'+str(value)+r'\s*\)',wrapper_text),f'Frozen wrapper profile mismatch: {name}')
    soc=next(p for p in rtl if p.name=='soc_top.v')
    legacy_fast_hit_absent=False
    for name,value in [('CACHE_FAST_HIT',0),('BRANCH_PREDICT_ENABLE',1),('L0_ENTRIES',8),('CACHE_LINE_WORDS',4),('VICTIM_ENTRIES',4)]:
        explicit=re.search(r'\.'+name+r'\s*\(\s*(\d+)\s*\)',wrapper_text)
        default=re.search(r'parameter\s+(?:integer\s+)?'+name+r'\s*=\s*(\d+)',soc.read_text())
        if name=='CACHE_FAST_HIT' and not explicit and not default:
            # The locked PD snapshot predates the optional FAST_HIT switch.
            # Do not invent a parameter value in the frozen source profile.
            # It is the old baseline view compared against current FAST_HIT=0.
            cache_sources=[p for p in rtl if '/hdl/cache/' in p.as_posix()]
            require(cache_sources and all('FAST_HIT' not in p.read_text() for p in cache_sources),'Unknown legacy cache FAST_HIT behavior')
            legacy_fast_hit_absent=True
            continue
        require(int((explicit or default)[1])==value if explicit or default else False,f'Frozen wrapper/default profile mismatch: {name}')
    source=ROOT/'asic/gls/tb_gls_soc.sv'
    refs=[]
    for name in cfg['refs']:
        with (ROOT/'results'/name).open(newline='') as f:
            reader=csv.DictReader(f)
            require(len(reader.fieldnames or [])==43 and set(reader.fieldnames or [])=={'kernel','config','config_id'}|set(FIELDS),'Reference CSV schema is incomplete or duplicated')
            rr=[r for r in reader if r['config']==args.design]
        for row in rr:
            require(all(row.get(k) is not None and str(row[k]).strip() for k in FIELDS),'Blank reference counter')
            nums={k:int(row[k]) for k in FIELDS}
            require(not invariants(nums) and nums['result_pass']==nums['invariant_pass']==1,'Reference counter invariants/self-check failed')
        table={r['kernel']:r for r in rr}
        require(len(rr)==12 and set(table)==set(KERNELS),'Reference must contain twelve unique kernels')
        refs.append(table)
    require(refs[0]==refs[1],'Independent ASIC reference frames differ')
    manifest=json.loads((ROOT/'results/rtl_manifest.json').read_text())
    inputs={p:sha(ROOT/p) for p in manifest['files']}
    require(inputs==manifest['files'] and len(inputs)==227,'Frozen RTL manifest mismatch')
    executable=Path(args.vsim).resolve()
    require(executable.is_file(),'Missing Questa executable')
    paths=[source,net,resolved,executable,Path(__file__).resolve(),ROOT/'scripts/snapshot_fields.py',ROOT/'results/rtl_manifest.json',ROOT/'asic/gls/saif_to_pins.py']+rtl
    paths += [ROOT/p for p in MODELS]+[ROOT/'results'/n for n in cfg['refs']]+[ROOT/'fw'/f'{k}.hex' for k in KERNELS]
    mapped='OPEN'
    if args.freeze_proof:
        proof=(ROOT/args.freeze_proof).resolve();d=json.loads(proof.read_text())
        require(d.get('status')=='VERIFIED_COUNTER_FREEZE_ALIAS' and d.get('design')==args.design and
                d.get('netlist_sha256')==sha(net) and d.get('expression')==cfg['freeze_expression'] and
                d.get('counter_hold_increment_bridge_verified') is True,'Mapped freeze proof does not match the exact final netlist/counter cone')
        paths.append(proof);mapped='VERIFIED_BOUND_TO_NETLIST'
    if args.run:
        require(mapped!='OPEN','--run requires reviewed mapped counter-freeze bridge receipt')
        require(len(args.liberty)==3 and all((ROOT/p).is_file() for p in args.liberty),'--run requires exactly the standard-cell TT and both SRAM TT liberty files')
        require({p.name for p in args.liberty}=={'sky130_fd_sc_hd__tt_025C_1v80.lib','sky130_sram_1kbyte_1rw1r_32x256_8_TT_1p8V_25C.lib','sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib'},'Wrong power-conversion library/corner filenames')
    paths += [(ROOT/p).resolve() for p in args.liberty]
    for p in paths:inputs[str(p)]=sha(p)
    def unchanged():
        for p,h in inputs.items():require(sha(ROOT/p)==h,f'Input changed: {p}')
    out.mkdir()
    tb=out/'tb_gls_soc_exact_window.sv';tb.write_text(generated_tb(source.read_text(),cfg['freeze_expression']),encoding='ascii',newline='\n')
    capture=out/'power_capture_exact.do';capture.write_text(capture_do(),encoding='ascii',newline='\n')
    compile_do=out/'compile.do'
    compile_do.write_text('onerror {quit -code 1 -f}\nvlib '+library+'\n'+
        'vlog -work '+library+' -timescale 1ns/1ps +define+FUNCTIONAL +define+UNIT_DELAY=#0 -suppress 2892,2902 '+ ' '.join(tcl_path(ROOT/p) for p in MODELS[:2])+'\n'+
        'vlog -work '+library+' -timescale 1ns/1ps '+' '.join(tcl_path(ROOT/p) for p in MODELS[2:])+'\n'+
        'vlog -work '+library+' -timescale 1ns/1ps -suppress 2892 '+tcl_path(net)+'\n'+
        'vlog -work '+library+' -sv +define+GLS_RAM16K '+tcl_path(tb)+'\necho {[PASS] EXACT_WINDOW_PRIVATE_LIBRARY_COMPILED}\nquit -code 0 -f\n',encoding='ascii',newline='\n')
    for k in kernels:
        do=out/f'{k}.do';do.write_text('onerror {quit -code 1 -f}\nvsim -onfinish stop -voptargs={+acc=rn+tb_gls_soc +acc=n+soc_asic_top} -gMEMFILE=fw/'+k+'.hex -gMAX_CYCLES=8000000 '+library+'.tb_gls_soc\nset SAIF '+tcl_path(out/f'{k}.raw.saif')+'\ndo '+tcl_path(capture)+'\nquit -code 0 -f\n',encoding='ascii',newline='\n')
    for p in out.iterdir():inputs[str(p)]=sha(p)
    receipt={'status':'PREPARED_NOT_EXECUTED','created':stamp(),'design':args.design,'pass':args.pass_no,
             'library':library,'netlist':str(net.relative_to(ROOT)),'PD_tag':cfg['tag'],
             'freeze_expression':cfg['freeze_expression'],'mapping_prerequisite':mapped,
             'kernels':kernels,'full_twelve_kernel_matrix':set(kernels)==set(KERNELS),
             'inputs_sha256':inputs,'native_commands':[],'cases':{},'minimum_Windows_free_MiB':args.min_free_mib,
             'wait_for_memory_opt_in':args.wait_for_memory,'memory_waits':[],
             'abort_before_next_native':str((out/'abort_before_next_native').relative_to(ROOT)),
             'timing_period_ps':20000,'power_or_full_LEC_claim':False,'independent_interval_counter':True,
             'profile':{'cache_KiB':4,'RAM_KiB':16,'current_reference_FAST_HIT':0,'frozen_snapshot_FAST_HIT_switch_absent':legacy_fast_hit_absent,'BRANCH_PREDICT_ENABLE':1,'L0_ENTRIES':8,
                        'CACHE_LINE_WORDS':4,'VICTIM_ENTRIES':4,'reference_counter_fields':40,'PD_RTL_sources':len(rtl)}}
    dst=out/'receipt.json'
    def save():dst.write_text(json.dumps(receipt,indent=2)+'\n',encoding='ascii')
    save()
    if not args.run:
        print(json.dumps({'status':receipt['status'],'folder':str(out.relative_to(ROOT)),'mapping':mapped}));return 0
    def native(command,log,sim=False):
        while True:
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
            wait['returned']=stamp();save()
        record={'command':command,'started':stamp(),'Windows_free_MiB':available,'log':str(log.relative_to(ROOT))};receipt['native_commands'].append(record);save()
        with log.open('wb') as f:p=subprocess.run(command,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
        record.update({'completed':stamp(),'native_exit':p.returncode,'log_sha256':sha(log)});save();unchanged()
        require(p.returncode==0,f'Native command failed: {log}')
        return p.returncode
    try:
        receipt['status']='RUNNING_FRESH_GLS_CAPTURE';save()
        native([args.vsim,'-c','-l',str(out/'compile.transcript'),'-wlf',str(out/'compile.wlf'),
                '-do','do '+tcl_path(compile_do)],out/'compile.log')
        text=(out/'compile.log').read_text(errors='replace')
        require('[PASS] EXACT_WINDOW_PRIVATE_LIBRARY_COMPILED' in text and not re.search(r'\*\*\s+(?:Fatal|Error)',text),'Private library compilation failed')
        for k in kernels:
            log=out/f'{k}.log';raw=out/f'{k}.raw.saif';pin=out/f'{k}.pins.saif'
            require(not raw.exists() and not pin.exists(),'Refuse stale SAIF')
            rc=native([args.vsim,'-c','-l',str(out/f'{k}.transcript'),'-wlf',str(out/f'{k}.wlf'),
                       '-do','do '+tcl_path(out/f'{k}.do')],log,True)
            window=inspect_log(log,int(refs[0][k]['mcycle']),rc,k)
            require(window['mcycle']==int(refs[0][k]['mcycle']),'Reference mismatch')
            raw_stats=inspect_saif(raw,window['duration_ps'])
            native([sys.executable,'-B','asic/gls/saif_to_pins.py',str(raw),str(net),str(pin)]+[str((ROOT/p).resolve()) for p in args.liberty],out/f'{k}.pins.log')
            pin_stats=inspect_saif(pin,window['duration_ps'])
            receipt['cases'][k]={'window':window,'raw_saif':raw_stats,'pin_saif':pin_stats,
                                 'reference_minstret':int(refs[0][k]['minstret']),'raw_log_sha256':sha(log)};save()
        unchanged()
        require(set(receipt['cases'])==set(kernels),'Incomplete capture matrix')
        receipt['status']='VERIFIED_EXACT_CAPTURE_SINGLE_PASS' if set(kernels)==set(KERNELS) else 'SINGLE_SCREEN_NOT_RESULT'
        receipt['completed']=stamp();save()
    except BaseException as exc:
        receipt['status']='STOPPED_REQUIRES_INSPECTION';receipt['error']=str(exc);save();raise
    print(json.dumps({'status':receipt['status'],'kernels':len(kernels),'STA_executions':0}));return 0

if __name__=='__main__':raise SystemExit(main())
