# Independent BHT source/IR review

The independent review passes for the frozen local BHT update and read
proofs. A separate module-scoped RTLIL parser and LSB-first SigSpec bit-vector
interpreter reconstruct the actual mux selectors and B data slices. The
reviewer imports no parser or evaluator from either BHT proof checker.

Both stored proof pairs remain byte-identical and equal in every decoded
field. Every pinned source, raw IR, recipe, and proof-helper hash still
matches. This review replays existing evidence; it starts no new frontend,
synthesis, simulator, solver, or flow.

For the read mux, the independent reconstruction checks all 256 unsigned
eight-bit addresses against the original `pc_f[9:2]` selector support and
the full 32-bit PC wire. Each address activates exactly one actual selector,
and its actual B slice consists of the matching two original table bits.
All 512 table bits remain symbolic and free.

For all 256 update muxes, the reconstruction checks every raw two-bit state
and both taken values. The 1,024 selector cases exclude the default without
an invariant. The 2,048 actual B-data evaluations also match the exact
current/signed source saturating update. The evaluator follows the original
shared `$mux` data cones and reduced single-bit output instead of assuming
that source-case order equals RTLIL concat order.

The saved negative controls have the stated local scope. Removing selector255
or state3 makes the corresponding local undefined default observable;
arbitrary default values0 and3 produce distinct copied-mux outputs.
Removing source state11 changes the actual taken1 source output from3 to
the explicit default1. Removing the final table entry makes index255 out
of range. No mutated frontend equivalence or whole-chip reachable trace is
asserted by these controls.

The independent parser has 18 finite controls for original-bit slicing,
nested concat order, constants/X markers, malformed SigSpecs, unsigned
selectors, and selector width rejection. A first preflight failed because
the new parser initially used global wire names across SRAM blackbox and
top modules. The failure and diagnosis remain saved. Only the new idle
reviewer was corrected to select exactly `soc_asic_top`; frozen proofs and
source files were unchanged. The successful audit peaked at56.94MiB under
a hard256MiB process cap.

Full sequential LEC, whole-source undefined-value abstraction, source/event
asynchronous reset correspondence, raw N1/final arbitrary-state coupling,
and four-state equivalence remain open. The 257 locally closed BHT connect
lines are not a whole-chip equivalence proof.

## Exact remaining GOLD classification

The reviewer directly classifies all original top-module functional X/Z
connect lines, excluding attributes. There are358 lines in total; subtracting
the256 update defaults and one read default leaves101 lines:

| Category | Connect lines | Scope still required |
| --- | ---: | --- |
| AXI SRAM wrapper `$pmux` defaults | 49 | Exact three-bit bank decoder/complement coverage and actual data ordering, including grouped `reduce_or` selectors |
| Icache hot-array `$pmux` defaults | 3 | Exact three-bit array-index coverage and original array/source correspondence |
| Cache AXI master `$pmux` defaults | 3 | Queue selector/reset-mux complementary coverage or consumer enable proof; raw states cannot be assumed equal |
| UART baud `$pmux` default | 1 | Exact free two-bit configuration decode and divisor-data correspondence |
| UART TX `$pmux` defaults | 8 | Source cases, grouped decoders, and original configuration/state cones |
| UART RX `$pmux` defaults | 3 | Configuration cases and parity selector cone |
| Regfile `$mux` X connections | 3 in two cells | Write-enable/consumer observability or exact no-consumer proof |
| Icache/Dcache tag-write `$mux` X connections | 4 in four cells | Disabled write-data/address sink proof |
| Module X/Z connections | 27 | 25 function temporaries plus two narrowed slices; verify every consumer/output sink before treating any as dead |

These counts are connect lines, not bit counts, defects, or discharged global
equivalence obligations. The JSON receipt contains every original line,
cell, port, source attribute and exact classification.

## Next bounded opportunity

The smallest independent next target is UART `count_max`, cell
`$procmux$25626` at original RTLIL line98143: `WIDTH=16`, `S_WIDTH=4`,
`A=16'x`. Its actual unsigned two-bit selectors compare `cfg_reg[1:0]`
against00,01,10,11. The source case explicitly specifies all four divisors.
A separate single-hypothesis proof can check those actual selectors and
data slices with all four configuration codes free, including a copied
missing-selector and changed-data-bit-order negative control. This is a
candidate until its independent paired execution and review finish.

The three Icache hot-array defaults at lines93615,93718,93728 also expose
complete unsigned three-bit0..7 decoder populations. They are later
opportunities and remain open here. The49 SRAM wrapper defaults should
receive one exact shared-bank-decoder hypothesis with checked grouped
selectors, rather than independent speculative coercions.

## Evidence

- [Independent review receipt](bht_definedness_independent_review_20261010.json).
- [Independent reviewer](../scripts/verification/review_bht_definedness.py).
- [Finite parser controls](bht_definedness_independent_parser_controls_20261010.json)
  and [control script](../scripts/verification/check_bht_review_parser_controls.py).
- [Retained preflight diagnosis](bht_definedness_review_preflight_20261010.json)
  and [traceback](bht_definedness_review_preflight_20261010_error.log).
- [Frozen read proof/scope](bht_read_default_definedness_20261010.md).
- [Frozen update and restricted-cut scope](lec_source_definedness_20261010.md).
