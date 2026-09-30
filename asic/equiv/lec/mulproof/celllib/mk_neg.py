"""FLOW_JOURNAL Incident 89: write cells_neg.il = the fa64 module of cells.il with its C input tied to 0
(negative control for prove_cells.ys: the miter against the good fa64 must FAIL)."""
s = open("cells.il").read()
blk = s[s.index("module \\fa64"):s.index("module \\fa63")]
bad = blk.replace("    connect \\C \\c\n", "    connect \\C 64'0\n")
assert bad != blk
open("cells_neg.il", "w", newline="\n").write(
    "# FLOW_JOURNAL Incident 89 negative control: $fa with C tied to 0 (must NOT equal fa64)\n" + bad)
print("cells_neg.il written")
