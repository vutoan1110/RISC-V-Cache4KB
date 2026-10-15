#!/usr/bin/env python3
"""Prove exactly three local GOLD write-buffer unused-A defaults, not full LEC.

The scalar head is an arbitrary Boolean bit and both entries are independent
symbolic bit vectors. No reset, memory initialization, validity, FSM invariant
or reachability premise is used. Four-state X/Z equivalence and the complete
source/frontend/undef bridge remain OPEN.
"""
from __future__ import annotations
import argparse
import ctypes
from ctypes import wintypes as w
import hashlib
import itertools
import json
import os
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
RAW='asic/equiv/lec/gold_flat_r14.il'
MAP='results/lec_source_x_remaining_20261010/remaining_origins.json'
HEAD=r'\u_soc.u_cache_axi_master.wb_head_q'
COMPLEMENT=r'$flatten\u_soc.\u_cache_axi_master.$not$/mnt/e/Projects/RISCV-research/asic/snapshots/rtl_r14/hdl/axi/cache_axi_master.v:357$14892_Y'
NOT_CELL=COMPLEMENT[:-2]
TARGETS={'$procmux$23979':('wb_strb_q',4,95579),'$procmux$23992':('wb_data_q',32,95589),'$procmux$24005':('wb_addr_q',16,95599)}
LIMIT=256*1024*1024
JOB=None

def require(ok,message):
    if not ok:raise RuntimeError(message)

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def memory_cap():
    global JOB
    require(os.name=='nt','UNKNOWN: this bounded native checker requires Windows JobObject enforcement')
    class Basic(ctypes.Structure):
        _fields_=[('ProcessTime',ctypes.c_int64),('JobTime',ctypes.c_int64),('Flags',w.DWORD),('MinWS',ctypes.c_size_t),('MaxWS',ctypes.c_size_t),('Active',w.DWORD),('Affinity',ctypes.c_size_t),('Priority',w.DWORD),('Scheduling',w.DWORD)]
    class IO(ctypes.Structure):
        _fields_=[(n,ctypes.c_uint64) for n in ('ReadOps','WriteOps','OtherOps','ReadBytes','WriteBytes','OtherBytes')]
    class Extended(ctypes.Structure):
        _fields_=[('Basic',Basic),('IO',IO),('ProcessLimit',ctypes.c_size_t),('JobLimit',ctypes.c_size_t),('PeakProcess',ctypes.c_size_t),('PeakJob',ctypes.c_size_t)]
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.CreateJobObjectW.argtypes=[ctypes.c_void_p,w.LPCWSTR];k.CreateJobObjectW.restype=w.HANDLE
    k.SetInformationJobObject.argtypes=[w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD];k.SetInformationJobObject.restype=w.BOOL
    k.AssignProcessToJobObject.argtypes=[w.HANDLE,w.HANDLE];k.AssignProcessToJobObject.restype=w.BOOL
    k.GetCurrentProcess.restype=w.HANDLE
    JOB=k.CreateJobObjectW(None,None);info=Extended();info.Basic.Flags=0x100;info.ProcessLimit=LIMIT
    require(JOB and k.SetInformationJobObject(JOB,9,ctypes.byref(info),ctypes.sizeof(info)) and k.AssignProcessToJobObject(JOB,k.GetCurrentProcess()),'UNKNOWN: 256 MiB hard process limit not enforced')
    return 'Windows per-process JobObject commit limit=256MiB'

def peak_memory():
    class Counters(ctypes.Structure):
        _fields_=[('cb',w.DWORD),('PageFaultCount',w.DWORD)]+[(n,ctypes.c_size_t) for n in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    state=Counters();state.cb=ctypes.sizeof(state)
    k=ctypes.WinDLL('kernel32');k.GetCurrentProcess.restype=w.HANDLE
    q=ctypes.WinDLL('psapi').GetProcessMemoryInfo;q.argtypes=[w.HANDLE,ctypes.c_void_p,w.DWORD];q.restype=w.BOOL
    require(q(k.GetCurrentProcess(),ctypes.byref(state),state.cb),'Memory probe failed')
    require(state.PeakPagefileUsage<=LIMIT,'UNKNOWN: memory bound exceeded')
    return {'peak_working_set_bytes':state.PeakWorkingSetSize,'peak_commit_bytes':state.PeakPagefileUsage}

def parse_cell(lines,start):
    first=lines[0].strip().split()
    require(len(first)==3 and first[0]=='cell','Malformed exact cell header')
    cell={'name':first[2],'type':first[1],'line':start,'parameters':{},'ports':{},'raw':'\n'.join(lines)+'\n'}
    for offset,line in enumerate(lines[1:],1):
        text=line.strip()
        if text=='end':continue
        m=re.fullmatch(r'(parameter|connect) (\\\S+) (.+)',text)
        require(m is not None,'Unsupported/malformed relevant cell statement')
        dst=cell['parameters'] if m[1]=='parameter' else cell['ports']
        require(m[2] not in dst,'Duplicate relevant parameter/port')
        dst[m[2]]=m[3] if m[1]=='parameter' else {'expression':m[3],'line':start+offset}
    return cell

def read_raw(path):
    targets=set(TARGETS)|{NOT_CELL};cells={};wires={};driver_counts={HEAD:0,COMPLEMENT:0};aliases=[]
    current=None;start=0;modules=[];module=None
    with Path(path).open(encoding='ascii') as f:
        for number,line in enumerate(f,1):
            require(len(line)<65536,'Oversized RTLIL line')
            text=line.strip()
            if current is not None:
                if current['retain']:current['lines'].append(line.rstrip('\n'))
                if text.startswith('connect '):
                    tokens=text.split(maxsplit=2)
                    if len(tokens)==3 and tokens[1] in (r'\Y',r'\Q',r'\X') and tokens[2] in driver_counts:driver_counts[tokens[2]]+=1
                if text=='end':
                    if current['retain']:
                        c=parse_cell(current['lines'],start);require(c['name'] not in cells,'Duplicate target cell');cells[c['name']]=c
                    current=None
                continue
            if text.startswith('module '):
                require(module is None,'Nested module');module=text.split()[1];modules.append(module)
            elif text.startswith('cell '):
                tokens=text.split();require(len(tokens)==3 and module==r'\soc_asic_top','Unexpected module/cell header')
                current={'retain':tokens[2] in targets,'lines':[line.rstrip('\n')]};start=number
            elif text.startswith('wire '):
                tokens=text.split();name=tokens[-1]
                if name==HEAD or name==COMPLEMENT or any(name==f'\\u_soc.u_cache_axi_master.{role}[{i}]' for role,_,_ in TARGETS.values() for i in (0,1)):
                    require(name not in wires,'Duplicate relevant wire');width=int(tokens[tokens.index('width')+1]) if 'width' in tokens else 1
                    wires[name]={'width':width,'line':number,'raw':text}
            elif text.startswith('connect '):
                tokens=text.split(maxsplit=2)
                if tokens[1] in driver_counts:aliases.append({'line':number,'raw':text})
            elif text=='end':module=None
    expected_modules=[r'\sky130_sram_1kbyte_1rw1r_32x256_8',r'\sky130_sram_2kbyte_1rw1r_32x512_8',r'\soc_asic_top']
    require(current is None and module is None and modules==expected_modules,'Incomplete/unexpected flattened raw IR')
    require(set(cells)==targets and not aliases and all(driver_counts[k]==1 for k in driver_counts),'Missing/ambiguous actual selector/target drivers')
    return cells,wires,driver_counts

def contract_source(path):
    text=Path(path).read_text(encoding='ascii')
    patterns={'depth':r'localparam\s+integer\s+WB_DEPTH\s*=\s*2\s*;', 'address_width':r'localparam\s+integer\s+WB_AW\s*=\s*16\s*;',
      'head':r'reg\s+wb_head_q\s*;', 'address_array':r'reg\s*\[WB_AW-1:0\]\s*wb_addr_q\s*\[0:WB_DEPTH-1\]\s*;',
      'data_array':r'reg\s*\[31:0\]\s*wb_data_q\s*\[0:WB_DEPTH-1\]\s*;', 'strobe_array':r'reg\s*\[3:0\]\s*wb_strb_q\s*\[0:WB_DEPTH-1\]\s*;',
      'address_read':r'addr_q\s*<=\s*\{16\x27h0000,\s*wb_addr_q\[wb_head_q\]\[WB_AW-1:2\],\s*2\x27b00\}\s*;',
      'data_read':r'wdata_q\s*<=\s*wb_data_q\[wb_head_q\]\s*;', 'strobe_read':r'wstrb_q\s*<=\s*wb_strb_q\[wb_head_q\]\s*;'}
    bound={}
    for name,pattern in patterns.items():
        matches=list(re.finditer(pattern,text));require(len(matches)==1,'Source contract missing/ambiguous: '+name)
        m=matches[0];bound[name]={'line':text.count('\n',0,m.start())+1,'statement':m[0]}
    return bound

def concat(expression):
    match=re.fullmatch(r'\{ (\S+) (\S+) \}',expression)
    require(match is not None,'Unsupported two-word raw concatenation')
    return list(match.groups()) # RTLIL writes MSB word first.

def prove(cell,wires,not_cell):
    role,width,origin=TARGETS[cell['name']]
    require(cell['type']=='$pmux' and cell['parameters']=={r'\S_WIDTH':'2',r'\WIDTH':str(width)} and set(cell['ports'])=={r'\A',r'\B',r'\S',r'\Y'},'Unsupported actual PMUX interface')
    require(cell['ports'][r'\A']=={'expression':f"{width}'x",'line':origin},'Wrong exact original unknown-A line')
    require(wires[HEAD]['width']==wires[COMPLEMENT]['width']==1,'Head/complement is not scalar')
    require(not_cell['type']=='$not' and not_cell['parameters']=={r'\A_SIGNED':'0',r'\A_WIDTH':'1',r'\Y_WIDTH':'1'} and set(not_cell['ports'])=={r'\A',r'\Y'} and not_cell['ports'][r'\A']['expression']==HEAD and not_cell['ports'][r'\Y']['expression']==COMPLEMENT,'Actual complement is not NOT of the same scalar head')
    entries=[f'\\u_soc.u_cache_axi_master.{role}[{i}]' for i in (0,1)]
    require(all(wires[e]['width']==width for e in entries),'Actual entry width mismatch')
    selectors=concat(cell['ports'][r'\S']['expression']);data=concat(cell['ports'][r'\B']['expression'])
    require(selectors==[COMPLEMENT,HEAD] and data==entries,'Raw selector/data order does not match the exact source array read')
    table=[];evaluations=0
    # Product proof: each bit is only a wire selection. Enumerating every
    # H,A,D0,D1 assignment for every output bit covers arbitrary whole vectors.
    for head in (0,1):
        values={HEAD:head,COMPLEMENT:head^1}
        bits=[values[x] for x in reversed(selectors)]
        require(sum(bits)==1,'Default or multihot reachable for free head')
        index=bits.index(1);selected=list(reversed(data))[index]
        require(selected==entries[head],'Wrong exact source data selection')
        for bit in range(width):
            for a,d0,d1 in itertools.product((0,1),repeat=3):
                source={entries[0]:d0,entries[1]:d1};actual=source[selected] if sum(bits)==1 else a
                require(actual==(d0,d1)[head],'Symbolic data/default influence detected');evaluations+=1
        table.append({'head':head,'selector_MSB_first':bits[::-1],'packed_selector':bits[0]|(bits[1]<<1),'selected_word_LSB_index':index,'selected_entry':selected,'unused_A':True})
    return {'status':'PROVED_LOCAL_TWO_VALUED_SYMBOLIC_UNUSED_A','original_raw_pmux':cell,'source_array':role,'width':width,'truth_table':table,'bit_product_evaluations':evaluations,'free_default_and_array_bits_per_bit':3,'head_codes_exhaustive':2}

def semantic_faults(cell):
    role,width,_=TARGETS[cell['name']];original=cell['raw'];s=cell['ports'][r'\S']['expression'];b=cell['ports'][r'\B']['expression']
    entries=concat(b)
    mutants={
      'missing_complement':original.replace('connect \\S '+s,"connect \\S { 1'0 "+HEAD+' }'),
      'duplicated_head':original.replace('connect \\S '+s,'connect \\S { '+HEAD+' '+HEAD+' }'),
      'selector_order_swapped':original.replace('connect \\S '+s,'connect \\S { '+HEAD+' '+COMPLEMENT+' }'),
      'data_order_swapped':original.replace('connect \\B '+b,'connect \\B { '+entries[1]+' '+entries[0]+' }')}
    controls=[]
    for label,raw in mutants.items():
        require(raw!=original,'Fault did not alter actual raw PMUX')
        mutant=parse_cell(raw.rstrip().splitlines(),cell['line'])
        sels=concat(mutant['ports'][r'\S']['expression']);words=concat(mutant['ports'][r'\B']['expression'])
        witness=None
        for head,a,d0,d1 in itertools.product((0,1),repeat=4):
            vals={HEAD:head,COMPLEMENT:head^1,"1'0":0};bits=[vals[x] for x in sels[::-1]]
            expected=(d0,d1)[head];data_values={entries[0]:d0,entries[1]:d1}
            actual=a if not sum(bits) else (data_values[words[::-1][bits.index(1)]] if sum(bits)==1 else 'MULTIHOT')
            if not sum(bits) or sum(bits)>1 or actual!=expected:
                witness={'head':head,'free_A_bit':a,'entry0_bit':d0,'entry1_bit':d1,'selector_MSB_first':bits[::-1],'actual_bit':actual,'source_expected_bit':expected,'default_selected':sum(bits)==0,'multihot':sum(bits)>1};break
        require(witness is not None,'Semantic fault produced no actual Boolean witness')
        controls.append({'fault':label,'status':'REJECTED_WITH_ACTUAL_RAW_WITNESS','mutated_raw_pmux':raw,'witness':witness})
    return controls

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    out=(ROOT/args.out).resolve();require(out.is_relative_to(ROOT/'results') and not out.exists(),'New result path under results required')
    enforcement=memory_cap()
    paths=[RAW,MAP,'asic/equiv/lec/gold_flat_r14.ys','asic/equiv/lec/gold_god_r14_aig.ys','hdl/axi/cache_axi_master.v','asic/snapshots/rtl_r14/hdl/axi/cache_axi_master.v','results/rtl_manifest.json',str(Path(__file__).relative_to(ROOT))]
    hashes={p:sha(ROOT/p) for p in paths}
    manifest=json.loads((ROOT/'results/rtl_manifest.json').read_text());require(manifest['count']==227 and manifest['files']['hdl/axi/cache_axi_master.v']==hashes['hdl/axi/cache_axi_master.v'],'Current manifest/source guard mismatch')
    require(hashes['hdl/axi/cache_axi_master.v']==hashes['asic/snapshots/rtl_r14/hdl/axi/cache_axi_master.v'],'Current and signed AXI source differ')
    mapping=json.loads((ROOT/MAP).read_text());candidates=[r for r in mapping['remaining_origins'] if r['group']=='AXI_write_buffer_read_default']
    require(len(candidates)==3 and {r['cell'] for r in candidates}==set(TARGETS) and mapping['input_sha256'][RAW]==hashes[RAW],'Wrong original remaining-map/raw input binding')
    sources={p:contract_source(ROOT/p) for p in ('hdl/axi/cache_axi_master.v','asic/snapshots/rtl_r14/hdl/axi/cache_axi_master.v')}
    cells,wires,drivers=read_raw(ROOT/RAW)
    targets=[];faults=[]
    for row in candidates:
        cell=cells[row['cell']]
        require(cell['ports'][r'\A']['line']==row['IR_line'] and cell['line']==row['actual_cell']['line'] and cell['parameters']==row['actual_cell']['parameters'] and cell['ports']==row['actual_cell']['ports'],'Classifier target disagrees with fresh raw parser')
        targets.append(prove(cell,wires,cells[NOT_CELL]));faults.append({'cell':cell['name'],'controls':semantic_faults(cell)})
    require(sum(t['bit_product_evaluations'] for t in targets)==832 and len(faults)==3,'Incomplete exact obligation set')
    require(all(sha(ROOT/p)==h for p,h in hashes.items()),'Frozen inputs changed during check')
    result={'status':'PROVED_LOCAL_AXI_WB_THREE_UNUSED_A_DEFAULTS_ONLY','full_sequential_LEC':'OPEN','whole_source_undefined_abstraction':'OPEN','four_state_X_or_Z_behavior_equivalence':'NOT_CLAIMED',
            'hypothesis':'Each actual scalar wb_head_q/not(wb_head_q) decoder selects exactly one of two independent array words; the original PMUX A is unused',
            'input_sha256':hashes,'source_contracts':sources,'actual_scalar_wires':wires,'actual_selector_output_driver_counts':drivers,'actual_complement_cell':cells[NOT_CELL],
            'targets':targets,'undefined_A_connect_lines_closed_locally':3,'output_bits_structurally_checked':52,'total_bit_product_evaluations':832,
            'state_or_initialization_premises':[],'selected_array_data':'Both entries independent symbolic bit vectors, not assumed zero or defined after reset',
            'whole_Y_definedness':'NOT_CLAIMED; selected data may be unreset/unknown, and all other source-X origins remain separate',
            'actual_raw_semantic_negative_controls':faults,'negative_control_count':12,'memory_enforcement':enforcement,'frontend_solver_simulator_executions':0}
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='ascii') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'targets':3,'negative_controls':12,'bit_evaluations':832,'memory':peak_memory(),'output_sha256':sha(out)}))
    return 0

if __name__=='__main__':raise SystemExit(main())
