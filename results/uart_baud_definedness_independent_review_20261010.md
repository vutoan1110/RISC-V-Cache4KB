# Independent UART baud definedness method review

The separate method review passes for the paired local UART baud proof.
It imports neither the UART proof checker nor the BHT RTLIL parser/evaluator.
A separate exact-top-module regex parser reads the original scalar decoder
cells and splits the original64-bit B binary constant into four MSB-first
16-bit words. It independently reconstructs the saved selector/data order.

Both saved proof receipts are still byte-identical and equal in every field;
no fields are ignored. Every source, raw IR, recipe, helper, control receipt
and checker hash pinned by the pair still matches. Current and signed source
case/default contracts and both UART parent-source bindings also match.

The original `$procmux$25626` at raw RTLIL line98143 has16-bit data,
four scalar selectors and undefined `A=16'x`. Its selectors compare exactly
the unsigned two-bit `cfg_reg[1:0]`, including the original logic-not zero
decoder. The raw wire declarations independently confirm32-bit `cfg_reg`,
16-bit `count_max`, and two-bit source `set_baud`; the original source-input
connection is the exact low configuration slice.

All four free codes00,01,10,11 select exactly one actual B word and reproduce
the exact source divisors20832,10416,5207,433. The default is never selected,
so all16 default data bits remain arbitrary without affecting the output.
No reset, initialization, state invariant, reachability premise or coercion
of source X to zero is used.

The independent evaluator recreates both raw in-memory semantic faults:
removing only the actual code3 selector makes defaults0 and65535 observable,
and reversing the actual selected16-bit B word changes433 to36224 while
retaining one active selector. Six additional controls reject wrong selector
width, signed comparison, changed configuration slice, undefined comparison
constant, changed source input width, and changed original config-wire width.
Controls have local supported-source/port/SigSpec scope; they do not claim a
mutated frontend correspondence or a reachable whole-chip counterexample.

The independent audit exited0 and peaked at56.16MiB under a hard256MiB
process cap. It starts no solver, frontend, WSL, simulator or hardware flow.
No source, RTL, frozen checker, proof receipt or shared document was changed.

With the earlier independent BHT review, this closes258 of the358 classified
GOLD functional X/Z connect lines and leaves100. Counts refer to connect
lines, not bits, defects or global equivalence obligations. Full sequential
LEC, whole-source undefined-value abstraction, source/event asynchronous
reset correspondence, raw N1/final arbitrary-state coupling and four-state
equivalence remain open.

Evidence:

- [Independent method receipt](uart_baud_definedness_independent_review_20261010.json).
- [Separate implementation](../scripts/verification/review_uart_baud_definedness.py).
- [Frozen paired proof and local scope](uart_baud_default_definedness_20261010.md).
- [Paired byte/field/hash comparison](uart_baud_default_definedness_20261010_verification.json),
  which retains its earlier pending-review snapshot.
- [Earlier independent BHT review/classification](bht_definedness_independent_review_20261010.md).

This later receipt resolves the earlier local UART method-review pending
status without rewriting the frozen pair or its dated comparison receipt.
