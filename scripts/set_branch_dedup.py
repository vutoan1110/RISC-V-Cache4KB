# -*- coding: utf-8 -*-
"""Connect the branch unit to is_branch_e instead of recomputing the condition.

datapath.v computes valid_e && (instr_e[6:0] == 7'b1100011) in two places: once
as is_branch_e, and once inline at the branch instance. They are the same
expression, so the second is a duplicate that opt_merge has to find -- and
opt_merge is the pass whose result turned out to depend on signal naming.

The port name is detected from branch.v so this works under either naming.

    python3 set_branch_dedup.py on|off
"""
import re
import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else None
if MODE not in ('on', 'off'):
    sys.exit('usage: set_branch_dedup.py on|off')

src = open('hdl/branch.v', 'rb').read().decode('utf-8').replace('\r\n', '\n')
m = re.search(r'^\s*(?:\(\* keep \*\)\s*\n)?\s*input\s+(branch(?:_en)?)\s*,',
              src, re.M)
if not m:
    sys.exit('could not find the branch enable port in hdl/branch.v')
PORT = m.group(1)
PAD = ' ' * (len('branch_en      ') - len(PORT))

DUP = "    .%s%s(valid_e && (instr_e[6:0] == 7'b1100011)) ," % (PORT, PAD)
DEDUP = "    .%s%s(is_branch_e) ," % (PORT, PAD)

path = 'hdl/datapath.v'
raw = open(path, 'rb').read()
crlf = raw.count(b'\r\n')
t = raw.decode('utf-8').replace('\r\n', '\n')

old, new = (DUP, DEDUP) if MODE == 'on' else (DEDUP, DUP)
if t.count(new) == 1 and t.count(old) == 0:
    print('dedup already %s' % MODE)
    sys.exit(0)
if t.count(old) != 1:
    sys.exit('expected one %r, found %d' % (old, t.count(old)))

t = t.replace(old, new, 1)
open(path, 'wb').write(
    (t.replace(chr(10), chr(13) + chr(10)) if crlf else t).encode('utf-8'))
print('dedup %s (port %s)' % (MODE, PORT))
