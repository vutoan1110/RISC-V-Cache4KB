"""Host health check: EQY's read_ids() tokenisation (shlex.split per line) on a text file or on synthetic lines.

Tells a bad file from a failing interpreter or machine (NHAT_KY.md section 9, "Loi may"). With --synth N the probe
builds N valid lines of the same shape as an EQY .ids file and checks the token count of every line, so a silently
wrong result fails as well as a crash. Prints progress every 20k lines (flushed), so the line at a crash is known.

    python3 asic/parse_ids_probe.py <file.ids>
    python3 asic/parse_ids_probe.py --synth 300000      # health check: run 8x, expect 8x "OK"
"""
import shlex
import sys


def synth_lines(n):
    for i in range(n):
        yield ('modname obj%d w=7:0 A:src="/mnt/e/Projects/RISCV-research/hdl/apb_performance_monitor.v:94.6-94.14" '
               'P=I\n' % i)


if len(sys.argv) == 3 and sys.argv[1] == "--synth":
    lines, expect = synth_lines(int(sys.argv[2])), 5
else:
    lines, expect = open(sys.argv[1]), None
n = 0
for n, line in enumerate(lines, 1):
    toks = shlex.split(line)
    if expect is not None and (len(toks) != expect or toks[1] != "obj%d" % (n - 1)):
        print("CORRUPT line=%d tokens=%r" % (n, toks[:3]), flush=True)
        sys.exit(3)
    if n % 20000 == 0:
        print("at", n, flush=True)
print("OK lines=%d py=%s" % (n, sys.version.split()[0]), flush=True)
