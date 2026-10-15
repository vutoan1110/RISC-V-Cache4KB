# Icache hot-array unused-default local proof

The three original Icache hot-array read `$pmux` A defaults are unused for
all Boolean three-bit indexes. Two independent sequential Windows CLI runs
produce byte-identical, all-field-identical proofs. A separate fresh parser
and MSB-first data-word interpreter independently replay the original source
bindings, all24 index cases and six local semantic fault controls. The later
method review passes without importing any existing RTLIL parser/evaluator
or the Icache proof checker.

The exact current/signed DM source chain binds the256-line Icache and
eight-entry L0 arrays. The controller main index is8 bits, the hot index3,
the hot tag25, the hot line128, and the miss-hot tag slice5. Source parameter
forwarding, array declarations, index expressions and three read accesses
match. The raw source connections bind request hot indexes to original
`pc_f[6:4]` and miss hot indexes to original `miss_index[2:0]`.

| Original cell | IR line | B slice selected | Width |
| --- | ---: | --- | ---: |
| `$procmux$22675` | 93615 | `hot_tag[hot_index]` | 25 |
| `$procmux$22684` | 93718 | `hot_line[hot_index]` | 128 |
| `$procmux$22693` | 93728 | `hot_tag[miss_hot_index][4:0]` | 5 |

Every actual decoder uses the full unsigned three-bit source slice and
covers codes0 through7 exactly once. Each actual B word/slice corresponds
to the source entry selected by that decoder, including actual concat bit
order. All raw index values and1,224 unique original array bit atoms remain
free. No initialization, reset, legal-state invariant, reachability relation
or source-X coercion is assumed.

The claim is only that these three A defaults do not enter the output
expression. Whole-Y definedness is explicitly **not claimed**: selected B
data may have other undefined origins, and every such data/state obligation
remains open. The5-bit reduced miss-tag read does not close the separate
20-bit unused/undefined high-slice origin.

Controls were frozen before the paired executions. For each mux, replacing
only actual selector7 with constant0 makes A selected at index7. Swapping
actual B words6 and7 changes the selected symbolic array word; a free-data
witness with the two words valued2 and1 gives original2 versus mutated1.
The separate implementation recreates these raw SigSpec faults and matches
the saved selector/B order. No mutated source/IR is written; no mutated
frontend correspondence or reachable full-chip trace is claimed.

Both proof processes exited0, each peaked below39MiB under a hard256MiB
process cap, and the independent review peaked below38MiB. No WSL,
frontend/synthesis, solver, simulator, flow, install or RTL edit was used.

Together with the reviewed BHT and UART baud results, this closes261 of358
classified GOLD functional X/Z connect lines and leaves97. Counts describe
connect lines, not bits, defects or whole-chip equivalence obligations.
Full sequential LEC, whole-source undefined abstraction, four-state
equivalence, raw N1/final arbitrary-state coupling and source/event reset
correspondence remain open.

Evidence:

- [Frozen checker](../scripts/verification/check_icache_hot_default_definedness.py)
  and [controls/input freeze](icache_hot_definedness_controls_20261010.json).
- [Pass1](icache_hot_default_definedness_20261010_p1.json) and
  [pass2](icache_hot_default_definedness_20261010_p2.json).
- [Paired and independent verification](icache_hot_default_definedness_20261010_verification.json).
- [Fresh independent reviewer](../scripts/verification/review_icache_hot_definedness.py)
  and [method receipt](icache_hot_definedness_independent_review_20261010.json).
- [Native execution record](icache_hot_definedness_execution_20261010.json).

Remaining97 lines comprise49 AXI SRAM-wrapper defaults, three cache-AXI
master defaults, eleven other UART defaults, seven `$mux` X connect lines,
and27 module X/Z connect lines. They were not tested as new hypotheses in
this experiment.
