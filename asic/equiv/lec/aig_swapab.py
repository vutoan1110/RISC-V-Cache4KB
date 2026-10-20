"""FLOW_JOURNAL Incident 89: swap the two 33-bit operand input groups of a pure multiplier AIG
(inputs 0..32 <-> 33..65), to test whether a structural mismatch is only the operand order (a*b vs b*a,
a transposed partial-product matrix). usage: python aig_swapab.py in.aig out.aig"""
import sys

import os
_here = os.path.dirname(os.path.abspath(__file__))
_src = open(os.path.join(_here, "mulsub.py")).read().split('if sys.argv[1] == "extract":')[0]
_src = _src.replace('__file__.replace("mulsub.py", "aigsim.py")', repr(os.path.join(_here, "aigsim.py")))
exec(_src)
I, outs, ands, ins, onames = read_aig(sys.argv[1])
assert I == 66
b = Builder(66)


def perm(v):          # input var v (1..66) -> swapped var
    k = v - 1
    return (k + 33 if k < 33 else k - 33) + 1


po = copy_cone(I, ands, outs, b, lambda v: 2 * perm(v) if v <= I else None)
b.write(sys.argv[2], po, ["A%d" % k for k in range(33)] + ["B%d" % k for k in range(33)], ["P%d" % k for k in range(64)])
print("%s: operands swapped, %d AND nodes" % (sys.argv[2], len(b.ands)))
