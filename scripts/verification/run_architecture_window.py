"""Verify the complete 1 MiB architecture adapter without changing frozen RTL.

The generated adapter corrects only six [18:2] memory indexes to [19:2].
Tests retain both current-source provenance and the adapter delta separately.
Existing ACT4 programs/signatures are replayed twice; an upper-half data and
instruction program proves the larger window and fails on the original TB.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VSIM = "C:/questasim64_2024.1/win64/vsim.exe"
BAD = re.compile(r"\*\*\s+(?:Error|Fatal):|\[FAIL\]|^#\s*Errors:\s*[1-9]", re.M|re.I)
PASS = re.compile(r"\[PASS\] Signature harness\s+(\S+)\s+retirements=(\d+)\s+cycles=(\d+)")
CORE = ["hdl/alu.v","hdl/aludec.v","hdl/branch.v","hdl/predictor/bht_2bit.v",
        "hdl/controller.v","hdl/datapath.v","hdl/extend.v","hdl/hazard_unit.v",
        "hdl/maindec.v","hdl/regfile.v","hdl/riscv_core.v","hdl/riscv_core_native.v"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def js(path, data):
    path.write_text(json.dumps(data,indent=2)+"\n",encoding="ascii")


def run(do, log):
    with log.open("w",encoding="utf-8") as f:
        rc = subprocess.run([VSIM,"-c","-do",do],cwd=ROOT,stdout=f,
                            stderr=subprocess.STDOUT,timeout=240).returncode
    return rc,log.read_text(encoding="utf-8",errors="replace")


def simulate(lib, hexf, sym, sig, log, cycles=2000000):
    do = (f"onerror {{quit -code 1 -f}}; vsim -onfinish stop -voptargs=+acc {lib}.tb_architecture_signature "
          f"+HEX={hexf.relative_to(ROOT).as_posix()} +SIGNATURE={sig.relative_to(ROOT).as_posix()} "
          f"+SIG_BEGIN={sym['begin_signature']:08x} +SIG_END={sym['end_signature']:08x} "
          f"+TOHOST_ADDR={sym['tohost']:08x} +MAX_CYCLES={cycles}; run -all; quit -code 0 -f")
    rc,txt = run(do,log)
    m = PASS.search(txt)
    if rc or BAD.search(txt) or not m or not sig.is_file():
        raise RuntimeError(f"Architecture simulation failed: {log.name}")
    return {"finish":m[1],"retirements":int(m[2]),"cycles":int(m[3]),"signature_sha256":sha(sig)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run",action="store_true")
    ap.add_argument("--tag",default="architecture_window_20261009")
    args=ap.parse_args()
    if not re.fullmatch(r"[a-z0-9_]+",args.tag):
        ap.error("invalid tag")
    out=ROOT/"results"/args.tag
    if out.exists():
        raise RuntimeError("Evidence directory already exists; choose a new tag")
    subprocess.run(["python","scripts/rtl_manifest.py","--check"],cwd=ROOT,
                   check=True,stdout=subprocess.PIPE)
    src=ROOT/"tb/architecture_signature_tb.sv"
    old=src.read_text(encoding="utf-8")
    if old.count("[18:2]") != 6:
        raise RuntimeError("Unexpected original memory adapter; inspect instead of patching")
    out.mkdir()
    adapter=out/"architecture_signature_tb.sv"
    adapter.write_text(old.replace("[18:2]","[19:2]"),encoding="ascii")
    spec=importlib.util.spec_from_file_location("prog",ROOT/"verification/uvm/seq/gen_soc_periph_irq.py")
    gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
    words=[gen.lui(5,1),gen.addi(6,0,0x11),gen.sw(6,5,0),gen.lui(7,0x81),
           gen.addi(6,0,0x22),gen.sw(6,7,0),gen.lw(10,5,0),gen.lw(11,7,0),
           gen.sw(10,7,8),gen.sw(11,7,12),gen.lui(5,0x90),0x000280e7,
           gen.sw(12,7,16),gen.HALT]
    high=out/"upper_half.hex"
    high.write_text("".join(f"{w:08x}\n" for w in words)+
                    f"@{0x90000//4:x}\n{gen.addi(12,0,0x33):08x}\n00008067\n",encoding="ascii")
    expected="00000022\n00000013\n00000011\n00000022\n00000033\n"
    sym_high={"begin_signature":0x81000,"end_signature":0x81014,"tohost":0xffffffff}
    images=ROOT/"verification/results/act4/images"
    history=ROOT/"verification/results/act4/dut_p1"
    suite=json.loads((history/"summary.json").read_text())
    if suite["passed"] != 43 or len(suite["results"]) != 43:
        raise RuntimeError("Existing ACT4 baseline must contain all43 passes")
    inputs={p.relative_to(ROOT).as_posix():sha(p) for p in [src,Path(__file__),history/"summary.json"]}
    inputs.update({p:sha(ROOT/p) for p in json.loads((ROOT/"results/rtl_manifest.json").read_text())["files"]})
    for item in suite["results"]:
        tid="__".join(Path(item["test"]).with_suffix("").parts)
        for p in (images/f"{tid}.hex",images/f"{tid}.sym.json",history/"signatures"/f"{tid}.signature"):
            inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    receipt={"status":"PREPARED","created":datetime.now().astimezone().isoformat(),"inputs":inputs,
             "adapter_delta":"six [18:2] -> [19:2] indexes; frozen source unchanged",
             "adapter_sha256":sha(adapter),"suite_cases":43,"upper_half_program_sha256":sha(high)}
    js(out/"verification.json",receipt)
    if not args.run:
        print("PREPARED: 43 ACT4 cases + upper-half data/instruction case, twice, original-adapter negative control")
        return 0
    pairs=[]
    for n in (1,2):
        lib=f"work_{args.tag}_p{n}"
        compile_do=out/f"compile_p{n}.do"
        compile_do.write_text(f"onerror {{quit -code 1 -f}}\nvlib {lib}\nvlog -sv -work {lib} "+
                              " ".join(CORE)+f" {adapter.relative_to(ROOT).as_posix()}\n"
                              "echo {[PASS] Architecture adapter compile}\nquit -code 0 -f\n",encoding="ascii")
        rc,txt=run(f"do {compile_do.relative_to(ROOT).as_posix()}",out/f"compile_p{n}.log")
        if rc or BAD.search(txt) or "[PASS] Architecture adapter compile" not in txt:
            raise RuntimeError(f"Architecture compile failed p{n}")
        sig=out/f"upper_half_p{n}.signature"
        result=simulate(lib,high,sym_high,sig,out/f"upper_half_p{n}.log",10000)
        if sig.read_text().lower() != expected:
            raise RuntimeError("Upper-half data/instruction signature mismatch")
        results={"upper_half":result}
        for i,item in enumerate(suite["results"],1):
            tid="__".join(Path(item["test"]).with_suffix("").parts)
            sym=json.loads((images/f"{tid}.sym.json").read_text())
            sig=out/f"{tid}_p{n}.signature"
            result=simulate(lib,images/f"{tid}.hex",sym,sig,out/f"{tid}_p{n}.log")
            if sig.read_bytes() != (history/"signatures"/f"{tid}.signature").read_bytes():
                raise RuntimeError(f"ACT4 signature differs from baseline: {tid}")
            for field in ("finish","retirements","cycles"):
                if result[field] != item[field]:
                    raise RuntimeError(f"ACT4 {field} changed: {tid}")
            results[tid]=result
            print(f"[PASS] p{n} {i}/43 {tid}",flush=True)
        pairs.append(results)
        js(out/f"measurements_p{n}.json",results)
    neg_lib=f"work_{args.tag}_original"
    do=f"onerror {{quit -code 1 -f}}; vlib {neg_lib}; vlog -sv -work {neg_lib} "+" ".join(CORE)+" tb/architecture_signature_tb.sv; quit -code 0 -f"
    rc,txt=run(do,out/"negative_compile.log")
    if rc or BAD.search(txt):
        raise RuntimeError("Original-adapter negative control failed to compile")
    try:
        simulate(neg_lib,high,sym_high,out/"negative.signature",out/"negative.log",10000)
    except RuntimeError:
        txt=(out/"negative.log").read_text()
        if "signature test timeout" not in txt:
            raise RuntimeError("Negative control failed for an unexpected cause")
    else:
        raise RuntimeError("Original 512KiB alias was not detected")
    if pairs[0] != pairs[1]:
        raise RuntimeError("Independent architecture passes differ")
    if any(sha(ROOT/p) != digest for p,digest in inputs.items()):
        raise RuntimeError("Frozen source or baseline input changed")
    receipt.update(status="VERIFIED_TWO_PASSES",paired_cases=44,act4_signatures_equal_baseline=43,
                   original_alias_negative_control="EXPECTED_TIMEOUT",
                   artifacts={p.relative_to(ROOT).as_posix():sha(p) for p in out.iterdir()
                              if p.is_file() and p.name != "verification.json"},
                   completed=datetime.now().astimezone().isoformat())
    js(out/"verification.json",receipt)
    print("[VERIFIED] 43 ACT4 + upper-half case twice; signatures/counters identical; old alias caught")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
