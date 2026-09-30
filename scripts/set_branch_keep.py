# -*- coding: utf-8 -*-
"""Add or remove (* keep *) on the branch enable.

The attribute stops Yosys dissolving that net into the surrounding cone, which
is what made opt_merge's result depend on the port's name. The current port name
is detected from branch.v, so this works under either naming and the paired
experiment stays single-variable.

    python3 set_branch_keep.py on|off
"""
import re
import sys

MODE = sys.argv[1] if len(sys.argv) > 1 else None
if MODE not in ('on', 'off'):
    sys.exit('usage: set_branch_keep.py on|off')

src = open('hdl/branch.v', 'rb').read().decode('utf-8').replace('\r\n', '\n')
m = re.search(r'^\s*(?:\(\* keep \*\)\s*\n)?\s*input\s+(branch(?:_en)?)\s*,',
              src, re.M)
if not m:
    sys.exit('could not find the branch enable port in hdl/branch.v')
PORT = m.group(1)
PAD = ' ' * (len('branch_en      ') - len(PORT))

PLAIN_PORT = "    input             %s%s," % (PORT, PAD)
KEPT_PORT = "    (* keep *)\n" + PLAIN_PORT

PLAIN_CONN = "    .%s%s(valid_e && (instr_e[6:0] == 7'b1100011)) ," % (PORT, PAD)
KEPT_CONN = "    .%s%s(branch_en_kept) ," % (PORT, PAD)

DECL = ("// Synthesis probe: a named, kept net for the branch enable. Without it,\n"
        "// how many identical cells opt_merge finds depends on this port's name.\n"
        "(* keep *) wire branch_en_kept = valid_e && (instr_e[6:0] == 7'b1100011);\n")
ANCHOR = "// --- Execute-stage: check the prediction\n"


def rw(path, subs):
    raw = open(path, 'rb').read()
    crlf = raw.count(b'\r\n')
    t = raw.decode('utf-8').replace('\r\n', '\n')
    for old, new in subs:
        if t.count(old) != 1:
            sys.exit('%s: expected one %r, found %d'
                     % (path, old[:50], t.count(old)))
        t = t.replace(old, new, 1)
    open(path, 'wb').write(
        (t.replace(chr(10), chr(13) + chr(10)) if crlf else t).encode('utf-8'))


if MODE == 'on':
    rw('hdl/branch.v', [(PLAIN_PORT, KEPT_PORT)])
    rw('hdl/datapath.v', [(PLAIN_CONN, KEPT_CONN), (ANCHOR, DECL + ANCHOR)])
else:
    rw('hdl/branch.v', [(KEPT_PORT, PLAIN_PORT)])
    rw('hdl/datapath.v', [(KEPT_CONN, PLAIN_CONN), (DECL + ANCHOR, ANCHOR)])

print('(* keep *) on %s: %s' % (PORT, MODE))
