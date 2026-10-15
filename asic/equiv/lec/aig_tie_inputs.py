"""2026-10-13: tie selected primary inputs of a binary AIGER file to constant 0, keeping every input and output (same
interface, same order), so the result can be mitered against the original with ABC &miter.
The inputs to tie are those whose symbol is NOT in the reference AIGER's input symbol table (the X / undriven sources
that `setundef -undriven -expose` added), or those matching --name-prefix.
usage: python aig_tie_inputs.py in.aig out.aig --ref reference.aig | --name-prefix PREFIX"""
import sys


def read(path):
    d = open(path, "rb").read()
    nl = d.index(b"\n")
    hdr = d[:nl].split()
    if hdr[0] != b"aig":
        sys.exit("binary AIGER expected")
    M, I, L, O, A = map(int, hdr[1:6])
    if L:
        sys.exit("latches not supported")
    pos = nl + 1
    outs = []
    for _ in range(O):
        e = d.index(b"\n", pos)
        outs.append(int(d[pos:e]))
        pos = e + 1
    ands = []
    for k in range(A):
        deltas = []
        for _ in range(2):
            x, sh = 0, 0
            while True:
                b = d[pos]
                pos += 1
                x |= (b & 0x7F) << sh
                sh += 7
                if not b & 0x80:
                    break
            deltas.append(x)
        lhs = 2 * (I + k + 1)
        r0 = lhs - deltas[0]
        r1 = r0 - deltas[1]
        ands.append((lhs, r0, r1))
    rest = d[pos:]
    syms = {}
    for line in rest.split(b"\n"):
        if line[:1] == b"i" and b" " in line:
            h, _, n = line.partition(b" ")
            if h[1:].isdigit():
                syms[int(h[1:])] = n.decode()
    return M, I, O, A, outs, ands, rest, syms


def enc(x):
    out = bytearray()
    while x & ~0x7F:
        out.append((x & 0x7F) | 0x80)
        x >>= 7
    out.append(x)
    return bytes(out)


src, dst = sys.argv[1], sys.argv[2]
M, I, O, A, outs, ands, rest, syms = read(src)
if "--ref" in sys.argv:
    # write_aiger gives the exposed undefined sources no symbol and numbers them after every input of the reference;
    # require that every reference input keeps its index and symbol, then tie exactly the inputs beyond them
    Ir, ref_syms = (lambda r: (r[1], r[7]))(read(sys.argv[sys.argv.index("--ref") + 1]))
    bad = [k for k, n in ref_syms.items() if syms.get(k) != n]
    if bad or I < Ir:
        sys.exit("reference inputs moved or renamed: %s" % bad[:5])
    tie = set(range(Ir, I))
    if any(k in syms for k in tie):
        sys.exit("an input beyond the reference has a symbol; refusing to tie it")
else:
    pre = sys.argv[sys.argv.index("--name-prefix") + 1]
    tie = {k for k, n in syms.items() if n.startswith(pre)}
tie_vars = {k + 1 for k in tie}                   # input k is variable k+1


def sub(lit):
    v = lit >> 1
    return (lit & 1) if v in tie_vars else lit    # literal 2v -> 0, 2v+1 -> 1


body = bytearray()
for lhs, r0, r1 in ands:
    a, b = sub(r0), sub(r1)
    if a < b:
        a, b = b, a
    body += enc(lhs - a) + enc(a - b)
header = b"aig %d %d 0 %d %d\n" % (M, I, O, A)
out = header + b"".join(b"%d\n" % sub(o) for o in outs) + bytes(body) + rest
open(dst, "wb").write(out)
print("tied %d of %d inputs to 0 (input indices %s..%s; %d ANDs, %d outputs)" % (len(tie), I, min(tie, default=None),
      max(tie, default=None), A, O))
