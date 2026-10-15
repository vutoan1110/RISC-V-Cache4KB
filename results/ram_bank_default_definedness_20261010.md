# Local main-RAM bank default proof, 2026-10-10

Two independent native executions prove that exactly49 original main-RAM
`$pmux` A defaults are never selected for Boolean bank inputs. The
[paired verification](ram_bank_default_definedness_20261010_verification.json)
checks every field and byte; the
[separate method review](ram_bank_definedness_independent_review_20261010.json)
uses its own module-regex parser and MSB-first bit interpreter.

The checked targets are one eight-bank read-data mux and eight each of read
address, write address, write data, write mask, write enable and chip select.
Actual selector cones contain32 original equality/zero/OR-group cells. Every
target checks all eight values of its actual unsigned three-bit read or write
bank input:392 cases per pass. No reset, FSM, one-hot, reachability or initial
state assumption is imposed. Any unsupported selector dependence or uncovered
case would fail the check.

All398 original selected-B data-bit atoms stay arbitrary, including macro
outputs, prior combinational bank values and state. The exact current/signed
RAM source algorithms match. Instance bindings specialize4096 words to eight
512-word banks; bank indexes are three bits. Raw B-word order matches the
original bank/read/write role for every case. This is a proof of unused A,
**not whole-Y definedness or initialized RAM contents**.

Each pass also checks98 actual raw semantic controls. Clearing the selected
bit of a copied raw S SigSpec exposes A and produces different outputs for
all-zero/all-one defaults. Swapping raw selected B bits/words or substituting
another actual B word produces an independently evaluated data witness.
No mutation is written to source or IR. Pre-run controls freeze the checker
before the two main CLIs and reject malformed/signed/changed-width decoders.

The independent review reconstructs all49 cells, all392 case records, all98
mutations and the complete32-cell selector cone. It imports neither the
checker, inventory parser nor shared BHT SigSpec interpreter. Its first attempt
deterministically rejected an unrelated instruction-wire offset declaration;
the [preserved diagnostic](ram_bank_definedness_review_attempt_20261010.json)
records the traceback and source hash. Only the new reviewer was fixed to
record unrelated metadata while still rejecting its use in any target
expression. The frozen checker/pair never changed. The corrected review
returns exit0; no resource-fault claim is made.

Main passes: native exit0/0, peak working sets57.37/57.45MB under a hard256MiB
cap. Corrected independent review: native exit0, peak58.89MB. No frontend,
simulator, SAT solve, RTL edit, running-flow change or shared document edit.

With paired and independent acceptance, local unused-default closure becomes
**310 of358 original connect lines;48 remain**. The earlier97-row inventory
is an immutable prior snapshot. Remaining48 comprise14 other PMUX A defaults
(AXI3, TX8, RX3), seven regfile/tag-write mux connect lines and27 module
connects. Full sequential LEC, complete source-X abstraction, four-state
semantics, arbitrary initial-state coupling and reset/event/macro timing
remain OPEN. These counts are lines, not bits or hardware defects.

Evidence: [pass1](ram_bank_default_definedness_20261010_p1.json),
[pass2](ram_bank_default_definedness_20261010_p2.json),
[pre-run controls](ram_bank_definedness_controls_20261010.json),
[execution record](ram_bank_definedness_execution_20261010.json).
Reproduce with
[`check_ram_bank_default_definedness.py`](../scripts/verification/check_ram_bank_default_definedness.py),
[`review_ram_bank_definedness.py`](../scripts/verification/review_ram_bank_definedness.py)
and [`audit_ram_bank_definedness_pair.py`](../scripts/verification/audit_ram_bank_definedness_pair.py).
