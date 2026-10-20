"""R16: add --fast (CACHE_FAST_HIT=1) to the three measurement runners. Default behaviour is byte-for-byte the old
vsim command: the generic is only passed when --fast is given (the R15-compiled libraries have no such parameter).
    python scripts/r16_fasthit/add_fast_option.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def edit(rel, pairs):
    p = ROOT / rel
    s = p.read_text(encoding="utf-8")
    for old, new in pairs:
        assert s.count(old) == 1, (rel, s.count(old), old)
        s = s.replace(old, new)
    p.write_text(s, encoding="utf-8", newline="\n")
    print("patched", rel)


edit("scripts/run_ablation.py", [
    ('    ap.add_argument("--lib", default="work")\n',
     '    ap.add_argument("--lib", default="work")\n'
     '    # R16 (review M1): answer main-array hits in ST_LOOKUP (CACHE_FAST_HIT=1); configurations 1-5 only.\n'
     '    ap.add_argument("--fast", action="store_true")\n'),
    ('            do = ("vsim -onfinish stop -gCACHE_CONFIG=%d -gMEMFILE=%s "',
     '            do = ("vsim -onfinish stop %s-gCACHE_CONFIG=%d -gMEMFILE=%s "'),
    ('                  % (cfg, hexfile, args.lines, args.lines, args.l0, args.bp,',
     '                  % ("-gCACHE_FAST_HIT=1 " if args.fast else "", cfg, hexfile, args.lines, args.lines, args.l0, args.bp,'),
])
edit("scripts/run_coremark.py", [
    ('ap.add_argument("--lib", default="work")\n',
     'ap.add_argument("--lib", default="work")\n'
     '# R16 (review M1): answer main-array hits in ST_LOOKUP (CACHE_FAST_HIT=1); configurations 1-5 only.\n'
     'ap.add_argument("--fast", action="store_true")\n'),
    ('    log = log_dir / ("coremark_%s_lc%d.log" % (name, args.lines))\n',
     '    log = log_dir / ("coremark_%s_lc%d%s.log" % (name, args.lines, "_fast" if args.fast else ""))\n'),
    ('    do = ("vsim -onfinish stop -gCACHE_CONFIG=%d -gMEMFILE=fw/coremark.hex "',
     '    do = ("vsim -onfinish stop %s-gCACHE_CONFIG=%d -gMEMFILE=fw/coremark.hex "'),
    ('          % (cfg, args.lines, args.lines, args.l0, args.imem, args.dmem,\n             args.lib, args.max_cycles))',
     '          % ("-gCACHE_FAST_HIT=1 " if args.fast else "", cfg, args.lines, args.lines, args.l0, args.imem, args.dmem,\n'
     '             args.lib, args.max_cycles))'),
])
edit("scripts/run_crossval.py", [
    ('    ap.add_argument("--lib", default="work")\n',
     '    ap.add_argument("--lib", default="work")\n'
     '    # R16 (review M1): answer main-array hits in ST_LOOKUP (CACHE_FAST_HIT=1); hit/miss must still match the model.\n'
     '    ap.add_argument("--fast", action="store_true")\n'),
    ('            do = ("vsim -onfinish stop -voptargs=+acc -gCACHE_CONFIG=%d "',
     '            do = ("vsim -onfinish stop -voptargs=+acc %s-gCACHE_CONFIG=%d "'),
    ('                  % (cfg, args.lines, args.lines, hexfile, args.lib, kern, MAX_CYCLES))',
     '                  % ("-gCACHE_FAST_HIT=1 " if args.fast else "", cfg, args.lines, args.lines, hexfile, args.lib, kern,\n'
     '                     MAX_CYCLES))'),
])
