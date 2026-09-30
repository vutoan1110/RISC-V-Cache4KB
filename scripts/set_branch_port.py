# -*- coding: utf-8 -*-
"""Flip the branch module's port between branch_en and branch.

Used for paired synthesis experiments: the same logic under two names, so the
naming sensitivity of the technology mapper can be measured under each area
setting rather than argued about. Column alignment is preserved in both
directions so that nothing but the identifier differs.

    python set_branch_port.py branch_en    # linted name, no shadow
    python set_branch_port.py branch       # original name, shadows the module
"""
import sys

WANT = sys.argv[1] if len(sys.argv) > 1 else None
if WANT not in ('branch', 'branch_en'):
    sys.exit('usage: set_branch_port.py branch|branch_en')

# (file, line-with-branch, line-with-branch_en)
FORMS = [
    ('hdl/branch.v',
     "    input             branch         ,",
     "    input             branch_en      ,"),
    ('hdl/branch.v',
     "always @(branch, funct3, reg1, reg2) begin",
     "always @(branch_en, funct3, reg1, reg2) begin"),
    ('hdl/branch.v',
     "    if (branch) begin",
     "    if (branch_en) begin"),
    ('hdl/datapath.v',
     "    .branch         (valid_e && (instr_e[6:0] == 7'b1100011)) ,",
     "    .branch_en      (valid_e && (instr_e[6:0] == 7'b1100011)) ,"),
]

texts = {}
for path, a, b in FORMS:
    if path not in texts:
        raw = open(path, 'rb').read()
        texts[path] = [raw.count(b'\r\n'),
                       raw.decode('utf-8').replace('\r\n', '\n')]

changed = already = 0
for path, a, b in FORMS:
    old, new = (b, a) if WANT == 'branch' else (a, b)
    t = texts[path][1]
    if t.count(new) == 1 and t.count(old) == 0:
        already += 1
        continue
    if t.count(old) != 1:
        sys.exit('%s: expected exactly one %r, found %d'
                 % (path, old, t.count(old)))
    texts[path][1] = t.replace(old, new, 1)
    changed += 1

for path, (crlf, t) in texts.items():
    open(path, 'wb').write(
        (t.replace(chr(10), chr(13) + chr(10)) if crlf else t).encode('utf-8'))

print('port is now %r (%d rewritten, %d already correct)'
      % (WANT, changed, already))
