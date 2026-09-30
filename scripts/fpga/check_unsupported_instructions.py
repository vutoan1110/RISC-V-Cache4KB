#!/usr/bin/env python3
"""Fail a benchmark when its disassembly contains DIV/REM opcodes."""
import argparse,re,subprocess,sys
from pathlib import Path
BAD=re.compile(r"^\s*[0-9a-f]+:\s+(?:[0-9a-f]+\s+)+(?P<op>divu?|remu?)\b",re.I|re.M)
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("elf",type=Path); ap.add_argument("--objdump",required=True); ap.add_argument("--dump",type=Path); a=ap.parse_args()
 p=subprocess.run([a.objdump,"-d",str(a.elf)],capture_output=True,text=True)
 if p.returncode: print(p.stderr,file=sys.stderr); return 2
 if a.dump: a.dump.write_text(p.stdout,encoding="utf-8")
 hits=sorted(set(m.group("op").lower() for m in BAD.finditer(p.stdout)))
 if hits: print("[FAIL] unsupported instruction(s): "+", ".join(hits)); return 1
 print("[PASS] no DIV/DIVU/REM/REMU instructions"); return 0
if __name__=="__main__": raise SystemExit(main())
