"""R16: a FAST_HIT mode for the M1/M2 sweep (run_m2_sweep.py --fast) and per-prefix compile scripts.
--fast: CACHE_FAST_HIT=1, libraries work_m2f_<k> (compiled from the R16 hdl/ by compile_m2f_<k>.do), outputs
results/m2/sweep_fast_p<pass>.csv and logs_fast_p<pass>/, DM points (CACHE_CONFIG 0, no FAST variant) skipped.
Without --fast the vsim command and every output name are exactly as before.
    python scripts/m2/add_fast_mode.py
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


edit("scripts/m2/run_m2_sweep.py", [
    ('OUT = ROOT / "results" / "m2"\n',
     'OUT = ROOT / "results" / "m2"\n'
     '# R16 --fast: CACHE_FAST_HIT=1 on the DSE / N-way points, own libraries and output names (set in main)\n'
     'FAST = False\nLIBPFX = "work_m2_"\n'),
    ('    return ("vsim -onfinish stop -gCACHE_CONFIG=%d -gMEMFILE=fw/%s.hex',
     '    return ("vsim -onfinish stop %s-gCACHE_CONFIG=%d -gMEMFILE=fw/%s.hex'),
    ('            % (p["cfg"], w, p["lines"], p["lines"], p["line_words"],',
     '            % ("-gCACHE_FAST_HIT=1 " if FAST else "", p["cfg"], w, p["lines"], p["lines"], p["line_words"],'),
    ('    lib = "work_m2_%d" % k\n', '    lib = "%s%d" % (LIBPFX, k)\n'),
    ('    ap.add_argument("--max-cycles", type=int, default=40000000)\n',
     '    ap.add_argument("--max-cycles", type=int, default=40000000)\n'
     '    ap.add_argument("--fast", action="store_true", help="R16 CACHE_FAST_HIT=1 (DSE / N-way points only)")\n'),
    ('    a = ap.parse_args()\n    pts = grid()\n',
     '    a = ap.parse_args()\n    global FAST, LIBPFX\n    FAST = a.fast\n    LIBPFX = "work_m2f_" if FAST else "work_m2_"\n'
     '    pts = grid()\n    if FAST:\n        pts = [p for p in pts if p["cfg"] != 0]\n'),
    ('            log = OUT / ("compile_m2_%d.log" % k)\n',
     '            log = OUT / ("compile_%s%d.log" % (LIBPFX[5:], k))\n'),
    ('"do scripts/m2/compile_m2_%d.do; quit -f" % k',
     '"do scripts/m2/compile_%s%d.do; quit -f" % (LIBPFX[5:], k)'),
    ('    logdir = OUT / ("logs_p%d" % a.pass_)\n',
     '    logdir = OUT / ("logs_%sp%d" % ("fast_" if FAST else "", a.pass_))\n'),
    ('    out = OUT / ("sweep_p%d.csv" % a.pass_)\n',
     '    out = OUT / ("sweep_%sp%d.csv" % ("fast_" if FAST else "", a.pass_))\n'),
])
edit("scripts/m2/make_compile_do.py", [
    ('n = int(sys.argv[1])\nfor k in range(1, n + 1):\n    lib = "work_m2_%d" % k\n',
     'n = int(sys.argv[1])\n# optional prefix: work_m2f_ for the R16 FAST_HIT libraries (compiled from the R16 hdl/)\npfx = sys.argv[2] if len(sys.argv) > 2 else "work_m2_"\nfor k in range(1, n + 1):\n    lib = "%s%d" % (pfx, k)\n'),
    ('    (ROOT / "scripts" / "m2" / ("compile_m2_%d.do" % k)).write_text(hdr + s, encoding="utf-8", newline="\\n")\n'
     '    print("wrote scripts/m2/compile_m2_%d.do (%d vlog commands)" % (k, nv))',
     '    (ROOT / "scripts" / "m2" / ("compile_%s.do" % lib[5:])).write_text(hdr + s, encoding="utf-8", newline="\\n")\n'
     '    print("wrote scripts/m2/compile_%s.do (%d vlog commands)" % (lib[5:], nv))'),
])
